"""Core style analyzer implementation."""

import logging
from pathlib import Path

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json

from ..state import StyleProfile

logger = logging.getLogger(__name__)


class StyleAnalyzer:
    """Extracts style profiles from writer samples."""

    def __init__(self):
        """Initialize the style analyzer."""
        pass  # Session will be created when needed

    async def extract_style(self, writer_dir: Path) -> StyleProfile:
        """Extract style profile from a writer's samples.

        Args:
            writer_dir: Directory containing writer's samples

        Returns:
            StyleProfile for the writer
        """
        # Discover files recursively
        files = list(writer_dir.glob("**/*.md"))
        files.extend(list(writer_dir.glob("**/*.txt")))

        if not files:
            logger.warning(f"No text files found in {writer_dir}")
            return self._default_profile()

        logger.info(f"  Found {len(files)} samples")

        # Read samples (limit to prevent context overflow)
        samples = []
        max_samples = 5
        max_chars_per_sample = 3000

        for file in files[:max_samples]:
            try:
                content = file.read_text()[:max_chars_per_sample]
                samples.append(f"=== {file.name} ===\n{content}")
            except Exception as e:
                logger.warning(f"  Could not read {file.name}: {e}")

        if not samples:
            logger.warning(f"  Could not read any samples from {writer_dir}")
            return self._default_profile()

        # Extract style with AI
        combined_samples = "\n\n".join(samples)
        prompt = f"""Analyze these writing samples and extract the author's style profile.

WRITING SAMPLES:
{combined_samples}

Extract the following style elements:

1. tone: Overall tone (e.g., formal, conversational, technical, humorous, academic)
2. vocabulary_level: Vocabulary complexity (simple, moderate, advanced)
3. sentence_structure: Typical sentence patterns (e.g., short and punchy, complex and flowing, varied)
4. paragraph_length: Typical paragraph length preference (short, medium, long, varied)
5. common_phrases: List 3-5 frequently used phrases or expressions
6. writing_patterns: List 3-5 structural patterns (e.g., starts with questions, uses lists, includes examples)
7. voice: Active vs passive voice preference (mostly active, mostly passive, balanced)
8. examples: List 2-3 example sentences that best capture the author's style

Return ONLY a JSON object with these fields. Do not include any other text or explanation."""

        try:
            # Use ClaudeSession for querying
            session_opts = SessionOptions()
            async with ClaudeSession(session_opts) as session:
                response = await session.query(prompt)
                data = parse_llm_json(response.content)

            if not isinstance(data, dict):
                raise ValueError("Invalid response format")

            return StyleProfile(
                writer_name=writer_dir.name,
                tone=data.get("tone", "conversational"),
                vocabulary_level=data.get("vocabulary_level", "moderate"),
                sentence_structure=data.get("sentence_structure", "varied"),
                paragraph_length=data.get("paragraph_length", "medium"),
                common_phrases=data.get("common_phrases", [])[:5],
                writing_patterns=data.get("writing_patterns", [])[:5],
                voice=data.get("voice", "mostly active"),
                examples=data.get("examples", [])[:3],
                sample_count=len(files),
            )
        except Exception as e:
            logger.error(f"  Failed to extract style: {e}")
            return self._default_profile()

    def _default_profile(self) -> StyleProfile:
        """Return a default style profile when extraction fails."""
        return StyleProfile(
            writer_name="unknown",
            tone="conversational",
            vocabulary_level="moderate",
            sentence_structure="varied",
            paragraph_length="medium",
            common_phrases=["for example", "in other words", "this means that"],
            writing_patterns=["uses examples", "explains concepts", "provides context"],
            voice="mostly active",
            examples=["This is how it works.", "Let me explain why.", "Consider this example."],
            sample_count=0,
        )
