"""
Citation system for knowledge synthesis

Manages source numbering, reference formatting, and citation context
for AI-driven citation insertion through prompt engineering.
"""

from dataclasses import dataclass


@dataclass
class SourceInfo:
    """Information about a single source for citation"""

    number: int
    title: str
    source_id: str
    url: str
    source_type: str  # 'local' or 'web'


@dataclass
class CitationContext:
    """Context for citations in synthesis"""

    numbered_sources: list[SourceInfo]
    reference_map: dict[str, SourceInfo]  # source_id -> SourceInfo


def get_title_and_url(source_id: str, content_map: dict) -> tuple[str | None, str | None]:
    """Extract title and URL from a source ID using pre-loaded content map

    Args:
        source_id: The source identifier (hash or URL)
        content_map: Pre-loaded dict of {content_id: ContentItem}

    Returns:
        Tuple of (title, url) where url is file:// for local or https:// for web
    """
    # For web sources, the source_id is the URL itself
    if source_id.startswith("http"):
        # Extract title from URL - use domain and path as fallback
        from urllib.parse import urlparse

        parsed = urlparse(source_id)
        title = f"{parsed.netloc}{parsed.path}".rstrip("/")
        return (title, source_id)

    # For local sources, use pre-loaded map (NO SCANNING)
    if source_id in content_map:
        content_item = content_map[source_id]
        # Use the title from ContentItem
        title = content_item.title
        # Create proper file:// URL with absolute path
        url = f"file://{content_item.source_path}"
        return (title, url)

    # Fallback: use source_id as title if we can't determine it
    title = f"Source {source_id[:8]}..." if len(source_id) > 8 else source_id
    url = f"file://{source_id}"  # Assume local if not http

    return (title, url)


def prepare_citations(source_ids: list[str], content_loader) -> CitationContext:
    """Prepare citation context from source IDs

    Args:
        source_ids: List of source identifiers from knowledge retrieval
        content_loader: ContentLoader instance for mapping sources to titles/URLs

    Returns:
        CitationContext with numbered sources and reference mapping
    """
    # Pre-load all content items ONCE (cache the mapping)
    content_map = {item.content_id: item for item in content_loader.load_all(quiet=True)}

    numbered_sources = []
    reference_map = {}

    for idx, source_id in enumerate(source_ids, start=1):
        # Pass the cached map instead of content_loader
        title, url = get_title_and_url(source_id, content_map)

        # Determine source type
        source_type = "web" if url and url.startswith("http") else "local"

        # Create source info
        source_info = SourceInfo(
            number=idx, title=title or f"Source {idx}", source_id=source_id, url=url or "", source_type=source_type
        )

        numbered_sources.append(source_info)
        reference_map[source_id] = source_info

    return CitationContext(numbered_sources=numbered_sources, reference_map=reference_map)


def filter_referenced_citations(content: str, citation_context: CitationContext) -> CitationContext:
    """Filter citation context to only include sources actually referenced in content.

    Args:
        content: The synthesized content with citation markers [N]
        citation_context: Full citation context with all sources

    Returns:
        Filtered CitationContext with only referenced sources
    """
    import re

    # Find all [N] markers in content
    cited_numbers = set()
    for match in re.finditer(r"\[(\d+)\]", content):
        cited_numbers.add(int(match.group(1)))

    # Filter to only cited sources
    filtered_sources = [src for src in citation_context.numbered_sources if src.number in cited_numbers]

    # Rebuild reference map with only filtered sources
    filtered_map = {src.source_id: src for src in filtered_sources}

    return CitationContext(numbered_sources=filtered_sources, reference_map=filtered_map)


def format_references(citation_context: CitationContext) -> str:
    """Format citation context as markdown reference list

    Args:
        citation_context: The prepared citation context

    Returns:
        Markdown-formatted reference list with numbered entries
    """
    if not citation_context.numbered_sources:
        return ""

    lines = ["## References", ""]

    for source in citation_context.numbered_sources:
        # Format as standard numbered list: N. [Title](url)
        if source.url:
            reference = f"{source.number}. [{source.title}]({source.url})"
        else:
            # No URL available, just show title
            reference = f"{source.number}. {source.title}"

        lines.append(reference)

    return "\n".join(lines)
