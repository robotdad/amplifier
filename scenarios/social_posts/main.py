#!/usr/bin/env python3
"""Social Media Post Generator - Main Orchestrator and CLI.

Coordinates the social post generation pipeline with state management.
"""

import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path

import click
from dotenv import load_dotenv

from amplifier.utils.logger import get_logger

from .content_analyzer import ContentAnalyzer
from .post_generator import PostGenerator
from .post_reviewer import PostReviewer
from .state import StateManager
from .state import slugify

logger = get_logger(__name__)


class SocialPostPipeline:
    """Orchestrates the social media post generation pipeline."""

    def __init__(self, state_manager: StateManager):
        """Initialize pipeline with state management.

        Args:
            state_manager: State manager instance
        """
        self.state = state_manager
        self.content_analyzer = ContentAnalyzer()
        self.post_generator = PostGenerator()
        self.post_reviewer = PostReviewer()

        # Store inputs
        self.article_path: Path | None = None
        self.article_content: str = ""

    async def run(
        self,
        article_path: Path,
        tone_override: str | None = None,
        guidance: str | None = None,
        count: int = 5,
        platforms: list[str] | None = None,
        include_hashtags: bool = False,
    ) -> bool:
        """Run the complete pipeline.

        Args:
            article_path: Path to article markdown file
            tone_override: Optional tone override
            guidance: Optional additional guidance
            count: Number of posts per platform
            platforms: Target platforms
            include_hashtags: Whether to include hashtags in posts

        Returns:
            True if successful, False otherwise
        """
        # Store paths and parameters
        self.article_path = article_path
        platforms = platforms or ["twitter", "linkedin", "bluesky"]
        self.include_hashtags = include_hashtags

        # Update state with inputs
        self.state.state.article_path = str(article_path)
        self.state.state.tone_override = tone_override
        self.state.state.guidance = guidance
        self.state.state.count = count
        self.state.state.platforms = platforms
        self.state.state.include_hashtags = include_hashtags
        self.state.save()

        # Load article content
        try:
            self.article_content = article_path.read_text(encoding="utf-8")
            logger.info(f"Loaded article: {article_path.name}")
        except Exception as e:
            logger.error(f"Could not read article: {e}")
            return False

        # Resume from saved stage if applicable
        stage = self.state.state.stage
        logger.info(f"Starting from stage: {stage}")

        try:
            # Execute pipeline stages
            if stage == "initialized":
                await self._analyze_content()
                stage = self.state.state.stage

            if stage == "analyzed":
                await self._generate_posts()
                stage = self.state.state.stage

            if stage == "generated":
                await self._review_posts()
                stage = self.state.state.stage

            # Save final output
            await self._save_output()
            self.state.mark_complete()

            return True

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return False

    async def _analyze_content(self) -> None:
        """Analyze article content."""
        logger.info("\n📊 Analyzing article content...")
        self.state.update_stage("analyzing")

        assert self.article_path is not None, "article_path must be set"
        analysis = await self.content_analyzer.analyze_content(self.article_path)

        # Convert to dict for storage
        analysis_dict = asdict(analysis)
        self.state.set_content_analysis(analysis_dict)
        self.state.update_stage("analyzed")

    async def _generate_posts(self) -> None:
        """Generate social media posts."""
        logger.info("\n✍️ Generating social media posts...")
        self.state.update_stage("generating")

        # Reconstruct ContentAnalysis from saved state
        from .content_analyzer import ContentAnalysis

        analysis = ContentAnalysis(**self.state.state.content_analysis)

        posts = await self.post_generator.generate_posts(
            analysis=analysis,
            article_content=self.article_content,
            platforms=self.state.state.platforms,
            count=self.state.state.count,
            guidance=self.state.state.guidance,
            tone_override=self.state.state.tone_override,
            include_hashtags=self.state.state.include_hashtags,
        )

        # Convert to dict for storage
        posts_dict = {
            "posts": [asdict(p) for p in posts.posts],
            "platforms": posts.platforms,
            "tone_used": posts.tone_used,
            "themes_incorporated": posts.themes_incorporated,
        }
        self.state.set_generated_posts(posts_dict)
        self.state.update_stage("generated")

    async def _review_posts(self) -> None:
        """Review generated posts for quality."""
        logger.info("\n🔍 Reviewing post quality...")
        self.state.update_stage("reviewing")

        # Reconstruct objects from saved state
        from .content_analyzer import ContentAnalysis
        from .post_generator import GeneratedPosts
        from .post_generator import SocialPost

        analysis = ContentAnalysis(**self.state.state.content_analysis)

        # Reconstruct posts
        posts = [SocialPost(**p) for p in self.state.state.generated_posts["posts"]]
        generated_posts = GeneratedPosts(
            posts=posts,
            platforms=self.state.state.generated_posts["platforms"],
            tone_used=self.state.state.generated_posts["tone_used"],
            themes_incorporated=self.state.state.generated_posts.get("themes_incorporated", []),
        )

        reviews = await self.post_reviewer.review_posts(
            generated_posts=generated_posts,
            content_analysis=analysis,
        )

        # Convert to dict for storage
        reviews_dict = {
            "reviews": [
                {
                    "post": asdict(r.post),
                    "clarity_score": r.clarity_score,
                    "engagement_score": r.engagement_score,
                    "platform_fit_score": r.platform_fit_score,
                    "overall_score": r.overall_score,
                    "suggestions": r.suggestions,
                }
                for r in reviews.reviews
            ],
            "average_score": reviews.average_score,
            "best_posts": [asdict(p) for p in reviews.best_posts],
            "needs_improvement": [
                {
                    "post": asdict(r.post),
                    "overall_score": r.overall_score,
                    "suggestions": r.suggestions,
                }
                for r in reviews.needs_improvement
            ],
        }
        self.state.set_reviewed_posts(reviews_dict)
        self.state.update_stage("reviewed")

    async def _save_output(self) -> None:
        """Save generated posts to output files."""
        # Create slug from article title
        title = self.state.state.content_analysis.get("article_title", "posts")
        slug = slugify(title)

        # Save JSON output
        json_output_path = self.state.session_dir / f"{slug}_posts.json"
        logger.info(f"\n💾 Saving posts to: {json_output_path.name}")

        output_data = {
            "article": self.state.state.content_analysis.get("article_title"),
            "tone": self.state.state.generated_posts.get("tone_used"),
            "platforms": self.state.state.platforms,
            "generation_time": self.state.state.created_at,
            "average_quality_score": self.state.state.reviewed_posts.get("average_score", 0),
            "posts": self.state.state.generated_posts.get("posts", []),
            "best_posts": self.state.state.reviewed_posts.get("best_posts", []),
            "reviews": self.state.state.reviewed_posts.get("reviews", []),
        }

        try:
            with open(json_output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ JSON output saved: {json_output_path}")
        except Exception as e:
            logger.error(f"Could not save JSON output: {e}")

        # Save markdown output
        md_output_path = self.state.session_dir / f"{slug}_posts.md"
        logger.info(f"💾 Saving markdown to: {md_output_path.name}")

        try:
            md_content = self._format_markdown_output(output_data)
            md_output_path.write_text(md_content, encoding="utf-8")
            logger.info(f"✅ Markdown output saved: {md_output_path}")
        except Exception as e:
            logger.error(f"Could not save markdown output: {e}")

    def _format_markdown_output(self, data: dict) -> str:
        """Format output data as markdown.

        Args:
            data: Output data dictionary

        Returns:
            Formatted markdown string
        """
        lines = []
        lines.append(f"# Social Media Posts: {data['article']}")
        lines.append("")
        lines.append(f"**Generated:** {data['generation_time']}")
        lines.append(f"**Tone:** {data['tone']}")
        lines.append(f"**Average Quality Score:** {data['average_quality_score']:.2f}")
        lines.append("")

        # Group posts by platform
        posts_by_platform = {}
        for post in data["posts"]:
            platform = post["platform"]
            if platform not in posts_by_platform:
                posts_by_platform[platform] = []
            posts_by_platform[platform].append(post)

        # Add best posts section
        if data.get("best_posts"):
            lines.append("## 🌟 Best Posts")
            lines.append("")
            for post in data["best_posts"]:
                lines.append(f"### {post['platform'].title()}")
                lines.append(f"> {post['text']}")
                lines.append(f"*({post['character_count']} chars)*")
                lines.append("")

        # Add all posts by platform
        lines.append("## All Generated Posts")
        lines.append("")

        for platform, posts in posts_by_platform.items():
            lines.append(f"### {platform.title()} Posts")
            lines.append("")
            for i, post in enumerate(posts, 1):
                lines.append(f"**Post {i}:**")
                lines.append(f"> {post['text']}")
                lines.append(f"*({post['character_count']} chars)*")

                # Find review for this post if available
                for review in data.get("reviews", []):
                    if review["post"]["text"] == post["text"]:
                        score = review["overall_score"]
                        lines.append(f"*Quality Score: {score:.2f}*")
                        if review.get("suggestions"):
                            lines.append("*Suggestions:*")
                            for suggestion in review["suggestions"]:
                                lines.append(f"  - {suggestion}")
                        break
                lines.append("")

        return "\n".join(lines)


# CLI Interface
@click.command()
@click.argument("article_path", type=click.Path(exists=True, path_type=Path))
@click.option("--tone", type=str, default=None, help="Override detected tone (e.g., professional, casual)")
@click.option("--guidance", type=str, default=None, help="Additional guidance for post generation")
@click.option("--count", type=int, default=5, help="Number of posts per platform (default: 5)")
@click.option(
    "--platforms",
    type=str,
    default="twitter,linkedin,bluesky",
    help="Comma-separated platforms (default: twitter,linkedin,bluesky)",
)
@click.option("--hashtags", is_flag=True, default=False, help="Include hashtags in posts (default: no hashtags)")
@click.option("--resume", is_flag=True, help="Resume from saved state")
@click.option("--reset", is_flag=True, help="Reset state and start fresh")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def main(
    article_path: Path,
    tone: str | None,
    guidance: str | None,
    count: int,
    platforms: str,
    hashtags: bool,
    resume: bool,
    reset: bool,
    verbose: bool,
):
    """Social Media Post Generator - Transform articles into engaging social posts.

    This tool analyzes your article to extract tone, themes, and key points,
    then generates platform-optimized social media posts with quality review.

    Example:
        python -m scenarios.social_posts article.md

        python -m scenarios.social_posts article.md \\
            --tone inspirational \\
            --platforms twitter,linkedin \\
            --count 3
    """
    # Load environment variables
    load_dotenv()

    # Setup logging
    if verbose:
        logger.logger.setLevel("DEBUG")

    # Parse platforms
    platform_list = [p.strip().lower() for p in platforms.split(",")]

    # Determine session directory
    session_dir = None
    if resume:
        # Find most recent session for resume
        base_dir = Path(".data/social_posts")
        if base_dir.exists():
            sessions = sorted([d for d in base_dir.iterdir() if d.is_dir()], reverse=True)
            if sessions:
                session_dir = sessions[0]
                logger.info(f"Resuming session: {session_dir.name}")

    # Create state manager
    state_manager = StateManager(session_dir)

    # Handle reset
    if reset:
        state_manager.reset()
        logger.info("State reset - starting fresh")

    # Check for resume
    if resume and state_manager.state_file.exists() and not reset:
        logger.info("Resuming from saved state")
        # Use saved parameters if not provided
        if state_manager.state.article_path and article_path is None:
            article_path = Path(state_manager.state.article_path)
        if state_manager.state.tone_override and tone is None:
            tone = state_manager.state.tone_override
        if state_manager.state.guidance and guidance is None:
            guidance = state_manager.state.guidance
        if state_manager.state.count:
            count = state_manager.state.count
        if state_manager.state.platforms:
            platform_list = state_manager.state.platforms

    # Create and run pipeline
    pipeline = SocialPostPipeline(state_manager)

    logger.info("🚀 Starting Social Media Post Generator")
    logger.info(f"  Session: {state_manager.session_dir}")
    logger.info(f"  Article: {article_path.name}")
    logger.info(f"  Platforms: {', '.join(platform_list)}")
    logger.info(f"  Posts per platform: {count}")
    if tone:
        logger.info(f"  Tone override: {tone}")
    if guidance:
        logger.info(f"  Guidance: {guidance}")

    success = asyncio.run(
        pipeline.run(
            article_path=article_path,
            tone_override=tone,
            guidance=guidance,
            count=count,
            platforms=platform_list,
            include_hashtags=hashtags,
        )
    )

    if success:
        logger.info("\n✨ Social post generation complete!")
        logger.info(f"📁 Output saved to: {state_manager.session_dir}")
        return 0
    logger.error("\n❌ Social post generation failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
