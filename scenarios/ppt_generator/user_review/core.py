"""User review handler for presentation feedback."""

import logging
import re
from pathlib import Path

from ..models import SlideContent
from ..models import UserReview

logger = logging.getLogger(__name__)


class UserReviewHandler:
    """Handles user review and feedback for presentations."""

    def parse_bracketed_comments(self, file_path: Path) -> list[dict]:
        """Parse bracketed comments from markdown file.

        Args:
            file_path: Path to markdown file with bracketed comments

        Returns:
            List of comment dictionaries with context
        """
        if not file_path.exists():
            logger.warning(f"Preview file not found: {file_path}")
            return []

        try:
            content = file_path.read_text()
            lines = content.split("\n")

            comments = []
            bracket_pattern = r"\[([^\]]+)\]"
            current_slide = 0

            for line_num, line in enumerate(lines):
                # Track current slide number
                if line.startswith("## Slide "):
                    try:
                        slide_num_match = re.match(r"## Slide (\d+):", line)
                        if slide_num_match:
                            current_slide = int(slide_num_match.group(1))
                    except (ValueError, AttributeError):
                        pass

                # Find bracketed comments
                matches = re.findall(bracket_pattern, line)
                for match in matches:
                    # Skip markdown image/link brackets
                    if line.strip().startswith("!") or line.strip().startswith("["):
                        continue

                    # Capture context (3 lines before/after)
                    context_lines = 3
                    start_idx = max(0, line_num - context_lines)
                    end_idx = min(len(lines), line_num + context_lines + 1)

                    context_before = lines[start_idx:line_num]
                    context_after = lines[line_num + 1 : end_idx]

                    comments.append(
                        {
                            "comment": match,
                            "slide_number": current_slide,
                            "line_number": line_num + 1,  # 1-indexed
                            "context_before": context_before,
                            "context_after": context_after,
                            "line_content": line,
                        }
                    )

            if comments:
                logger.info(f"Found {len(comments)} bracketed comments")
                for comment in comments[:3]:  # Log first few
                    logger.info(f"  Slide {comment['slide_number']}: [{comment['comment']}]")
            else:
                logger.info("No bracketed comments found")

            return comments

        except Exception as e:
            logger.error(f"Error parsing comments: {e}")
            return []

    def get_user_review(self, preview_file: Path) -> UserReview:
        """Get user review for presentation.

        Args:
            preview_file: Path to preview markdown file

        Returns:
            UserReview object with feedback
        """
        print("\n" + "=" * 60)
        print("📋 PRESENTATION LAYOUT PREVIEW")
        print("=" * 60)
        print(f"\nPreview file: {preview_file}")
        print("\n📝 REVIEW INSTRUCTIONS:")
        print("  1. Open the layout preview in your editor")
        print("  2. Review the full presentation layout")
        print("  3. Add [bracketed comments] where you want changes")
        print("     Example: 'This bullet [needs more detail about ROI]'")
        print("  4. Save the file and return here")
        print("\nOptions:")
        print("  • Type 'done' when you've added comments")
        print("  • Type 'approve' to accept without changes")
        print("  • Type 'skip' to skip review (proceed to PPT generation)")
        print("-" * 60)

        while True:
            user_input = input("\nYour choice (done/approve/skip): ").strip().lower()

            if user_input in ["approve", "approved"]:
                logger.info("User approved presentation layout")
                return UserReview(approved=True, comments=[])

            if user_input == "skip":
                logger.info("User skipped review")
                return UserReview(approved=True, comments=[])  # Treat skip as approval

            if user_input == "done":
                # Parse comments from file
                comments = self.parse_bracketed_comments(preview_file)

                if comments:
                    logger.info(f"Processing {len(comments)} user comments")
                    return UserReview(approved=False, comments=comments)
                print("\n⚠️  No bracketed comments found in the file.")
                print("Please add [bracketed comments] or type 'approve' to continue.")
                continue

            print(f"\n⚠️  Invalid choice: '{user_input}'")
            print("Please type 'done', 'approve', or 'skip'")
            continue

    async def apply_feedback(self, slides: list[SlideContent], review: UserReview) -> list[SlideContent]:
        """Apply user feedback to regenerate affected slides.

        Args:
            slides: Current slides
            review: User review with comments

        Returns:
            Updated slides with feedback applied
        """
        if review.approved or not review.comments:
            return slides

        # Group comments by slide number
        slides_to_update = {}
        for comment in review.comments:
            slide_num = comment["slide_number"]
            if slide_num not in slides_to_update:
                slides_to_update[slide_num] = []
            slides_to_update[slide_num].append(comment)

        logger.info(f"Slides requiring updates: {list(slides_to_update.keys())}")

        # Log the feedback that would be applied
        for slide_num, comments in slides_to_update.items():
            logger.info(f"Slide {slide_num} feedback:")
            for comment in comments:
                logger.info(f"  - {comment['comment']}")

        # Note: Full regeneration would happen through the slide_content module
        # For now, we return the slides as-is since regeneration requires
        # re-running the content generation pipeline with the feedback
        # This will be handled at the pipeline level
        return slides
