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
            Retrieved knowledge
        """
        if not self.knowledge_path.exists():
            logger.warning(f"Knowledge file not found: {self.knowledge_path}")
            return RetrievedKnowledge()

        # Combine topic and question for search
        search_text = topic.lower()
        if question:
            search_text += " " + question.lower()

        knowledge = RetrievedKnowledge()
        seen_concepts = set()
        seen_relationships = set()
        seen_insights = set()
        seen_patterns = set()

        try:
            with open(self.knowledge_path) as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        entry = json.loads(line)

                        # Check if entry is relevant
                        if not self._is_relevant(entry, search_text):
                            continue

                        # Extract concepts
                        if "concepts" in entry:
                            for concept in entry["concepts"]:
                                if isinstance(concept, dict):
                                    concept_text = concept.get("text", "")
                                else:
                                    concept_text = str(concept)

                                if concept_text and concept_text not in seen_concepts:
                                    knowledge.concepts.append(concept_text)
                                    seen_concepts.add(concept_text)
                                    if len(knowledge.concepts) >= self.config.max_concepts:
                                        break

                        # Extract relationships
                        if "relationships" in entry:
                            for rel in entry["relationships"]:
                                if isinstance(rel, dict):
                                    rel_text = rel.get("text", "")
                                else:
                                    rel_text = str(rel)

                                if rel_text and rel_text not in seen_relationships:
                                    knowledge.relationships.append(rel_text)
                                    seen_relationships.add(rel_text)
                                    if len(knowledge.relationships) >= self.config.max_relationships:
                                        break

                        # Extract insights
                        if "insights" in entry:
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
                        if "patterns" in entry:
                            for pattern in entry["patterns"]:
                                if isinstance(pattern, dict):
                                    pattern_text = pattern.get("text", "")
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

                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON line in extractions: {line[:100]}")
                        continue

        except Exception as e:
            logger.error(f"Error retrieving knowledge: {e}")

        logger.info(
            f"Retrieved: {len(knowledge.concepts)} concepts, "
            f"{len(knowledge.relationships)} relationships, "
            f"{len(knowledge.insights)} insights, "
            f"{len(knowledge.patterns)} patterns"
        )

        return knowledge

    def _is_relevant(self, entry: dict, search_text: str) -> bool:
        """Check if entry is relevant to search.

        Args:
            entry: Knowledge entry
            search_text: Search text

        Returns:
            True if relevant
        """
        # Check various fields for relevance
        fields_to_check = ["content", "concepts", "relationships", "insights", "patterns", "source_id"]

        for field in fields_to_check:
            if field in entry:
                field_value = entry[field]
                if isinstance(field_value, str):
                    if any(term in field_value.lower() for term in search_text.split()):
                        return True
                elif isinstance(field_value, list):
                    for item in field_value:
                        if isinstance(item, str):
                            if any(term in item.lower() for term in search_text.split()):
                                return True
                        elif (
                            isinstance(item, dict)
                            and "text" in item
                            and any(term in item["text"].lower() for term in search_text.split())
                        ):
                            return True

        return False
