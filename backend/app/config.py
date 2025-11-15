from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    #MongoDB settings
    mongodb_url: str
    database_name: str = "github_explorer"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 9999
    debug: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

settings = Settings()
