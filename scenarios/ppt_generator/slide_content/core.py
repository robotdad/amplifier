"""Generate content for individual slides."""

import logging

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json

from ..models import ContextAnalysis
from ..models import PresentationOutline
from ..models import SlideContent
from ..models import SlideType

logger = logging.getLogger(__name__)


async def generate_slide_content(
    outline: PresentationOutline, analysis: ContextAnalysis, direction: str
) -> list[SlideContent]:
    """Generate content for each slide in the presentation.

    Args:
        outline: Presentation outline
        analysis: Context analysis results
        direction: User's instructions

    Returns:
        List of SlideContent objects
    """
    slides = []
    slide_number = 1

    # Generate title slide
    title_slide = SlideContent(
        slide_number=slide_number,
        slide_type=SlideType.TITLE,
        title=outline.title,
        subtitle=outline.subtitle,
        bullet_points=[],
        speaker_notes=f"Welcome to this presentation on {outline.title}. {outline.flow_description}",
        layout_preference="title",
    )
    slides.append(title_slide)
    slide_number += 1

    # Generate content slides for each section
    for section in outline.sections:
        for slide_title in section.slides:
            # Generate content for this slide
            slide_content = await _generate_single_slide(
                slide_number=slide_number,
                slide_title=slide_title,
                section=section,
                analysis=analysis,
                outline=outline,
                direction=direction,
            )
            slides.append(slide_content)
            slide_number += 1

    logger.info(f"Generated content for {len(slides)} slides")
    return slides


async def _generate_single_slide(
    slide_number: int,
    slide_title: str,
    section,
    analysis: ContextAnalysis,
    outline: PresentationOutline,
    direction: str,
) -> SlideContent:
    """Generate content for a single slide."""

    # Determine slide type
    slide_type = SlideType.CONTENT
    if any(word in slide_title.lower() for word in ["conclusion", "summary"]):
        slide_type = SlideType.CONCLUSION
    elif any(word in slide_title.lower() for word in ["agenda", "overview", "outline"]):
        slide_type = SlideType.SECTION
    elif any(word in slide_title.lower() for word in ["thank", "question", "contact"]):
        slide_type = SlideType.CONCLUSION

    prompt = f"""Generate content for slide #{slide_number} in a presentation.

Presentation: {outline.title}
Section: {section.section_title}
Slide Title: {slide_title}
Key Points for Section: {", ".join(section.key_points[:3])}
Visual Suggestions: {", ".join(section.visual_suggestions[:2]) if section.visual_suggestions else "None"}

Context:
- Target Audience: {analysis.target_audience}
- Tone: {analysis.tone}
- Technical Level: {analysis.technical_level}
- User Direction: {direction}

Generate appropriate content including:
1. A refined slide title (improve "{slide_title}" if needed)
2. Optional subtitle (if it adds value)
3. 3-5 bullet points (concise, impactful, presentation-ready)
4. Detailed speaker notes (what to actually say when presenting)
5. Layout preference

Special Instructions:
{"Focus on summarizing key takeaways and next steps" if slide_type == SlideType.CONCLUSION else ""}
{"List the main sections/topics to be covered" if slide_type == SlideType.SECTION else ""}
{"Make the content engaging and memorable" if slide_type == SlideType.CONTENT else ""}

Format as JSON:
{{
    "title": "Refined Slide Title",
    "subtitle": "Optional subtitle or null",
    "bullet_points": [
        "• First key point (concise)",
        "• Second key point",
        "• Third key point"
    ],
    "speaker_notes": "Detailed notes for the presenter...",
    "layout_preference": "content_with_image"
}}"""

    options = SessionOptions(
        system_prompt="You are creating engaging PowerPoint content. Make slides visually appealing with concise bullet points and comprehensive speaker notes. Respond only with valid JSON.",
        retry_attempts=2,
    )

    async with ClaudeSession(options) as session:
        result = await session.query(prompt)
        response = result.content

    # Parse response
    slide_data = parse_llm_json(response)

    # Ensure we have a dict, not a list
    if isinstance(slide_data, list) and slide_data:
        slide_data = slide_data[0] if isinstance(slide_data[0], dict) else {}
    elif not isinstance(slide_data, dict):
        slide_data = None

    if not slide_data:
        # Fallback content
        slide_data = {
            "title": slide_title,
            "subtitle": None,
            "bullet_points": ["Key point 1", "Key point 2", "Key point 3"],
            "speaker_notes": f"Present the content for {slide_title}",
            "layout_preference": "content",
        }

    # Create SlideContent object
    slide = SlideContent(
        slide_number=slide_number,
        slide_type=slide_type,
        title=slide_data.get("title", slide_title),
        subtitle=slide_data.get("subtitle"),
        bullet_points=slide_data.get("bullet_points", []),
        speaker_notes=slide_data.get("speaker_notes", ""),
        layout_preference=slide_data.get("layout_preference", "content"),
    )

    return slide


async def regenerate_slide_with_feedback(
    slide: SlideContent, comments: list[dict], analysis: ContextAnalysis, direction: str
) -> SlideContent:
    """Regenerate a single slide incorporating user feedback.

    Args:
        slide: Original slide to regenerate
        comments: List of comment dictionaries for this slide
        analysis: Context analysis for maintaining consistency
        direction: Original presentation direction

    Returns:
        Regenerated SlideContent with feedback incorporated
    """
    # Build feedback text from comments
    feedback_text = "\n".join([f"- {c['comment']}" for c in comments])

    # Build prompt that includes original content and feedback
    prompt = f"""Regenerate this presentation slide incorporating user feedback.

ORIGINAL SLIDE:
Slide #{slide.slide_number}
Title: {slide.title}
{"Subtitle: " + str(slide.subtitle) if slide.subtitle else ""}
Content:
{chr(10).join(slide.bullet_points)}

Speaker Notes: {slide.speaker_notes[:200] + "..." if slide.speaker_notes and len(slide.speaker_notes) > 200 else slide.speaker_notes or ""}

USER FEEDBACK TO ADDRESS:
{feedback_text}

PRESENTATION CONTEXT:
Direction: {direction}
Main Topics: {", ".join(analysis.main_topics[:5])}
Technical Level: {analysis.technical_level}
Target Audience: {analysis.target_audience}
Tone: {analysis.tone}

IMPORTANT:
- Address ALL the user feedback points
- Maintain consistency with the overall presentation context
- Keep the same slide type and general purpose
- Improve clarity and impact based on the feedback

Generate updated slide content that fully addresses the feedback.

Format as JSON:
{{
    "title": "Updated Slide Title",
    "subtitle": "Optional subtitle or null",
    "bullet_points": [
        "• Updated first point",
        "• Updated second point",
        "• Updated third point"
    ],
    "speaker_notes": "Updated detailed notes for the presenter...",
    "layout_preference": "{slide.layout_preference}"
}}"""

    options = SessionOptions(
        system_prompt="You are improving PowerPoint slides based on user feedback. Address all feedback points while maintaining presentation consistency. Respond only with valid JSON.",
        retry_attempts=2,
    )

    try:
        async with ClaudeSession(options) as session:
            result = await session.query(prompt)
            response = result.content

        # Parse response
        slide_data = parse_llm_json(response)

        # Ensure we have a dict, not a list
        if isinstance(slide_data, list) and slide_data:
            slide_data = slide_data[0] if isinstance(slide_data[0], dict) else {}
        elif not isinstance(slide_data, dict):
            slide_data = None

        if not slide_data:
            logger.warning(f"Failed to parse regenerated content for slide {slide.slide_number}, keeping original")
            return slide

        # Create updated SlideContent object, preserving original attributes
        regenerated_slide = SlideContent(
            slide_number=slide.slide_number,
            slide_type=slide.slide_type,
            title=slide_data.get("title", slide.title),
            subtitle=slide_data.get("subtitle"),
            bullet_points=slide_data.get("bullet_points", slide.bullet_points),
            speaker_notes=slide_data.get("speaker_notes", slide.speaker_notes),
            layout_preference=slide_data.get("layout_preference", slide.layout_preference),
            visual_type=slide.visual_type,  # Preserve visual planning
            visual_context=slide.visual_context,  # Preserve visual context
        )

        logger.info(f"Successfully regenerated slide {slide.slide_number} with feedback")
        return regenerated_slide

    except Exception as e:
        logger.error(f"Error regenerating slide {slide.slide_number}: {e}")
        # Return original slide on error
        return slide
