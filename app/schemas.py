from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectStage(str, Enum):
    new_setup = "new_setup"
    expansion = "expansion"
    operating = "operating"


class BusinessProfileCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    industry_category: str = Field(min_length=2, max_length=80)
    location_district: str = Field(min_length=2, max_length=80)
    investment_amount: float = Field(ge=0)
    project_stage: ProjectStage
    employee_count: int = Field(ge=0)
    user_id: UUID | None = None


class BusinessProfile(BusinessProfileCreate):
    id: UUID
    created_at: str | None = None


class Approval(BaseModel):
    approval_id: str
    name: str
    department: str
    required_documents: list[str]
    sla_days: int
    dependencies: list[str]
    source: str
    applicability_reason: str


class ChecklistResponse(BaseModel):
    profile_id: UUID
    approvals: list[Approval]
    generated_by: str = "deterministic_rules_engine"


class IntakeChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    profile_context: dict[str, Any] = Field(default_factory=dict)


class IntakeChatResponse(BaseModel):
    reply: str
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    source: str = "ollama_cloud:gemma4:31b-cloud"


class ExplanationRequest(BaseModel):
    approval_id: str
    profile: BusinessProfileCreate


class ExplanationResponse(BaseModel):
    approval_id: str
    explanation: str
    source: str
    model: str


class HealthResponse(BaseModel):
    status: str
    llm_configured: bool
    supabase_configured: bool


class Scheme(BaseModel):
    scheme_id: str
    name: str
    government_level: str
    department: str
    category: str
    description: str
    benefits: list[str]
    eligibility: list[str]
    required_documents: list[str]
    application_url: str
    source_url: str
    last_verified_at: date
    tags: list[str] = Field(default_factory=list)


class SchemeListResponse(BaseModel):
    items: list[Scheme]
    total: int
    page: int
    page_size: int


class SchemeMatch(BaseModel):
    scheme: Scheme
    match_score: int = Field(ge=0, le=100)
    reasons: list[str]
    missing_information: list[str] = Field(default_factory=list)


class SchemeMatchResponse(BaseModel):
    profile_id: UUID
    matches: list[SchemeMatch]
    source: str = "illustrative_mock_catalogue"


class DocumentReview(BaseModel):
    review_id: UUID
    file_name: str
    content_type: str
    status: str
    score: int = Field(ge=0, le=100)
    summary: str
    strengths: list[str]
    issues: list[str]
    recommendations: list[str]
    extracted_text_preview: str = ""
    model: str
    source: str = "ai_assisted_prevalidation"


class MaitriSubmissionResponse(BaseModel):
    submission_id: str
    status: str
    message: str
    simulated: bool = True
