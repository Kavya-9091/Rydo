import json
from dataclasses import dataclass
from typing import Any

from app.ai.providers.base import LLMProvider
from app.ai.schemas import ChatMessage, LLMResponse
from app.ai.tool_calling.entity_extractor import extract_entities
from app.ai.tool_calling.registry import ToolRegistry
from app.ai.tool_calling.schemas import ToolExecutionContext

SYSTEM_PROMPT = """
You are an AI Ride Assistant for a ride booking platform.
Follow this flow:
1. Understand the user's intent.
2. Extract entities: pickup, destination, ride time, vehicle type, ride id, payment id, rating.
3. Choose exactly the right tool when a real backend action or lookup is needed.
4. If required information is missing, ask one concise follow-up question instead of calling a tool.
5. After tool execution, explain the result naturally.
Never claim an action succeeded unless a tool result says success=true.
If pickup coordinates, destination coordinates, ride time, or vehicle type is missing for booking, ask a concise clarification.
Valid vehicle types: bike, auto, mini, sedan, suv, luxury.
Return clear, friendly responses.
""".strip()


@dataclass(frozen=True)
class OrchestrationStep:
    name: str
    status: str
    details: dict[str, Any]


class RideAssistantOrchestrator:
    def __init__(self, llm: LLMProvider, registry: ToolRegistry) -> None:
        self._llm = llm
        self._registry = registry

    async def run(self, user_message: str, context: ToolExecutionContext) -> LLMResponse:
        entities = _entities_with_memory(user_message, context.request_context)
        _apply_request_context(entities, context.request_context, user_message)
        steps: list[OrchestrationStep] = [
            OrchestrationStep(
                name="receive_message",
                status="completed",
                details={"message_length": len(user_message)},
            ),
            OrchestrationStep(
                name="extract_entities",
                status="completed" if not entities.missing_fields else "partial",
                details=entities.as_prompt_context(),
            )
        ]
        deterministic_response = self._try_deterministic_tool_execution(entities, context, steps)
        if deterministic_response:
            return deterministic_response

        messages = [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(
                role="user",
                content=(
                    f"User message: {user_message}\n\n"
                    f"Pre-extracted entities:\n{json.dumps(entities.as_prompt_context(), default=str)}\n\n"
                    "Use the extracted values when calling tools. If missing_fields is not empty, ask for those details."
                ),
            ),
        ]
        planning_response = await self._llm.generate_with_tools(messages, self._registry.definitions())
        steps.append(
            OrchestrationStep(
                name="plan_intent_and_tools",
                status="completed",
                details={
                    "tool_call_count": len(planning_response.tool_calls),
                    "tools": [call.name for call in planning_response.tool_calls],
                    "provider": planning_response.metadata.get("provider"),
                },
            )
        )
        if not planning_response.tool_calls:
            planning_response.metadata["orchestration_steps"] = [_step_data(step) for step in steps]
            return planning_response

        tool_payloads = []
        for call in planning_response.tool_calls:
            result = self._registry.execute(call.name, call.arguments, context)
            payload = {"tool_call_id": call.id, "tool": call.name, "arguments": call.arguments, "result": result.model_dump()}
            tool_payloads.append(payload)
            steps.append(
                OrchestrationStep(
                    name="execute_tool",
                    status="completed" if result.success else "failed",
                    details={
                        "tool": call.name,
                        "success": result.success,
                        "message": result.message,
                    },
                )
            )

        final_messages = messages + [
            ChatMessage(role="assistant", content=planning_response.content or "I will use a backend tool to help with that."),
            ChatMessage(
                role="user",
                content=(
                    f"Tool results:\n{json.dumps(tool_payloads, default=str)}\n\n"
                    "Respond to the customer naturally. If a tool failed because fields are missing, ask for only the missing fields."
                ),
            ),
        ]
        final_response = await self._llm.generate(final_messages, temperature=0.2)
        steps.append(
            OrchestrationStep(
                name="generate_final_response",
                status="completed",
                details={"provider": final_response.metadata.get("provider")},
            )
        )
        final_response.metadata["tool_results"] = tool_payloads
        final_response.metadata["orchestration_steps"] = [_step_data(step) for step in steps]
        return final_response

    def _try_deterministic_tool_execution(
        self,
        entities: Any,
        context: ToolExecutionContext,
        steps: list[OrchestrationStep],
    ) -> LLMResponse | None:
        if entities.intent == "general":
            return None
        if entities.missing_fields:
            steps.append(
                OrchestrationStep(
                    name="ask_follow_up",
                    status="completed",
                    details={"missing_fields": entities.missing_fields},
                )
            )
            return LLMResponse(
                content=_follow_up_message(entities.missing_fields),
                metadata={
                    "provider": "deterministic_orchestrator",
                    "intent": entities.intent,
                    "orchestration_steps": [_step_data(step) for step in steps],
                },
            )

        tool_name = entities.intent
        arguments = _tool_arguments_from_entities(entities)
        result = self._registry.execute(tool_name, arguments, context)
        steps.append(
            OrchestrationStep(
                name="execute_tool",
                status="completed" if result.success else "failed",
                details={"tool": tool_name, "success": result.success, "message": result.message},
            )
        )
        tool_payload = {
            "tool_call_id": f"deterministic-{tool_name}",
            "tool": tool_name,
            "arguments": arguments,
            "result": result.model_dump(),
        }
        return LLMResponse(
            content=_tool_response_message(tool_name, result),
            metadata={
                "provider": "deterministic_orchestrator",
                "intent": entities.intent,
                "tool_results": [tool_payload],
                "orchestration_steps": [_step_data(step) for step in steps],
            },
        )


def _step_data(step: OrchestrationStep) -> dict[str, Any]:
    return {"name": step.name, "status": step.status, "details": step.details}


def _entities_with_memory(user_message: str, request_context: dict[str, Any]) -> Any:
    history = request_context.get("chat_history") if isinstance(request_context, dict) else None
    if not isinstance(history, list):
        return extract_entities(user_message)

    user_messages = [
        str(item.get("content", "")).strip()
        for item in history[-8:]
        if isinstance(item, dict) and item.get("role") == "user" and str(item.get("content", "")).strip()
    ]
    extracted_messages = [extract_entities(message) for message in user_messages + [user_message]]
    current = extracted_messages[-1]
    if current.intent in {"start_ride", "complete_ride", "reject_ride", "accept_ride"} and not current.ride_id:
        current.ride_id = _latest_ride_id_from_context(request_context)
    if current.intent == "general" and not current.vehicle_type and _looks_like_continuation(user_message):
        for previous in reversed(extracted_messages[:-1]):
            if previous.intent != "general":
                current.intent = previous.intent
                break

    if not _has_explicit_route(user_message):
        for previous in extracted_messages[:-1]:
            if previous.intent != "book_ride":
                continue
            if current.intent == "general":
                current.intent = "book_ride"
            _merge_missing_booking_value(current, previous)

    current.missing_fields = _recompute_missing_fields(current)
    return current


def _looks_like_continuation(message: str) -> bool:
    normalized = message.strip().lower()
    if not normalized:
        return False
    if _has_explicit_route(normalized):
        return False
    if len(normalized.split()) <= 5:
        return True
    return bool(__import__("re").search(r"\b(current location|my location|pickup|destination|drop|bike|auto|mini|sedan|suv|luxury)\b", normalized))


def _has_explicit_route(message: str) -> bool:
    normalized = message.strip().lower()
    if __import__("re").search(r"\bfrom\s+.+?\s+\bto\s+.+", normalized):
        return True
    return bool(
        __import__("re").search(
            r"\bpickup(?:\s+location)?\s*:.+?(?:drop|dropoff|drop-off|destination|destinantion)(?:\s+location)?\s*:",
            normalized,
        )
    )


def _merge_missing_booking_value(target: Any, source: Any) -> None:
    if not target.pickup and source.pickup:
        target.pickup = source.pickup
        target.pickup_latitude = source.pickup_latitude
        target.pickup_longitude = source.pickup_longitude
    if not target.destination and source.destination:
        target.destination = source.destination
        target.dropoff_latitude = source.dropoff_latitude
        target.dropoff_longitude = source.dropoff_longitude
    if not target.vehicle_type and source.vehicle_type:
        target.vehicle_type = source.vehicle_type
    if not target.ride_time and source.ride_time:
        target.ride_time = source.ride_time


def _latest_ride_id_from_context(request_context: dict[str, Any]) -> str | None:
    history = request_context.get("chat_history") if isinstance(request_context, dict) else None
    if not isinstance(history, list):
        return None
    for item in reversed(history[-12:]):
        if not isinstance(item, dict):
            continue
        content = str(item.get("content", ""))
        match = __import__("re").search(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            content,
        )
        if match:
            return match.group(0)
    return None


def _apply_request_context(entities: Any, request_context: dict[str, Any], user_message: str) -> None:
    lower = user_message.lower()
    booking_context = request_context.get("booking") if isinstance(request_context, dict) else None
    if not isinstance(booking_context, dict):
        return

    pickup = booking_context.get("pickup")
    destination = booking_context.get("destination")
    vehicle_type = booking_context.get("vehicle_type")

    if ("current location" in lower or "my location" in lower) and isinstance(pickup, dict):
        _fill_pickup(entities, pickup)
    if entities.intent == "book_ride":
        if not entities.pickup and isinstance(pickup, dict):
            _fill_pickup(entities, pickup)
        if not entities.destination and isinstance(destination, dict):
            _fill_destination(entities, destination)
        if not entities.vehicle_type and isinstance(vehicle_type, str):
            entities.vehicle_type = vehicle_type

    entities.missing_fields = _recompute_missing_fields(entities)


def _fill_pickup(entities: Any, pickup: dict[str, Any]) -> None:
    entities.pickup = pickup.get("displayName") or pickup.get("display_name")
    entities.pickup_latitude = pickup.get("latitude")
    entities.pickup_longitude = pickup.get("longitude")


def _fill_destination(entities: Any, destination: dict[str, Any]) -> None:
    entities.destination = destination.get("displayName") or destination.get("display_name")
    entities.dropoff_latitude = destination.get("latitude")
    entities.dropoff_longitude = destination.get("longitude")


def _recompute_missing_fields(entities: Any) -> list[str]:
    if entities.intent != "book_ride":
        return entities.missing_fields
    required = {
        "pickup": entities.pickup,
        "pickup_coordinates": entities.pickup_latitude is not None and entities.pickup_longitude is not None,
        "destination": entities.destination,
        "destination_coordinates": entities.dropoff_latitude is not None and entities.dropoff_longitude is not None,
        "vehicle_type": entities.vehicle_type,
        "ride_time": entities.ride_time,
    }
    return [field for field, value in required.items() if not value]


def _tool_arguments_from_entities(entities: Any) -> dict[str, Any]:
    return {
        "pickup_address": entities.pickup,
        "pickup_latitude": entities.pickup_latitude,
        "pickup_longitude": entities.pickup_longitude,
        "dropoff_address": entities.destination,
        "dropoff_latitude": entities.dropoff_latitude,
        "dropoff_longitude": entities.dropoff_longitude,
        "ride_time": entities.ride_time,
        "vehicle_type": entities.vehicle_type,
        "ride_id": entities.ride_id,
        "payment_id": entities.payment_id,
        "rating": entities.rating,
        "registration_numbers": entities.registration_numbers,
    }


def _follow_up_message(missing_fields: list[str]) -> str:
    labels = {
        "pickup": "pickup location",
        "pickup_coordinates": "pickup location",
        "destination": "destination",
        "destination_coordinates": "destination",
        "vehicle_type": "vehicle type",
        "ride_time": "ride time",
        "ride_id": "ride ID",
        "rating": "rating",
    }
    readable = []
    for field in missing_fields:
        label = labels.get(field, field.replace("_", " "))
        if label not in readable:
            readable.append(label)
    if len(readable) == 1:
        return f"Sure, please share the {readable[0]}."
    return f"Sure, please share the {', '.join(readable[:-1])}, and {readable[-1]}."


def _tool_response_message(tool_name: str, result: Any) -> str:
    if not result.success:
        return result.message
    data = result.data or {}
    if tool_name == "book_ride":
        fare = data.get("estimated_fare")
        ride_id = data.get("ride_id")
        return (
            f"Your {data.get('vehicle_type', 'ride')} ride has been requested from "
            f"{data.get('pickup_address')} to {data.get('dropoff_address')}. "
            f"Estimated fare is INR {fare}. Ride ID: {ride_id}. Waiting for driver acceptance."
        )
    if tool_name == "estimate_fare":
        return f"Estimated fare is INR {data.get('estimated_fare')} for about {data.get('distance_km')} km."
    if tool_name == "nearest_driver":
        return f"Nearest driver is about {data.get('distance_km')} km away and should reach in {data.get('eta_minutes')} minutes."
    if tool_name == "accept_ride":
        return f"Ride accepted. Ride ID: {data.get('ride_id')}. Head to {data.get('pickup_address')} for pickup."
    if tool_name == "reject_ride":
        return f"Ride rejected. Ride ID: {data.get('ride_id')}. We will look for another driver."
    if tool_name == "start_ride":
        return f"Ride started. Ride ID: {data.get('ride_id')}. Drive safely to {data.get('dropoff_address')}."
    if tool_name == "complete_ride":
        return f"Ride completed. Ride ID: {data.get('ride_id')}. Final fare is INR {data.get('final_fare') or data.get('estimated_fare')}. The customer can pay now."
    if tool_name == "approve_vehicles":
        approved = data.get("approved") or []
        not_found = data.get("not_found") or []
        message = f"Approved vehicles: {', '.join(approved)}." if approved else "No vehicles were approved."
        if not_found:
            message += f" Not found: {', '.join(not_found)}."
        return message
    return result.message
