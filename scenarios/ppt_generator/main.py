"""Main pipeline orchestrator for PowerPoint generation."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

import click

from amplifier.config.paths import paths

from .content_analysis.core import analyze_context
from .diagram_generation.core import generate_diagrams
from .image_generation.core import generate_images
from .models import PipelineState
from .outline_generation.core import generate_outline
from .ppt_assembly.core import assemble_presentation
from .slide_content.core import generate_slide_content
from .state import StateManager
from .visual_planning.core import determine_visual_needs

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class PPTGeneratorPipeline:
    """Main pipeline for PowerPoint generation."""

    def __init__(self, output_dir: Path):
        """Initialize the pipeline."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.state_mgr = StateManager(self.output_dir)
        self.state: PipelineState | None = None

    def _generate_layout_preview(self) -> Path:
        """Generate markdown preview of slide layouts.

        Returns:
            Path to the generated preview file
        """
        if not self.state or not self.state.slides:
            raise ValueError("No slides available for preview")

        # Import here to avoid linter removing it
        from .layout_preview.core import generate_layout_preview

        preview_file = generate_layout_preview(self.state, self.output_dir)
        logger.info(f"Layout preview generated: {preview_file}")
        return preview_file

    def _save_prompts(self):
        """Save all prompts to prompts.json for diagnostics."""
        if not self.state:
            return

        # Import here to avoid linter removing it
        from .utils.prompts import save_prompts

        save_prompts(self.state.diagrams, self.state.images, self.output_dir)

    async def _get_user_review(self, preview_file: Path):
        """Get user review of the presentation layout.

        Args:
            preview_file: Path to the preview markdown file

        Returns:
            UserReview object with feedback
        """
        # Import here to avoid linter removing it
        from .user_review.core import UserReviewHandler

        handler = UserReviewHandler()
        review = handler.get_user_review(preview_file)
        return review

    async def run(
        self,
        context_files: list[str],
        direction: str,
        template_path: Path | None = None,
        target_slides: int = 10,
        style_images: str = "professional, modern, clean",
        skip_images: bool = False,
        skip_diagrams: bool = False,
        skip_review: bool = False,
        resume: bool = False,
    ) -> Path:
        """Run the PowerPoint generation pipeline.

        Args:
            context_files: List of context file paths
            direction: User's instructions for the presentation
            template_path: Optional PPTX template
            target_slides: Target number of slides
            style_images: Art style for images
            skip_images: Whether to skip image generation
            skip_diagrams: Whether to skip diagram generation
            skip_review: Whether to skip interactive user review stage
            resume: Whether to resume from previous session

        Returns:
            Path to generated PowerPoint file
        """
        # Convert context files to Path objects
        context_paths = [Path(f) for f in context_files]

        # Load or create session
        if resume:
            self.state = self.state_mgr.load()
            if self.state:
                logger.info(f"Resuming from {self.state_mgr.get_resume_point()}")
            else:
                logger.warning("No existing session found, starting new")

        if not self.state:
            self.state = self.state_mgr.initialize(
                context_files=context_paths,
                direction=direction,
                template_path=template_path,
                target_slides=target_slides,
                style_images=style_images,
                skip_images=skip_images,
                skip_diagrams=skip_diagrams,
                skip_review=skip_review,
            )

        try:
            # Stage 1: Context Analysis
            if not self.state.context_analysis_complete:
                logger.info("Stage 1: Analyzing context files...")
                analysis = await analyze_context(
                    context_files=self.state.context_files,
                    direction=self.state.direction,
                    target_slides=self.state.target_slides,
                )
                self.state.analysis = analysis
                self.state_mgr.update_stage("context_analysis")
                logger.info(f"Analysis complete: {len(analysis.main_topics)} topics identified")

            # Stage 2: Outline Generation
            if not self.state.outline_complete:
                logger.info("Stage 2: Generating presentation outline...")
                if not self.state.analysis:
                    raise ValueError("Analysis not completed before outline generation")
                outline = await generate_outline(
                    analysis=self.state.analysis,
                    direction=self.state.direction,
                    target_slides=self.state.target_slides,
                )
                self.state.outline = outline
                self.state_mgr.update_stage("outline")
                logger.info(f"Outline complete: {outline.total_slides} slides planned")

            # Stage 3: Slide Content Generation
            if not self.state.content_complete:
                logger.info("Stage 3: Generating slide content...")
                if not self.state.outline or not self.state.analysis:
                    raise ValueError("Outline or analysis not completed before content generation")
                slides = await generate_slide_content(
                    outline=self.state.outline,
                    analysis=self.state.analysis,
                    direction=self.state.direction,
                )
                self.state.slides = slides
                self.state_mgr.update_stage("content")
                logger.info(f"Content complete: {len(slides)} slides generated")

            # Stage 4: Visual Planning
            if not self.state.visual_planning_complete:
                logger.info("Stage 4: Planning visuals for slides...")
                if not self.state.analysis:
                    raise ValueError("Analysis not completed before visual planning")
                # Convert analysis to dict for context
                analysis_context = {
                    "main_topics": self.state.analysis.main_topics,
                    "technical_level": self.state.analysis.technical_level,
                }
                slides = await determine_visual_needs(
                    slides=self.state.slides,
                    analysis_context=analysis_context,
                )
                self.state.slides = slides
                self.state_mgr.update_stage("visual_planning")

                # Count visual needs
                diagram_count = sum(1 for s in slides if s.visual_type.value in ["diagram", "both"])
                image_count = sum(1 for s in slides if s.visual_type.value in ["image", "both"])
                logger.info(f"Visual planning complete: {diagram_count} diagrams, {image_count} images needed")

            # Stage 5a: Diagram Generation
            if not self.state.diagrams_complete and not self.state.skip_diagrams:
                logger.info("Stage 5a: Generating diagrams...")
                diagrams = await generate_diagrams(
                    slides=self.state.slides,
                    output_dir=self.output_dir,
                )
                self.state.diagrams = diagrams
                self.state_mgr.update_stage("diagrams")
                logger.info(f"Generated {len(diagrams)} diagrams")

            # Stage 5b: Image Generation
            if not self.state.images_complete and not self.state.skip_images:
                logger.info("Stage 5b: Generating images...")
                images = await generate_images(
                    slides=self.state.slides,
                    style_images=self.state.style_images,
                    output_dir=self.output_dir,
                )
                self.state.images = images
                self.state_mgr.update_stage("images")
                logger.info(f"Generated {len(images)} images")

            # Save prompts for diagnostics
            if self.state.diagrams or self.state.images:
                self._save_prompts()

            # Stage 6: Review (New Stage)
            if not self.state.review_complete and not self.state.skip_review:
                logger.info("Stage 6: Generating layout preview for review...")

                # Generate markdown preview with full content
                preview_file = self._generate_layout_preview()

                # Get user review
                logger.info("Getting user review...")
                review = await self._get_user_review(preview_file)
                self.state.user_review = review

                # Apply feedback if provided
                if not review.approved and review.comments:
                    logger.info(f"Applying {len(review.comments)} feedback comments...")

                    # Import feedback processor
                    from .feedback_processor.core import apply_feedback

                    # Ensure we have analysis before applying feedback
                    if not self.state.analysis:
                        logger.error("Cannot apply feedback without context analysis")
                    else:
                        # Apply feedback (regenerate affected slides)
                        self.state.slides = await apply_feedback(
                            slides=self.state.slides,
                            review=review,
                            analysis=self.state.analysis,
                            direction=self.state.direction,
                        )

                        # Save updated state (state_mgr already has reference to self.state)
                        self.state_mgr.save()
                        logger.info("Feedback applied successfully")

                self.state_mgr.update_stage("review")
                logger.info("Review stage complete")

            # Stage 7: PowerPoint Assembly
            if not self.state.ppt_complete:
                logger.info("Stage 7: Assembling PowerPoint presentation...")

                # Determine output filename
                output_filename = "presentation.pptx"
                output_path = self.output_dir / output_filename

                # Assemble presentation
                output_path = await assemble_presentation(
                    slides=self.state.slides,
                    diagrams=self.state.diagrams,
                    images=self.state.images,
                    template_path=self.state.template_path,
                    output_path=output_path,
                )

                self.state.output_file = output_path
                self.state_mgr.update_stage("ppt")
                logger.info(f"Presentation assembled: {output_path}")

            logger.info(f"✅ Presentation complete: {self.state.output_file}")
            logger.info(f"Total cost: ${self.state.total_cost:.4f}")

            if not self.state.output_file:
                raise ValueError("No output file generated")
            return self.state.output_file

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            self.state_mgr.add_error(self.state_mgr.get_resume_point(), str(e))
            raise


@click.group()
def cli():
    """PowerPoint Generator CLI."""
    pass


@cli.command(name="generate", context_settings={"ignore_unknown_options": True})
@click.argument("context_files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--direction", "-d", required=True, help="Instructions for the presentation")
@click.option("--template", "-t", type=click.Path(exists=True, path_type=Path), help="PPTX template file")
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory (default: .data/ppt_generator/{name}_{timestamp})",
)
@click.option("--slides", default=10, help="Target number of slides")
@click.option("--style-images", default="professional, modern, clean", help="Art style for images")
@click.option("--skip-images", is_flag=True, help="Skip image generation")
@click.option("--skip-diagrams", is_flag=True, help="Skip diagram generation")
@click.option("--skip-review", is_flag=True, help="Skip interactive user review stage")
@click.option("--resume", is_flag=True, help="Resume from previous session")
def generate_ppt(
    context_files,
    direction,
    template,
    output_dir,
    slides,
    style_images,
    skip_images,
    skip_diagrams,
    skip_review,
    resume,
):
    """Generate PowerPoint presentation from context files.

    This tool analyzes your context files and generates a complete PowerPoint
    presentation with AI-generated content, diagrams, and images.

    Example:
        amplifier ppt-generator document.md notes.txt -d "Create a sales pitch" --slides 12
    """
    # Convert context files to strings
    context_files = [str(f) for f in context_files]

    # Determine output directory using amplifier paths
    if output_dir is None:
        # Use .data/ppt_generator with timestamp (following article_illustrator pattern)
        base_dir = paths.data_dir / "ppt_generator"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create descriptive name from first context file
        first_file = Path(context_files[0])
        name = first_file.stem

        output_dir = base_dir / f"{name}_{timestamp}"
        logger.info(f"Using output directory: {output_dir}")
    else:
        output_dir = Path(output_dir)

    # Create pipeline
    pipeline = PPTGeneratorPipeline(output_dir=output_dir)

    # Run async pipeline
    try:
        result = asyncio.run(
            pipeline.run(
                context_files=context_files,
                direction=direction,
                template_path=template,
                target_slides=slides,
                style_images=style_images,
                skip_images=skip_images,
                skip_diagrams=skip_diagrams,
                skip_review=skip_review,
                resume=resume,
            )
        )

        click.echo("\n✅ Presentation generated successfully!")
        click.echo(f"📁 Output: {result}")

    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        raise click.ClickException(str(e))


@cli.command(name="create-template")
@click.option("--output", "-o", type=click.Path(path_type=Path), default="my_template.pptx")
def create_template(output):
    """Generate a customizable PowerPoint template."""
    from .template_generator.core import generate_template

    template_path = generate_template(Path(output))
    click.echo(f"✅ Template created: {template_path}")
    click.echo("\nNext steps:")
    click.echo("  1. Open template in PowerPoint")
    click.echo("  2. Customize design (View → Slide Master)")
    click.echo("  3. Save template")
    click.echo(f"  4. Use with: --template {output}")


def main():
    """Main entry point."""
    # If no subcommand, default to 'generate'
    import sys

    if len(sys.argv) > 1 and not sys.argv[1].startswith("-") and sys.argv[1] not in ["generate", "create-template"]:
        # First arg is a file, not a command - insert 'generate'
        sys.argv.insert(1, "generate")
    cli()


if __name__ == "__main__":
    main()
