from dataclasses import dataclass
from typing import Protocol

from app.ai.providers.base import LLMProvider
from app.ai.schemas import LLMResponse
from app.ai.tool_calling.entity_extractor import extract_entities
from app.ai.tool_calling.orchestrator import RideAssistantOrchestrator
from app.ai.tool_calling.registry import ToolRegistry
from app.ai.tool_calling.schemas import ToolExecutionContext


@dataclass(frozen=True)
class AgentRoute:
    agent_name: str
    reason: str


class RideSpecialistAgent(Protocol):
    name: str

    async def run(self, message: str, context: ToolExecutionContext) -> LLMResponse:
        raise NotImplementedError


class ToolCallingSpecialistAgent:
    def __init__(self, *, name: str, llm: LLMProvider, registry: ToolRegistry) -> None:
        self.name = name
        self._orchestrator = RideAssistantOrchestrator(llm=llm, registry=registry)

    async def run(self, message: str, context: ToolExecutionContext) -> LLMResponse:
        response = await self._orchestrator.run(message, context)
        response.metadata["agent"] = self.name
        return response


class VehicleRegistrationAgent:
    name = "vehicle_agent"

    async def run(self, message: str, context: ToolExecutionContext) -> LLMResponse:
        if getattr(context.user, "role", None) != "driver":
            return LLMResponse(
                content="Vehicle registration is available for driver accounts. Please log in as a driver to continue.",
                metadata={"provider": "deterministic_agent", "agent": self.name, "intent": "register_vehicle"},
            )
        return LLMResponse(
            content=(
                "To register a vehicle, use the Register vehicle section on the Driver Dashboard. "
                "Choose the vehicle type, make, model, and color, enter the registration number and capacity, "
                "then submit it for admin approval."
            ),
            metadata={"provider": "deterministic_agent", "agent": self.name, "intent": "register_vehicle"},
        )


class RoleGuardAgent:
    name = "role_guard_agent"

    async def run(self, message: str, context: ToolExecutionContext) -> LLMResponse:
        role = str(getattr(context.user, "role", "") or "").lower()
        return LLMResponse(
            content=(
                f"You are logged in as a {role or 'non-customer'} account. "
                "Ride booking is available only from a customer account. Please log in as a customer to book a ride."
            ),
            metadata={"provider": "deterministic_agent", "agent": self.name, "intent": "blocked_customer_booking", "blocked_role": role},
        )


class SupervisorAgent:
    def route(self, message: str, context: ToolExecutionContext) -> AgentRoute:
        role = str(getattr(context.user, "role", "") or "").lower()
        lower = message.lower()
        entities = extract_entities(message)

        if _is_vehicle_registration_intent(lower):
            return AgentRoute("vehicle_agent", "driver_vehicle_registration")

        if role != "customer" and entities.intent in {"book_ride", "cancel_ride", "rate_ride"}:
            return AgentRoute("role_guard_agent", f"customer_only_intent:{role}:{entities.intent}")

        if role == "admin" or entities.intent == "approve_vehicles":
            return AgentRoute("admin_agent", f"role_or_intent:{role}:{entities.intent}")

        if entities.intent in {"accept_ride", "reject_ride", "start_ride", "complete_ride", "nearest_driver", "get_driver_location"}:
            return AgentRoute("driver_agent", f"driver_intent:{entities.intent}")

        if entities.intent in {"payment_status"} or _is_payment_intent(lower):
            return AgentRoute("payment_agent", f"payment_intent:{entities.intent}")

        if entities.intent in {"book_ride", "cancel_ride", "get_ride_status", "ride_history", "estimate_fare", "rate_ride"}:
            return AgentRoute("booking_agent", f"ride_intent:{entities.intent}")

        if _is_support_intent(lower):
            return AgentRoute("support_agent", "support_keywords")

        return AgentRoute("support_agent", "general_message")


class MultiAgentRideAssistant:
    def __init__(self, *, llm: LLMProvider, registry: ToolRegistry) -> None:
        self._supervisor = SupervisorAgent()
        self._agents: dict[str, RideSpecialistAgent] = {
            "booking_agent": ToolCallingSpecialistAgent(name="booking_agent", llm=llm, registry=registry),
            "driver_agent": ToolCallingSpecialistAgent(name="driver_agent", llm=llm, registry=registry),
            "payment_agent": ToolCallingSpecialistAgent(name="payment_agent", llm=llm, registry=registry),
            "admin_agent": ToolCallingSpecialistAgent(name="admin_agent", llm=llm, registry=registry),
            "support_agent": ToolCallingSpecialistAgent(name="support_agent", llm=llm, registry=registry),
            "vehicle_agent": VehicleRegistrationAgent(),
            "role_guard_agent": RoleGuardAgent(),
        }

    async def run(self, message: str, context: ToolExecutionContext) -> LLMResponse:
        route = self._supervisor.route(message, context)
        agent = self._agents[route.agent_name]
        response = await agent.run(message, context)
        response.metadata["multi_agent"] = {
            "supervisor": "supervisor_agent",
            "selected_agent": route.agent_name,
            "route_reason": route.reason,
        }
        return response


def _is_vehicle_registration_intent(lower: str) -> bool:
    return (
        ("register" in lower or "add" in lower or "create" in lower or "submit" in lower)
        and any(word in lower for word in ["vehicle", "bike", "auto", "car", "sedan", "suv"])
    )


def _is_payment_intent(lower: str) -> bool:
    return any(phrase in lower for phrase in ["pay now", "make payment", "payment", "paid"])


def _is_support_intent(lower: str) -> bool:
    return any(word in lower for word in ["help", "support", "issue", "problem", "refund", "faq", "question"])
