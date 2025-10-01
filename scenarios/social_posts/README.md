# Social Media Post Generator

Transform your articles into engaging social media posts with AI-powered content analysis and platform optimization.

## The Problem

You've written a great article or blog post, and now you need to promote it on social media. But crafting engaging posts for different platforms is time-consuming:

- Each platform has different character limits and conventions
- You need to capture the essence of your article in bite-sized pieces
- The tone needs to match both your content and the platform
- You want posts that drive engagement, not just announce "new blog post"

Manually creating multiple posts for multiple platforms can take hours and often results in generic, uninspiring content.

## The Solution

This tool uses a three-stage AI pipeline to transform your article into platform-optimized social media posts:

1. **Analyze** - Extract tone, themes, and key points from your article
2. **Generate** - Create platform-specific posts matching your content's voice
3. **Review** - Score posts for quality and engagement potential

The result? High-quality, engaging social media posts that capture your article's essence and are optimized for each platform.

## Quick Start

```bash
# Generate posts from your article
python -m scenarios.social_posts article.md

# Customize tone and platforms
python -m scenarios.social_posts article.md \
    --tone inspirational \
    --platforms twitter,linkedin \
    --count 3
```

## Installation

```bash
# Install dependencies (if not already installed)
pip install -e .

# Set your OpenAI API key
export OPENAI_API_KEY="your-key-here"
```

## Usage Examples

### Basic Usage

Generate posts for all default platforms (Twitter, LinkedIn, Bluesky):

```bash
python -m scenarios.social_posts my_article.md
```

### Override Tone

Force a specific tone regardless of content analysis:

```bash
python -m scenarios.social_posts tech_article.md --tone conversational
```

### Select Specific Platforms

Generate posts only for selected platforms:

```bash
python -m scenarios.social_posts article.md --platforms twitter,mastodon
```

### Add Custom Guidance

Provide additional instructions for post generation:

```bash
python -m scenarios.social_posts article.md \
    --guidance "Include a call-to-action and mention our upcoming webinar"
```

### Resume from Interruption

If the process was interrupted, resume from where it left off:

```bash
python -m scenarios.social_posts article.md --resume
```

## What You Get

After running the tool, you'll find in your session directory:

1. **`{slug}_posts.json`** - Structured data with all posts and quality scores
2. **`{slug}_posts.md`** - Readable markdown with posts organized by platform
3. **`state.json`** - Pipeline state for resume capability

### Output Structure

The markdown output includes:

- **Best Posts** - Top-scoring posts across all platforms
- **All Posts by Platform** - Complete set organized by platform
- **Quality Scores** - Each post's clarity, engagement, and platform fit scores
- **Improvement Suggestions** - AI-generated tips for lower-scoring posts

## How It Works

### Stage 1: Content Analysis

The tool first analyzes your article to understand:
- **Tone** - Professional, casual, technical, inspirational, etc.
- **Themes** - Main topics and concepts (3-5 themes)
- **Key Points** - Specific insights and arguments (5-7 points)

### Stage 2: Post Generation

Using the analysis, the tool generates platform-optimized posts:
- **Character Limits** - Respects platform-specific limits (280 for Twitter, 500 for Mastodon, etc.)
- **Platform Conventions** - Adapts style for each platform's culture
- **Content Variety** - Each post highlights different aspects of your article
- **Tone Matching** - Maintains consistency with your article's voice

### Stage 3: Quality Review

Each post is reviewed and scored on:
- **Clarity** (30%) - Is the message clear and understandable?
- **Engagement** (40%) - Will it encourage interaction?
- **Platform Fit** (30%) - Does it follow platform best practices?

Posts scoring below 0.7 receive specific improvement suggestions.

## Advanced Options

### Command-Line Options

- `--tone` - Override the detected tone (professional, casual, technical, etc.)
- `--guidance` - Add specific instructions for generation
- `--count` - Number of posts per platform (default: 5)
- `--platforms` - Comma-separated list of platforms
- `--resume` - Resume from a previous session
- `--reset` - Clear state and start fresh
- `--verbose` - Enable detailed logging

### Supported Platforms

- **twitter** - 280 characters, punchy and engaging
- **linkedin** - Up to 3000 characters, professional tone
- **bluesky** - 280 characters, conversational style
- **mastodon** - 500 characters, community-focused
- **threads** - 500 characters, casual and visual

## The Metacognitive Recipe

This tool implements a "Understand → Create → Refine" approach:

1. **Understand** deeply - Extract the essence of your content
2. **Create** authentically - Generate posts that match your voice
3. **Refine** systematically - Score and improve for maximum impact

## Session Management

Each run creates a timestamped session in `.data/social_posts/`:

```
.data/social_posts/
└── 20240115_143022/
    ├── state.json              # Pipeline state
    ├── article-title_posts.json    # Structured output
    └── article-title_posts.md      # Readable output
```

Sessions can be resumed if interrupted, ensuring you never lose progress.

## Tips for Best Results

1. **Well-Structured Articles** - Use clear headings and paragraphs
2. **Compelling Content** - The tool amplifies what's already there
3. **Platform Strategy** - Choose platforms where your audience is active
4. **Tone Consistency** - Let the tool detect tone unless you have specific needs
5. **Review and Edit** - Use the generated posts as a starting point

## Architecture

The tool follows a modular "brick and stud" architecture:

```
social_posts/
├── content_analyzer/   # Brick 1: Extract tone and themes
├── post_generator/     # Brick 2: Generate platform posts
├── post_reviewer/      # Brick 3: Score and review quality
├── state.py           # Session persistence
└── main.py           # Orchestrator
```

Each module is self-contained with clear interfaces, making it easy to modify or extend.

## Troubleshooting

### No API Key
```
ValueError: OpenAI API key required
```
**Solution:** Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-key-here"
```

### Article Not Found
```
Error: Invalid value for 'ARTICLE_PATH': Path 'article.md' does not exist
```
**Solution:** Provide the correct path to your markdown file.

### Resume Not Working
```
Warning: Could not load state
```
**Solution:** The session may be corrupted. Use `--reset` to start fresh.

## Contributing

This tool is part of the Amplifier scenarios collection. To contribute improvements or report issues, please see the main project repository.

## License

See the main Amplifier project for license information.