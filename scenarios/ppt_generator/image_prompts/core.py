"""Generate image prompts for slides."""

import logging

from amplifier.ccsdk_toolkit import ClaudeSession

from ..models import SlideContent

logger = logging.getLogger(__name__)


async def generate_image_prompts(
    slides: list[SlideContent], style_images: str | None = None
) -> tuple[dict[int, str], float]:
    """Generate image prompts for slides that need visuals.

    Args:
        slides: List of slide content
        style_images: Optional art style for images

    Returns:
        Tuple of (dict mapping slide_number to prompt, cost)
    """
    prompts = {}
    total_cost = 0.0

    # Determine which slides need images
    # Skip title slide, agenda, thank you slides typically
    for slide in slides:
        if slide.layout_preference == "title" or slide.slide_type.value == "title":
            continue  # Title slides don't typically need images

        # Check if it's a special slide type
        title_lower = slide.title.lower()
        if any(word in title_lower for word in ["agenda", "overview", "thank", "question", "contact"]):
            continue

        # Generate prompt for this slide
        prompt, cost = await _generate_single_prompt(slide, style_images)
        if prompt:
            prompts[slide.slide_number] = prompt
            # Note: We don't store in slide object as it doesn't have image_prompt attribute
            total_cost += cost

    logger.info(f"Generated {len(prompts)} image prompts")
    logger.debug(f"Image prompt generation cost: ${total_cost:.4f}")

    return prompts, total_cost


async def _generate_single_prompt(slide: SlideContent, style: str | None = None) -> tuple[str | None, float]:
    """Generate image prompt for a single slide.

    Args:
        slide: Slide content
        style: Optional art style

    Returns:
        Tuple of (prompt or None, cost)
    """
    # Build the context for prompt generation
    style_guidance = f" in {style} style" if style else ""

    prompt = f"""Create a detailed image generation prompt for a PowerPoint slide.

Slide Title: {slide.title}
Slide Content: {", ".join(slide.bullet_points[:3]) if slide.bullet_points else "No bullet points"}
Speaker Notes Preview: {slide.speaker_notes[:200] if slide.speaker_notes else "No notes"}

Create a visually compelling image prompt that:
1. Relates directly to the slide content
2. Is professional and appropriate for presentations
3. Avoids text or words in the image
4. Uses metaphor or visual representation of concepts
5. Is suitable for a rectangular slide background or illustration{style_guidance}

Return ONLY the image prompt, no explanation. Make it detailed and specific.
Example format: "A modern digital illustration of interconnected nodes representing a network, with glowing blue connections on a dark background, minimalist style"
"""

    from amplifier.ccsdk_toolkit import SessionOptions

    options = SessionOptions(
        system_prompt="You are an expert at creating image generation prompts for professional presentations. Create clear, detailed prompts that result in appropriate business visuals.",
        retry_attempts=2,
    )

    async with ClaudeSession(options) as session:
        result = await session.query(prompt)
        response = result.content

    # Clean up the response
    image_prompt = response.strip()

    # Remove quotes if present
    if image_prompt.startswith('"') and image_prompt.endswith('"'):
        image_prompt = image_prompt[1:-1]

    # Add style suffix if not already included
    if style and style.lower() not in image_prompt.lower():
        image_prompt = f"{image_prompt}, {style}"

    cost = 0.0  # ClaudeSession doesn't track costs directly
    return image_prompt, cost
