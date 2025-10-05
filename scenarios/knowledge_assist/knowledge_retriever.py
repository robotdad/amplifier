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

        # Combine topic and question for search
        search_text = topic.lower()
        if question:
            search_text += " " + question.lower()

        # Collect all entries with relevance scores
        entries_with_scores = []

        try:
            with open(self.knowledge_path) as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        entry = json.loads(line)
                        score = self._calculate_relevance_score(entry, search_text)
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
        if entries_with_scores and entries_with_scores[0][1] < 10.0:
            # All matches are weak
            logger.warning(f"Weak relevance matches (top score: {entries_with_scores[0][1]:.1f})")
            # Still return results but with a warning - main.py will handle the escape hatch
        elif entries_with_scores:
            logger.info(f"Top relevance score: {entries_with_scores[0][1]:.1f}")

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

    def _calculate_relevance_score(self, entry: dict, search_text: str) -> float:
        """Calculate relevance score for entry with phrase matching.

        Args:
            entry: Knowledge entry
            search_text: Search text

        Returns:
            Relevance score (higher is better)
        """
        score = 0.0
        entry_json = json.dumps(entry).lower()

        # Exact phrase match (highest weight)
        if search_text in entry_json:
            score += 100.0

        # Check for phrase matches in key fields
        for concept in entry.get("concepts", []):
            concept_text = (concept.get("name", "") if isinstance(concept, dict) else str(concept)).lower()
            if search_text in concept_text:
                score += 50.0  # Phrase in concept name
            else:
                # Individual word matches in concepts
                for word in search_text.split():
                    if len(word) > 2 and word in concept_text:
                        score += 5.0

        for insight in entry.get("insights", []):
            insight_text = (insight.get("text", "") if isinstance(insight, dict) else str(insight)).lower()
            if search_text in insight_text:
                score += 30.0  # Phrase in insight
            else:
                for word in search_text.split():
                    if len(word) > 2 and word in insight_text:
                        score += 3.0

        for pattern in entry.get("patterns", []):
            pattern_text = (pattern.get("name", "") if isinstance(pattern, dict) else str(pattern)).lower()
            if search_text in pattern_text:
                score += 30.0  # Phrase in pattern
            else:
                for word in search_text.split():
                    if len(word) > 2 and word in pattern_text:
                        score += 3.0

        # Check relationships
        for rel in entry.get("relationships", []):
            if isinstance(rel, dict):
                rel_text = f"{rel.get('subject', '')} {rel.get('predicate', '')} {rel.get('object', '')}".lower()
            else:
                rel_text = str(rel).lower()

            if search_text in rel_text:
                score += 20.0  # Phrase in relationship
            else:
                for word in search_text.split():
                    if len(word) > 2 and word in rel_text:
                        score += 2.0

        # Check content field if it exists
        if "content" in entry:
            content_text = str(entry["content"]).lower()
            if search_text in content_text:
                score += 10.0
            else:
                for word in search_text.split():
                    if len(word) > 2 and word in content_text:
                        score += 1.0

        # Individual word matches in full entry (lower weight)
        # Only count substantive words (not common words like "the")
        common_words = {
            "the",
            "and",
            "for",
            "with",
            "from",
            "about",
            "this",
            "that",
            "what",
            "how",
            "why",
            "when",
            "where",
            "who",
        }
        for word in search_text.split():
            if len(word) > 3 and word not in common_words and word in entry_json:
                score += 0.5

        return score
