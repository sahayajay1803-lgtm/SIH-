from functools import lru_cache
from typing import Any
from uuid import UUID

from supabase import Client, create_client

from app.config import get_settings
from app.schemas import BusinessProfileCreate


@lru_cache
def get_supabase() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)


def insert_profile(profile: BusinessProfileCreate) -> dict[str, Any]:
    payload = profile.model_dump(mode="json")
    result = get_supabase().table("business_profiles").insert(payload).execute()
    if not result.data:
        raise RuntimeError("Supabase did not return the created profile")
    return result.data[0]


def get_profile(profile_id: UUID) -> dict[str, Any] | None:
    result = get_supabase().table("business_profiles").select("*").eq("id", str(profile_id)).maybe_single().execute()
    return result.data
