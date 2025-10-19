from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_prefix="AGENT_"
    )

    # OpenAI
    openai_api_key: str = "dummy-key-for-tests"  # Default for tests, should be overridden in production
    openai_model: str = "gpt-4o-mini"  # или "gpt-4o"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 2000


settings = AgentSettings()
