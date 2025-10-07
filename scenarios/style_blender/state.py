"""State management for style blender pipeline."""

import logging
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from amplifier.ccsdk_toolkit import ClaudeSession

logger = logging.getLogger(__name__)


@dataclass
class StyleProfile:
    """Style profile for a single writer."""

    writer_name: str
    tone: str
    vocabulary_level: str
    sentence_structure: str
    paragraph_length: str
    common_phrases: list[str] = field(default_factory=list)
    writing_patterns: list[str] = field(default_factory=list)
    voice: str = ""
    examples: list[str] = field(default_factory=list)
    sample_count: int = 0


@dataclass
class BlendedStyleProfile:
    """Blended style profile from multiple writers."""

    source_writers: list[str] = field(default_factory=list)
    tone: str = ""
    vocabulary_level: str = ""
    sentence_structure: str = ""
    paragraph_length: str = ""
    common_phrases: list[str] = field(default_factory=list)
    writing_patterns: list[str] = field(default_factory=list)
    voice: str = ""
    examples: list[str] = field(default_factory=list)
    blending_strategy: str = ""
    attribution: dict[str, list[str]] = field(default_factory=dict)  # writer -> contributions


@dataclass
class StyleBlenderState:
    """Complete state for style blending session."""

    # Input configuration
    input_dirs: list[Path] = field(default_factory=list)
    output_dir: Path | None = None
    num_samples: int = 3

    # Processing state
    current_stage: str = "initializing"
    writers_processed: list[str] = field(default_factory=list)
    style_profiles: dict[str, StyleProfile] = field(default_factory=dict)
    blended_profile: BlendedStyleProfile | None = None
    generated_samples: list[Path] = field(default_factory=list)

    # Session tracking
    session_id: str = ""
    total_writers: int = 0
    error_messages: list[str] = field(default_factory=list)

    def save(self, session: ClaudeSession) -> None:
        """Save current state to session."""
        # Note: ClaudeSession doesn't currently support save_state
        # This is a placeholder for future implementation
        logger.debug(f"State tracking: stage={self.current_stage}, writers={len(self.writers_processed)}")

    @classmethod
    def load(cls, session: ClaudeSession) -> "StyleBlenderState":
        """Load state from session or create new."""
        # Note: ClaudeSession doesn't currently support load_state
        # For now, always return a new state
        # Future implementation could use file-based persistence
        return cls()

    def should_skip_writer(self, writer_name: str) -> bool:
        """Check if writer was already processed."""
        return writer_name in self.writers_processed

    def add_style_profile(self, writer_name: str, profile: StyleProfile) -> None:
        """Add a processed style profile."""
        self.style_profiles[writer_name] = profile
        if writer_name not in self.writers_processed:
            self.writers_processed.append(writer_name)
        logger.debug(f"Added profile for {writer_name}")

    def mark_blended(self, profile: BlendedStyleProfile) -> None:
        """Mark blending as complete."""
        self.blended_profile = profile
        self.current_stage = "blended"
        logger.debug("Marked blending complete")

    def add_generated_sample(self, path: Path) -> None:
        """Track generated sample."""
        if path not in self.generated_samples:
            self.generated_samples.append(path)
        logger.debug(f"Added generated sample: {path.name}")
