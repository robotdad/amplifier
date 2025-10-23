# Migration Notes

**For users of `scenarios/transcribe` from amplifier.transcripts2**

## What Changed

The transcribe functionality has been restructured as:

### 1. Reusable Tools (amplifier-dev)
- **`tool-whisper`** - OpenAI Whisper transcription (available to all amplifier users)
- **`tool-youtube-dl`** - YouTube download + metadata (available to all amplifier users)

### 2. Standalone Application (this repo)
- **`amplifier-app-transcribe`** - Complete transcription app with CLI and web interface

## If You Were Using scenarios/transcribe

### Old Way (scenarios/transcribe)

```bash
# Clone repo
git clone https://github.com/robotdad/amplifier.transcripts2
cd amplifier.transcripts2

# Install dependencies
make install

# Run transcription
python -m scenarios.transcribe "https://youtube.com/watch?v=..."
```

### New Way (amplifier-app-transcribe)

```bash
# No clone needed - run directly via uvx
uvx --from git+https://github.com/robotdad/amplifier-app-transcribe transcribe "https://youtube.com/watch?v=..."
```

### What's Better

**Easier to use**:
- No repository cloning
- No dependency installation
- No virtual environment setup
- Just run with uvx

**Richer experience**:
- Beautiful Rich CLI with progress bars
- Clear status updates and results tables
- Same resume capability
- Same output organization

**More flexible**:
- Use tools in your own amplifier workflows
- Compose with other amplifier tools
- Build custom applications using the tools

## Using the Tools in Amplifier Workflows

The extracted tools are now available for any amplifier session:

```yaml
# ~/.amplifier/profiles/transcribe.md
---
profile:
  name: transcribe
  extends: base

tools:
  - module: tool-whisper
    source: git+https://github.com/microsoft/amplifier-dev@main#subdirectory=amplifier-module-tool-whisper
  - module: tool-youtube-dl
    source: git+https://github.com/microsoft/amplifier-dev@main#subdirectory=amplifier-module-tool-youtube-dl
---
```

Then use in conversation:
```bash
amplifier run --profile transcribe
> "Download and transcribe https://youtube.com/watch?v=..."
```

The AI will automatically use both tools to complete the task.

## Feature Parity

All features from `scenarios/transcribe` are preserved:

| Feature | scenarios/transcribe | amplifier-app-transcribe |
|---------|---------------------|--------------------------|
| YouTube download | ✅ | ✅ |
| Local file support | ✅ | ✅ |
| Whisper transcription | ✅ | ✅ |
| Timestamp formatting | ✅ | ✅ |
| AI insights (summaries + quotes) | ✅ | ✅ |
| Resume capability | ✅ | ✅ |
| Batch processing | ✅ | ✅ |
| Cost estimation | ✅ | ✅ |
| Audio caching | ✅ | ✅ |
| Index generation | ✅ | ✅ |
| **Rich CLI progress** | ❌ | ✅ (new) |
| **uvx distribution** | ❌ | ✅ (new) |

## Output Compatibility

Output format and location remain the same:

```
~/transcripts/
├── index.md
├── video-id/
│   ├── audio.mp3
│   ├── transcript.md
│   └── insights.md
```

Existing transcripts work with the new app. The index command still works:

```bash
uvx --from git+https://github.com/robotdad/amplifier-app-transcribe transcribe index
```

## API Keys

Same environment variables:

```bash
export OPENAI_API_KEY=sk-...      # For transcription
export ANTHROPIC_API_KEY=sk-ant-... # For insights (optional)
```

## Command Changes

### Basic Usage

```bash
# Old
python -m scenarios.transcribe "URL"

# New
uvx --from git+https://github.com/robotdad/amplifier-app-transcribe transcribe "URL"
```

### Options

Most options remain the same:

| Option | Old | New | Notes |
|--------|-----|-----|-------|
| Resume | `--resume` | `--resume` | Same |
| Output dir | `--output-dir DIR` | `--output-dir DIR` | Same |
| Skip insights | `--no-enhance` | `--no-enhance` | Same |
| Force download | `--force-download` | `--force-download` | Same |
| Session dir | `--session-dir DIR` | `--session-dir DIR` | Same |

## Dependencies

### External Dependencies

Same external dependencies required:

```bash
# ffmpeg (required)
brew install ffmpeg  # macOS
sudo apt-get install ffmpeg  # Ubuntu
```

### Python Dependencies

Handled automatically by uvx - no manual installation needed.

## Migration Checklist

If migrating from scenarios/transcribe:

- [ ] Existing transcripts: No action needed (compatible)
- [ ] API keys: Same environment variables
- [ ] ffmpeg: Already installed (no change)
- [ ] Workflow: Use uvx instead of python -m
- [ ] Custom scripts: Update to call uvx command

## Questions?

- **Usage help**: See [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/microsoft/amplifier-dev/issues)
- **Tool documentation**: See tool-whisper and tool-youtube-dl READMEs
