"""Main orchestrator for style blending pipeline."""

import asyncio
import logging
import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions

from .content_generator import ContentGenerator
from .state import StyleBlenderState
from .style_analyzer import StyleAnalyzer
from .style_blender import StyleBlender

# Load environment variables from .env
load_dotenv()

logger = logging.getLogger(__name__)


def _create_index(state: StyleBlenderState, input_dirs: list[Path], samples_dir: Path) -> str:
    """Create markdown index documenting the style blend.

    Args:
        state: Pipeline state with profiles and blend info
        input_dirs: Input directories/files used
        samples_dir: Directory where samples were saved

    Returns:
        Markdown content for index
    """
    profile = state.blended_profile
    if not profile:
        return "# Style Blend Index\n\nNo profile available."

    # Format source writers
    writers_list = "\n".join(
        f"- **{w}** ({state.style_profiles[w].sample_count} samples)" for w in profile.source_writers
    )

    # Format samples
    samples_list = "\n".join(f"- [{s.name}](output/{s.name})" for s in state.generated_samples)

    return f"""# Style Blend Index

## Source Writers

{writers_list}

## Blended Style Profile

**Strategy:** {profile.blending_strategy}

**Tone:** {profile.tone}
**Vocabulary:** {profile.vocabulary_level}
**Sentence Structure:** {profile.sentence_structure}
**Voice:** {profile.voice}

### Common Phrases
{chr(10).join(f'- "{phrase}"' for phrase in profile.common_phrases)}

### Writing Patterns
{chr(10).join(f"- {pattern}" for pattern in profile.writing_patterns)}

### Example Sentences
{chr(10).join(f"> {ex}" for ex in profile.examples)}

## Generated Samples

{samples_list}

## Usage with blog_writer

```bash
make blog-write IDEA=your_idea.md WRITINGS={samples_dir}
```
"""


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
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize session for state management
    session_opts = SessionOptions()
    session = ClaudeSession(session_opts)

    # Load or create state
    state = StyleBlenderState.load(session) if resume else StyleBlenderState()

    # Update configuration
    state.input_dirs = input_dirs
    state.output_dir = output_dir
    state.num_samples = num_samples

    # Discover writers from files and directories
    writers = []
    for input_path in input_dirs:
        if not input_path.exists():
            logger.warning(f"Input path does not exist: {input_path}")
            continue

        if input_path.is_file():
            # Single file = one writer
            if input_path.suffix in [".md", ".txt"]:
                writers.append(input_path)
            else:
                logger.warning(f"Skipping non-text file: {input_path}")

        elif input_path.is_dir():
            # Check for subdirectories with text files (each = one writer)
            has_subdirs = False
            for subdir in input_path.iterdir():
                # Only include subdirectory if it's a valid dir and has text files
                if (
                    subdir.is_dir()
                    and not subdir.name.startswith(".")
                    and (list(subdir.glob("**/*.md")) or list(subdir.glob("**/*.txt")))
                ):
                    writers.append(subdir)
                    has_subdirs = True

            # If no subdirectories with text, treat directory itself as one writer
            if not has_subdirs and (list(input_path.glob("**/*.md")) or list(input_path.glob("**/*.txt"))):
                writers.append(input_path)

    # Remove duplicates and validate
    writers = list(set(writers))
    if len(writers) < 2:
        logger.error(f"Need at least 2 writers to blend styles, found {len(writers)}")
        if len(writers) == 1:
            logger.error(f"Found: {writers[0].name}")
        logger.error("Tip: Each file or directory with text files = one writer")
        sys.exit(1)

    state.total_writers = len(writers)
    logger.info(f"\n📚 Discovered {len(writers)} writers:")
    for writer_path in writers:
        writer_name = writer_path.stem if writer_path.is_file() else writer_path.name
        if writer_path.is_file():
            logger.info(f"  • {writer_name} (single file)")
        else:
            file_count = len(list(writer_path.glob("**/*.md"))) + len(list(writer_path.glob("**/*.txt")))
            logger.info(f"  • {writer_name} ({file_count} files)")

    # Save initial state
    state.save(session)

    # Stage 1: Analyze styles
    logger.info("\n=== Stage 1: Analyzing Writer Styles ===")
    analyzer = StyleAnalyzer()

    for writer_path in writers:
        writer_name = writer_path.stem if writer_path.is_file() else writer_path.name

        # Skip if already processed
        if state.should_skip_writer(writer_name):
            logger.info(f"Skipping {writer_name} (already processed)")
            continue

        logger.info(f"\nAnalyzing {writer_name}...")
        try:
            profile = await analyzer.extract_style(writer_path)
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

    # Save individual writer profiles for diagnostics
    import json
    from dataclasses import asdict

    for writer_name, profile in state.style_profiles.items():
        profile_json = output_dir / f"writer_{writer_name}.json"
        with open(profile_json, "w") as f:
            json.dump(asdict(profile), f, indent=2)
    logger.info(f"\n💾 Saved {len(state.style_profiles)} individual writer profiles")

    # Stage 2: Blend styles
    logger.info("\n=== Stage 2: Blending Styles ===")
    if state.current_stage != "blended" or not state.blended_profile:
        blender = StyleBlender()
        try:
            blended, blend_prompt = await blender.blend_styles(list(state.style_profiles.values()))
            state.mark_blended(blended)
            state.save(session)

            # Save blended profile to JSON for diagnostics
            import json
            from dataclasses import asdict

            profile_json = output_dir / "blended_profile.json"
            with open(profile_json, "w") as f:
                json.dump(asdict(blended), f, indent=2)
            logger.info(f"  ✓ Saved blended profile to {profile_json.name}")

            # Save blending prompt for diagnostics
            blend_prompt_file = output_dir / "prompt_blending.txt"
            blend_prompt_file.write_text(blend_prompt)
            logger.info(f"  ✓ Saved blending prompt to {blend_prompt_file.name}")

            logger.info("  ✓ Successfully blended styles from all writers")
        except Exception as e:
            logger.error(f"  ✗ Failed to blend styles: {e}")
            sys.exit(1)
    else:
        logger.info("  → Using previously blended profile")

    # Stage 3: Generate sample writings
    logger.info(f"\n=== Stage 3: Generating {num_samples} Sample Writings ===")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create output subdirectory for samples
    samples_dir = output_dir / "output"
    samples_dir.mkdir(exist_ok=True)

    generator = ContentGenerator()
    already_generated = len(state.generated_samples)

    if not state.blended_profile:
        logger.error("No blended profile available")
        sys.exit(1)

    for i in range(already_generated, num_samples):
        logger.info(f"\nGenerating sample {i + 1}/{num_samples}...")
        try:
            sample, prompt = await generator.generate_sample(
                state.blended_profile,
                sample_number=i + 1,
                topic_hint=f"sample_{i + 1}",
            )

            # Save sample to output/ subdirectory
            output_file = samples_dir / f"blended_sample_{i + 1:02d}.md"
            output_file.write_text(sample)

            # Save prompt for diagnostics
            prompt_file = output_dir / f"prompt_sample_{i + 1:02d}.txt"
            prompt_file.write_text(prompt)

            state.add_generated_sample(output_file)
            state.save(session)  # Save after each sample
            logger.info(f"  ✓ Saved to output/{output_file.name}")
        except Exception as e:
            logger.error(f"  ✗ Failed to generate sample {i + 1}: {e}")
            state.error_messages.append(f"Failed to generate sample {i + 1}: {e}")

    # Create index documenting the blend
    if state.blended_profile and state.generated_samples:
        index_path = output_dir / "index.md"
        index_content = _create_index(state, input_dirs, samples_dir)
        index_path.write_text(index_content)
        logger.info(f"\n📋 Created index: {index_path.name}")

    # Summary
    logger.info("\n=== Pipeline Complete ===")
    logger.info(f"Writers analyzed: {len(state.style_profiles)}")
    logger.info(f"Samples generated: {len(state.generated_samples)}")
    logger.info(f"Session directory: {output_dir}")

    if state.error_messages:
        logger.warning(f"\nEncountered {len(state.error_messages)} errors:")
        for msg in state.error_messages[:3]:
            logger.warning(f"  • {msg}")

    logger.info("\n✨ Blended samples are ready for use with blog_writer:")
    logger.info(f"  make blog-write IDEA=your_idea.md WRITINGS={samples_dir}")


@click.command()
@click.option(
    "--input-dirs",
    "-i",
    multiple=True,
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Files or directories containing writer samples (file=1 writer, dir=multiple writers)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory to save blended samples (default: .data/style_blender/<timestamp>/)",
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
    output_dir: Path | None,
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

    # Check API key requirement
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("❌ ANTHROPIC_API_KEY not found in environment")
        logger.error("")
        logger.error("Style blending requires Claude AI to analyze and blend writing styles.")
        logger.error("Please set your API key:")
        logger.error("  export ANTHROPIC_API_KEY='your-key-here'")
        logger.error("")
        logger.error("Get your API key at: https://console.anthropic.com/")
        sys.exit(1)

    # Create session directory if no output specified
    if output_dir is None:
        from datetime import datetime

        base_dir = Path(".data/style_blender")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = base_dir / timestamp
        logger.info(f"📁 Session directory: {output_dir}")

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
