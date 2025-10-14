"""Generate Mermaid diagrams and convert to images."""

import logging
import os
import subprocess
import tempfile
from pathlib import Path

from anthropic import Anthropic

from ..models import DiagramType
from ..models import SlideContent
from ..models import SlideDiagram
from ..models import VisualType

logger = logging.getLogger(__name__)


async def generate_diagrams(slides: list[SlideContent], output_dir: Path) -> list[SlideDiagram]:
    """Generate Mermaid diagrams for slides that need them.

    Args:
        slides: List of slides with visual planning complete
        output_dir: Directory to save diagram images

    Returns:
        List of generated diagrams with image paths
    """
    # Create diagrams directory
    diagrams_dir = output_dir / "diagrams"
    diagrams_dir.mkdir(exist_ok=True)

    # Filter slides that need diagrams
    slides_needing_diagrams = [s for s in slides if s.visual_type in [VisualType.DIAGRAM, VisualType.BOTH]]

    if not slides_needing_diagrams:
        logger.info("No slides need diagrams")
        return []

    diagrams = []
    # Initialize Anthropic client with API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        return []

    client = Anthropic(api_key=api_key)

    for slide in slides_needing_diagrams:
        try:
            diagram = await _generate_single_diagram(slide, diagrams_dir, client)
            if diagram:
                diagrams.append(diagram)
        except Exception as e:
            logger.error(f"Failed to generate diagram for slide {slide.slide_number}: {e}")
            continue

    logger.info(f"Generated {len(diagrams)} diagrams")
    return diagrams


async def _generate_single_diagram(slide: SlideContent, output_dir: Path, client: Anthropic) -> SlideDiagram | None:
    """Generate a single diagram for a slide."""

    # Create prompt for diagram generation
    prompt = f"""Create a Mermaid diagram for this presentation slide.

Slide Title: {slide.title}
Slide Content: {chr(10).join(slide.bullet_points)}
Visual Context: {slide.visual_context or "Create an appropriate diagram"}

Generate a clear, professional Mermaid diagram that illustrates the key concepts.
Choose the most appropriate diagram type:
- flowchart: for processes and workflows
- sequenceDiagram: for interactions over time
- classDiagram: for structures and relationships
- stateDiagram-v2: for state machines
- erDiagram: for entity relationships
- gantt: for timelines
- pie: for proportions
- gitGraph: for branching flows

Respond with:
1. The diagram type (one word from above list)
2. A brief description of what the diagram shows
3. The complete Mermaid code

Format:
TYPE: [type]
DESCRIPTION: [description]
MERMAID:
```mermaid
[your mermaid code here]
```"""

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022", max_tokens=2000, messages=[{"role": "user", "content": prompt}]
        )

        # Handle different response types from Anthropic API
        content = ""
        if response.content and len(response.content) > 0:
            first_content = response.content[0]
            # Check the type of content block and extract text
            from anthropic.types import TextBlock

            if isinstance(first_content, TextBlock):
                content = first_content.text
            else:
                # For other content block types, use string representation
                content = str(first_content)

        if not content:
            logger.warning("Empty response from API")
            return None

        # Parse response
        lines = content.split("\n") if isinstance(content, str) else []
        description = "Diagram for slide"
        mermaid_code = ""

        # Extract components
        diagram_type_enum = DiagramType.FLOWCHART  # default enum value
        for i, line in enumerate(lines):
            if line.startswith("TYPE:"):
                type_str = line.replace("TYPE:", "").strip().lower()
                # Map to DiagramType enum
                type_map = {
                    "flowchart": DiagramType.FLOWCHART,
                    "sequencediagram": DiagramType.SEQUENCE,
                    "classdiagram": DiagramType.CLASS,
                    "statediagram": DiagramType.STATE,
                    "erdiagram": DiagramType.ER,
                    "gantt": DiagramType.GANTT,
                    "pie": DiagramType.PIE,
                    "gitgraph": DiagramType.GIT,
                }
                diagram_type_enum = type_map.get(type_str, DiagramType.FLOWCHART)
            elif line.startswith("DESCRIPTION:"):
                description = line.replace("DESCRIPTION:", "").strip()
            elif "```mermaid" in line:
                # Extract mermaid code block
                start_idx = i + 1
                for j in range(start_idx, len(lines)):
                    if "```" in lines[j]:
                        mermaid_code = "\n".join(lines[start_idx:j])
                        break

        if not mermaid_code:
            # Try to extract any code block
            import re

            code_match = re.search(r"```(?:mermaid)?\n(.*?)\n```", content, re.DOTALL)
            if code_match:
                mermaid_code = code_match.group(1)

        if not mermaid_code:
            logger.warning(f"No Mermaid code found for slide {slide.slide_number}")
            return None

        # Create diagram object
        diagram = SlideDiagram(
            slide_number=slide.slide_number,
            diagram_type=diagram_type_enum,
            title=slide.title,
            description=description,
            mermaid_code=mermaid_code,
        )

        # Save Mermaid code
        mermaid_file = output_dir / f"slide_{slide.slide_number}_diagram.mmd"
        mermaid_file.write_text(mermaid_code)
        logger.info(f"Saved Mermaid code to {mermaid_file}")

        # Try to render to image
        image_path = await _render_mermaid_to_image(mermaid_code, slide.slide_number, output_dir)
        if image_path:
            diagram.image_path = image_path
            logger.info(f"Rendered diagram image: {image_path}")

        return diagram

    except Exception as e:
        logger.error(f"Failed to generate diagram: {e}")
        return None


async def _render_mermaid_to_image(mermaid_code: str, slide_number: int, output_dir: Path) -> Path | None:
    """Render Mermaid code to PNG image.

    Tries multiple methods:
    1. mmdc (Mermaid CLI) if installed
    2. Playwright with HTML rendering
    3. Returns None if rendering fails (Mermaid code is still saved)
    """
    output_image = output_dir / f"slide_{slide_number}_diagram.png"

    # Method 1: Try mmdc (Mermaid CLI)
    if _check_mmdc_available():
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as temp_mmd:
                temp_mmd.write(mermaid_code)
                temp_mmd.flush()

                result = subprocess.run(
                    ["mmdc", "-i", temp_mmd.name, "-o", str(output_image), "-b", "white", "--width", "1600"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0 and output_image.exists():
                    Path(temp_mmd.name).unlink()
                    return output_image
                logger.warning(f"mmdc failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"mmdc rendering failed: {e}")

    # Method 2: Try Playwright
    try:
        from playwright.async_api import async_playwright

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{ startOnLoad: true }});</script>
    <style>
        body {{ background: white; padding: 20px; }}
        .mermaid {{ text-align: center; }}
    </style>
</head>
<body>
    <div class="mermaid">
{mermaid_code}
    </div>
</body>
</html>"""

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html_content)
            await page.wait_for_timeout(2000)  # Wait for Mermaid to render

            # Screenshot the diagram
            element = await page.query_selector(".mermaid")
            if element:
                await element.screenshot(path=str(output_image))
                await browser.close()
                return output_image
            await browser.close()

    except ImportError:
        logger.warning("Playwright not installed, cannot render diagram to image")
    except Exception as e:
        logger.warning(f"Playwright rendering failed: {e}")

    logger.warning("Could not render diagram to image, Mermaid code saved as .mmd file")
    return None


def _check_mmdc_available() -> bool:
    """Check if mmdc (Mermaid CLI) is available."""
    try:
        result = subprocess.run(["mmdc", "--version"], capture_output=True, timeout=5)
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False
