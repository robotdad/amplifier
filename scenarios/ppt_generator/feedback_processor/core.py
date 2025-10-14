"""Core feedback application logic for regenerating slides based on user comments."""

import logging
from collections import defaultdict

from ..models import ContextAnalysis
from ..models import SlideContent
from ..models import UserReview

logger = logging.getLogger(__name__)


async def apply_feedback(
    slides: list[SlideContent], review: UserReview, analysis: ContextAnalysis, direction: str
) -> list[SlideContent]:
    """Apply user feedback by regenerating affected slides.

    Args:
        slides: Original slides
        review: User review with comments
        analysis: Context analysis for regeneration
        direction: Original direction

    Returns:
        Updated slides with feedback incorporated
    """
    if review.approved or not review.comments:
        logger.info("No feedback to apply - review approved or no comments")
        return slides

    # Group comments by slide number
    comments_by_slide = _group_comments_by_slide(review.comments)
    logger.info(f"Applying feedback to {len(comments_by_slide)} slides")

    # Import regeneration function from slide_content module
    from ..slide_content.core import regenerate_slide_with_feedback

    # Create updated slides list
    updated_slides = []

    for slide in slides:
        if slide.slide_number in comments_by_slide:
            # This slide has feedback - regenerate it
            slide_comments = comments_by_slide[slide.slide_number]
            logger.info(f"Regenerating slide {slide.slide_number} with {len(slide_comments)} comments")

            try:
                regenerated_slide = await regenerate_slide_with_feedback(
                    slide=slide, comments=slide_comments, analysis=analysis, direction=direction
                )
                updated_slides.append(regenerated_slide)
                logger.info(f"Successfully regenerated slide {slide.slide_number}")
            except Exception as e:
                logger.error(f"Failed to regenerate slide {slide.slide_number}: {e}")
                # Keep original slide on failure
                updated_slides.append(slide)
        else:
            # No feedback for this slide - keep original
            updated_slides.append(slide)

    logger.info(f"Feedback application complete - {len(comments_by_slide)} slides updated")
    return updated_slides


def _group_comments_by_slide(comments: list[dict]) -> dict[int, list[dict]]:
    """Group comments by slide number.

    Args:
        comments: List of comment dictionaries from UserReview

    Returns:
        Dictionary mapping slide numbers to their comments
    """
    grouped = defaultdict(list)
    for comment in comments:
        slide_num = comment.get("slide_number", 0)
        if slide_num > 0:  # Ignore comments without valid slide numbers
            grouped[slide_num].append(comment)

    # Convert defaultdict to regular dict for cleaner debugging
    return dict(grouped)
