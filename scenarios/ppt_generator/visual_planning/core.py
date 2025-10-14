"""Determine visual needs for slides (diagrams vs images)."""

import logging

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json

from ..models import SlideContent
from ..models import VisualType

logger = logging.getLogger(__name__)


async def determine_visual_needs(slides: list[SlideContent], analysis_context: dict) -> list[SlideContent]:
    """Determine which slides need diagrams vs images.

    Args:
        slides: List of slides with content
        analysis_context: Context from analysis phase

    Returns:
        Updated slides with visual_type and visual_context
    """
    # Batch process slides for efficiency
    batch_size = 5
    for i in range(0, len(slides), batch_size):
        batch = slides[i : i + batch_size]
        await _process_batch(batch, analysis_context)

    logger.info(f"Visual planning complete for {len(slides)} slides")
    return slides


async def _process_batch(batch: list[SlideContent], analysis_context: dict) -> None:
    """Process a batch of slides for visual needs."""

    # Skip title slide
    slides_to_process = [s for s in batch if s.slide_type.value != "title"]
    if not slides_to_process:
        return

    prompt = f"""Analyze these slides and determine what type of visual would enhance each one.

Context: {analysis_context.get("technical_level", "general")} presentation about {analysis_context.get("main_topics", ["topics"])[0]}

Slides to analyze:
"""

    for slide in slides_to_process:
        prompt += f"""
Slide {slide.slide_number}: {slide.title}
- Type: {slide.slide_type.value}
- Content: {"; ".join(slide.bullet_points[:3])}
"""

    prompt += """

For each slide, determine:
1. Visual type: "none" (no visual needed), "diagram" (process/flow/structure), "image" (conceptual/metaphorical), or "both"
2. Visual context: Why this visual type would help (1 sentence)
3. Specific suggestion: What kind of diagram or image

Consider:
- Technical slides often benefit from diagrams (flowcharts, architecture, sequences)
- Conceptual slides benefit from metaphorical images
- Data-heavy slides need charts/graphs
- Some slides are better text-only

Format as JSON:
{
    "visuals": [
        {
            "slide_number": 2,
            "visual_type": "diagram",
            "visual_context": "Shows the process flow clearly",
            "suggestion": "flowchart showing steps from input to output"
        }
    ]
}"""

    options = SessionOptions(
        system_prompt="You are a presentation design expert determining optimal visual strategies. Focus on visuals that truly enhance understanding, not decoration. Respond only with valid JSON.",
        retry_attempts=2,
    )

    async with ClaudeSession(options) as session:
        result = await session.query(prompt)
        response = result.content

    # Parse response
    visual_data = parse_llm_json(response)

    # Ensure we have a dict, not a list
    if isinstance(visual_data, list) and visual_data:
        visual_data = visual_data[0] if isinstance(visual_data[0], dict) else {}
    elif not isinstance(visual_data, dict):
        visual_data = {}

    if not visual_data or "visuals" not in visual_data:
        logger.warning("Failed to parse visual planning response")
        return

    # Apply visual decisions to slides
    visual_map = {v["slide_number"]: v for v in visual_data.get("visuals", [])}

    for slide in slides_to_process:
        if slide.slide_number in visual_map:
            visual_info = visual_map[slide.slide_number]

            # Map string to enum
            visual_type_str = visual_info.get("visual_type", "none").lower()
            if visual_type_str == "diagram":
                slide.visual_type = VisualType.DIAGRAM
            elif visual_type_str == "image":
                slide.visual_type = VisualType.IMAGE
            elif visual_type_str == "both":
                slide.visual_type = VisualType.BOTH
            else:
                slide.visual_type = VisualType.NONE

            slide.visual_context = visual_info.get("visual_context", "")

            # Log decision
            if slide.visual_type != VisualType.NONE:
                logger.debug(
                    f"Slide {slide.slide_number}: {slide.visual_type.value} - {visual_info.get('suggestion', '')}"
                )
