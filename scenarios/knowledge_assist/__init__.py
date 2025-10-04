"""Knowledge-assist scenario tool for research synthesis.

A tool for synthesizing knowledge from extracted insights and web search.
"""

from .config import KnowledgeAssistConfig
from .knowledge_retriever import KnowledgeRetriever
from .knowledge_retriever import RetrievedKnowledge
from .output_generator import OutputGenerator
from .session import SessionInfo
from .session import SessionManager
from .synthesis_engine import SynthesisEngine
from .synthesis_engine import SynthesisResult

__all__ = [
    "KnowledgeAssistConfig",
    "KnowledgeRetriever",
    "RetrievedKnowledge",
    "OutputGenerator",
    "SessionInfo",
    "SessionManager",
    "SynthesisEngine",
    "SynthesisResult",
]

__version__ = "0.1.0"
