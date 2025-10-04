#!/usr/bin/env python3
"""Knowledge-assist CLI tool for research synthesis."""

import logging
import os
import sys

from amplifier.content_loader import ContentLoader

from .citation_system import prepare_citations
from .config import KnowledgeAssistConfig
from .knowledge_retriever import KnowledgeRetriever
from .output_generator import OutputGenerator
from .session import SessionManager
from .synthesis_engine import SynthesisEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for knowledge-assist."""
    # Get topic and question from environment
    topic = os.getenv("TOPIC")
    question = os.getenv("QUESTION")

    if not topic:
        logger.error("TOPIC environment variable is required")
        logger.info("Usage: TOPIC='your topic' [QUESTION='optional question'] amplifier knowledge-assist")
        sys.exit(1)

    logger.info(f"Research topic: {topic}")
    if question:
        logger.info(f"Research question: {question}")

    try:
        # Load configuration
        config = KnowledgeAssistConfig()
        config.ensure_output_dir()

        # Initialize components (before session creation)
        retriever = KnowledgeRetriever(config.knowledge_path, config)
        engine = SynthesisEngine(config, config.prompts_dir)
        generator = OutputGenerator()

        # Retrieve knowledge FIRST
        logger.info("Retrieving knowledge from extractions...")
        knowledge = retriever.retrieve(topic, question)

        # Validate knowledge was retrieved SECOND
        total_knowledge = (
            len(knowledge.concepts) + len(knowledge.relationships) + len(knowledge.insights) + len(knowledge.patterns)
        )

        if total_knowledge == 0:
            logger.error("No knowledge found in knowledge base for this topic!")
            logger.info("\nSuggestions:")
            logger.info("  1. If knowledge base is empty, run: make knowledge-sync")
            logger.info("  2. Try broader search terms if your topic is too specific")
            logger.info(f"  3. Check knowledge file exists at: {config.knowledge_path}")
            logger.info("  4. Verify ~/.amplifier/ directory structure is intact")
            sys.exit(1)

        if total_knowledge < 3:
            logger.warning(f"Only found {total_knowledge} knowledge items - results may be limited")
            logger.info("Consider using broader search terms for better results")

        # Create session THIRD (only after successful knowledge validation)
        session_manager = SessionManager(config.output_dir)
        session = session_manager.create_session(topic, question)
        logger.info(f"Session created: {session.id}")

        # Check if web search is needed
        web_results = None
        if engine.needs_web_search(topic, question):
            logger.info("Temporal terms detected - web search will be performed...")
            # Pass empty list to indicate web search is requested
            # OpenAI's built-in web search will handle the actual search
            web_results = []

        # Prepare citation context
        logger.info("Preparing citations...")
        content_loader = ContentLoader()  # Use the real ContentLoader - it reads from .env
        citation_context = prepare_citations(knowledge.sources, content_loader)
        logger.info(f"Prepared {len(citation_context.numbered_sources)} source citations")

        # Synthesize knowledge
        logger.info(f"Synthesizing with {config.model}...")
        synthesis_result = engine.synthesize(topic, question, knowledge, web_results, citation_context)

        # Update session stats
        session.stats = {
            "concepts_retrieved": len(knowledge.concepts),
            "relationships_retrieved": len(knowledge.relationships),
            "insights_retrieved": len(knowledge.insights),
            "patterns_retrieved": len(knowledge.patterns),
            "sources": len(knowledge.sources),
            "web_results": len(web_results) if web_results else 0,
            "model": synthesis_result.model_used,
            "tokens_used": synthesis_result.tokens_used,
        }

        # Generate output
        logger.info("Generating output...")
        generator.generate(
            topic=topic,
            question=question,
            synthesis_result=synthesis_result,
            knowledge=knowledge,
            output_path=session.output_path,
            citation_context=citation_context,
        )

        # Save updated session info
        session_manager._save_session_info(session)

        logger.info(f"✓ Research synthesis complete: {session.output_path}")
        logger.info(f"  - {session.stats['concepts_retrieved']} concepts")
        logger.info(f"  - {session.stats['relationships_retrieved']} relationships")
        logger.info(f"  - {session.stats['insights_retrieved']} insights")
        logger.info(f"  - {session.stats['patterns_retrieved']} patterns")
        if session.stats["web_results"] > 0:
            logger.info(f"  - {session.stats['web_results']} web results")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
