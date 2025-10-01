"""State Management Module for Social Media Post Generator.

Handles pipeline state persistence for resume capability.
Saves state after every operation to enable interruption recovery.
"""

import re
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Any

from amplifier.ccsdk_toolkit.defensive.file_io import read_json_with_retry
from amplifier.ccsdk_toolkit.defensive.file_io import write_json_with_retry
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug.

    Args:
        text: Text to slugify

    Returns:
        Slugified string (lowercase, dashes for spaces, no special chars)
    """
    # Convert to lowercase
    slug = text.lower()
    # Replace spaces and underscores with dashes
    slug = re.sub(r"[\s_]+", "-", slug)
    # Remove special characters (keep alphanumeric and dashes)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    # Remove multiple consecutive dashes
    slug = re.sub(r"-+", "-", slug)
    # Strip leading/trailing dashes
    slug = slug.strip("-")
    # Limit length
    if len(slug) > 50:
        slug = slug[:50].rsplit("-", 1)[0]
    return slug or "social-posts"


@dataclass
class PipelineState:
    """Complete pipeline state for persistence."""

    # Current pipeline stage
    stage: str = "initialized"  # initialized -> analyzing -> generating -> reviewing -> complete

    # Module outputs
    content_analysis: dict[str, Any] = field(default_factory=dict)
    generated_posts: dict[str, Any] = field(default_factory=dict)
    reviewed_posts: dict[str, Any] = field(default_factory=dict)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Input parameters
    article_path: str | None = None
    tone_override: str | None = None
    guidance: str | None = None
    count: int = 5
    platforms: list[str] = field(default_factory=lambda: ["twitter", "linkedin", "bluesky"])
    include_hashtags: bool = False
    output_dir: str | None = None


class StateManager:
    """Manages pipeline state with automatic persistence."""

    def __init__(self, session_dir: Path | None = None):
        """Initialize state manager.

        Args:
            session_dir: Path to session directory (default: .data/social_posts/<timestamp>/)
        """
        if session_dir is None:
            # Create new session directory with timestamp
            base_dir = Path(".data/social_posts")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = base_dir / timestamp

        self.session_dir = session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.session_dir / "state.json"
        self.state = self._load_state()

    def _load_state(self) -> PipelineState:
        """Load state from file or create new."""
        if self.state_file.exists():
            try:
                data = read_json_with_retry(self.state_file)
                logger.info(f"Resumed state from: {self.state_file}")
                logger.info(f"  Stage: {data.get('stage', 'unknown')}")
                return PipelineState(**data)
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
                logger.info("Starting fresh pipeline")

        return PipelineState()

    def save(self) -> None:
        """Save current state to file."""
        self.state.updated_at = datetime.now().isoformat()

        try:
            state_dict = asdict(self.state)
            write_json_with_retry(state_dict, self.state_file)
            logger.debug(f"State saved to: {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            # Don't fail the pipeline on state save errors

    def update_stage(self, stage: str) -> None:
        """Update pipeline stage and save.

        Args:
            stage: New stage name
        """
        old_stage = self.state.stage
        self.state.stage = stage
        logger.info(f"Pipeline stage: {old_stage} → {stage}")
        self.save()

    def set_content_analysis(self, analysis: dict[str, Any]) -> None:
        """Save content analysis results.

        Args:
            analysis: Analysis results dictionary
        """
        self.state.content_analysis = analysis
        self.save()

    def set_generated_posts(self, posts: dict[str, Any]) -> None:
        """Save generated posts.

        Args:
            posts: Generated posts dictionary
        """
        self.state.generated_posts = posts
        self.save()

    def set_reviewed_posts(self, reviews: dict[str, Any]) -> None:
        """Save post reviews.

        Args:
            reviews: Review results dictionary
        """
        self.state.reviewed_posts = reviews
        self.save()

    def is_complete(self) -> bool:
        """Check if pipeline is complete.

        Returns:
            True if pipeline completed
        """
        return self.state.stage == "complete"

    def mark_complete(self) -> None:
        """Mark pipeline as complete."""
        self.update_stage("complete")
        logger.info("✅ Pipeline complete!")

    def reset(self) -> None:
        """Reset state for fresh run."""
        self.state = PipelineState()
        self.save()
        logger.info("State reset for fresh pipeline run")
