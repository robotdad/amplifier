# Style Blender

Blend writing styles from multiple authors to create unique voice profiles for blog_writer.

## The Problem

The `blog_writer` tool needs sample writings to extract an author's style, but what if you don't have any? Or what if you want to create a unique voice by blending styles from multiple writers? That's where Style Blender comes in.

## The Solution

Style Blender analyzes writing samples from multiple authors, extracts their individual style characteristics, then intelligently blends them to create a new, harmonious writing voice. It generates sample writings in this blended style that can be fed directly to `blog_writer`.

## Quick Start

```bash
# Blend styles from two specific writers
make style-blend INPUT=writers/ OUTPUT=blended_samples/

# Or use Python directly with multiple sources
python -m scenarios.style_blender \
    --input-dirs writer1/ writer2/ writer3/ \
    --output-dir my_blended_style/ \
    --num-samples 5
```

Then use the blended samples with blog_writer:

```bash
python -m scenarios.blog_writer \
    --writings-dir blended_samples/ \
    --topic "Your topic here"
```

## How It Works

Style Blender uses a 3-stage pipeline to create blended writing samples:

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│ Stage 1:        │     │ Stage 2:     │     │ Stage 3:        │
│ Style Analyzer  │────▶│ Style        │────▶│ Content         │
│                 │     │ Blender      │     │ Generator       │
├─────────────────┤     ├──────────────┤     ├─────────────────┤
│ Extract style   │     │ Blend        │     │ Generate 3-5    │
│ from each       │     │ multiple     │     │ sample writings │
│ writer's        │     │ styles into  │     │ using blended   │
│ samples         │     │ unified      │     │ style           │
│                 │     │ profile      │     │                 │
└─────────────────┘     └──────────────┘     └─────────────────┘
```

### Stage 1: Style Analysis
- Discovers writing samples recursively (`**/*.md`, `**/*.txt`)
- Extracts tone, vocabulary, sentence structure, common phrases
- Creates a StyleProfile for each writer
- Saves progress after each writer (resumable)

### Stage 2: Style Blending
- Combines structural patterns using statistical averaging
- Synthesizes tone and voice elements using AI
- Creates attribution map showing each writer's contributions
- Produces a BlendedStyleProfile

### Stage 3: Content Generation
- Generates 3-5 sample writings (300-500 words each)
- Uses different topic categories for variety
- Applies the blended style naturally
- Saves as markdown files ready for blog_writer

## Directory Structure

Your input directories should be organized like this:

```
writers/
├── hemingway/
│   ├── old_man_sea.txt
│   └── sun_also_rises.md
├── woolf/
│   ├── lighthouse.md
│   └── dalloway.txt
└── orwell/
    ├── 1984.md
    └── animal_farm.txt
```

Or you can specify multiple separate directories:

```bash
python -m scenarios.style_blender \
    -i ~/documents/writer1/ \
    -i ~/samples/writer2/ \
    -i ~/texts/writer3/
```

## Usage Examples

### Basic Usage

Blend two writers:

```bash
# Minimum case - blend two writers
python -m scenarios.style_blender \
    -i technical_writer/ -i creative_writer/ \
    -o blended_tech_creative/
```

### Multiple Writers

Blend many writers for a rich, complex style:

```bash
# Blend 5+ writers
python -m scenarios.style_blender \
    -i writers/ \
    -o complex_blend/ \
    -n 10  # Generate 10 samples
```

### Resume Interrupted Session

Style Blender saves its progress after each writer and sample:

```bash
# Start processing
python -m scenarios.style_blender -i big_library/ -o output/

# Interrupt with Ctrl+C...
# Later, resume where you left off:
python -m scenarios.style_blender -i big_library/ -o output/ --resume
```

### Verbose Mode

See detailed processing information:

```bash
python -m scenarios.style_blender \
    -i writers/ -o output/ --verbose
```

## Integration with blog_writer

The generated samples are specifically formatted for blog_writer:

```bash
# Step 1: Blend styles
make style-blend INPUT=favorite_writers/ OUTPUT=my_voice/

# Step 2: Use blended style for blog generation
python -m scenarios.blog_writer \
    --writings-dir my_voice/ \
    --topic "The Future of AI" \
    --output-dir blog_posts/
```

## Troubleshooting

### No files found
- Ensure your input directories contain `.md` or `.txt` files
- File discovery is recursive - files can be in subdirectories
- Hidden directories (starting with `.`) are skipped

### Need at least 2 writers
- Style blending requires multiple sources
- Each writer needs at least one readable text file
- If you have nested directories, each subdirectory counts as a writer

### AI extraction failures
- The tool uses defensive utilities to handle JSON parsing
- Statistical blending is used as fallback if AI fails
- Partial results are saved - you can always resume

### Memory/Performance
- Large files are truncated to 3000 chars per sample
- Maximum 5 samples per writer are analyzed
- Progress is saved incrementally to handle large batches

## What's Next

Once you have your blended samples:

1. **Review the samples** - Check if the blended style matches your vision
2. **Iterate if needed** - Try different writer combinations
3. **Use with blog_writer** - Generate unlimited content in your new voice
4. **Fine-tune** - Edit samples manually for even better results

## Advanced Tips

### Creating Persona Libraries

Build a library of blended personas for different content needs:

```bash
# Professional technical writer
python -m scenarios.style_blender \
    -i tech_writers/ -o personas/technical/

# Friendly educator
python -m scenarios.style_blender \
    -i educators/ -o personas/educator/

# Creative storyteller
python -m scenarios.style_blender \
    -i fiction_writers/ -o personas/storyteller/
```

### Weighted Blending

While not directly supported, you can influence blending by including more samples from preferred writers:

```
writers/
├── main_influence/      # 10 samples
│   └── many_samples.md
├── secondary/          # 3 samples
│   └── few_samples.md
└── minor/              # 1 sample
    └── one_sample.md
```

### Quality Control

The tool shows which writers contributed what:

```
=== Stage 2: Blending Styles ===
  ✓ Blending strategy: harmonious blend of technical precision and creative flow

Attribution:
  • hemingway: conciseness, active voice
  • woolf: flowing sentences, introspection
  • orwell: clarity, directness
```

Use this to understand your blended voice better.

## Requirements

- Python 3.11+
- Claude API access (via amplifier.ccsdk_toolkit)
- At least 2 directories with writing samples
- Markdown (.md) or text (.txt) files

## Architecture Notes

Style Blender follows the modular design philosophy:

- **Separation of concerns**: Each stage is independent
- **Defensive programming**: Handles AI failures gracefully
- **Incremental saves**: Never lose progress
- **Clear visibility**: Shows what's happening at each step

The tool prioritizes reliability over perfection - it's better to complete with a statistical blend than fail entirely when AI has issues.