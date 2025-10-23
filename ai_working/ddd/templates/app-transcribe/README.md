# Transcribe: Turn Videos into Searchable Transcripts

**Transform YouTube videos and audio files into searchable, readable transcripts with AI-powered insights.**

## Quick Start

No installation needed - run directly with uvx:

```bash
uvx --from git+https://github.com/robotdad/amplifier-app-transcribe transcribe "https://youtube.com/watch?v=..."
```

On first run, uvx automatically downloads and caches the app from GitHub. Future runs start instantly.

## What It Does

Transcribe is a complete transcription pipeline that:

1. **Downloads** audio from YouTube or processes local files
2. **Transcribes** using OpenAI's Whisper API
3. **Formats** into readable paragraphs with clickable timestamps
4. **Generates insights** - AI summaries and key quotes
5. **Organizes output** - Clean folder structure with indexes

**The result**: Searchable, readable transcripts you can reference forever.

## Features

### Multi-Source Support
- **YouTube videos** - Paste any URL
- **Local audio** - MP3, WAV, M4A, MP4, etc.
- **Batch processing** - Multiple files at once

### Beautiful CLI
- Rich progress bars and status updates
- Clear cost estimates before processing
- Results summary table
- Resume capability if interrupted

### Smart Organization
```
~/transcripts/
├── index.md                    # Auto-generated index
├── video-id-1/
│   ├── audio.mp3              # Preserved audio
│   ├── transcript.md          # Formatted transcript
│   └── insights.md            # AI summary + quotes
└── video-id-2/
    └── ...
```

### AI Insights (Optional)
- **Summaries** - Key points and themes
- **Quotes** - Important moments with timestamps
- **Searchable** - Full-text search across all transcripts

## Usage Examples

### Single YouTube Video

```bash
uvx --from git+https://github.com/robotdad/amplifier-app-transcribe transcribe "https://youtube.com/watch?v=dQw4w9WgXcQ"
```

What happens:
- Downloads audio from YouTube
- Transcribes with Whisper API
- Formats into readable paragraphs
- Generates AI insights
- Saves to `~/transcripts/`

### Local Audio File

```bash
uvx --from git+https://github.com/robotdad/amplifier-app-transcribe transcribe meeting-recording.mp3
```

Works with any audio/video format that ffmpeg supports.

### Batch Processing

```bash
uvx --from git+https://github.com/robotdad/amplifier-app-transcribe transcribe video1.mp4 "https://youtube.com/..." podcast.mp3
```

Processes each file sequentially with progress updates.

### Resume After Interruption

```bash
# If interrupted (Ctrl+C), just run again:
uvx --from git+https://github.com/robotdad/amplifier-app-transcribe transcribe --resume video1.mp4 video2.mp4
```

The app picks up where it left off, skipping already-processed files.

### Custom Output Directory

```bash
uvx --from git+https://github.com/robotdad/amplifier-app-transcribe transcribe "URL" --output-dir ~/my-transcripts
```

### Skip AI Insights

```bash
# Faster, cheaper - just transcription
uvx --from git+https://github.com/robotdad/amplifier-app-transcribe transcribe "URL" --no-enhance
```

## Configuration

### API Keys Required

Set environment variables OR create a `.env` file:

**Option 1: Environment Variables**
```bash
export OPENAI_API_KEY=sk-...      # For transcription (Whisper)
export ANTHROPIC_API_KEY=sk-ant-... # For insights (optional)
```

**Option 2: .env File**

Create `.env` in your working directory:
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

See `.env.example` in the repository for a template.

### Default Settings

- **Output**: `~/transcripts/`
- **AI insights**: Enabled (disable with `--no-enhance`)
- **Caching**: Downloads cached (skip with `--force-download`)

### Cost Information

For current pricing:
- **Whisper API**: Check [OpenAI Pricing](https://openai.com/pricing)
- **Claude API** (for insights): Check [Anthropic Pricing](https://anthropic.com/pricing)

The app shows cost estimates before processing based on current API rates.

## Output Format

### transcript.md

Readable transcript with clickable timestamps:

```markdown
## Transcript

[00:00:00](https://youtube.com/watch?v=...&t=0s)
The speaker begins by introducing the main topic...

[00:02:30](https://youtube.com/watch?v=...&t=150s)
Key point about the methodology used in the research...
```

### insights.md

AI-generated analysis:

```markdown
## Summary

The video discusses [main themes]...

## Key Quotes

> "Important insight here"
> — [00:05:30](link)

> "Another significant point"
> — [00:12:15](link)
```

### index.md

Auto-generated catalog of all transcripts with search capability.

## Troubleshooting

### "yt-dlp is not installed"

This shouldn't happen with uvx. If it does:
```bash
pip install yt-dlp
```

### "ffmpeg not found"

Install ffmpeg for audio processing:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/
```

### "Audio file too large"

Whisper has a 25MB limit. The app auto-compresses, but very large files may need manual compression:

```bash
ffmpeg -i huge-file.wav -b:a 64k -ar 16000 output.mp3
```

### "API key not found"

Set your API keys as environment variables:
```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...  # Optional, for insights
```

## Command Reference

```
usage: uvx --from git+https://github.com/robotdad/amplifier-app-transcribe transcribe [OPTIONS] SOURCES...

arguments:
  SOURCES              YouTube URLs or local file paths

options:
  --resume            Resume from last checkpoint
  --output-dir DIR    Custom output location
  --no-enhance        Skip AI insights (faster, cheaper)
  --force-download    Re-download even if cached
  --help             Show this help
```

## Advanced Usage

### Generate Index Only

```bash
uvx --from git+https://github.com/robotdad/amplifier-app-transcribe transcribe index
```

Regenerates `index.md` from existing transcripts.

### Custom Session Directory

```bash
uvx --from git+https://github.com/robotdad/amplifier-app-transcribe transcribe --session-dir /path/to/session SOURCES...
```

Useful for resuming specific sessions.

## Architecture

Built on amplifier-dev tools:
- **tool-whisper** - OpenAI Whisper integration
- **tool-youtube-dl** - YouTube downloads
- **Rich** - Beautiful CLI output
- **Click** - Command-line interface

The app demonstrates composing amplifier tools into complete workflows.

## Learn More

- **HOW_THIS_APP_WAS_MADE.md** - Creation story and design decisions
- **MIGRATION_NOTES.md** - For users of the original scenarios/transcribe
- [Amplifier Dev](https://github.com/microsoft/amplifier-dev) - The framework behind this app

## Contributing

> [!NOTE]
> This project is not currently accepting external contributions, but we're actively working toward opening this up. We value community input and look forward to collaborating in the future. For now, feel free to fork and experiment!

Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit [Contributor License Agreements](https://cla.opensource.microsoft.com).

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
