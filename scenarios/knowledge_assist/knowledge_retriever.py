"""Knowledge retrieval from extractions.jsonl."""

import json
import logging
from pathlib import Path

from pydantic import BaseModel
from pydantic import Field

logger = logging.getLogger(__name__)


class RetrievedKnowledge(BaseModel):
    """Retrieved knowledge from extractions."""

    concepts: list[str] = Field(default_factory=list, description="Extracted concepts")
    relationships: list[str] = Field(default_factory=list, description="Extracted relationships")
    insights: list[str] = Field(default_factory=list, description="Extracted insights")
    patterns: list[str] = Field(default_factory=list, description="Extracted patterns")
    sources: list[str] = Field(default_factory=list, description="Source files")
    match_quality: str = Field(default="unknown", description="Quality of retrieval matches: good, poor, or none")


class KnowledgeRetriever:
    """Retrieves relevant knowledge from extractions."""

    def __init__(self, knowledge_path: Path, config):
        """Initialize retriever.

        Args:
            knowledge_path: Path to extractions.jsonl file
            config: Knowledge assist configuration
        """
        self.knowledge_path = knowledge_path
        self.config = config

    def retrieve(self, topic: str, question: str | None = None) -> RetrievedKnowledge:
        """Retrieve relevant knowledge for topic and question.

        Args:
            topic: Research topic
            question: Optional specific question

        Returns:
            Retrieved knowledge with match quality indicator
        """
        if not self.knowledge_path.exists():
            logger.warning(f"Knowledge file not found: {self.knowledge_path}")
            return RetrievedKnowledge()

        # Collect all entries with relevance scores
        entries_with_scores = []

        try:
            with open(self.knowledge_path) as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        entry = json.loads(line)
                        score = self._calculate_relevance_score(entry, topic, question)
                        if score > 0:
                            entries_with_scores.append((entry, score))
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON line in extractions: {line[:100]}")
                        continue

        except Exception as e:
            logger.error(f"Error retrieving knowledge: {e}")
            return RetrievedKnowledge()

        # Sort by relevance score
        entries_with_scores.sort(key=lambda x: x[1], reverse=True)

        # Check match quality
        if entries_with_scores:
            top_score = entries_with_scores[0][1]
            logger.info(f"Top relevance score: {top_score:.1f}")
            if top_score < 10.0:
                logger.warning("Weak topic matches - results may be off-topic")

        # Build knowledge from top scored entries
        knowledge = RetrievedKnowledge()
        seen_concepts = set()
        seen_relationships = set()
        seen_insights = set()
        seen_patterns = set()

        for entry, _score in entries_with_scores:
            # Extract concepts
            if "concepts" in entry and len(knowledge.concepts) < self.config.max_concepts:
                for concept in entry["concepts"]:
                    if isinstance(concept, dict):
                        concept_text = concept.get("name", "")
                    else:
                        concept_text = str(concept)

                    if concept_text and concept_text not in seen_concepts:
                        knowledge.concepts.append(concept_text)
                        seen_concepts.add(concept_text)
                        if len(knowledge.concepts) >= self.config.max_concepts:
                            break

            # Extract relationships
            if "relationships" in entry and len(knowledge.relationships) < self.config.max_relationships:
                for rel in entry["relationships"]:
                    if isinstance(rel, dict):
                        subject = rel.get("subject", "")
                        predicate = rel.get("predicate", "")
                        obj = rel.get("object", "")
                        if subject and predicate and obj:
                            rel_text = f"{subject} {predicate} {obj}"
                        else:
                            rel_text = ""
                    else:
                        rel_text = str(rel)

                    if rel_text and rel_text not in seen_relationships:
                        knowledge.relationships.append(rel_text)
                        seen_relationships.add(rel_text)
                        if len(knowledge.relationships) >= self.config.max_relationships:
                            break

            # Extract insights
            if "insights" in entry and len(knowledge.insights) < self.config.max_insights:
                for insight in entry["insights"]:
                    if isinstance(insight, dict):
                        insight_text = insight.get("text", "")
                    else:
                        insight_text = str(insight)

                    if insight_text and insight_text not in seen_insights:
                        knowledge.insights.append(insight_text)
                        seen_insights.add(insight_text)
                        if len(knowledge.insights) >= self.config.max_insights:
                            break

            # Extract patterns
            if "patterns" in entry and len(knowledge.patterns) < self.config.max_patterns:
                for pattern in entry["patterns"]:
                    if isinstance(pattern, dict):
                        pattern_text = pattern.get("name", "")
                    else:
                        pattern_text = str(pattern)

                    if pattern_text and pattern_text not in seen_patterns:
                        knowledge.patterns.append(pattern_text)
                        seen_patterns.add(pattern_text)
                        if len(knowledge.patterns) >= self.config.max_patterns:
                            break

            # Track source
            if "source_id" in entry and entry["source_id"] not in knowledge.sources:
                knowledge.sources.append(entry["source_id"])

            # Stop if we have enough of everything
            if (
                len(knowledge.concepts) >= self.config.max_concepts
                and len(knowledge.relationships) >= self.config.max_relationships
                and len(knowledge.insights) >= self.config.max_insights
                and len(knowledge.patterns) >= self.config.max_patterns
            ):
                break

        # Add match quality indicator to knowledge object
        if entries_with_scores:
            knowledge.match_quality = "good" if entries_with_scores[0][1] >= 10.0 else "poor"
        else:
            knowledge.match_quality = "none"

        logger.info(
            f"Retrieved: {len(knowledge.concepts)} concepts, "
            f"{len(knowledge.relationships)} relationships, "
            f"{len(knowledge.insights)} insights, "
            f"{len(knowledge.patterns)} patterns "
            f"(quality: {knowledge.match_quality if hasattr(knowledge, 'match_quality') else 'unknown'})"
        )

        return knowledge

    def _calculate_relevance_score(self, entry: dict, topic: str, question: str | None = None) -> float:
        """Calculate relevance with topic-dominant scoring.

        Args:
            entry: Knowledge entry
            topic: Research topic (primary, 80% weight)
            question: Optional question (secondary, 20% weight)

        Returns:
            Relevance score (higher is better)
        """
        # Build searchable text from entry
        entry_json = json.dumps(entry).lower()

        # Score topic relevance (primary driver)
        topic_score = self._score_text_against_query(entry_json, topic.lower())

        # Score question relevance (secondary refinement)
        question_score = 0.0
        if question:
            question_score = self._score_text_against_query(entry_json, question.lower())

        # Weighted combination: topic dominates (80/20 split)
        final_score = (topic_score * 0.8) + (question_score * 0.2)

        return final_score

    def _score_text_against_query(self, text: str, query: str) -> float:
        """Score text relevance against a single query string.

        Uses phrase matching (highest), bigram matching (medium),
        and individual word matching (lowest) with position weighting.

        Args:
            text: Text to score (should be lowercase)
            query: Query string (should be lowercase)

        Returns:
            Relevance score
        """
        score = 0.0

        # Exact phrase match (highest value)
        if query in text:
            score += 100.0

        # Split into words for further matching
        query_words = [w for w in query.split() if len(w) > 2]  # Skip tiny words

        # Bigram matching (adjacent word pairs)
        for i in range(len(query_words) - 1):
            bigram = f"{query_words[i]} {query_words[i + 1]}"
            if bigram in text:
                score += 30.0

        # Individual word matching with position weighting
        for i, word in enumerate(query_words):
            # Earlier words in query are more important (slight decay)
            position_weight = max(0.5, 1.0 - (i * 0.05))

            count = text.count(word)
            if count > 0:
                # Diminishing returns for multiple occurrences
                score += min(count, 3) * position_weight

        return score
