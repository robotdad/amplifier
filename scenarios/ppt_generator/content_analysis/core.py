"""Core content analysis functionality."""

import logging
from pathlib import Path

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json

from ..models import ContextAnalysis

logger = logging.getLogger(__name__)


async def analyze_context(context_files: list[Path], direction: str, target_slides: int) -> ContextAnalysis:
    """Analyze context files to understand content for presentation.

    Args:
        context_files: List of file paths to analyze
        direction: User's instructions for the presentation
        target_slides: Target number of slides

    Returns:
        ContextAnalysis object with extracted information
    """
    # Read all context files
    combined_content = []
    for file_path in context_files:
        if not file_path.exists():
            logger.warning(f"Context file not found: {file_path}")
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
            combined_content.append(f"--- File: {file_path.name} ---\n{content}")
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")

    if not combined_content:
        raise ValueError("No valid context files found")

    combined_text = "\n\n".join(combined_content)

    # Prepare analysis prompt
    prompt = f"""Analyze the following content to prepare for creating a PowerPoint presentation.

User Direction: {direction}
Target Slides: {target_slides}

Context Content:
{combined_text[:10000]}  # Limit context to avoid token limits

Please analyze and provide:
1. Main topics/themes of the presentation (3-5 topics)
2. Key concepts to highlight (5-10 concepts)
3. Target audience based on content
4. Appropriate tone (professional, casual, educational, technical, etc.)
5. Technical level (beginner, intermediate, advanced, expert)
6. Suggested flow/narrative structure
7. Visual opportunities (what could benefit from diagrams, charts, images)

Format your response as JSON:
{{
    "main_topics": ["topic1", "topic2", ...],
    "key_concepts": ["concept1", "concept2", ...],
    "target_audience": "...",
    "tone": "...",
    "technical_level": "...",
    "suggested_flow": "A narrative description of how the presentation should flow",
    "visual_opportunities": ["opportunity1", "opportunity2", ...]
}}"""

    # Call Claude for analysis
    options = SessionOptions(
        system_prompt="You are an expert presentation designer analyzing content to create effective PowerPoint presentations. Focus on identifying the key information architecture and visual opportunities. Respond only with valid JSON.",
        retry_attempts=2,
    )

    async with ClaudeSession(options) as session:
        result = await session.query(prompt)
        response = result.content

    # Parse response using defensive parsing
    analysis_data = parse_llm_json(response)

    # Ensure it's a dict
    if not isinstance(analysis_data, dict):
        # Provide fallback structure
        logger.warning("Failed to parse analysis, using defaults")
        analysis_data = {
            "main_topics": ["Main Topic"],
            "key_concepts": ["Key Concept 1", "Key Concept 2"],
            "target_audience": "general audience",
            "tone": "professional",
            "technical_level": "intermediate",
            "suggested_flow": "Introduction → Main Points → Conclusion",
            "visual_opportunities": ["Process diagrams", "Data charts"],
        }

    # Create ContextAnalysis object
    analysis = ContextAnalysis(
        main_topics=analysis_data.get("main_topics", ["Main Topic"]),
        key_concepts=analysis_data.get("key_concepts", []),
        target_audience=analysis_data.get("target_audience", "general audience"),
        tone=analysis_data.get("tone", "professional"),
        technical_level=analysis_data.get("technical_level", "intermediate"),
        suggested_flow=analysis_data.get("suggested_flow", "Linear progression"),
        visual_opportunities=analysis_data.get("visual_opportunities", []),
    )

    logger.info(f"Context analysis complete. Topics: {', '.join(analysis.main_topics[:3])}")
    return analysis
