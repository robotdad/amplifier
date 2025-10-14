"""Data models for PPT generation pipeline with enhanced visual support."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class VisualType(str, Enum):
    """Type of visual for a slide."""

    NONE = "none"
    DIAGRAM = "diagram"
    IMAGE = "image"
    BOTH = "both"


class DiagramType(str, Enum):
    """Type of diagram."""

    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    CLASS = "class"
    STATE = "state"
    ER = "er"
    GANTT = "gantt"
    PIE = "pie"
    BAR = "bar"
    JOURNEY = "journey"
    GIT = "git"
    GRAPH = "graph"
    MINDMAP = "mindmap"


class SlideType(str, Enum):
    """Type of slide."""

    TITLE = "title"
    SECTION = "section"
    CONTENT = "content"
    BULLETS = "bullets"
    DIAGRAM = "diagram"
    IMAGE = "image"
    MIXED = "mixed"
    CONCLUSION = "conclusion"


class ContextAnalysis(BaseModel):
    """Analysis of input context files."""

    main_topics: list[str]
    key_concepts: list[str]
    target_audience: str
    tone: str
    technical_level: str
    suggested_flow: str
    visual_opportunities: list[str]


class OutlineSection(BaseModel):
    """A section in the presentation outline."""

    section_title: str
    slides: list[str]
    key_points: list[str]
    visual_suggestions: list[str] = []


class PresentationOutline(BaseModel):
    """Complete presentation outline."""

    title: str
    subtitle: str | None = None
    sections: list[OutlineSection]
    total_slides: int
    flow_description: str


class SlideContent(BaseModel):
    """Content for a single slide."""

    slide_number: int
    slide_type: SlideType
    title: str
    subtitle: str | None = None
    bullet_points: list[str] = []
    speaker_notes: str | None = None
    visual_type: VisualType = VisualType.NONE
    visual_context: str | None = None  # Why this visual is needed
    layout_preference: str = "default"  # Layout hint for assembly


class SlideDiagram(BaseModel):
    """Diagram specification for a slide."""

    slide_number: int
    diagram_type: DiagramType
    title: str
    description: str
    mermaid_code: str
    image_path: Path | None = None  # Set after conversion
    width: int = 800
    height: int = 600


class SlideImage(BaseModel):
    """Image specification for a slide."""

    slide_number: int
    title: str
    prompt: str
    style_modifiers: str
    image_path: Path | None = None  # Set after generation
    width: int = 1024
    height: int = 768


class UserReview(BaseModel):
    """User review feedback for presentation."""

    approved: bool = False
    comments: list[dict[str, Any]] = []  # Stores bracketed comments with context
    iteration: int = 0
    reviewed_at: datetime = Field(default_factory=datetime.now)


class PipelineState(BaseModel):
    """Complete pipeline state for resumability."""

    # Configuration
    context_files: list[Path]
    direction: str
    template_path: Path | None = None
    output_dir: Path
    target_slides: int = 10
    style_images: str = "professional, modern, clean"
    skip_images: bool = False
    skip_diagrams: bool = False
    skip_review: bool = False

    # Stage completion flags
    context_analysis_complete: bool = False
    outline_complete: bool = False
    content_complete: bool = False
    visual_planning_complete: bool = False
    diagrams_complete: bool = False
    images_complete: bool = False
    review_complete: bool = False  # New stage
    ppt_complete: bool = False

    # Stage outputs
    analysis: ContextAnalysis | None = None
    outline: PresentationOutline | None = None
    slides: list[SlideContent] = []
    diagrams: list[SlideDiagram] = []
    images: list[SlideImage] = []
    user_review: UserReview | None = None  # New field
    output_file: Path | None = None

    # Metadata
    total_tokens: int = 0
    total_cost: float = 0.0
    errors: list[dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        """Pydantic config."""

        json_encoders = {Path: str, datetime: lambda v: v.isoformat()}

    def save(self, path: Path):
        """Save state to JSON file."""
        path.write_text(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, path: Path) -> "PipelineState":
        """Load state from JSON file."""
        data = cls.model_validate_json(path.read_text())
        # Convert string paths back to Path objects
        if data.context_files:
            data.context_files = [Path(f) for f in data.context_files]
        if data.template_path:
            data.template_path = Path(data.template_path)
        data.output_dir = Path(data.output_dir)
        if data.output_file:
            data.output_file = Path(data.output_file)
        return data

    def update_stage(self, stage: str, complete: bool = True):
        """Update stage completion status."""
        setattr(self, f"{stage}_complete", complete)
        self.updated_at = datetime.now()
