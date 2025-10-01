"""Content analysis for extracting tone, themes, and key points from articles."""

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

import requests

from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ContentAnalysis:
    """Results from content analysis."""

    tone: str
    themes: list[str]
    key_points: list[str]
    article_title: str
    word_count: int


class ContentAnalyzer:
    """Analyzes article content to extract tone, themes, and key points."""

    def __init__(self, api_key: str | None = None):
        """Initialize analyzer with OpenAI API key.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")

    async def analyze_content(self, article_path: Path) -> ContentAnalysis:
        """Analyze article content to extract tone, themes, and key points.

        Args:
            article_path: Path to article markdown file

        Returns:
            ContentAnalysis with extracted information
        """
        # Read article
        content = article_path.read_text(encoding="utf-8")

        # Extract title
        title = self._extract_title(content, article_path)

        # Count words
        word_count = len(content.split())

        logger.info(f"Analyzing article: {title}")
        logger.info(f"  Word count: {word_count}")

        # Analyze tone
        tone = await self._analyze_tone(content)
        logger.info(f"  Detected tone: {tone}")

        # Extract themes and key points
        themes, key_points = await self._extract_themes_and_points(content)
        logger.info(f"  Found {len(themes)} themes, {len(key_points)} key points")

        return ContentAnalysis(
            tone=tone,
            themes=themes,
            key_points=key_points,
            article_title=title,
            word_count=word_count,
        )

    def _extract_title(self, content: str, file_path: Path) -> str:
        """Extract title from content or filename.

        Args:
            content: Article content
            file_path: Path to article file

        Returns:
            Article title
        """
        lines = content.split("\n")
        for line in lines[:10]:
            if line.startswith("# "):
                return line[2:].strip()

        # Fallback to filename
        return file_path.stem.replace("-", " ").replace("_", " ").title()

    async def _analyze_tone(self, content: str) -> str:
        """Analyze the tone of the article.

        Args:
            content: Article content

        Returns:
            Detected tone
        """
        prompt = f"""Analyze the tone of this article and return a single descriptive word or short phrase.

Choose the MOST APPROPRIATE from these options:
- professional (business-focused, formal)
- casual (relaxed, conversational)
- technical (detailed, specialized)
- academic (scholarly, research-based)
- thought-provoking (analytical, questioning)
- inspirational (motivational, uplifting)
- humorous (light, entertaining)

Avoid generic terms like "engaging" or "informative".
Focus on the writing style, not the content enthusiasm.

Article:
{content[:3000]}

Return only the tone, nothing else."""

        response = self._call_openai(prompt, max_tokens=50, temperature=0.3)
        return self._clean_response(response)

    async def _extract_themes_and_points(self, content: str) -> tuple[list[str], list[str]]:
        """Extract main themes and key points from article.

        Args:
            content: Article content

        Returns:
            Tuple of (themes, key_points)
        """
        prompt = f"""Analyze this article and extract:
1. Main themes (3-5 broad topics)
2. Key points (5-7 specific insights or arguments)

Return as JSON with this structure:
{{
    "themes": ["theme1", "theme2", ...],
    "key_points": ["point1", "point2", ...]
}}

Article:
{content[:4000]}

JSON:"""

        response = self._call_openai(prompt, max_tokens=500, temperature=0.3)

        try:
            # Clean and parse JSON
            json_str = self._extract_json(response)
            data = json.loads(json_str)
            themes = data.get("themes", [])[:5]
            key_points = data.get("key_points", [])[:7]
            return themes, key_points
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse themes/points: {e}")
            return [], []

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
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

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
            logger.error(f"OpenAI API error: {e}")
            raise

    def _clean_response(self, response: str) -> str:
        """Clean LLM response to extract plain text.

        Args:
            response: Raw LLM response

        Returns:
            Cleaned text
        """
        # Remove markdown code blocks
        response = re.sub(r"```[\w]*\n?", "", response)
        response = response.strip()

        # If it's JSON, try to extract a field
        if response.startswith("{"):
            try:
                data = json.loads(response)
                if isinstance(data, dict) and "tone" in data:
                    return data["tone"]
            except json.JSONDecodeError:
                pass

        return response

    def _extract_json(self, response: str) -> str:
        """Extract JSON from LLM response.

        Args:
            response: LLM response possibly containing JSON

        Returns:
            Extracted JSON string
        """
        # Remove markdown code blocks
        response = re.sub(r"```(?:json)?\n?", "", response)

        # Find JSON object or array
        match = re.search(r"(\{.*\}|\[.*\])", response, re.DOTALL)
        if match:
            return match.group(1)

        return response.strip()
