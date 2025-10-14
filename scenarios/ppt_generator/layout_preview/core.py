"""Generate markdown layout preview for user review."""

import logging
from pathlib import Path

from ..models import PipelineState

logger = logging.getLogger(__name__)


def generate_layout_preview(state: PipelineState, output_dir: Path) -> Path:
    """Generate markdown preview of presentation layout.

    Args:
        state: Current pipeline state with slides and visuals
        output_dir: Directory to save preview file

    Returns:
        Path to generated preview markdown file
    """
    if not state.slides:
        raise ValueError("No slides available to preview")

    # Create lookup maps for visuals
    diagram_map = {d.slide_number: d for d in state.diagrams}
    image_map = {i.slide_number: i for i in state.images}

    # Build markdown preview
    preview_lines = []

    # Header
    preview_lines.append("# Presentation Layout Preview")
    preview_lines.append("")
    preview_lines.append("**Format**: 16:9 Widescreen")
    preview_lines.append(f"**Total Slides**: {len(state.slides)}")
    preview_lines.append("")

    # Process each slide
    for slide in state.slides:
        preview_lines.append(f"## Slide {slide.slide_number}: {slide.title}")
        preview_lines.append(f"**Type**: {slide.slide_type.value}")

        # Add subtitle if present
        if slide.subtitle:
            preview_lines.append(f"**Subtitle**: {slide.subtitle}")

        # Check for visuals
        has_diagram = slide.slide_number in diagram_map
        has_image = slide.slide_number in image_map

        if has_diagram or has_image:
            visual_type = []
            if has_diagram:
                visual_type.append("Diagram")
            if has_image:
                visual_type.append("Image")
            positioning = "right side" if slide.bullet_points else "centered"
            preview_lines.append(f"**Visual**: {' + '.join(visual_type)} ({positioning})")

        preview_lines.append("")

        # Add content (bullets) - FULL content, no truncation
        if slide.bullet_points:
            preview_lines.append("**Content**:")
            for bullet in slide.bullet_points:
                # Strip bullet characters as they'll be added by PowerPoint
                clean_text = bullet.lstrip("•-*").strip()
                preview_lines.append(f"- {clean_text}")
            preview_lines.append("")

        # Add speaker notes - FULL notes, no truncation
        if slide.speaker_notes:
            preview_lines.append("**Speaker Notes**:")
            preview_lines.append(slide.speaker_notes)
            preview_lines.append("")

        # Add diagram information if present
        if has_diagram:
            diagram = diagram_map[slide.slide_number]
            preview_lines.append("**Diagram Details**:")
            preview_lines.append(f"- Type: {diagram.diagram_type.value}")
            preview_lines.append(f"- Description: {diagram.description}")
            if diagram.image_path and diagram.image_path.exists():
                # Use relative path from output_dir for markdown
                rel_path = (
                    diagram.image_path.relative_to(output_dir)
                    if diagram.image_path.is_relative_to(output_dir)
                    else diagram.image_path.name
                )
                preview_lines.append(f"- Preview: ![Diagram]({rel_path})")
            preview_lines.append("")

        # Add image information if present
        if has_image:
            image = image_map[slide.slide_number]
            preview_lines.append("**Image Prompt**:")
            preview_lines.append(f"> {image.prompt}")
            preview_lines.append("")
            if image.style_modifiers:
                preview_lines.append(f"**Style**: {image.style_modifiers}")
                preview_lines.append("")
            if image.image_path and image.image_path.exists():
                # Use relative path from output_dir for markdown
                rel_path = (
                    image.image_path.relative_to(output_dir)
                    if image.image_path.is_relative_to(output_dir)
                    else image.image_path.name
                )
                preview_lines.append("**Image Preview**:")
                preview_lines.append(f"![Image]({rel_path})")
                preview_lines.append("")

        # Add separator between slides
        preview_lines.append("---")
        preview_lines.append("")

    # Add instructions for user
    preview_lines.append("## Review Instructions")
    preview_lines.append("")
    preview_lines.append("To request changes:")
    preview_lines.append("1. Add [bracketed comments] where you want modifications")
    preview_lines.append("2. Example: `This bullet [needs more detail about ROI]`")
    preview_lines.append("3. Save the file and return to the terminal")
    preview_lines.append("4. Type 'done' when you've added comments")
    preview_lines.append("5. Or type 'approve' to proceed without changes")

    # Join all lines
    preview_content = "\n".join(preview_lines)

    # Save to file
    preview_file = output_dir / "layout_preview.md"
    preview_file.write_text(preview_content)

    logger.info(f"Layout preview generated: {preview_file}")

    return preview_file
