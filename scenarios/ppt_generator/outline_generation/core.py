"""Generate presentation outline from analyzed content."""

import logging

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json

from ..models import ContextAnalysis
from ..models import OutlineSection
from ..models import PresentationOutline

logger = logging.getLogger(__name__)


async def generate_outline(analysis: ContextAnalysis, direction: str, target_slides: int) -> PresentationOutline:
    """Generate presentation outline from analysis.

    Args:
        analysis: Context analysis results
        direction: User's instructions
        target_slides: Target number of slides

    Returns:
        PresentationOutline object
    """
    prompt = f"""Create a detailed presentation outline based on this analysis:

Main Topics: {", ".join(analysis.main_topics)}
Key Concepts: {", ".join(analysis.key_concepts[:7])}
Target Audience: {analysis.target_audience}
Tone: {analysis.tone}
Technical Level: {analysis.technical_level}
Suggested Flow: {analysis.suggested_flow}

User Direction: {direction}
Target Slides: {target_slides} (including title and conclusion)

Create a structured outline that includes:
1. Title slide
2. Agenda/Overview slide (if appropriate for length)
3. Content sections with clear progression
4. Conclusion/Summary slide
5. Thank you/Questions slide (if appropriate)

Each section should build on the previous one and support the overall narrative.

Format your response as JSON:
{{
    "title": "Compelling Presentation Title",
    "subtitle": "Subtitle or tagline (optional)",
    "sections": [
        {{
            "section_title": "Section Name",
            "slides": ["Slide 1 Title", "Slide 2 Title"],
            "key_points": ["Point 1", "Point 2"],
            "visual_suggestions": ["Diagram type", "Image concept"]
        }}
    ],
    "total_slides": {target_slides},
    "flow_description": "How the presentation flows from start to finish"
}}"""

    options = SessionOptions(
        system_prompt="You are an expert presentation designer creating compelling PowerPoint outlines. Focus on logical flow, audience engagement, and visual storytelling. Respond only with valid JSON.",
        retry_attempts=2,
    )

    async with ClaudeSession(options) as session:
        result = await session.query(prompt)
        response = result.content

    # Parse response using defensive parsing
    outline_data = parse_llm_json(response)

    # Ensure we have a dict, not a list
    if isinstance(outline_data, list) and outline_data:
        outline_data = outline_data[0] if isinstance(outline_data[0], dict) else {}
    elif not isinstance(outline_data, dict):
        outline_data = None

    if not outline_data:
        # Provide fallback
        logger.warning("Failed to parse outline, using defaults")
        outline_data = {
            "title": " ".join(analysis.main_topics[:2]),
            "subtitle": "",
            "sections": [
                {
                    "section_title": "Introduction",
                    "slides": ["Welcome", "Agenda"],
                    "key_points": ["Overview", "Objectives"],
                    "visual_suggestions": [],
                },
                {
                    "section_title": "Main Content",
                    "slides": [f"Topic {i + 1}" for i in range(target_slides - 4)],
                    "key_points": analysis.key_concepts[:3],
                    "visual_suggestions": ["Process diagram"],
                },
                {
                    "section_title": "Conclusion",
                    "slides": ["Summary", "Thank You"],
                    "key_points": ["Key takeaways"],
                    "visual_suggestions": [],
                },
            ],
            "total_slides": target_slides,
            "flow_description": "Introduction → Main Points → Conclusion",
        }

    # Create OutlineSection objects
    sections = []
    for section_data in outline_data.get("sections", []):
        section = OutlineSection(
            section_title=section_data.get("section_title", "Section"),
            slides=section_data.get("slides", []),
            key_points=section_data.get("key_points", []),
            visual_suggestions=section_data.get("visual_suggestions", []),
        )
        sections.append(section)

    # Create PresentationOutline object
    outline = PresentationOutline(
        title=outline_data.get("title", "Presentation"),
        subtitle=outline_data.get("subtitle"),
        sections=sections,
        total_slides=outline_data.get("total_slides", target_slides),
        flow_description=outline_data.get("flow_description", "Linear progression"),
    )

    logger.info(f"Outline generated: {outline.title} ({outline.total_slides} slides)")
    return outline
