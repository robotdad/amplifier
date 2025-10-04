"""Synthesis engine using OpenAI Responses API."""

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
