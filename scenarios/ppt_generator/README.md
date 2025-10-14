# PPT Generator: AI-Powered Presentation Creation

**Transform your content files into professional PowerPoint presentations with AI-generated visuals.**

## The Problem

You need to create presentations but:
- Converting content to slides is time-consuming and tedious
- Maintaining visual consistency across slides is difficult
- Creating technical diagrams requires specialized tools and expertise
- Finding appropriate images takes hours of searching
- Translating complex ideas into visual narratives is challenging
- Every revision means manually updating multiple slides

## The Solution

PPT Generator is a sophisticated 7-stage AI pipeline that transforms your content into professional presentations:

1. **Analyzes** your context files to understand the content deeply
2. **Structures** the presentation with logical flow and sections
3. **Generates** slide-by-slide content with appropriate depth
4. **Plans** visual elements (diagrams for concepts, images for engagement)
5. **Creates** Mermaid diagrams and AI images that match your content
6. **Reviews** layout with you for feedback using bracketed comments
7. **Assembles** everything into a polished 16:9 widescreen PPTX file

**The result**: Professional presentations generated in minutes, not hours, with consistent quality and visual appeal.

## Quick Start

**Prerequisites**: Complete the [Amplifier setup instructions](../../README.md#-step-by-step-setup) first, then:
- Ensure OpenAI API key is set as `OPENAI_API_KEY` environment variable
- Optional: DALL-E access for AI image generation
- Optional: Corporate PPTX template for branding

### Basic Usage

```bash
# Using Makefile (recommended)
make ppt-gen \
  CONTEXT="overview.md features.md" \
  DIRECTION="Create a technical presentation for developers"

# Or using Python directly
python -m scenarios.ppt_generator overview.md features.md \
  --direction "Create a technical presentation for developers" \
  --slides 10
```

The tool will:
1. Analyze your context files
2. Generate presentation structure and content
3. Create appropriate visuals (diagrams and images)
4. Show you a preview for review
5. Build the final PowerPoint file

### Your First Presentation

Try this simple example:

```bash
# Create a test file
echo "# AI Revolution
## The Impact on Business
- Automation of routine tasks
- Enhanced decision making
- New business models" > ai_content.md

# Generate presentation
make ppt-gen \
  CONTEXT="ai_content.md" \
  DIRECTION="Create an executive presentation about AI transformation"

# Output will be in .data/ppt_generator/{name}_{timestamp}/presentation.pptx
```

## Usage Examples

### Basic Presentation

Generate a simple presentation from markdown files:

```bash
make ppt-gen \
  CONTEXT="docs/overview.md docs/features.md" \
  DIRECTION="Create a product strategy presentation for 2024"
```

### With Corporate Template

Use your company's PowerPoint template for consistent branding:

```bash
make ppt-gen \
  CONTEXT="reports/quarterly.md" \
  DIRECTION="Create quarterly review presentation" \
  TEMPLATE="templates/corporate_template.pptx"
```

### Technical Architecture Presentation

Generate with emphasis on technical diagrams:

```bash
make ppt-gen \
  CONTEXT="architecture/*.md" \
  DIRECTION="Create system architecture overview with detailed diagrams" \
  SLIDES=20
```

The tool automatically detects technical content and creates:
- Flow diagrams for processes
- Architecture diagrams for systems
- Sequence diagrams for interactions
- Component diagrams for structures

### Marketing Presentation with Custom Visuals

Control the visual style:

```bash
make ppt-gen \
  CONTEXT="marketing/brand.md" \
  DIRECTION="Create brand evolution presentation" \
  STYLE="vibrant, colorful, modern startup aesthetic"
```

### Fast Generation (Skip Images)

For quicker results when images aren't needed:

```bash
make ppt-gen \
  CONTEXT="report.md" \
  DIRECTION="Create data analysis presentation" \
  SKIP_IMAGES=true
```

### Resume from Previous Session

Continue a partially completed generation:

```bash
# Resume automatically picks up from where it left off
python -m scenarios.ppt_generator notes.md \
  --direction "Create presentation" \
  --resume
```

## How It Works

### The 7-Stage Pipeline

1. **Context Analysis** (`content_analysis/`)
   - Analyzes all source files to extract key concepts
   - Identifies main topics and relationships
   - Determines technical level and audience
   - Creates a knowledge map of your content

2. **Outline Generation** (`outline_generation/`)
   - Designs presentation flow and narrative arc
   - Creates logical sections and transitions
   - Allocates content across slides
   - Plans information density per slide

3. **Slide Content** (`slide_content/`)
   - Generates detailed content for each slide
   - Writes compelling titles and bullet points
   - Creates speaker notes with additional context
   - Ensures consistent tone and style

4. **Visual Planning** (`visual_planning/`)
   - Analyzes each slide's content type
   - Determines: diagram, image, both, or text-only
   - Specifies diagram types (flowchart, architecture, etc.)
   - Plans image subjects and styles

5. **Visual Creation** (parallel stages)
   - **5a. Diagrams** (`diagram_generation/`): Creates Mermaid diagrams for technical content
   - **5b. Images** (`image_generation/`): Generates DALL-E images for engagement
   - Converts diagrams to PNG with proper sizing
   - Optimizes all visuals for slide layouts

6. **User Review** (`user_review/` + `feedback_processor/`)
   - Generates `layout_preview.md` with full content
   - Shows complete presentation layout before assembly
   - Accepts bracketed comments like `[add more detail here]`
   - **Regenerates slides** with your feedback using AI
   - Options: done (apply comments), approve (no changes), or skip

7. **PPT Assembly** (`ppt_assembly/`)
   - Creates 16:9 widescreen PowerPoint file
   - Smart visual positioning (right side with text, centered without)
   - Applies templates and consistent styling
   - Embeds images and diagrams properly
   - Saves to `presentation.pptx`

### Key Features

- **Smart Visual Layout**: Positions visuals on the right when there's content, centers them for visual-only slides
- **Full Content Preview**: Review shows all content without truncation
- **Bracketed Comments**: Add `[your feedback here]` in the preview for targeted changes
- **Progress Persistence**: Every stage saves state for resumability
- **Diagnostic Output**: `prompts.json` captures all AI prompts for debugging
- **Modern Format**: 16:9 widescreen presentations (not 4:3)

### File Structure

Each session creates organized output in `.data/ppt_generator/{name}_{timestamp}/`:
```
session_directory/
├── state.json           # Pipeline state for resume
├── layout_preview.md    # Full presentation preview
├── prompts.json        # All AI prompts (diagnostic)
├── presentation.pptx   # Final output
├── images/             # Generated images
│   ├── slide_2.png
│   └── slide_5.png
└── diagrams/          # Generated diagrams
    ├── slide_3.png
    └── slide_4.png
```

## Configuration

### Command-Line Options

```bash
python -m scenarios.ppt_generator <context_files> [OPTIONS]

Required:
  CONTEXT_FILES         One or more files with your content
  --direction, -d      Instructions for the presentation

Optional:
  --template, -t       PPTX template file for branding
  --output-dir, -o     Output directory (default: .data/ppt_generator/{name}_{timestamp})
  --slides            Target number of slides (default: 10)
  --style-images      Art style for images (default: "professional, modern, clean")
  --skip-images       Skip image generation for speed
  --skip-diagrams     Skip diagram generation
  --skip-review       Skip interactive review stage (for automated runs)
  --resume           Resume from previous session
```

### Makefile Variables

```bash
make ppt-gen \
  CONTEXT="file1.md file2.md"     # Required: source files
  DIRECTION="instructions"         # Required: what to create
  TEMPLATE="template.pptx"        # Optional: branding template
  OUTPUT="custom/path"             # Optional: output location
  SLIDES=15                        # Optional: slide count
  STYLE="art style"               # Optional: image style
  SKIP_IMAGES=true                # Optional: faster generation
  SKIP_DIAGRAMS=true              # Optional: text only
  SKIP_REVIEW=true                # Optional: for automated runs
```

### Environment Variables

```bash
# Required
export OPENAI_API_KEY="your-key-here"

# Optional model customization (defaults shown)
export PPT_ANALYSIS_MODEL="gpt-4o-mini"    # Context analysis (fast)
export PPT_OUTLINE_MODEL="gpt-4o"          # Structure planning (smart)
export PPT_CONTENT_MODEL="gpt-4o"          # Content generation (quality)
export PPT_VISUAL_MODEL="gpt-4o-mini"      # Visual planning (fast)
export PPT_DIAGRAM_MODEL="gpt-4o"          # Diagram generation (accurate)
export PPT_IMAGE_MODEL="dall-e-3"          # Image generation
```

## Troubleshooting

### Common Issues

**"No context files provided"**
- Ensure you provide at least one file as input
- Check file paths are correct and files exist
- Use full paths if relative paths aren't working

**"Direction is required"**
- Always provide `--direction` or `-d` with instructions
- Be specific: "Create technical overview" is better than "Make presentation"

**"Template not applied correctly"**
- Use a PPTX file (not POTX or PPT)
- Ensure template has standard slide layouts
- Check template file isn't corrupted
- Template should have at least Title, Title and Content, and Section layouts

**"Diagrams not rendering"**
- Check the `diagrams/` folder for generated PNG files
- Verify Mermaid syntax in `prompts.json` if debugging
- Some content may not be suitable for diagrams
- Use `--skip-diagrams` to test without them

**"Image generation failed"**
- Verify DALL-E API access and credits
- Check API rate limits (usually 5 images per minute)
- Review image prompts in `prompts.json`
- Use `--skip-images` for faster generation without images

**"Session resume not working"**
- Check `state.json` exists in the session directory
- Verify you're in the same directory when resuming
- Use `--resume` flag without other parameters
- Check `.data/ppt_generator/` for session folders

### Review Stage Issues

**"Can't find layout_preview.md"**
- File is created in the session directory
- Full path is shown in the console output
- Check `.data/ppt_generator/{name}_{timestamp}/`

**"Bracketed comments not detected"**
- Use square brackets: `[like this]`
- Avoid markdown link syntax: `[text](url)` will be ignored
- Save the file after adding comments
- Comments should be inline with content, not on separate lines
- After typing `done`, check console - it will show how many comments were found

**"Comments were found but slides weren't regenerated"**
- Check console output for "Applying X feedback comments..." message
- Verify the stage didn't error out before regeneration
- If regeneration fails for a slide, the original is kept
- Check `state.json` to see if review_complete is marked

### Performance Tips

- **Start small**: Test with 5-10 slides first
- **Skip visuals for speed**: Use `--skip-images` and/or `--skip-diagrams`
- **Use focused content**: Specific documents work better than entire folders
- **Prepare content**: Well-structured markdown with clear headings works best
- **Set realistic targets**: 10-15 slides is optimal for most presentations

### Debug Information

The tool saves diagnostic data for troubleshooting:

- **state.json**: Current pipeline state and progress
- **prompts.json**: All AI prompts and parameters used
- **layout_preview.md**: Full presentation content before assembly
- **Console output**: Stage-by-stage progress and any errors

Run with Python directly to see more detailed output:
```bash
python -m scenarios.ppt_generator document.md \
  --direction "Create presentation" \
  2>&1 | tee debug.log
```

## Best Practices

### Content Preparation

1. **Structure your content** with clear hierarchy:
   ```markdown
   # Main Topic
   ## Key Section
   ### Subsection
   - Bullet point
   - Another point
     - Sub-bullet
   ```

2. **Name files descriptively** for better context:
   ```
   project/
   ├── 01_executive_summary.md
   ├── 02_problem_statement.md
   ├── 03_proposed_solution.md
   └── 04_implementation_plan.md
   ```

3. **Include technical details** for automatic diagram generation:
   - System architectures → architecture diagrams
   - Process flows → flowcharts
   - Data relationships → entity diagrams
   - User journeys → sequence diagrams

### Direction Writing

Write clear, specific directions:

**Good directions:**
- "Create a technical presentation for developers about our API architecture"
- "Build an investor pitch focusing on market opportunity and growth"
- "Generate training material for new employees about our product"

**Avoid vague directions:**
- "Make it good"
- "Create presentation"
- "Professional slides"

### Using the Review Stage

The review stage (Stage 6) lets you refine the presentation before final assembly:

1. **Review the preview**: Open `layout_preview.md` in your editor
2. **Add feedback**: Insert `[bracketed comments]` where you want changes
3. **Be specific**: `[Add revenue numbers here]` is better than `[more detail]`
4. **Save and type 'done'**: The tool will regenerate those slides with your feedback
5. **Assembly continues**: Your improved slides are used in the final PowerPoint

**What happens when you add comments:**
- The tool identifies slides with `[comments]`
- Regenerates only those slides using AI, incorporating your feedback
- Preserves slides without comments (saves cost and time)
- Continues to assembly with the updated content

Example feedback:
```markdown
## Slide 3: Market Opportunity

- Global market size: $50B [update this to 2024 numbers]
- Annual growth rate: 15% [add source citation]
- Key segments [expand with specific percentages and regional breakdown]
```

After you type `done`, Slide 3 will be regenerated with updated numbers, citation, and expanded segmentation.

### Template Guidelines

For best results with templates:
- Use standard PowerPoint layouts (Title, Content, Two Content)
- Keep master slide formatting simple
- Test with a small presentation first
- See [Template Guide](templates/template_guide.md) for detailed instructions

### Optimal Configurations

**Quick draft (5 minutes):**
```bash
make ppt-gen CONTEXT="notes.md" DIRECTION="Quick overview" SKIP_IMAGES=true SLIDES=5
```

**Detailed technical (15 minutes):**
```bash
make ppt-gen CONTEXT="*.md" DIRECTION="Technical deep-dive" SLIDES=15
```

**Executive presentation (10 minutes):**
```bash
make ppt-gen CONTEXT="summary.md" DIRECTION="Executive briefing" TEMPLATE="exec.pptx" SLIDES=8
```

## How to Give Feedback

During the review stage, the tool shows you the complete presentation and lets you refine it:

### Option 1: Add Inline Comments (Regenerates Slides)
Edit the preview file and add `[bracketed comments]` where you want changes:
```markdown
This slide explains our approach [need specific example here]
The revenue projection shows growth [add comparison to last year]
Market opportunity is growing [include specific market size data]
```

When you type `done`, the tool:
1. Identifies which slides have comments
2. **Regenerates only those slides** using AI with your feedback
3. Continues to PowerPoint assembly with the improved slides

**Result**: Your feedback is incorporated into the final presentation, not just noted.

### Option 2: Approve As-Is
Type `approve` if the presentation is perfect. Skips regeneration and proceeds to assembly.

### Option 3: Skip Review
Type `skip` to proceed without viewing the preview. Useful for automated runs or when you trust the AI.

## Learn More

- **[HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md)** - Build your own AI pipeline tools
- **[Template Guide](templates/template_guide.md)** - Create custom PowerPoint templates
- **[Blog Writer](../blog_writer/)** - Similar pattern for blog generation
- **[Amplifier Scenarios](../)** - Collection of AI-powered tools

## What Makes This Different

Unlike simple "prompt-to-slides" tools, PPT Generator:

1. **Thinks in stages** - Each stage optimized for its specific task
2. **Creates real visuals** - Not just text slides with bullet points
3. **Maintains coherence** - Content flows logically across all slides
4. **Supports iteration** - Review and refine until perfect
5. **Preserves progress** - Resume from any stage if interrupted
6. **Respects your brand** - Works with your existing templates

## Credits

Built using the Amplifier framework's metacognitive recipe pattern. This tool demonstrates how breaking complex tasks into specialized stages produces superior results.

---

**Created with Amplifier** - From a single conversation describing the desired outcome and thinking process. See [HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md) to learn how.