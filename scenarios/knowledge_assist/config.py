"""Configuration for knowledge-assist scenario tool."""

import os
from pathlib import Path

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class KnowledgeAssistConfig(BaseSettings):
    """Configuration for the knowledge-assist tool."""

    # Pydantic v2 settings configuration
    model_config = SettingsConfigDict(
        env_prefix="KNOWLEDGE_ASSIST_",
        env_file=Path(__file__).parent.parent.parent / ".env",  # Project root .env
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Data paths
    knowledge_path: Path = Field(
        default=Path(".data/knowledge/extractions.jsonl"), description="Path to knowledge extractions file"
    )
    output_dir: Path = Field(
        default=Path(".data/knowledge_assist/sessions"), description="Directory for session outputs"
    )
    prompts_dir: Path = Field(
        default=Path(__file__).parent / "prompts", description="Directory containing prompt templates"
    )
    extractions_dir: Path = Field(default=Path(".data/knowledge"), description="Directory containing extraction files")

    # OpenAI configuration
    # First try KNOWLEDGE_ASSIST_API_KEY env var, then OPENAI_API_KEY from .env
    api_key: str | None = Field(default=None, alias="OPENAI_API_KEY", description="OpenAI API key")
    model: str = Field(default="gpt-4o", description="OpenAI model to use")
    web_search_model: str = Field(
        default="gpt-4o",
        description="Model to use when web search is needed - consider gpt-4o-search-preview if available",
    )
    temperature: float = Field(default=0.7, description="Temperature for synthesis")
    max_tokens: int = Field(default=2000, description="Maximum tokens for response")

    # Retrieval settings
    max_concepts: int = Field(default=10, description="Maximum concepts to retrieve")
    max_relationships: int = Field(default=8, description="Maximum relationships to retrieve")
    max_insights: int = Field(default=5, description="Maximum insights to retrieve")
    max_patterns: int = Field(default=5, description="Maximum patterns to retrieve")

    # Web search settings
    temporal_terms: list[str] = Field(
        default=["latest", "recent", "current", "2024", "2025", "new", "updated", "today"],
        description="Terms that trigger web search",
    )
    max_web_results: int = Field(default=5, description="Maximum web search results to include")

    @field_validator("api_key", mode="before")
    @classmethod
    def get_api_key(cls, v):
        """Get API key from environment if not provided."""
        # If value is provided, use it
        if v:
            return v
        # Otherwise check environment variable
        return os.getenv("OPENAI_API_KEY")

    def ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
