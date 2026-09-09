from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Maha Approval Intelligence API"
    environment: str = "development"
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:5173"
    supabase_url: str = ""
    supabase_key: str = ""
    llm_provider: str = "glm_cloud"
    glm_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    glm_api_key: str = ""
    glm_model: str = "glm-5.3"
    llm_timeout_seconds: float = 90.0
    llm_max_concurrency: int = 4

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
