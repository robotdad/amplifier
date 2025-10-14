"""State management for PPT generation pipeline."""

import logging
from datetime import datetime
from pathlib import Path

from .models import PipelineState

logger = logging.getLogger(__name__)


class StateManager:
    """Manages pipeline state for resumability."""

    def __init__(self, output_dir: Path):
        """Initialize state manager."""
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = output_dir / ".pipeline_state.json"
        self.state: PipelineState | None = None

    def initialize(
        self,
        context_files: list[Path],
        direction: str,
        template_path: Path | None = None,
        target_slides: int = 10,
        style_images: str = "professional, modern, clean",
        skip_images: bool = False,
        skip_diagrams: bool = False,
        skip_review: bool = False,
    ) -> PipelineState:
        """Initialize a new pipeline state."""
        self.state = PipelineState(
            context_files=context_files,
            direction=direction,
            template_path=template_path,
            output_dir=self.output_dir,
            target_slides=target_slides,
            style_images=style_images,
            skip_images=skip_images,
            skip_diagrams=skip_diagrams,
            skip_review=skip_review,
        )
        self.save()
        logger.info(f"Initialized new pipeline state in {self.output_dir}")
        return self.state

    def load(self) -> PipelineState | None:
        """Load existing state if available."""
        if not self.state_file.exists():
            return None

        try:
            self.state = PipelineState.load(self.state_file)
            logger.info(f"Loaded existing state from {self.state_file}")
            return self.state
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None

    def save(self):
        """Save current state to disk."""
        if not self.state:
            return

        try:
            self.state.save(self.state_file)
            logger.debug(f"Saved state to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def update_stage(self, stage: str, complete: bool = True):
        """Update stage completion status."""
        if self.state:
            self.state.update_stage(stage, complete)
            self.save()

    def add_error(self, stage: str, error: str):
        """Add error to state."""
        if self.state:
            self.state.errors.append({"stage": stage, "error": error, "timestamp": datetime.now().isoformat()})
            self.save()

    def get_resume_point(self) -> str:
        """Determine where to resume pipeline."""
        if not self.state:
            return "start"

        stages = [
            ("context_analysis", "context_analysis_complete"),
            ("outline", "outline_complete"),
            ("content", "content_complete"),
            ("visual_planning", "visual_planning_complete"),
            ("diagrams", "diagrams_complete"),
            ("images", "images_complete"),
            ("review", "review_complete"),
            ("ppt", "ppt_complete"),
        ]

        for stage_name, flag_name in stages:
            if not getattr(self.state, flag_name):
                return stage_name

        return "complete"

    def get_progress_summary(self) -> dict:
        """Get summary of pipeline progress."""
        if not self.state:
            return {"status": "not_started"}

        return {
            "status": "in_progress" if self.get_resume_point() != "complete" else "complete",
            "resume_point": self.get_resume_point(),
            "stages": {
                "context_analysis": self.state.context_analysis_complete,
                "outline": self.state.outline_complete,
                "content": self.state.content_complete,
                "visual_planning": self.state.visual_planning_complete,
                "diagrams": self.state.diagrams_complete,
                "images": self.state.images_complete,
                "review": self.state.review_complete,
                "ppt": self.state.ppt_complete,
            },
            "slides_generated": len(self.state.slides),
            "diagrams_generated": len(self.state.diagrams),
            "images_generated": len(self.state.images),
            "errors": len(self.state.errors),
            "total_cost": self.state.total_cost,
        }
