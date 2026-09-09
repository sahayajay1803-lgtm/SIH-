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
    source: str = "glm_cloud:glm-5.3"


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
