"""
DEPRECATED: This module is deprecated and should not be used.
Use amplifier.content_loader.ContentLoader instead.

This module was replaced with the proper ContentLoader from amplifier.content_loader
which provides the correct mapping of content_id to titles and file paths.

The previous implementation was trying to reconstruct mappings from knowledge files,
but the real ContentLoader already has all the necessary information.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ContentLoader:
    """Loads and maps content from knowledge extractions"""

    def __init__(self, config):
        """Initialize content loader

        Args:
            config: Knowledge assist configuration
        """
        self.config = config
        self.knowledge_path = config.knowledge_path
        self._knowledge_map = None

    def get_knowledge_map(self) -> dict:
        """Get mapping of source IDs to file information

        Returns a dictionary mapping source hash IDs to file metadata:
        {
            "hash_id": {
                "path": "path/to/file.md",
                "title": "Document Title",
                "type": "markdown"
            }
        }

        Returns:
            Dictionary mapping source IDs to file information
        """
        if self._knowledge_map is not None:
            return self._knowledge_map

        self._knowledge_map = {}

        # Try to load knowledge file to get source mappings
        if self.knowledge_path.exists():
            try:
                with open(self.knowledge_path) as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            source_id = entry.get("source")
                            if source_id and source_id not in self._knowledge_map:
                                # Extract file path from metadata if available
                                metadata = entry.get("metadata", {})
                                file_path = metadata.get("file_path", "")

                                if not file_path and ":" in source_id:
                                    # Try to infer from source format
                                    # Source might be in format "filename.md:hash"
                                    file_part = source_id.split(":")[0]
                                    if file_part.endswith((".md", ".txt", ".rst")):
                                        file_path = file_part

                                if file_path:
                                    # Create entry for this source
                                    path_obj = Path(file_path)
                                    title = path_obj.stem.replace("_", " ").replace("-", " ").title()

                                    self._knowledge_map[source_id] = {
                                        "path": str(path_obj),
                                        "title": title,
                                        "type": path_obj.suffix.lstrip(".") if path_obj.suffix else "unknown",
                                    }
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.debug(f"Error processing knowledge entry: {e}")
                            continue

            except Exception as e:
                logger.warning(f"Could not load knowledge mappings: {e}")

        # Also check extraction directory for direct file mappings
        extractions_dir = self.config.extractions_dir
        if extractions_dir and extractions_dir.exists():
            try:
                # Look for extraction files that might contain source mappings
                for extraction_file in extractions_dir.glob("*.jsonl"):
                    with open(extraction_file) as f:
                        for line in f:
                            try:
                                entry = json.loads(line.strip())
                                source_id = entry.get("source")
                                metadata = entry.get("metadata", {})

                                # Check if we have file_path in metadata
                                file_path = metadata.get("file_path", "")
                                if source_id and file_path and source_id not in self._knowledge_map:
                                    path_obj = Path(file_path)
                                    title = metadata.get(
                                        "title", path_obj.stem.replace("_", " ").replace("-", " ").title()
                                    )

                                    self._knowledge_map[source_id] = {
                                        "path": str(path_obj),
                                        "title": title,
                                        "type": metadata.get(
                                            "file_type", path_obj.suffix.lstrip(".") if path_obj.suffix else "unknown"
                                        ),
                                    }
                            except Exception:
                                continue
            except Exception as e:
                logger.debug(f"Could not load extraction mappings: {e}")

        return self._knowledge_map
