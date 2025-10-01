"""Generate engaging social media posts from analyzed content."""

import json
import os
import re
from dataclasses import dataclass
from dataclasses import field

import requests

from amplifier.utils.logger import get_logger

from ..content_analyzer import ContentAnalysis

logger = get_logger(__name__)


@dataclass
class SocialPost:
    """A single social media post."""

    text: str
    platform: str
    character_count: int


@dataclass
class GeneratedPosts:
    """Collection of generated social media posts."""

    posts: list[SocialPost]
    platforms: list[str]
    tone_used: str
    themes_incorporated: list[str] = field(default_factory=list)


class PostGenerator:
    """Generates social media posts from analyzed content."""

    def __init__(self, api_key: str | None = None):
        """Initialize generator with OpenAI API key.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")

    async def generate_posts(
        self,
        analysis: ContentAnalysis,
        article_content: str,
        platforms: list[str] | None = None,
        count: int = 5,
        guidance: str | None = None,
        tone_override: str | None = None,
        include_hashtags: bool = False,
    ) -> GeneratedPosts:
        """Generate social media posts based on content analysis.

        Args:
            analysis: Content analysis results
            article_content: Original article content
            platforms: Target platforms (default: twitter, linkedin, bluesky)
            count: Number of posts to generate per platform
            guidance: Optional additional guidance
            tone_override: Optional tone override
            include_hashtags: Whether to include hashtags in posts

        Returns:
            GeneratedPosts with platform-optimized posts
        """
        platforms = platforms or ["twitter", "linkedin", "bluesky"]
        tone = tone_override or analysis.tone

        logger.info(f"Generating {count} posts per platform")
        logger.info(f"  Platforms: {', '.join(platforms)}")
        logger.info(f"  Tone: {tone}")

        all_posts = []

        for platform in platforms:
            posts = await self._generate_platform_posts(
                platform=platform,
                analysis=analysis,
                article_content=article_content,
                tone=tone,
                count=count,
                guidance=guidance,
                include_hashtags=include_hashtags,
            )
            all_posts.extend(posts)
            logger.info(f"  Generated {len(posts)} {platform} posts")

        return GeneratedPosts(
            posts=all_posts,
            platforms=platforms,
            tone_used=tone,
            themes_incorporated=analysis.themes[:3],  # Top 3 themes
        )

    async def _generate_platform_posts(
        self,
        platform: str,
        analysis: ContentAnalysis,
        article_content: str,
        tone: str,
        count: int,
        guidance: str | None,
        include_hashtags: bool = False,
    ) -> list[SocialPost]:
        """Generate posts for a specific platform.

        Args:
            platform: Target platform
            analysis: Content analysis
            article_content: Article content
            tone: Tone to use
            count: Number of posts
            guidance: Additional guidance
            include_hashtags: Whether to include hashtags

        Returns:
            List of social posts for the platform
        """
        char_limit = self._get_platform_char_limit(platform)
        platform_tips = self._get_platform_tips(platform, include_hashtags)
        length_guidance = self._get_length_guidance(platform)
        tone_instruction = self._get_tone_instruction(tone)

        # Build context from analysis
        themes_text = ", ".join(analysis.themes[:3]) if analysis.themes else "general topics"
        points_text = "\n".join([f"- {p}" for p in analysis.key_points[:5]])
        guidance_text = f"\nAdditional guidance: {guidance}" if guidance else ""

        # Build explicit hashtag instruction
        hashtag_instruction = "" if include_hashtags else "\nNote: Please don't include hashtags in these posts."

        prompt = f"""Create {count} {platform} posts about this article.
{hashtag_instruction}

Article: {analysis.article_title}
Main themes: {themes_text}

Key points to cover:
{points_text}

Platform: {platform}
- Character limit: {char_limit}
- Length guidance: {length_guidance}
- Style: {platform_tips}

Tone and style:
{tone_instruction}

Writing guidelines:
- Use emojis sparingly (only when they add value)
- Exclamation points should be rare
- Focus on providing value and insights
- Be authentic without being overly enthusiastic
{guidance_text}

Article excerpt:
{article_content[:3000]}

Please generate exactly {count} posts as a JSON array of strings.
Each post should be unique and highlight different aspects.
{"Remember: no hashtags for these posts." if not include_hashtags else ""}

Posts:"""

        # LinkedIn posts need much more tokens due to their length (800-1200 chars each)
        max_tokens = 3000 if platform.lower() == "linkedin" else 1000
        response = self._call_openai(prompt, max_tokens=max_tokens, temperature=0.8)
        raw_posts = self._parse_posts_response(response)

        # Convert to SocialPost objects
        posts = []
        for text in raw_posts[:count]:
            # Strip hashtags if not wanted
            if not include_hashtags:
                text = self._strip_hashtags(text)

            # Ensure within character limit
            if len(text) > char_limit:
                text = self._truncate_with_ellipsis(text, char_limit)

            posts.append(
                SocialPost(
                    text=text,
                    platform=platform,
                    character_count=len(text),
                )
            )

        return posts

    def _get_platform_char_limit(self, platform: str) -> int:
        """Get character limit for platform.

        Args:
            platform: Platform name

        Returns:
            Character limit
        """
        limits = {
            "twitter": 280,
            "bluesky": 280,
            "linkedin": 3000,  # LinkedIn allows longer posts
            "mastodon": 500,
            "threads": 500,
        }
        return limits.get(platform.lower(), 280)

    def _get_length_guidance(self, platform: str) -> str:
        """Get platform-specific length guidance."""
        guidance = {
            "linkedin": "LinkedIn posts should be substantial - aim for 800-1200 characters. This is a professional platform where readers expect depth, so use multiple paragraphs to provide context, insights, and analysis.",
            "twitter": "Keep it concise around 200-250 characters to maximize engagement.",
            "bluesky": "Similar to Twitter, 200-280 characters works well.",
            "mastodon": "Use 300-400 characters for more thoughtful content.",
            "threads": "Flexible length, 200-400 characters is a good range.",
        }
        return guidance.get(platform.lower(), "Use appropriate length for the platform.")

    def _get_tone_instruction(self, tone: str) -> str:
        """Get explicit tone instructions."""
        tone_map = {
            "casual": "Write in a relaxed, conversational style. Keep it genuine without being overly enthusiastic.",
            "professional": "Maintain a measured, authoritative tone. Focus on facts and insights without hype.",
            "technical": "Use precise technical language. Focus on accuracy and clarity.",
            "academic": "Use scholarly tone with careful word choice. Present information objectively.",
            "inspirational": "Be uplifting but grounded. Avoid clichés and excessive excitement.",
            "thought-provoking": "Pose questions and insights that encourage reflection.",
            "humorous": "Light humor is fine, but keep it subtle and professional.",
        }
        default = "Write in a measured, professional tone. Be informative rather than promotional. Use enthusiasm sparingly - only when the content genuinely warrants it."
        return tone_map.get(tone.lower(), default)

    def _get_platform_tips(self, platform: str, include_hashtags: bool = False) -> str:
        """Get platform-specific writing tips.

        Args:
            platform: Platform name
            include_hashtags: Whether to include hashtags

        Returns:
            Writing tips for the platform
        """
        base_tips = {
            "twitter": "Be concise and engaging",
            "bluesky": "Slightly more conversational",
            "linkedin": "Professional and substantive with detailed insights",
            "mastodon": "Community-focused and thoughtful",
            "threads": "Casual and conversational",
        }

        hashtag_guidance = {
            "twitter": "Include 1-2 relevant hashtags",
            "bluesky": "Add 1-2 hashtags if relevant",
            "linkedin": "Use 3-5 professional industry hashtags",
            "mastodon": "Include hashtags for discoverability",
            "threads": "Use 1-2 trending hashtags",
        }

        no_hashtag_guidance = {
            "twitter": "Skip the hashtags and focus on the content",
            "bluesky": "No hashtags needed here",
            "linkedin": "Professional insights without hashtags",
            "mastodon": "No hashtags for this one",
            "threads": "No hashtags, just good storytelling",
        }

        platform_key = platform.lower()
        base = base_tips.get(platform_key, "Clear, engaging content")
        hashtag_tip = hashtag_guidance[platform_key] if include_hashtags else no_hashtag_guidance[platform_key]

        return f"{base}. {hashtag_tip}"

    def _truncate_with_ellipsis(self, text: str, limit: int) -> str:
        """Truncate text to limit with ellipsis.

        Args:
            text: Text to truncate
            limit: Character limit

        Returns:
            Truncated text
        """
        if len(text) <= limit:
            return text

        # Leave room for ellipsis
        truncated = text[: limit - 3].rsplit(" ", 1)[0]
        return truncated + "..."

    def _strip_hashtags(self, text: str) -> str:
        """Remove hashtags from text.

        Args:
            text: Text potentially containing hashtags

        Returns:
            Text with hashtags removed
        """
        # Remove hashtags at end of text
        text = re.sub(r"\s*#\w+\s*$", "", text)
        # Remove hashtags anywhere in text
        text = re.sub(r"\s*#\w+", "", text)
        # Clean up extra spaces
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _call_openai(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Call OpenAI API.

        Args:
            prompt: Prompt to send
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Model response
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "gpt-5-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": max_tokens,
        }
        # GPT-5 models only support temperature=1 (default), so we don't include it

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            error_detail = ""
            if response is not None and hasattr(response, "text"):
                error_detail = f" - Response: {response.text}"
            logger.error(f"OpenAI API error: {e}{error_detail}")
            raise

    def _parse_posts_response(self, response: str) -> list[str]:
        """Parse posts from LLM response.

        Args:
            response: Raw LLM response

        Returns:
            List of post texts
        """
        # Remove markdown code blocks
        response = re.sub(r"```[\w]*\n?", "", response)

        # Try to parse as JSON
        try:
            # Look for JSON array
            match = re.search(r"\[.*\]", response, re.DOTALL)
            if match:
                data = json.loads(match.group())
                if isinstance(data, list):
                    return [str(item).strip() for item in data if item]
        except json.JSONDecodeError:
            pass

        # Try to parse JSON object with posts
        try:
            if "{" in response:
                match = re.search(r"\{.*\}", response, re.DOTALL)
                if match:
                    data = json.loads(match.group())
                    if isinstance(data, dict):
                        # Look for posts in various keys
                        for key in ["posts", "tweets", "content", "items"]:
                            if key in data and isinstance(data[key], list):
                                return [str(item).strip() for item in data[key] if item]
        except json.JSONDecodeError:
            pass

        # Fallback: treat lines as posts
        lines = response.strip().split("\n")
        posts = []
        for line in lines:
            # Remove numbering and bullet points
            line = re.sub(r"^\d+\.\s*", "", line)
            line = re.sub(r"^[-*•]\s*", "", line)
            line = line.strip().strip('"').strip("'")
            if line and len(line) > 20:  # Minimum length
                posts.append(line)

        return posts
