import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.schemas import (
    BusinessProfile,
    BusinessProfileCreate,
    ChecklistResponse,
    DocumentReview,
    ExplanationRequest,
    ExplanationResponse,
    IntakeChatRequest,
    IntakeChatResponse,
    MaitriSubmissionResponse,
    SchemeListResponse,
    SchemeMatchResponse,
)
from app.services.document_review import extract_document, review_document
from app.services.llm import LLMUnavailable, OllamaCloudClient, parse_json_object
from app.services.maitri import submit_to_mock_maitri
from app.services.rag import retrieve
from app.services.rules import evaluate_profile, find_approval
from app.services.schemes import list_schemes, match_schemes
from app.services.supabase import get_profile, insert_profile

router = APIRouter()
settings = get_settings()
llm = OllamaCloudClient(settings.ollama_base_url, settings.ollama_api_key, settings.ollama_model, settings.llm_timeout_seconds, settings.llm_max_concurrency)

INTAKE_SYSTEM = """You are a careful intake assistant for a Maharashtra industrial approval platform.
Return JSON with keys reply, extracted_fields, missing_fields. Never decide legal eligibility or invent approvals.
Extract only explicit facts. Required fields: industry_category, location_district, investment_amount, project_stage, employee_count.
Ask a concise clarification when a required value is absent or ambiguous."""

EXPLANATION_SYSTEM = """You explain an approval already selected by a deterministic rules engine.
Use only the supplied profile, approval facts, and retrieved source context. Do not change whether it applies, invent legal thresholds, or provide legal advice.
Treat retrieved context as reference material, not as proof of legal applicability. Mention that the source is illustrative when it is illustrative. Return plain text in under 120 words."""

ALLOWED_DOCUMENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}


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


@router.get("/schemes", response_model=SchemeListResponse)
def schemes(search: str = "", government_level: str | None = None, category: str | None = None, page: int = 1, page_size: int = 20) -> SchemeListResponse:
    if page < 1 or page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="page must be positive and page_size must be between 1 and 100")
    results = list_schemes(search, government_level, category)
    start = (page - 1) * page_size
    return SchemeListResponse(items=results[start : start + page_size], total=len(results), page=page, page_size=page_size)


@router.get("/profiles/{profile_id}/schemes", response_model=SchemeMatchResponse)
def profile_schemes(profile_id: UUID) -> SchemeMatchResponse:
    stored = get_profile(profile_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile = BusinessProfileCreate.model_validate(stored)
    return SchemeMatchResponse(profile_id=profile_id, matches=match_schemes(profile))


@router.post("/ai/intake", response_model=IntakeChatResponse)
async def intake(request: IntakeChatRequest) -> IntakeChatResponse:
    prompt = json.dumps({"profile_context": request.profile_context, "user_message": request.message})
    try:
        raw = await llm.generate(prompt, INTAKE_SYSTEM)
        data = parse_json_object(raw)
        return IntakeChatResponse.model_validate(data)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Ollama Cloud returned a non-JSON intake response") from exc
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/ai/status")
async def ai_status() -> dict[str, Any]:
    try:
        return {"model": settings.ollama_model, **await llm.status()}
    except LLMUnavailable as exc:
        return {"model": settings.ollama_model, "available": False, "configured": False, "detail": str(exc)}


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
        return ExplanationResponse(approval_id=approval.approval_id, explanation=explanation, source=approval.source, model=settings.ollama_model)
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


@router.post("/ai/documents/review", response_model=DocumentReview)
async def document_review(file: UploadFile = File(...)) -> DocumentReview:
    if file.content_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(status_code=415, detail="Only PDF, JPG, and PNG files are supported")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded document is empty")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="The document must be 10 MB or smaller")
    try:
        extracted = extract_document(file.filename or "uploaded-document", file.content_type, content)
        return await review_document(extracted, llm)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/maitri/submit", response_model=MaitriSubmissionResponse)
def maitri_submit(profile_id: UUID, file_name: str, review_id: UUID) -> MaitriSubmissionResponse:
    result = submit_to_mock_maitri(str(profile_id), file_name, str(review_id))
    return MaitriSubmissionResponse.model_validate(result)
