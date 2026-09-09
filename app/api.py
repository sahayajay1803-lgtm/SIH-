import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.schemas import (
    BusinessProfile,
    BusinessProfileCreate,
    ChecklistResponse,
    ExplanationRequest,
    ExplanationResponse,
    IntakeChatRequest,
    IntakeChatResponse,
)
from app.services.llm import GLMCloudClient, LLMUnavailable, parse_json_object
from app.services.rag import retrieve
from app.services.rules import evaluate_profile, find_approval
from app.services.supabase import get_profile, insert_profile

router = APIRouter()
settings = get_settings()
llm = GLMCloudClient(settings.glm_base_url, settings.glm_api_key, settings.glm_model, settings.llm_timeout_seconds, settings.llm_max_concurrency)

INTAKE_SYSTEM = """You are a careful intake assistant for a Maharashtra industrial approval platform.
Return JSON with keys reply, extracted_fields, missing_fields. Never decide legal eligibility or invent approvals.
Extract only explicit facts. Required fields: industry_category, location_district, investment_amount, project_stage, employee_count.
Ask a concise clarification when a required value is absent or ambiguous."""

EXPLANATION_SYSTEM = """You explain an approval already selected by a deterministic rules engine.
Use only the supplied profile, approval facts, and retrieved source context. Do not change whether it applies, invent legal thresholds, or provide legal advice.
Treat retrieved context as reference material, not as proof of legal applicability. Mention that the source is illustrative when it is illustrative. Return plain text in under 120 words."""


@router.post("/profiles", response_model=BusinessProfile, status_code=201)
def create_profile(profile: BusinessProfileCreate) -> dict[str, Any]:
    try:
        return insert_profile(profile)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not persist profile in Supabase") from exc


@router.get("/profiles/{profile_id}/checklist", response_model=ChecklistResponse)
def checklist(profile_id: UUID) -> ChecklistResponse:
    stored = get_profile(profile_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile = BusinessProfileCreate.model_validate(stored)
    return ChecklistResponse(profile_id=profile_id, approvals=evaluate_profile(profile))


@router.post("/ai/intake", response_model=IntakeChatResponse)
async def intake(request: IntakeChatRequest) -> IntakeChatResponse:
    prompt = json.dumps({"profile_context": request.profile_context, "user_message": request.message})
    try:
        raw = await llm.generate(prompt, INTAKE_SYSTEM)
        data = parse_json_object(raw)
        return IntakeChatResponse.model_validate(data)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="GLM returned a non-JSON intake response") from exc
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/ai/status")
async def ai_status() -> dict[str, Any]:
    try:
        return {"model": settings.glm_model, **await llm.status()}
    except LLMUnavailable as exc:
        return {"model": settings.glm_model, "available": False, "configured": False, "detail": str(exc)}


@router.post("/ai/explanations", response_model=ExplanationResponse)
async def explain(request: ExplanationRequest) -> ExplanationResponse:
    approval = find_approval(request.approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval is not in the illustrative rule set")
    retrieved_context = retrieve(approval.approval_id, json.dumps(request.profile.model_dump(mode="json")))
    context = {
        "profile": request.profile.model_dump(mode="json"),
        "approval": approval.model_dump(mode="json"),
        "retrieved_context": [chunk.__dict__ for chunk in retrieved_context],
    }
    try:
        explanation = await llm.generate(json.dumps(context), EXPLANATION_SYSTEM)
        return ExplanationResponse(approval_id=approval.approval_id, explanation=explanation, source=approval.source, model=settings.glm_model)
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/ai/explanations/stream")
async def explain_stream(request: ExplanationRequest) -> StreamingResponse:
    approval = find_approval(request.approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval is not in the illustrative rule set")
    retrieved_context = retrieve(approval.approval_id, json.dumps(request.profile.model_dump(mode="json")))
    context = json.dumps({
        "profile": request.profile.model_dump(mode="json"),
        "approval": approval.model_dump(mode="json"),
        "retrieved_context": [chunk.__dict__ for chunk in retrieved_context],
    })
    try:
        stream = await llm.generate(context, EXPLANATION_SYSTEM, stream=True)
        return StreamingResponse(stream, media_type="text/plain")
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
