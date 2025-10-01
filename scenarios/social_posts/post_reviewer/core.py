"""Review and score social media posts for quality and engagement potential."""

import json
import os
import re
from dataclasses import dataclass
from dataclasses import field

import requests

from amplifier.utils.logger import get_logger

from ..content_analyzer import ContentAnalysis
from ..post_generator import GeneratedPosts
from ..post_generator import SocialPost

logger = get_logger(__name__)


@dataclass
class PostReview:
    """Review results for a single post."""

    post: SocialPost
    clarity_score: float  # 0-1: How clear and understandable
    engagement_score: float  # 0-1: Potential for likes/shares
    platform_fit_score: float  # 0-1: How well it fits platform norms
    overall_score: float  # 0-1: Combined score
    suggestions: list[str] = field(default_factory=list)


@dataclass
class ReviewedPosts:
    """Collection of reviewed posts with quality scores."""

    reviews: list[PostReview]
    average_score: float
    best_posts: list[SocialPost]  # Top-scoring posts
    needs_improvement: list[PostReview]  # Posts with low scores


class PostReviewer:
    """Reviews generated posts for quality and engagement potential."""

    def __init__(self, api_key: str | None = None):
        """Initialize reviewer with OpenAI API key.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")

    async def review_posts(
        self,
        generated_posts: GeneratedPosts,
        content_analysis: ContentAnalysis,
        min_score_threshold: float = 0.7,
    ) -> ReviewedPosts:
        """Review generated posts for quality.

        Args:
            generated_posts: Posts to review
            content_analysis: Original content analysis
            min_score_threshold: Minimum score to be considered good

        Returns:
            ReviewedPosts with scores and suggestions
        """
        logger.info(f"Reviewing {len(generated_posts.posts)} posts...")

        reviews = []
        for post in generated_posts.posts:
            review = await self._review_single_post(
                post=post,
                content_analysis=content_analysis,
                tone=generated_posts.tone_used,
            )
            reviews.append(review)

        # Calculate average score
        total_score = sum(r.overall_score for r in reviews)
        average_score = total_score / len(reviews) if reviews else 0

        # Identify best posts and those needing improvement
        sorted_reviews = sorted(reviews, key=lambda r: r.overall_score, reverse=True)
        best_posts = [r.post for r in sorted_reviews if r.overall_score >= min_score_threshold][:5]
        needs_improvement = [r for r in sorted_reviews if r.overall_score < min_score_threshold]

        logger.info(f"  Average score: {average_score:.2f}")
        logger.info(f"  Best posts: {len(best_posts)}")
        logger.info(f"  Needs improvement: {len(needs_improvement)}")

        return ReviewedPosts(
            reviews=reviews,
            average_score=average_score,
            best_posts=best_posts,
            needs_improvement=needs_improvement,
        )

    async def _review_single_post(
        self,
        post: SocialPost,
        content_analysis: ContentAnalysis,
        tone: str,
    ) -> PostReview:
        """Review a single post.

        Args:
            post: Post to review
            content_analysis: Original content analysis
            tone: Expected tone

        Returns:
            PostReview with scores and suggestions
        """
        prompt = f"""Review this {post.platform} post for quality and engagement potential.

Post ({post.character_count} chars):
"{post.text}"

Context:
- Article: {content_analysis.article_title}
- Expected tone: {tone}
- Platform: {post.platform}

Score these aspects (0.0-1.0):
1. Clarity: Is the message clear and easy to understand?
2. Engagement: Will it encourage likes, shares, comments?
3. Platform Fit: Does it match {post.platform} best practices?

Also provide 1-2 specific suggestions for improvement (if needed).

Return as JSON:
{{
    "clarity_score": 0.0-1.0,
    "engagement_score": 0.0-1.0,
    "platform_fit_score": 0.0-1.0,
    "suggestions": ["suggestion1", "suggestion2"]
}}"""

        response = self._call_openai(prompt, max_tokens=300, temperature=0.3)

        try:
            # Parse review scores
            json_str = self._extract_json(response)
            data = json.loads(json_str)

            clarity_score = min(1.0, max(0.0, float(data.get("clarity_score", 0.5))))
            engagement_score = min(1.0, max(0.0, float(data.get("engagement_score", 0.5))))
            platform_fit_score = min(1.0, max(0.0, float(data.get("platform_fit_score", 0.5))))
            suggestions = data.get("suggestions", [])[:2]

            # Calculate overall score (weighted average)
            overall_score = clarity_score * 0.3 + engagement_score * 0.4 + platform_fit_score * 0.3

            return PostReview(
                post=post,
                clarity_score=clarity_score,
                engagement_score=engagement_score,
                platform_fit_score=platform_fit_score,
                overall_score=overall_score,
                suggestions=suggestions,
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse review: {e}")
            # Return neutral scores if parsing fails
            return PostReview(
                post=post,
                clarity_score=0.5,
                engagement_score=0.5,
                platform_fit_score=0.5,
                overall_score=0.5,
                suggestions=[],
            )

    async def suggest_improvements(
        self,
        reviews: list[PostReview],
        content_analysis: ContentAnalysis,
    ) -> dict[str, list[str]]:
        """Generate improvement suggestions for low-scoring posts.

        Args:
            reviews: Post reviews
            content_analysis: Original content analysis

        Returns:
            Dict mapping post text to improvement suggestions
        """
        improvements = {}

        for review in reviews:
            if review.overall_score < 0.7 and review.suggestions:
                improvements[review.post.text[:50] + "..."] = review.suggestions

        return improvements

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

    def _extract_json(self, response: str) -> str:
        """Extract JSON from LLM response.

        Args:
            response: LLM response possibly containing JSON

        Returns:
            Extracted JSON string
        """
        # Remove markdown code blocks
        response = re.sub(r"```(?:json)?\n?", "", response)

        # Find JSON object
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            return match.group()

        return response.strip()
