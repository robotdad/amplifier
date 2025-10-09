"""Core style blending implementation."""

import logging
from collections import Counter

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json

from ..state import BlendedStyleProfile
from ..state import StyleProfile

logger = logging.getLogger(__name__)


class StyleBlender:
    """Blends multiple writing styles into a unified profile."""

    def __init__(self):
        """Initialize the style blender."""
        pass  # Session will be created when needed

    async def blend_styles(self, profiles: list[StyleProfile]) -> tuple[BlendedStyleProfile, str]:
        """Blend multiple style profiles into one.

        Args:
            profiles: List of style profiles to blend

        Returns:
            Tuple of (BlendedStyleProfile combining all inputs, prompt used)
        """
        if len(profiles) < 2:
            raise ValueError(f"Need at least 2 profiles to blend, got {len(profiles)}")

        logger.info(f"  Blending {len(profiles)} style profiles...")

        # Statistical blending for structural elements
        blended = BlendedStyleProfile()
        blended.source_writers = [p.writer_name for p in profiles]

        # Analyze paragraph lengths
        para_lengths = [p.paragraph_length for p in profiles]
        para_counter = Counter(para_lengths)
        if para_counter.most_common(1)[0][1] >= len(profiles) / 2:
            # Majority agreement
            blended.paragraph_length = para_counter.most_common(1)[0][0]
        else:
            # No consensus - use varied
            blended.paragraph_length = "varied"

        # Collect all phrases and patterns
        all_phrases = []
        all_patterns = []
        all_examples = []

        for profile in profiles:
            all_phrases.extend(profile.common_phrases)
            all_patterns.extend(profile.writing_patterns)
            all_examples.extend(profile.examples)

        # Use AI to synthesize tone, voice, and style elements
        prompt = self._build_blending_prompt(profiles)

        try:
            # Use ClaudeSession for querying
            session_opts = SessionOptions()
            async with ClaudeSession(session_opts) as session:
                response = await session.query(prompt)

                # Log response for debugging
                if not response.content:
                    raise ValueError("Empty response from AI service")

                logger.debug(f"AI response (first 500 chars): {response.content[:500]}")

                # Parse JSON response
                data = parse_llm_json(response.content)

                if not data:
                    # Show actual response to help debug
                    logger.error("❌ Failed to parse JSON from AI response")
                    logger.error(f"Response (first 1000 chars):\n{response.content[:1000]}")
                    raise ValueError("Could not extract JSON from AI response - see above")

                if not isinstance(data, dict):
                    logger.error(f"❌ AI returned {type(data)} instead of dict: {data}")
                    raise ValueError(f"Expected dict, got {type(data)}")

            # Apply AI-generated blend
            blended.tone = data.get("blended_tone", "balanced")
            blended.vocabulary_level = data.get("blended_vocabulary", "moderate")
            blended.sentence_structure = data.get("blended_sentence_structure", "varied")
            blended.voice = data.get("blended_voice", "mostly active")
            blended.blending_strategy = data.get("strategy", "harmonious blend")

            # Select most representative phrases and patterns
            blended.common_phrases = data.get("selected_phrases", all_phrases[:5])
            blended.writing_patterns = data.get("selected_patterns", all_patterns[:5])
            blended.examples = data.get("synthesized_examples", all_examples[:3])

            # Track attribution
            blended.attribution = data.get("attribution", {})

            logger.info(f"  ✓ Blending strategy: {blended.blending_strategy}")

        except Exception as e:
            logger.error(f"❌ Style blending failed: {e}")
            logger.error("")
            logger.error("This usually means:")
            logger.error("  1. Missing or invalid ANTHROPIC_API_KEY")
            logger.error("  2. Network connection issues")
            logger.error("  3. AI service temporarily unavailable")
            raise

        return blended, prompt

    def _build_blending_prompt(self, profiles: list[StyleProfile]) -> str:
        """Build prompt for AI-powered style blending."""
        profile_descriptions = []
        for p in profiles:
            desc = f"""Writer: {p.writer_name}
- Tone: {p.tone}
- Vocabulary: {p.vocabulary_level}
- Sentence structure: {p.sentence_structure}
- Voice: {p.voice}
- Common phrases: {", ".join(p.common_phrases[:3]) if p.common_phrases else "none"}
- Patterns: {", ".join(p.writing_patterns[:3]) if p.writing_patterns else "none"}"""
            profile_descriptions.append(desc)

        combined = "\n\n".join(profile_descriptions)

        return f"""Analyze these writing style profiles and create a blended style that harmoniously combines elements from all writers.

STYLE PROFILES:
{combined}

Create a blended style combining the best elements from each writer. Extract:

1. blended_tone: Combined tone (e.g., "technical yet conversational", "formal with humor", "academic but accessible")
2. blended_vocabulary: Overall vocabulary level (simple, moderate, advanced, mixed)
3. blended_sentence_structure: Combined sentence patterns (e.g., "varied - mix of short punchy and complex flowing")
4. blended_voice: Voice preference (mostly active, mostly passive, balanced)
5. selected_phrases: List of 5 phrases from the writers that work well together
6. selected_patterns: List of 5 writing patterns to combine (e.g., "uses examples", "asks questions", "tells stories")
7. synthesized_examples: List of 3 example sentences demonstrating the blended style
8. strategy: One sentence describing how you blended these styles
9. attribution: Object with writer names as keys, each listing 2-3 main contributions from that writer

Return ONLY a JSON object with these exact fields. Do not include any other text or explanation."""
