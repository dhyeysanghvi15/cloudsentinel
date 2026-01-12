from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    aws_region: str = "us-east-1"
    env: str = "local"

    # $0 AWS bill by default:
    # - no AWS resources are created
    # - all AWS calls are disabled unless explicitly enabled
    aws_scan_enabled: bool = False

    cors_origins: str = "http://localhost:3000"

    project_tag: str = "cloudsentinel"
    owner_tag: str = "dhyey"
    allow_admin_sim: bool = True

    log_level: str = "INFO"

    data_dir: str = "data"


def get_settings() -> Settings:
    return Settings()
