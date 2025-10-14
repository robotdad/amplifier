"""Image generation wrapper for PPT slides."""

import logging
from pathlib import Path

from anthropic import Anthropic

from ..models import SlideContent
from ..models import SlideImage
from ..models import VisualType

logger = logging.getLogger(__name__)


async def generate_images(slides: list[SlideContent], style_images: str, output_dir: Path) -> list[SlideImage]:
    """Generate images for slides that need them.

    Args:
        slides: List of slides with visual planning complete
        style_images: Style description for images
        output_dir: Directory to save images

    Returns:
        List of generated images with paths
    """
    # Create images directory
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)

    # Filter slides that need images
    slides_needing_images = [s for s in slides if s.visual_type in [VisualType.IMAGE, VisualType.BOTH]]

    if not slides_needing_images:
        logger.info("No slides need images")
        return []

    images = []
    client = Anthropic()

    # Use article_illustrator if available
    try:
        from scenarios.article_illustrator.image_generation import ImageGenerator  # noqa: F401

        return await _generate_with_illustrator(slides_needing_images, style_images, output_dir)
    except ImportError:
        logger.info("article_illustrator not available, using direct generation")

    # Fallback to direct prompt generation
    for slide in slides_needing_images:
        try:
            image = await _generate_single_image(slide, style_images, images_dir, client)
            if image:
                images.append(image)
        except Exception as e:
            logger.error(f"Failed to generate image for slide {slide.slide_number}: {e}")
            continue

    logger.info(f"Generated {len(images)} images")
    return images


async def _generate_with_illustrator(slides: list[SlideContent], style: str, output_dir: Path) -> list[SlideImage]:
    """Generate images using article_illustrator."""
    from scenarios.article_illustrator.image_generation import ImageGenerator
    from scenarios.article_illustrator.models import IllustrationPoint
    from scenarios.article_illustrator.models import ImagePrompt

    # Initialize generator
    generator = ImageGenerator(
        apis=["gptimage"],  # Default to GPT for now
        output_dir=output_dir,
        cost_limit=None,
    )

    # Convert slides to ImagePrompts
    prompts = []
    slide_images = []

    for slide in slides:
        # Create illustration point
        point = IllustrationPoint(
            section_title=slide.title,
            section_index=slide.slide_number,
            line_number=0,
            context_before="",
            context_after="",
            importance="high" if slide.slide_type.value == "title" else "medium",
            suggested_placement="after_intro",  # Use valid placement: before_section, after_intro, mid_section
        )

        # Create prompt with style
        prompt_text = _create_image_prompt(slide, style)

        image_prompt = ImagePrompt(
            illustration_id=f"slide_{slide.slide_number}",
            point=point,
            base_prompt=prompt_text,
            style_modifiers=[style],
            full_prompt=f"{prompt_text}, {style}",
            metadata={"slide_number": str(slide.slide_number)},  # Convert to string for metadata
        )
        prompts.append(image_prompt)

    # Generate all images
    try:
        results = await generator.generate_images(prompts, save_callback=None)

        # Convert results to SlideImages
        for i, result in enumerate(results):
            if i < len(slides):
                slide = slides[i]
                slide_image = SlideImage(
                    slide_number=slide.slide_number,
                    title=slide.title,
                    prompt=prompts[i].full_prompt,
                    style_modifiers=style,
                    image_path=result.primary.local_path if result.primary else None,
                )
                slide_images.append(slide_image)

                if result.primary:
                    logger.info(f"Generated image for slide {slide.slide_number}")
    except Exception as e:
        logger.error(f"Failed to generate images with illustrator: {e}")

    return slide_images


async def _generate_single_image(
    slide: SlideContent, style: str, output_dir: Path, client: Anthropic
) -> SlideImage | None:
    """Generate a single image for a slide using direct prompting."""

    prompt_text = _create_image_prompt(slide, style)

    # Create SlideImage object
    slide_image = SlideImage(
        slide_number=slide.slide_number,
        title=slide.title,
        prompt=prompt_text,
        style_modifiers=style,
        image_path=None,  # Would need actual image generation API
    )

    # Note: This is a placeholder - actual image generation would require
    # integration with DALL-E, Midjourney, or other image generation APIs
    logger.info(f"Generated image prompt for slide {slide.slide_number}: {prompt_text[:100]}...")

    # Save prompt for reference
    prompt_file = output_dir / f"slide_{slide.slide_number}_prompt.txt"
    prompt_file.write_text(f"{prompt_text}\nStyle: {style}")

    return slide_image


def _create_image_prompt(slide: SlideContent, style: str) -> str:
    """Create an image generation prompt for a slide."""

    # Build context from slide content
    context = slide.title
    if slide.bullet_points:
        context += ". " + ". ".join(slide.bullet_points[:2])

    # Create descriptive prompt
    if slide.visual_context:
        base_prompt = slide.visual_context
    else:
        # Generate appropriate prompt based on slide type
        if slide.slide_type.value == "title":
            base_prompt = f"A compelling header image representing '{slide.title}'"
        elif slide.slide_type.value == "conclusion":
            base_prompt = f"An inspiring conclusion image for '{slide.title}'"
        else:
            base_prompt = f"A professional illustration for the concept: {context}"

    return base_prompt
