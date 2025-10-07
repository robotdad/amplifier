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
    depth = os.getenv("DEPTH", "quick")
    mode = os.getenv("MODE", "research")
    resume_session_id = os.getenv("RESUME")

    # Validate mode
    if mode not in ["research", "code"]:
        logger.error(f"Invalid MODE: {mode}. Must be 'research' or 'code'")
        sys.exit(1)

    # Handle resume case
    if resume_session_id:
        logger.info(f"Resuming session: {resume_session_id}")
        # Topic/question will be loaded from session
    elif not topic:
        logger.error("TOPIC environment variable is required (unless RESUME is specified)")
        logger.info(
            "Usage: TOPIC='your topic' [QUESTION='optional question'] [DEPTH=quick|deep] amplifier knowledge-assist"
        )
        logger.info("   Or: RESUME='session_id' amplifier knowledge-assist")
        sys.exit(1)

    if topic:
        logger.info(f"Research topic: {topic}")
        if question:
            logger.info(f"Research question: {question}")
        logger.info(f"Synthesis depth: {depth}")
        logger.info(f"Synthesis mode: {mode}")

    try:
        # Load configuration
        config = KnowledgeAssistConfig()
        config.depth = depth  # Override with command-line value
        config.mode = mode  # Override with command-line value
        config.ensure_output_dir()

        # Initialize components (before session creation)
        retriever = KnowledgeRetriever(config.knowledge_path, config)
        engine = SynthesisEngine(config, config.prompts_dir)
        generator = OutputGenerator()
        session_manager = SessionManager(config.output_dir)

        # Handle resume case
        if resume_session_id:
            session = session_manager.load_session(resume_session_id)
            if not session:
                logger.error(f"Session {resume_session_id} not found")
                sys.exit(1)
            topic = session.topic
            question = session.question
            logger.info(f"Restored topic: {topic}")
            if question:
                logger.info(f"Restored question: {question}")

            # For resume, we need to regenerate knowledge and citations
            # (session state management for these is complex and not implemented yet)
            logger.info("Retrieving knowledge from extractions...")
            knowledge = retriever.retrieve(topic, question)

            # Check retrieval quality for resume case
            total_knowledge = (
                len(knowledge.concepts)
                + len(knowledge.relationships)
                + len(knowledge.insights)
                + len(knowledge.patterns)
            )
            if hasattr(knowledge, "match_quality") and knowledge.match_quality == "poor":
                logger.warning("\n⚠️  WARNING: Retrieved knowledge has LOW RELEVANCE to your query!")
                logger.warning(f"Retrieved {total_knowledge} items but relevance scores are weak")
                logger.info("\n🔍 Proceeding with low-quality matches - results may be off-topic")

            # Check if web search is needed
            web_results = None
            if engine.needs_web_search(topic, question):
                logger.info("Temporal terms detected - web search will be performed...")
                web_results = []

            # Prepare citation context
            logger.info("Preparing citations...")
            content_loader = ContentLoader()
            citation_context = prepare_citations(knowledge.sources, content_loader)
            logger.info(f"Prepared {len(citation_context.numbered_sources)} source citations")
        else:
            # Retrieve knowledge FIRST
            logger.info("Retrieving knowledge from extractions...")
            if not topic:  # This should never happen due to earlier check, but helps type checker
                logger.error("Topic is required")
                sys.exit(1)
            knowledge = retriever.retrieve(topic, question)

            # Validate knowledge was retrieved SECOND
            total_knowledge = (
                len(knowledge.concepts)
                + len(knowledge.relationships)
                + len(knowledge.insights)
                + len(knowledge.patterns)
            )

            if total_knowledge == 0:
                logger.error("No knowledge found in knowledge base for this topic!")
                logger.info("\nSuggestions:")
                logger.info("  1. If knowledge base is empty, run: make knowledge-sync")
                logger.info("  2. Try broader search terms if your topic is too specific")
                logger.info(f"  3. Check knowledge file exists at: {config.knowledge_path}")
                logger.info("  4. Verify ~/.amplifier/ directory structure is intact")
                sys.exit(1)

            # Check if retrieval quality is acceptable (escape hatch)
            if hasattr(knowledge, "match_quality") and knowledge.match_quality == "poor":
                logger.warning("\n⚠️  WARNING: Retrieved knowledge has LOW RELEVANCE to your query!")
                logger.warning(f"Retrieved {total_knowledge} items but relevance scores are weak")
                logger.info("\nThis typically means:")
                logger.info("  - Your knowledge base may not contain relevant content for this topic")
                logger.info("  - The search terms might be too specific or use different terminology")
                logger.info("  - Consider running 'make knowledge-sync' to update your knowledge base")
                logger.info("\nSuggestions:")
                logger.info("  - Try more general or alternative terms")
                logger.info("  - Use different phrasing for your question")
                logger.info("  - Check if your topic uses specialized terminology")
                logger.info("\n🔍 Proceeding with low-quality matches - results may be off-topic or hallucinated")
                logger.info("━" * 60 + "\n")

            elif total_knowledge < 3:
                logger.warning(f"Only found {total_knowledge} knowledge items - results may be limited")
                logger.info("Consider using broader search terms for better results")

            # Create session THIRD (only after successful knowledge validation)
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
        if depth == "deep":
            logger.info(f"Starting deep synthesis with {config.model} (3-stage pipeline)...")
            synthesis_result = engine.synthesize_deep(
                topic, question, knowledge, web_results, citation_context, session
            )
        else:
            logger.info(f"Synthesizing with {config.model} (quick mode)...")
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
