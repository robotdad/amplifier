---
profile:
  name: youtube-downloader
  extends: base

tools:
  - module: tool-youtube-dl
    source: git+https://github.com/robotdad/amplifier-module-tool-youtube-dl@main
    config:
      output_dir: ~/downloads
      audio_only: true
---

# YouTube Downloader Profile

Enables YouTube audio/video downloading in amplifier sessions.

## Quick Start

1. Install ffmpeg (required):
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   ```

2. Activate this profile:
   ```bash
   amplifier run --profile youtube-downloader
   ```

3. Download in conversation:
   ```
   > Download audio from https://youtube.com/watch?v=dQw4w9WgXcQ
   ```

## What It Does

This profile adds the `tool-youtube-dl` module to your amplifier session, enabling the AI to:

- Download audio from YouTube videos
- Extract metadata (title, duration, uploader)
- Cache downloads to avoid re-downloading
- Convert to MP3 format automatically

## Configuration

The tool is configured to:
- Save downloads to `~/downloads/`
- Extract audio only (not full video)
- Cache downloaded files

### Custom Configuration

Copy this profile to `~/.amplifier/profiles/my-youtube.md` and adjust settings:

```yaml
tools:
  - module: tool-youtube-dl
    source: git+https://github.com/robotdad/amplifier-module-tool-youtube-dl@main
    config:
      output_dir: ~/my-videos
      audio_only: false  # Download full video
```

## Example Workflows

### Download Single Video Audio

```
> Download audio from https://youtube.com/watch?v=...
```

The AI will:
1. Extract video metadata
2. Download best quality audio
3. Convert to MP3
4. Save to ~/downloads/

### Download to Custom Location

```
> Download audio from https://youtube.com/watch?v=... and save to ~/podcasts/
```

The AI can override the default output directory per request.

### Extract Metadata Only

```
> Get information about https://youtube.com/watch?v=...
```

The AI can extract metadata without downloading the full content.

## Combining with Whisper

Use both tools together for transcription workflows:

```yaml
---
profile:
  name: video-transcription
  extends: base

tools:
  - module: tool-youtube-dl
    source: git+https://github.com/robotdad/amplifier-module-tool-youtube-dl@main
  - module: tool-whisper
    source: git+https://github.com/robotdad/amplifier-module-tool-whisper@main
---
```

Then:
```
> Download and transcribe https://youtube.com/watch?v=...
```

The AI will automatically use both tools in sequence.

## Caching Behavior

By default, the tool caches downloads:
- First download: Fetches from YouTube
- Subsequent requests: Uses cached file (instant)

This saves bandwidth and time for repeated access to the same content.

## Troubleshooting

### "yt-dlp is not installed"

The dependency should be installed automatically. If not:
```bash
cd amplifier-module-tool-youtube-dl
uv add yt-dlp
```

### "ffmpeg not found"

Install ffmpeg for your platform. It's required for audio extraction:
- macOS: `brew install ffmpeg`
- Ubuntu: `sudo apt-get install ffmpeg`
- Windows: Download from ffmpeg.org

### "Failed to download URL"

Common issues:
- Video is private or removed
- Age-restricted (may require authentication)
- Geographic restrictions
- Network issues

Try the URL in a regular browser first to verify it's accessible.

### "Could not find downloaded audio file"

This means ffmpeg isn't working properly. Verify:
```bash
ffmpeg -version
```

If not found, reinstall ffmpeg.

## Learn More

- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [Amplifier Profiles Guide](https://github.com/microsoft/amplifier-dev/docs/profiles.md)
- [Tool Development](https://github.com/microsoft/amplifier-dev/docs/tool-development.md)
