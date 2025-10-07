"""Main orchestrator for style blending pipeline."""

import asyncio
import logging
import sys
from pathlib import Path

import click

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions

from .content_generator import ContentGenerator
from .state import StyleBlenderState
from .style_analyzer import StyleAnalyzer
from .style_blender import StyleBlender

logger = logging.getLogger(__name__)


async def run_pipeline(
    input_dirs: list[Path],
    output_dir: Path,
    num_samples: int = 3,
    resume: bool = False,
) -> None:
    """Run the complete style blending pipeline.

    Args:
        input_dirs: List of directories containing writer samples
        output_dir: Directory to save blended samples
        num_samples: Number of sample writings to generate
        resume: Whether to resume from saved state
    """
    # Initialize session for state management
    session_opts = SessionOptions()
    session = ClaudeSession(session_opts)

    # Load or create state
    state = StyleBlenderState.load(session) if resume else StyleBlenderState()

    # Update configuration
    state.input_dirs = input_dirs
    state.output_dir = output_dir
    state.num_samples = num_samples

    # Discover writer directories
    writers = []
    for input_dir in input_dirs:
        if not input_dir.exists():
            logger.warning(f"Input directory does not exist: {input_dir}")
            continue

        # Each subdirectory is a writer
        for writer_dir in input_dir.iterdir():
            if writer_dir.is_dir() and not writer_dir.name.startswith("."):
                writers.append(writer_dir)

        # Also check if input_dir itself contains writing samples
        if list(input_dir.glob("**/*.md")) or list(input_dir.glob("**/*.txt")):
            writers.append(input_dir)

    # Remove duplicates and validate
    writers = list(set(writers))
    if len(writers) < 2:
        logger.error(f"Need at least 2 writers to blend styles, found {len(writers)}")
        sys.exit(1)

    state.total_writers = len(writers)
    logger.info(f"Processing {len(writers)} writers:")
    for writer in writers[:3]:
        logger.info(f"  • {writer.name}")
    if len(writers) > 3:
        logger.info(f"  ... and {len(writers) - 3} more")

    # Save initial state
    state.save(session)

    # Stage 1: Analyze styles
    logger.info("\n=== Stage 1: Analyzing Writer Styles ===")
    analyzer = StyleAnalyzer()

    for writer_dir in writers:
        writer_name = writer_dir.name

        # Skip if already processed
        if state.should_skip_writer(writer_name):
            logger.info(f"Skipping {writer_name} (already processed)")
            continue

        logger.info(f"\nAnalyzing {writer_name}...")
        try:
            profile = await analyzer.extract_style(writer_dir)
            profile.writer_name = writer_name
            state.add_style_profile(writer_name, profile)
            state.save(session)  # Save after each writer
            logger.info(f"  ✓ Extracted style profile for {writer_name}")
        except Exception as e:
            logger.error(f"  ✗ Failed to analyze {writer_name}: {e}")
            state.error_messages.append(f"Failed to analyze {writer_name}: {e}")
            continue

    # Validate we have enough profiles
    if len(state.style_profiles) < 2:
        logger.error(f"Need at least 2 style profiles, only have {len(state.style_profiles)}")
        sys.exit(1)

    # Stage 2: Blend styles
    logger.info("\n=== Stage 2: Blending Styles ===")
    if state.current_stage != "blended" or not state.blended_profile:
        blender = StyleBlender()
        try:
            blended = await blender.blend_styles(list(state.style_profiles.values()))
            state.mark_blended(blended)
            state.save(session)
            logger.info("  ✓ Successfully blended styles from all writers")
        except Exception as e:
            logger.error(f"  ✗ Failed to blend styles: {e}")
            sys.exit(1)
    else:
        logger.info("  → Using previously blended profile")

    # Stage 3: Generate sample writings
    logger.info(f"\n=== Stage 3: Generating {num_samples} Sample Writings ===")
    output_dir.mkdir(parents=True, exist_ok=True)

    generator = ContentGenerator()
    already_generated = len(state.generated_samples)

    if not state.blended_profile:
        logger.error("No blended profile available")
        sys.exit(1)

    for i in range(already_generated, num_samples):
        logger.info(f"\nGenerating sample {i + 1}/{num_samples}...")
        try:
            sample = await generator.generate_sample(
                state.blended_profile,
                sample_number=i + 1,
                topic_hint=f"sample_{i + 1}",
            )

            # Save sample
            output_file = output_dir / f"blended_sample_{i + 1:02d}.md"
            output_file.write_text(sample)
            state.add_generated_sample(output_file)
            state.save(session)  # Save after each sample
            logger.info(f"  ✓ Saved to {output_file.name}")
        except Exception as e:
            logger.error(f"  ✗ Failed to generate sample {i + 1}: {e}")
            state.error_messages.append(f"Failed to generate sample {i + 1}: {e}")

    # Summary
    logger.info("\n=== Pipeline Complete ===")
    logger.info(f"Writers analyzed: {len(state.style_profiles)}")
    logger.info(f"Samples generated: {len(state.generated_samples)}")
    logger.info(f"Output directory: {output_dir}")

    if state.error_messages:
        logger.warning(f"\nEncountered {len(state.error_messages)} errors:")
        for msg in state.error_messages[:3]:
            logger.warning(f"  • {msg}")

    logger.info("\nBlended samples are ready for use with blog_writer:")
    logger.info(f"  python -m scenarios.blog_writer --writings-dir {output_dir} ...")


@click.command()
@click.option(
    "--input-dirs",
    "-i",
    multiple=True,
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Directories containing writer samples (can specify multiple)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("blended_samples"),
    help="Directory to save blended samples",
)
@click.option(
    "--num-samples",
    "-n",
    type=int,
    default=3,
    help="Number of sample writings to generate (default: 3)",
)
@click.option(
    "--resume",
    is_flag=True,
    help="Resume from saved state",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def main(
    input_dirs: tuple[Path, ...],
    output_dir: Path,
    num_samples: int,
    resume: bool,
    verbose: bool,
) -> None:
    """Blend writing styles from multiple authors to create new samples.

    This tool analyzes writing samples from multiple authors, blends their
    styles, and generates new writing samples that combine elements from
    all source writers. Perfect for creating style samples for blog_writer.

    Examples:

        # Blend styles from two writers:
        python -m scenarios.style_blender -i writer1/ -i writer2/ -o blended/

        # Generate 5 samples from multiple sources:
        python -m scenarios.style_blender -i writers/ -o samples/ -n 5

        # Resume interrupted session:
        python -m scenarios.style_blender -i writers/ -o samples/ --resume
    """
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=[logging.StreamHandler()],
    )

    # Validate inputs
    if not input_dirs:
        logger.error("No input directories specified")
        sys.exit(1)

    # Run async pipeline
    try:
        asyncio.run(run_pipeline(list(input_dirs), output_dir, num_samples, resume))
    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user. Progress saved - use --resume to continue.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
