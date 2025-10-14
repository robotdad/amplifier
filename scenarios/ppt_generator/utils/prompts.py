"""Prompt saving utilities for diagnostics."""

import json
import logging
from pathlib import Path

from ..models import SlideDiagram
from ..models import SlideImage

logger = logging.getLogger(__name__)


def save_prompts(diagrams: list[SlideDiagram], images: list[SlideImage], output_dir: Path) -> None:
    """Save all prompts to prompts.json for diagnostics.

    Args:
        diagrams: List of diagram specifications
        images: List of image specifications
        output_dir: Directory to save prompts file
    """
    prompts_data = {
        "diagrams": [],
        "images": [],
    }

    # Save diagram prompts
    for diagram in diagrams:
        prompts_data["diagrams"].append(
            {
                "slide_number": diagram.slide_number,
                "diagram_type": diagram.diagram_type.value,
                "title": diagram.title,
                "description": diagram.description,
                "mermaid_code": diagram.mermaid_code,
            }
        )

    # Save image prompts
    for image in images:
        prompts_data["images"].append(
            {
                "slide_number": image.slide_number,
                "title": image.title,
                "prompt": image.prompt,
                "style": image.style_modifiers,
            }
        )

    # Write to file
    prompts_file = output_dir / "prompts.json"
    try:
        prompts_file.write_text(json.dumps(prompts_data, indent=2))
        logger.info(f"Saved prompts to {prompts_file}")
    except Exception as e:
        logger.error(f"Failed to save prompts: {e}")
