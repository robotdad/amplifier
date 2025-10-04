"""Synthesis engine using OpenAI Responses API."""

import json
import logging

from openai import OpenAI
from openai.types.responses import WebSearchToolParam
from pydantic import BaseModel
from pydantic import Field

from .citation_system import CitationContext
from .knowledge_retriever import RetrievedKnowledge

logger = logging.getLogger(__name__)


class SynthesisResult(BaseModel):
    """Result from synthesis engine."""

    content: str = Field(description="Synthesized markdown content")
    web_citations: list[dict] = Field(default_factory=list, description="Web search citations")
    model_used: str = Field(description="Model used for synthesis")
    tokens_used: int | None = Field(default=None, description="Tokens used")


class SynthesisEngine:
    """Synthesizes knowledge using OpenAI."""

    def __init__(self, config, prompts_dir):
        """Initialize synthesis engine.

        Args:
            config: Knowledge assist configuration
            prompts_dir: Directory containing prompt templates
        """
        self.config = config
        self.prompts_dir = prompts_dir

        # Initialize OpenAI client with API key
        if not config.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=config.api_key)

    def synthesize(
        self,
        topic: str,
        question: str | None,
        knowledge: RetrievedKnowledge,
        web_results: list | None = None,
        citation_context: CitationContext | None = None,
    ) -> SynthesisResult:
        """Synthesize knowledge into research output.

        Args:
            topic: Research topic
            question: Optional specific question
            knowledge: Retrieved knowledge
            web_results: Optional web search results
            citation_context: Optional citation context for source numbering

        Returns:
            Synthesis result
        """
        # Build the prompt as a single string for Responses API
        prompt = self._build_prompt(topic, question, knowledge, web_results, citation_context)

        # Log prompt for debugging web search issues
        if web_results is not None:
            logger.debug(f"Topic: {topic}, Question: {question}")
            logger.debug("Using Responses API with web search enabled")

        try:
            # Use OpenAI Responses API (NOT Chat Completions API)
            # The Responses API uses 'input' parameter instead of 'messages'
            tools = []
            if web_results is not None:
                # Enable web search tool when needed
                tools = [WebSearchToolParam(type="web_search")]
                logger.info("Web search enabled - using Responses API with web_search tool")

            # Call the Responses API with the correct parameters
            response = self.client.responses.create(
                model="gpt-4o",  # Use gpt-4o model
                input=prompt,  # Single string input, NOT messages array
                tools=tools,  # Include web_search tool if needed
            )

            # Extract content from Responses API format
            # The output is a list of items, find the first message item
            content = "Error: No content returned from synthesis"
            web_citations = []

            for output_item in response.output:
                # Look for ResponseOutputMessage type
                if hasattr(output_item, "type") and output_item.type == "message":
                    # Extract text from the message content
                    if hasattr(output_item, "content") and output_item.content:
                        for content_item in output_item.content:
                            # Look for text content (ResponseOutputText)
                            if hasattr(content_item, "type") and content_item.type == "output_text":
                                content = content_item.text

                                # Debug: Log the actual structure
                                if web_results is not None:
                                    logger.debug(
                                        f"Content item type: {content_item.type if hasattr(content_item, 'type') else 'no type'}"
                                    )
                                    logger.debug(f"Has annotations: {hasattr(content_item, 'annotations')}")
                                    if hasattr(content_item, "annotations"):
                                        logger.debug(f"Annotations type: {type(content_item.annotations)}")
                                        logger.debug(
                                            f"Annotations length: {len(content_item.annotations) if content_item.annotations else 0}"
                                        )
                                        if content_item.annotations:
                                            logger.debug(
                                                f"First annotation: {content_item.annotations[0] if len(content_item.annotations) > 0 else 'none'}"
                                            )

                                # Extract web citations from annotations if present
                                if web_results is not None and hasattr(content_item, "annotations"):
                                    for annotation in content_item.annotations:
                                        # Check for URL citations (web search results)
                                        if hasattr(annotation, "type") and annotation.type == "url_citation":
                                            citation = {
                                                "title": annotation.title
                                                if hasattr(annotation, "title")
                                                else "Web Source",
                                                "url": annotation.url if hasattr(annotation, "url") else "",
                                                "snippet": "",  # URL citations don't have text/snippet field
                                            }
                                            web_citations.append(citation)
                                break  # Found the text content, exit inner loop
                    break  # Found the message, exit outer loop

            # Extract tokens if available
            tokens_used = response.usage.total_tokens if hasattr(response, "usage") and response.usage else None

            if web_results is not None:
                if web_citations:
                    logger.info(f"Extracted {len(web_citations)} web citations from Responses API")
                else:
                    logger.info("Web search performed - citations embedded inline in response")
                    # Add a note that web search was used but citations are inline
                    web_citations.append(
                        {
                            "title": "Web Search",
                            "url": "",
                            "snippet": "Web search was performed. Citations are embedded inline in the synthesis.",
                        }
                    )

            return SynthesisResult(
                content=content, web_citations=web_citations, model_used="gpt-4o", tokens_used=tokens_used
            )

        except Exception as e:
            logger.error(f"Error during synthesis: {e}")
            raise

    def _build_prompt(
        self,
        topic: str,
        question: str | None,
        knowledge: RetrievedKnowledge,
        web_results: list | None,
        citation_context: CitationContext | None = None,
    ) -> str:
        """Build synthesis prompt.

        Args:
            topic: Research topic
            question: Optional specific question
            knowledge: Retrieved knowledge
            web_results: Optional web search results
            citation_context: Optional citation context for source numbering

        Returns:
            Formatted prompt
        """
        # Load prompt template
        prompt_path = self.prompts_dir / "research_quick.txt"
        if prompt_path.exists():
            with open(prompt_path) as f:
                template = f.read()
        else:
            # Fallback template if file doesn't exist
            template = self._get_default_template()

        # Format knowledge sections
        concepts_text = "\n".join(f"- {c}" for c in knowledge.concepts) if knowledge.concepts else "None found"
        relationships_text = (
            "\n".join(f"- {r}" for r in knowledge.relationships) if knowledge.relationships else "None found"
        )
        insights_text = "\n".join(f"- {i}" for i in knowledge.insights) if knowledge.insights else "None found"
        patterns_text = "\n".join(f"- {p}" for p in knowledge.patterns) if knowledge.patterns else "None found"

        # Format web results if available
        web_text = ""
        if web_results is not None:  # Web search was requested
            web_text = "\n## Web Search Instructions:\n"
            web_text += "Please search for and include the most current and up-to-date information "
            web_text += f"about '{topic}'"
            if question:
                web_text += f", specifically focusing on: {question}"
            web_text += "\n\nIncorporate recent developments, current best practices, and latest trends from reliable sources.\n"

        # Build citation instructions if citation context provided
        citation_instructions = ""
        numbered_sources = ""
        if citation_context and citation_context.numbered_sources:
            citation_instructions = """
## Citation Instructions

When synthesizing, cite sources using [1], [2] format on FIRST mention only.
Example: "The concept of emergence [1] is fundamental to understanding complex systems."

Cite naturally when introducing concepts from these sources. Only cite when directly referencing specific knowledge from a source.
"""
            numbered_sources = "\n## Available Sources\n\n"
            for source in citation_context.numbered_sources:
                numbered_sources += f"[{source.number}]: {source.title}\n"

        # Replace placeholders
        prompt = template.replace("{TOPIC}", topic)
        prompt = prompt.replace("{QUESTION}", question if question else "General research on this topic")
        prompt = prompt.replace("{CONCEPTS}", concepts_text)
        prompt = prompt.replace("{RELATIONSHIPS}", relationships_text)
        prompt = prompt.replace("{INSIGHTS}", insights_text)
        prompt = prompt.replace("{PATTERNS}", patterns_text)
        prompt = prompt.replace("{WEB_RESULTS}", web_text)
        prompt = prompt.replace("{CITATION_INSTRUCTIONS}", citation_instructions)
        prompt = prompt.replace("{NUMBERED_SOURCES}", numbered_sources)

        return prompt

    def _get_default_template(self) -> str:
        """Get default prompt template.

        Returns:
            Default template
        """
        return """You are a research assistant that synthesizes knowledge into clear, insightful markdown documents.

# Research Request

## Topic: {TOPIC}

## Question: {QUESTION}

## Available Knowledge

### Concepts:
{CONCEPTS}

### Relationships:
{RELATIONSHIPS}

### Insights:
{INSIGHTS}

### Patterns:
{PATTERNS}

{WEB_RESULTS}

{CITATION_INSTRUCTIONS}
{NUMBERED_SOURCES}

---

Please synthesize the above knowledge into a comprehensive research document. Structure your response as follows:

1. Start with a clear title
2. Provide a synthesis that addresses the topic and any specific question
3. Include a "Key Insights" section with the most important findings
4. End with a "Related Concepts" section listing relevant connected ideas

Focus on creating a coherent narrative that connects the various pieces of knowledge. Be specific and actionable where possible."""

    def needs_web_search(self, topic: str, question: str | None = None) -> bool:
        """Check if web search is needed based on temporal terms.

        Args:
            topic: Research topic
            question: Optional question

        Returns:
            True if web search is needed
        """
        search_text = topic.lower()
        if question:
            search_text += " " + question.lower()

        return any(term in search_text for term in self.config.temporal_terms)

    def synthesize_deep(
        self,
        topic: str,
        question: str | None,
        knowledge: RetrievedKnowledge,
        web_results: list | None = None,
        citation_context: CitationContext | None = None,
        session=None,
    ) -> SynthesisResult:
        """Deep synthesis with 3-stage pipeline.

        Args:
            topic: Research topic
            question: Optional specific question
            knowledge: Retrieved knowledge
            web_results: Optional web search results
            citation_context: Optional citation context for source numbering
            session: Session object for saving intermediate results

        Returns:
            Synthesis result
        """
        logger.info("Starting deep synthesis pipeline...")

        # Check for resume capability
        stage1_result = None
        stage2_result = None

        if session and hasattr(session, "stage_results"):
            stage1_result = session.stage_results.get("stage1")
            stage2_result = session.stage_results.get("stage2")
            if stage1_result:
                logger.info("Resuming from saved Stage 1 results")
            if stage2_result:
                logger.info("Resuming from saved Stage 2 results")

        # Stage 1: Analyze knowledge
        if not stage1_result:
            logger.info("Stage 1: Analyzing knowledge...")
            stage1_result = self._stage1_analyze(topic, question, knowledge, citation_context)
            if session:
                session.save_stage_result("stage1", stage1_result)
            logger.info(
                f"Stage 1 complete: {len(stage1_result.get('main_themes', []))} themes, {len(stage1_result.get('knowledge_gaps', []))} gaps identified"
            )

        # Stage 2: Augment with web search (conditional)
        if not stage2_result and stage1_result.get("knowledge_gaps"):
            logger.info(f"Stage 2: Augmenting {len(stage1_result['knowledge_gaps'])} knowledge gaps...")
            stage2_result = self._stage2_augment(
                topic, question, stage1_result["knowledge_gaps"], stage1_result.get("response_id")
            )
            if session:
                session.save_stage_result("stage2", stage2_result)
            logger.info(f"Stage 2 complete: {len(stage2_result.get('augmented_insights', []))} insights added")
        else:
            if not stage1_result.get("knowledge_gaps"):
                logger.info("Stage 2: Skipped (no knowledge gaps identified)")
            stage2_result = None

        # Stage 3: Generate comprehensive report
        logger.info("Stage 3: Generating comprehensive report...")
        synthesis_result = self._stage3_generate(
            topic,
            question,
            knowledge,
            stage1_result,
            stage2_result,
            citation_context,
            stage1_result.get("response_id") if not stage2_result else stage2_result.get("response_id"),
        )

        logger.info("Deep synthesis pipeline complete")
        return synthesis_result

    def _stage1_analyze(
        self,
        topic: str,
        question: str | None,
        knowledge: RetrievedKnowledge,
        citation_context: CitationContext | None = None,
    ) -> dict:
        """Stage 1: Analyze knowledge to identify themes and gaps.

        Returns:
            JSON analysis with main_themes, knowledge_gaps, suggested_outline
        """
        # Load analyze prompt template
        prompt_path = self.prompts_dir / "research_analyze.txt"
        if prompt_path.exists():
            with open(prompt_path) as f:
                template = f.read()
        else:
            # Fallback template
            template = """You are a research analyst. Analyze the provided knowledge and identify:

1. Main themes and patterns
2. Knowledge gaps that need filling
3. A suggested outline for comprehensive coverage

Topic: {TOPIC}
Question: {QUESTION}

## Available Knowledge

### Concepts:
{CONCEPTS}

### Relationships:
{RELATIONSHIPS}

### Insights:
{INSIGHTS}

### Patterns:
{PATTERNS}

{NUMBERED_SOURCES}

Return your analysis as JSON with the structure:
{
  "main_themes": ["theme1", "theme2", ...],
  "knowledge_gaps": ["gap1", "gap2", ...],
  "suggested_outline": ["section1", "section2", ...]
}"""

        # Format knowledge
        concepts_text = "\n".join(f"- {c}" for c in knowledge.concepts) if knowledge.concepts else "None found"
        relationships_text = (
            "\n".join(f"- {r}" for r in knowledge.relationships) if knowledge.relationships else "None found"
        )
        insights_text = "\n".join(f"- {i}" for i in knowledge.insights) if knowledge.insights else "None found"
        patterns_text = "\n".join(f"- {p}" for p in knowledge.patterns) if knowledge.patterns else "None found"

        numbered_sources = ""
        if citation_context and citation_context.numbered_sources:
            numbered_sources = "\n## Available Sources\n\n"
            for source in citation_context.numbered_sources:
                numbered_sources += f"[{source.number}]: {source.title}\n"

        prompt = template.replace("{TOPIC}", topic)
        prompt = prompt.replace("{QUESTION}", question if question else "General research on this topic")
        prompt = prompt.replace("{CONCEPTS}", concepts_text)
        prompt = prompt.replace("{RELATIONSHIPS}", relationships_text)
        prompt = prompt.replace("{INSIGHTS}", insights_text)
        prompt = prompt.replace("{PATTERNS}", patterns_text)
        prompt = prompt.replace("{NUMBERED_SOURCES}", numbered_sources)

        try:
            # Add JSON instruction to prompt
            prompt += "\n\nIMPORTANT: Return ONLY valid JSON with no other text."

            response = self.client.responses.create(model=self.config.model, input=prompt)

            # Extract JSON from response
            content = ""
            response_id = response.id if hasattr(response, "id") else None

            for output_item in response.output:
                if hasattr(output_item, "type") and output_item.type == "message":
                    if hasattr(output_item, "content") and output_item.content:
                        for content_item in output_item.content:
                            if hasattr(content_item, "type") and content_item.type == "output_text":
                                content = content_item.text
                                break
                    break

            # Try to extract JSON from the response (might have markdown or other text)
            try:
                # Try parsing directly first
                result = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown blocks or other formats
                import re

                json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # Try finding JSON object pattern
                    json_match = re.search(r"\{.*\}", content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group(0))
                    else:
                        raise ValueError("No valid JSON found in response")

            result["response_id"] = response_id
            return result

        except Exception as e:
            logger.error(f"Stage 1 analysis failed: {e}")
            logger.debug(f"Response content: {content[:500]}")
            # Return empty analysis on failure
            return {"main_themes": [], "knowledge_gaps": [], "suggested_outline": []}

    def _stage2_augment(
        self,
        topic: str,
        question: str | None,
        knowledge_gaps: list,
        previous_response_id: str | None = None,
    ) -> dict:
        """Stage 2: Augment knowledge gaps with web search.

        Returns:
            JSON with augmented insights
        """
        # Load augment prompt template
        prompt_path = self.prompts_dir / "research_augment.txt"
        if prompt_path.exists():
            with open(prompt_path) as f:
                template = f.read()
        else:
            # Fallback template
            template = """You are a research augmenter. Use web search to fill these knowledge gaps:

Topic: {TOPIC}
Question: {QUESTION}

## Knowledge Gaps to Fill:
{GAPS}

Search for current, authoritative information to address each gap. Focus on:
- Recent developments and trends
- Best practices and methodologies
- Expert opinions and research findings
- Practical applications and examples

Return augmented insights as JSON:
{
  "augmented_insights": [
    {"gap": "original gap", "findings": "what you found", "sources": ["source1", "source2"]}
  ]
}"""

        gaps_text = "\n".join(f"- {gap}" for gap in knowledge_gaps)

        prompt = template.replace("{TOPIC}", topic)
        prompt = prompt.replace("{QUESTION}", question if question else "General research on this topic")
        prompt = prompt.replace("{GAPS}", gaps_text)

        try:
            # Include previous response for context chaining
            # Add JSON instruction to prompt
            prompt += "\n\nIMPORTANT: Return ONLY valid JSON with no other text."

            kwargs = {
                "model": self.config.web_search_model,
                "input": prompt,
                "tools": [WebSearchToolParam(type="web_search")],
            }

            if previous_response_id:
                kwargs["previous_response_id"] = previous_response_id

            response = self.client.responses.create(**kwargs)

            # Extract JSON from response
            content = ""
            response_id = response.id if hasattr(response, "id") else None

            for output_item in response.output:
                if hasattr(output_item, "type") and output_item.type == "message":
                    if hasattr(output_item, "content") and output_item.content:
                        for content_item in output_item.content:
                            if hasattr(content_item, "type") and content_item.type == "output_text":
                                content = content_item.text
                                break
                    break

            # Try to extract JSON from the response (might have markdown or other text)
            try:
                # Try parsing directly first
                result = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown blocks or other formats
                import re

                json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # Try finding JSON object pattern
                    json_match = re.search(r"\{.*\}", content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group(0))
                    else:
                        raise ValueError("No valid JSON found in response")

            result["response_id"] = response_id
            return result

        except Exception as e:
            logger.error(f"Stage 2 augmentation failed: {e}")
            logger.debug(f"Response content: {content[:500]}")
            return {"augmented_insights": []}

    def _stage3_generate(
        self,
        topic: str,
        question: str | None,
        knowledge: RetrievedKnowledge,
        stage1_result: dict,
        stage2_result: dict | None,
        citation_context: CitationContext | None,
        previous_response_id: str | None = None,
    ) -> SynthesisResult:
        """Stage 3: Generate comprehensive research report.

        Returns:
            Final synthesis result
        """
        # Load generate prompt template
        prompt_path = self.prompts_dir / "research_generate.txt"
        if prompt_path.exists():
            with open(prompt_path) as f:
                template = f.read()
        else:
            # Fallback template
            template = """You are a research synthesizer. Generate a comprehensive 2-3 page research report.

Topic: {TOPIC}
Question: {QUESTION}

## Analysis Results:
### Main Themes:
{THEMES}

### Suggested Outline:
{OUTLINE}

## Original Knowledge:
### Concepts:
{CONCEPTS}

### Relationships:
{RELATIONSHIPS}

### Insights:
{INSIGHTS}

### Patterns:
{PATTERNS}

{AUGMENTED_SECTION}

{CITATION_INSTRUCTIONS}
{NUMBERED_SOURCES}

Generate a comprehensive, well-structured markdown report that:
1. Follows the suggested outline
2. Integrates all available knowledge coherently
3. Incorporates augmented insights where relevant
4. Provides actionable recommendations
5. Cites sources appropriately using [1], [2] format

The report should be 2-3 pages (800-1200 words) with clear sections and practical insights."""

        # Format all inputs
        themes_text = "\n".join(f"- {t}" for t in stage1_result.get("main_themes", []))
        outline_text = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(stage1_result.get("suggested_outline", [])))

        concepts_text = "\n".join(f"- {c}" for c in knowledge.concepts) if knowledge.concepts else "None found"
        relationships_text = (
            "\n".join(f"- {r}" for r in knowledge.relationships) if knowledge.relationships else "None found"
        )
        insights_text = "\n".join(f"- {i}" for i in knowledge.insights) if knowledge.insights else "None found"
        patterns_text = "\n".join(f"- {p}" for p in knowledge.patterns) if knowledge.patterns else "None found"

        augmented_section = ""
        if stage2_result and stage2_result.get("augmented_insights"):
            augmented_section = "\n## Augmented Insights (from web research):\n"
            for aug in stage2_result["augmented_insights"]:
                augmented_section += f"\n### {aug.get('gap', 'Unknown gap')}\n"
                augmented_section += f"{aug.get('findings', 'No findings')}\n"
                if aug.get("sources"):
                    augmented_section += f"Sources: {', '.join(aug['sources'])}\n"

        citation_instructions = ""
        numbered_sources = ""
        if citation_context and citation_context.numbered_sources:
            citation_instructions = """
## Citation Instructions

Cite sources using [1], [2] format when referencing specific knowledge.
Only cite on first mention of concepts from these sources."""
            numbered_sources = "\n## Available Sources\n\n"
            # Limit sources to prevent prompt overflow (max 100 sources)
            max_sources = 100
            sources_to_include = citation_context.numbered_sources[:max_sources]
            for source in sources_to_include:
                numbered_sources += f"[{source.number}]: {source.title}\n"

            # Add note if sources were truncated
            if len(citation_context.numbered_sources) > max_sources:
                numbered_sources += (
                    f"\n... and {len(citation_context.numbered_sources) - max_sources} more sources available\n"
                )

        prompt = template.replace("{TOPIC}", topic)
        prompt = prompt.replace("{QUESTION}", question if question else "General research on this topic")
        prompt = prompt.replace("{THEMES}", themes_text)
        prompt = prompt.replace("{OUTLINE}", outline_text)
        prompt = prompt.replace("{CONCEPTS}", concepts_text)
        prompt = prompt.replace("{RELATIONSHIPS}", relationships_text)
        prompt = prompt.replace("{INSIGHTS}", insights_text)
        prompt = prompt.replace("{PATTERNS}", patterns_text)
        prompt = prompt.replace("{AUGMENTED_SECTION}", augmented_section)
        prompt = prompt.replace("{CITATION_INSTRUCTIONS}", citation_instructions)
        prompt = prompt.replace("{NUMBERED_SOURCES}", numbered_sources)

        try:
            # Include previous response for context chaining
            kwargs = {"model": self.config.model, "input": prompt}

            if previous_response_id:
                kwargs["previous_response_id"] = previous_response_id

            # Log prompt size for debugging
            prompt_size = len(prompt)
            logger.info(f"Stage 3 prompt size: {prompt_size} characters")
            if prompt_size > 50000:
                logger.warning(f"Large prompt detected: {prompt_size} characters may cause issues")

            response = self.client.responses.create(**kwargs)

            # Extract content
            content = ""
            for output_item in response.output:
                if hasattr(output_item, "type") and output_item.type == "message":
                    if hasattr(output_item, "content") and output_item.content:
                        for content_item in output_item.content:
                            if hasattr(content_item, "type") and content_item.type == "output_text":
                                content = content_item.text
                                break
                    break

            # Check for refusal or empty content
            if not content or "unable to help" in content.lower():
                logger.error(
                    f"Stage 3: Model refused or returned empty content. Content length: {len(content) if content else 0}"
                )
                if content:
                    logger.debug(f"Response preview: {content[:200]}")

            tokens_used = response.usage.total_tokens if hasattr(response, "usage") and response.usage else None

            return SynthesisResult(
                content=content, web_citations=[], model_used=self.config.model, tokens_used=tokens_used
            )

        except Exception as e:
            logger.error(f"Stage 3 generation failed: {e}", exc_info=True)
            # Return a basic synthesis on failure
            return SynthesisResult(
                content=f"# {topic}\n\nError generating deep synthesis. Please try again.",
                web_citations=[],
                model_used=self.config.model,
                tokens_used=0,
            )
