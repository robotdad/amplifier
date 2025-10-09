"""Core content generation implementation."""

import logging

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions

from ..state import BlendedStyleProfile

logger = logging.getLogger(__name__)

# Topic categories for variety
TOPIC_CATEGORIES = [
    "technology and innovation",
    "personal development",
    "business and entrepreneurship",
    "science and discovery",
    "creativity and arts",
    "health and wellness",
    "education and learning",
    "society and culture",
    "environment and sustainability",
    "future trends",
]


class ContentGenerator:
    """Generates sample writings using blended style profiles."""

    def __init__(self):
        """Initialize the content generator."""
        pass  # Session will be created when needed

    async def generate_sample(
        self,
        profile: BlendedStyleProfile,
        sample_number: int = 1,
        topic_hint: str | None = None,
    ) -> tuple[str, str]:
        """Generate a sample writing in the blended style.

        Args:
            profile: Blended style profile to use
            sample_number: Sample number (for variety)
            topic_hint: Optional topic hint

        Returns:
            Tuple of (generated markdown content, prompt used)
        """
        # Select topic category
        category = TOPIC_CATEGORIES[(sample_number - 1) % len(TOPIC_CATEGORIES)]

        # Build generation prompt
        prompt = self._build_generation_prompt(profile, category, sample_number)

        try:
            # Use ClaudeSession for querying
            session_opts = SessionOptions()
            async with ClaudeSession(session_opts) as session:
                response = await session.query(prompt)
                content = response.content.strip()

            # Ensure it starts with a title
            if not content.startswith("#"):
                lines = content.split("\n")
                if lines and not lines[0].startswith("#"):
                    # Generate a title from first line
                    title = lines[0][:50].strip().title()
                    content = f"# {title}\n\n{content}"

            return content, prompt

        except Exception as e:
            logger.error(f"  Failed to generate sample: {e}")
            # Return a fallback sample
            return self._generate_fallback(category, sample_number), prompt

    def _build_generation_prompt(
        self,
        profile: BlendedStyleProfile,
        category: str,
        sample_number: int,
    ) -> str:
        """Build prompt for content generation."""
        # Format style elements
        phrases_text = (
            f"Common phrases to naturally incorporate: {', '.join(profile.common_phrases)}"
            if profile.common_phrases
            else ""
        )

        patterns_text = (
            f"Writing patterns to follow: {', '.join(profile.writing_patterns)}" if profile.writing_patterns else ""
        )

        examples_text = ""
        if profile.examples:
            examples_text = "Example sentences in this style:\n" + "\n".join(f"- {ex}" for ex in profile.examples[:2])

        return f"""Write a blog post in the following blended writing style.

STYLE PROFILE:
- Tone: {profile.tone}
- Vocabulary level: {profile.vocabulary_level}
- Sentence structure: {profile.sentence_structure}
- Paragraph length: {profile.paragraph_length}
- Voice preference: {profile.voice}
- Blending approach: {profile.blending_strategy}

{phrases_text}
{patterns_text}

{examples_text}

REQUIREMENTS:
- Topic category: {category}
- Length: 300-500 words
- Format: Markdown with a clear title (use # for title)
- Make it engaging and authentic to the style
- Vary the specific topic (sample #{sample_number})

Write a complete, self-contained blog post that demonstrates this blended writing style naturally.
Do not include any meta-commentary about the style itself."""

    def _generate_fallback(self, category: str, sample_number: int) -> str:
        """Generate a simple fallback sample if AI fails."""
        titles = {
            "technology and innovation": "The Future of Digital Connection",
            "personal development": "Small Steps, Big Changes",
            "business and entrepreneurship": "Building Something That Matters",
            "science and discovery": "Understanding Our Complex World",
            "creativity and arts": "Finding Your Creative Voice",
            "health and wellness": "The Path to Better Living",
            "education and learning": "Learning in the Modern Age",
            "society and culture": "Communities in Transition",
            "environment and sustainability": "Choices for Tomorrow",
            "future trends": "What Comes Next",
        }

        title = titles.get(category, "Thoughts on Progress")

        return f"""# {title}

We live in interesting times. The pace of change continues to accelerate, bringing both
opportunities and challenges. As we navigate this evolving landscape, certain patterns
emerge that help us make sense of it all.

Consider how much has shifted in recent years. What seemed impossible a decade ago is
now commonplace. This transformation touches every aspect of our lives, from how we
work to how we connect with others.

The key is finding balance. While embracing new possibilities, we must also remember
the fundamental principles that guide us. Innovation works best when it builds upon a
foundation of understanding and purpose.

Looking ahead, the path forward requires both courage and wisdom. We need to be willing
to experiment and learn, while also being thoughtful about the implications of our choices.
Each decision we make today shapes the world of tomorrow.

This is our opportunity. By approaching challenges with curiosity and determination, we
can create meaningful progress. The future isn't something that happens to us - it's
something we actively shape through our actions and intentions.

The journey continues, and there's much work to be done. But with the right mindset and
collaborative spirit, we can build something truly worthwhile.
"""
