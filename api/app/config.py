from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    aws_region: str = "us-east-1"
    env: str = "local"

    storage_mode: str = "local"  # local|aws
    artifact_bucket: str | None = None
    scans_table: str = "cloudsentinel-local-scans"
    ddb_endpoint: str | None = None

    cors_origins: str = "http://localhost:3000"

    project_tag: str = "cloudsentinel"
    owner_tag: str = "dhyey"
    allow_admin_sim: bool = False

    log_level: str = "INFO"


def get_settings() -> Settings:
    return Settings()

