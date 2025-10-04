"""Minimal session management for knowledge-assist."""

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel
from pydantic import Field


class SessionInfo(BaseModel):
    """Information about a knowledge-assist session."""

    id: str = Field(description="Session ID (timestamp-based)")
    timestamp: datetime = Field(description="Session start time")
    topic: str = Field(description="Research topic")
    question: str | None = Field(default=None, description="Optional question")
    output_path: Path = Field(description="Path to output file")
    stats: dict = Field(default_factory=dict, description="Session statistics")

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class SessionManager:
    """Minimal session manager."""

    def __init__(self, output_dir: Path):
        """Initialize session manager.

        Args:
            output_dir: Directory to store session outputs
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, topic: str, question: str | None = None) -> SessionInfo:
        """Create a new session.

        Args:
            topic: Research topic
            question: Optional question

        Returns:
            Session information
        """
        timestamp = datetime.now()
        session_id = timestamp.strftime("%Y%m%d_%H%M%S")

        # Create date-based subdirectory
        date_dir = self.output_dir / timestamp.strftime("%Y-%m-%d")
        date_dir.mkdir(parents=True, exist_ok=True)

        # Create session output file in date directory
        output_filename = f"{timestamp.strftime('%H%M%S')}_{self._sanitize_filename(topic[:50])}.md"
        output_path = date_dir / output_filename

        session = SessionInfo(
            id=session_id, timestamp=timestamp, topic=topic, question=question, output_path=output_path, stats={}
        )

        # Save session info in date directory
        self._save_session_info(session)

        # Update index file
        self._update_index(session)

        return session

    def _sanitize_filename(self, text: str) -> str:
        """Sanitize text for filename.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized filename
        """
        # Replace spaces with underscores, remove special characters
        sanitized = "".join(c if c.isalnum() or c in "-_" else "_" for c in text)
        # Remove multiple underscores
        while "__" in sanitized:
            sanitized = sanitized.replace("__", "_")
        return sanitized.strip("_").lower()

    def _save_session_info(self, session: SessionInfo) -> None:
        """Save session info to JSON file.

        Args:
            session: Session information
        """
        # Save info file in the same directory as the output
        info_path = session.output_path.parent / f"{session.id}_info.json"
        with open(info_path, "w") as f:
            json.dump(
                {
                    "id": session.id,
                    "timestamp": session.timestamp.isoformat(),
                    "topic": session.topic,
                    "question": session.question,
                    "output_path": str(session.output_path),
                    "stats": session.stats,
                },
                f,
                indent=2,
            )

    def _update_index(self, session: SessionInfo) -> None:
        """Update the index.md file with new session entry.

        Args:
            session: Session information
        """
        index_path = self.output_dir / "index.md"

        # Read existing index or create header
        if index_path.exists():
            with open(index_path) as f:
                existing_content = f.read()
            # Find where entries start (after header)
            if "## Sessions\n" in existing_content:
                header, entries = existing_content.split("## Sessions\n", 1)
                header += "## Sessions\n"
            else:
                header = existing_content
                entries = ""
        else:
            header = "# Knowledge Assist Sessions\n\nAuto-generated index of all research sessions.\n\n## Sessions\n"
            entries = ""

        # Create new entry (most recent first)
        date_str = session.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        topic_display = session.topic[:100] + "..." if len(session.topic) > 100 else session.topic
        relative_path = session.timestamp.strftime("%Y-%m-%d") / Path(session.output_path.name)
        new_entry = f"- **{date_str}** - [{topic_display}]({relative_path})"
        if session.question:
            question_display = session.question[:50] + "..." if len(session.question) > 50 else session.question
            new_entry += f" - _{question_display}_"
        new_entry += "\n"

        # Combine with existing entries (new entry first)
        updated_content = header + new_entry + entries

        # Write updated index
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(index_path, "w") as f:
            f.write(updated_content)
