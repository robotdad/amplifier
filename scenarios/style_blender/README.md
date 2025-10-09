# Style Blender - Writing Style Synthesis

Blend writing styles from multiple authors to create unique voice profiles for blog_writer.

## The Problem

You want to use `blog_writer` to create content in a specific voice, but:
- **You don't have existing blog posts** to extract your style from
- **Your current writing is too dry** (technical docs, business memos)
- **You can't use someone else's writing directly** - that would be plagiarism
- **You want a unique blend** combining elements from writers you admire

## The Solution

Style Blender analyzes writing samples from 2+ authors, extracts their individual style characteristics, then intelligently blends them to create a new, harmonious writing voice. It generates sample writings in this blended style that can be fed directly to `blog_writer`.

## Features

- **Multi-Author Analysis**: Extract style from 2-10 different writers
- **Flexible Input**: Accepts individual files or directories of samples
- **AI-Powered Blending**: Intelligently combines styles (not just averaging)
- **Sample Generation**: Creates 3-5 blog posts demonstrating the blended style
- **Comprehensive Diagnostics**: Saves all profiles, prompts, and analysis
- **blog_writer Compatible**: Output ready for direct use with blog_writer

## Quick Start

```bash
# Blend styles from writer directories
make style-blend INPUT=writers/

# Or blend from specific files (useful for mixed collections)
make style-blend INPUT="lovecraft.txt,carroll.txt,poe.txt"

# Or mix both
make style-blend INPUT="hemingway_dir/,woolf.txt,faulkner_dir/"
```

Then use the blended samples with blog_writer:

```bash
make blog-write IDEA=your_idea.md WRITINGS=.data/style_blender/20251008_183052/output
```

## Usage

### Basic Usage

```bash
make style-blend INPUT=~/books/
```

Automatically saves to `.data/style_blender/<timestamp>/`

### With Options

```bash
make style-blend INPUT=~/collections/ NUM_SAMPLES=5
```

### Custom Output Directory

```bash
make style-blend INPUT=writers/ OUTPUT=my_blended_style/
```

### Python CLI

```bash
python -m scenarios.style_blender \
    --input-dirs writer1/ writer2.txt writer3/ \
    --num-samples 5 \
    --verbose
```

## Input Organization

**Each file or directory = one writer**

### Option 1: Directory per writer (multiple samples)
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

make style-blend INPUT=writers/
```

### Option 2: One file per writer
```
collections/
├── lovecraft_complete.txt
├── carroll_alice.txt
└── poe_collected.txt

make style-blend INPUT="collections/lovecraft_complete.txt,collections/carroll_alice.txt,collections/poe_collected.txt"
```

### Option 3: Mix files and directories
```
make style-blend INPUT="hemingway_dir/,woolf.txt,orwell.md"
```

**Note:** Subdirectories with images, videos, or other non-text files are automatically ignored.

## Output Structure

```
.data/style_blender/20251008_183052/
├── index.md                     ← Overview with blend analysis and links
├── blended_profile.json         ← Diagnostic: final blended style data
├── writer_Alice.json            ← Diagnostic: individual style analysis
├── writer_cthulu.json           ← Diagnostic: individual style analysis
├── prompt_blending.txt          ← Diagnostic: prompt used for blending
├── prompt_sample_01.txt         ← Diagnostic: prompt for sample 1
├── prompt_sample_02.txt         ← Diagnostic: prompt for sample 2
├── prompt_sample_03.txt         ← Diagnostic: prompt for sample 3
└── output/                      ← Clean path for blog_writer
    ├── blended_sample_01.md     ← 300-500 word blog post
    ├── blended_sample_02.md     ← 300-500 word blog post
    └── blended_sample_03.md     ← 300-500 word blog post
```

**Use the `output/` subdirectory with blog_writer** - it contains only the generated samples, not the diagnostic files.

## How It Works

### 3-Stage Pipeline

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

For each writer:
- Discovers text files recursively (`.md`, `.txt`)
- Reads up to 5 files, 3,000 characters each (~15K chars total)
- Extracts: tone, vocabulary, sentence structure, common phrases, patterns
- Creates a StyleProfile for each writer
- Saves individual profiles to JSON

### Stage 2: Style Blending

- Combines structural patterns (paragraph length, etc.)
- Synthesizes tone and voice elements using AI
- Creates attribution map showing each writer's contributions
- Produces a BlendedStyleProfile
- Saves blended profile and blending prompt to disk

### Stage 3: Content Generation

- Generates 3-5 sample blog posts (300-500 words each)
- Uses different topic categories for variety
- Applies the blended style naturally
- Saves samples to `output/` subdirectory
- Saves generation prompts for diagnostics

**Code handles**: File I/O, iteration, state management, error recovery
**AI handles**: Style understanding, blending synthesis, creative content generation

## Requirements

- **API Key**: Set `ANTHROPIC_API_KEY` in `.env` or environment
- **Minimum 2 writers**: Can't blend a single style
- **Text files**: Supports `.md` and `.txt` formats

## Troubleshooting

### "ANTHROPIC_API_KEY not found"

**Problem**: API key not configured

**Solution**: Add to your `.env` file:
```bash
ANTHROPIC_API_KEY=your-key-here
```

Get your key at: https://console.anthropic.com/

### "Need at least 2 writers to blend styles"

**Problem**: Only found one writer or file

**Solution**: Ensure you provide 2+ files or directories. Remember:
- Each file = one writer
- Each directory = one writer

### Alice/Carroll Dominates the Blend

**Problem**: One writer's style is overrepresented in output

**Solution**: This is normal variability in AI blending. Try:
1. Re-run the tool (stochastic outputs vary)
2. Check diagnostic files to see the blend breakdown
3. Adjust input samples (shorter excerpts vs full books)

### Images or PDFs Not Working

**Problem**: Tool only finds markdown/text files

**Solution**: Currently only `.md` and `.txt` files are supported. Images and other files are automatically skipped.

## Learn More

- **[HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md)** - Create your own tool like this
- **[Scenario Tools](../)** - More tools like this one
- **[Amplifier](https://github.com/microsoft/amplifier)** - The framework that powers these tools

## Integration with blog_writer

Style Blender is designed as a companion to blog_writer:

```bash
# Step 1: Blend styles
make style-blend INPUT=favorite_authors/

# Step 2: Use blended samples to write blog posts
make blog-write IDEA=your_idea.md WRITINGS=.data/style_blender/20251008_183052/output
```

The generated samples teach blog_writer the blended voice, which it then applies to your ideas.

## What's Next?

1. **Use it** - Blend styles from authors you admire
2. **Inspect diagnostics** - Check the JSON and prompts to understand the blend
3. **Experiment** - Try different author combinations
4. **Create content** - Use blended samples with blog_writer
5. **Share back** - Let others learn from your experience

---

**Built with Amplifier** - Created by describing the goal and thinking process in one conversation. See [HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md) for how you can create tools like this.
