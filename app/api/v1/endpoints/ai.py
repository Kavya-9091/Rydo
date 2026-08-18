import uuid
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.orchestration.orchestrator import AIOrchestrator
from app.ai.multi_agent import MultiAgentRideAssistant
from app.ai.providers.factory import get_llm_provider
from app.ai.tool_calling.schemas import ToolExecutionContext
from app.ai.tool_calling.tools import create_ride_tool_registry
from app.api.deps import get_current_user, get_db
from app.core.settings import get_settings
from app.infrastructure.database.models.ai_conversation_model import AIConversationModel
from app.infrastructure.database.models.user_model import UserModel
from app.schemas.requests.ai_requests import AIChatRequest, AIMessageRequest, TripSummaryRequest
from app.schemas.responses.ai_responses import AIChatResponse, AIConversationResponse, AIProviderStatusResponse

router = APIRouter(prefix="/ai", tags=["AI"])
logger = logging.getLogger(__name__)


@router.get("/provider-status", response_model=AIProviderStatusResponse)
def provider_status(current_user: UserModel = Depends(get_current_user)) -> AIProviderStatusResponse:
    settings = get_settings()
    if settings.ai_default_provider == "claude":
        return AIProviderStatusResponse(
            provider="claude",
            configured=bool(settings.anthropic_api_key),
            model=settings.anthropic_model,
        )
    return AIProviderStatusResponse(
        provider="openai",
        configured=bool(settings.openai_api_key),
        model=settings.openai_model,
    )


@router.post("/chat", response_model=AIChatResponse)
async def chat(
    request_body: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> AIChatResponse:
    try:
        response = await MultiAgentRideAssistant(
            llm=get_llm_provider(),
            registry=create_ride_tool_registry(),
        ).run(
            request_body.message,
            ToolExecutionContext(db=db, user=current_user, request_context=request_body.context),
        )
        status_value = "completed"
    except Exception as exc:
        logger.exception("ai_chat_failed")
        response = type(
            "FallbackResponse",
            (),
            {
                "content": "I could not connect to the live AI model right now. Please try again in a moment, or use the Book screen to continue.",
                "metadata": {"provider": "error_fallback", "error": exc.__class__.__name__},
            },
        )()
        status_value = "failed"

    metadata = response.metadata
    conversation = AIConversationModel(
        user_id=current_user.id,
        conversation_type="ride_booking",
        user_message=request_body.message,
        assistant_message=response.content,
        metadata_json=metadata,
        status=status_value,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    tool_executed, ride_id = _extract_chat_tool_metadata(metadata)
    return AIChatResponse(
        reply=response.content,
        toolExecuted=tool_executed,
        rideId=ride_id,
        conversationId=conversation.id,
        metadata=metadata,
    )


@router.post("/booking-assistant", response_model=AIConversationResponse)
async def booking_assistant(
    request_body: AIMessageRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> AIConversationResponse:
    try:
        response = await MultiAgentRideAssistant(
            llm=get_llm_provider(),
            registry=create_ride_tool_registry(),
        ).run(
            request_body.message,
            ToolExecutionContext(db=db, user=current_user),
        )
    except Exception as exc:
        logger.exception("ai_booking_assistant_failed")
        response = type(
            "FallbackResponse",
            (),
            {
                "content": "I could not connect to the live AI model right now. Please try again in a moment, or use the Book screen to continue.",
                "metadata": {"provider": "error_fallback", "error": exc.__class__.__name__},
            },
        )()
    conversation = AIConversationModel(
        user_id=current_user.id,
        conversation_type="ride_booking",
        user_message=request_body.message,
        assistant_message=response.content,
        metadata_json=response.metadata,
        status="completed",
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return AIConversationResponse.model_validate(conversation)


def _extract_chat_tool_metadata(metadata: dict | None) -> tuple[str | None, uuid.UUID | None]:
    if not metadata:
        return None, None

    tool_results = metadata.get("tool_results")
    if not isinstance(tool_results, list) or not tool_results:
        return None, None

    first_result = tool_results[0]
    if not isinstance(first_result, dict):
        return None, None

    tool_name = first_result.get("tool")
    ride_id = None
    result = first_result.get("result")
    if isinstance(result, dict):
        data = result.get("data")
        if isinstance(data, dict) and data.get("ride_id"):
            try:
                ride_id = uuid.UUID(str(data["ride_id"]))
            except ValueError:
                ride_id = None

    return str(tool_name) if tool_name else None, ride_id


@router.post("/support", response_model=AIConversationResponse)
async def customer_support(
    request_body: AIMessageRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> AIConversationResponse:
    response = await AIOrchestrator().run("customer_support", request_body.message)
    conversation = AIConversationModel(
        user_id=current_user.id,
        conversation_type="customer_support",
        user_message=request_body.message,
        assistant_message=response.content,
        metadata_json=response.metadata,
        status="completed",
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return AIConversationResponse.model_validate(conversation)


@router.post("/rides/{ride_id}/summary", response_model=AIConversationResponse)
async def trip_summary(
    ride_id: uuid.UUID,
    request_body: TripSummaryRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> AIConversationResponse:
    message = request_body.ride_notes or f"Generate a customer-friendly summary for ride {ride_id}."
    response = await AIOrchestrator().run("trip_summary", message)
    conversation = AIConversationModel(
        user_id=current_user.id,
        ride_id=ride_id,
        conversation_type="trip_summary",
        user_message=message,
        assistant_message=response.content,
        metadata_json=response.metadata,
        status="completed",
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return AIConversationResponse.model_validate(conversation)
