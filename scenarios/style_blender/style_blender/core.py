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

    async def blend_styles(self, profiles: list[StyleProfile]) -> BlendedStyleProfile:
        """Blend multiple style profiles into one.

        Args:
            profiles: List of style profiles to blend

        Returns:
            BlendedStyleProfile combining all inputs
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
                data = parse_llm_json(response.content)

            if not isinstance(data, dict):
                raise ValueError("Invalid response format")

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
            logger.warning(f"  AI blending failed, using statistical blend: {e}")
            # Fallback to pure statistical blending
            blended = self._statistical_blend(profiles, blended, all_phrases, all_patterns, all_examples)

        return blended

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

Create a blended style that:
1. Combines the best elements from each writer
2. Creates a coherent, unified voice
3. Maintains readability and flow

Return a JSON object with:
- blended_tone: A tone that combines elements from all writers
- blended_vocabulary: Appropriate vocabulary level
- blended_sentence_structure: Sentence pattern approach
- blended_voice: Voice preference (active/passive balance)
- selected_phrases: List of 5 phrases that work well together
- selected_patterns: List of 5 writing patterns to use
- synthesized_examples: List of 3 example sentences in the blended style
- strategy: Brief description of the blending approach (1 sentence)
- attribution: Object mapping writer names to their main contributions

Focus on creating a natural, coherent blend rather than awkward combinations."""

    def _statistical_blend(
        self,
        profiles: list[StyleProfile],
        blended: BlendedStyleProfile,
        all_phrases: list[str],
        all_patterns: list[str],
        all_examples: list[str],
    ) -> BlendedStyleProfile:
        """Fallback statistical blending when AI fails."""
        # Most common values
        tones = [p.tone for p in profiles]
        vocabs = [p.vocabulary_level for p in profiles]
        structures = [p.sentence_structure for p in profiles]
        voices = [p.voice for p in profiles]

        blended.tone = Counter(tones).most_common(1)[0][0] if tones else "conversational"
        blended.vocabulary_level = Counter(vocabs).most_common(1)[0][0] if vocabs else "moderate"
        blended.sentence_structure = Counter(structures).most_common(1)[0][0] if structures else "varied"
        blended.voice = Counter(voices).most_common(1)[0][0] if voices else "mostly active"

        # Select diverse phrases and patterns
        blended.common_phrases = list(dict.fromkeys(all_phrases))[:5]
        blended.writing_patterns = list(dict.fromkeys(all_patterns))[:5]
        blended.examples = all_examples[:3]

        blended.blending_strategy = "statistical averaging of common elements"

        # Simple attribution
        blended.attribution = {p.writer_name: [p.tone] for p in profiles}

        return blended
