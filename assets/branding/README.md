# Amplifier Branding Assets

This folder contains official Amplifier branding assets for use across all Amplifier projects.

## Source

The icon originates from the [microsoft-amplifier](https://github.com/microsoft-amplifier) GitHub user account, which is used to give Amplifier co-authorship credit on commits when the AI assists with code.

- Avatar URL: https://avatars.githubusercontent.com/u/240397093?v=4
- GitHub User ID: 240397093

## Icons

| File | Size | Purpose |
|------|------|---------|
| `amplifier-icon-original.png` | 460x460 | Original source (GitHub avatar) |
| `amplifier-icon-256.png` | 256x256 | Large app icon |
| `amplifier-icon-128.png` | 128x128 | Medium app icon |
| `amplifier-icon-64.png` | 64x64 | Standard app icon |
| `amplifier-icon-44.png` | 44x44 | Small UI icon (2x retina) |
| `amplifier-icon-32.png` | 32x32 | Small app icon |
| `amplifier-icon-22.png` | 22x22 | Small UI icon (1x) |
| `amplifier-icon-16.png` | 16x16 | Tiny icon (favicons, etc.) |
| `Amplifier.icns` | Multi-size | macOS app icon bundle (16-256px) |
| `MenuBarIcon.png` | 18x18 | macOS menu bar template (1x) |
| `MenuBarIcon@2x.png` | 36x36 | macOS menu bar template (2x) |

## Menu Bar Icons

The `MenuBarIcon*.png` files are **template images** (black + alpha). macOS automatically tints them for light/dark mode. Use these for system tray / menu bar icons.

## Full Color Icons

The `amplifier-icon-*.png` files are full color. Use these for:
- App icons
- In-app UI headers
- Documentation
- Marketing materials
- README badges

## Generating New Sizes

From the source icon:

```python
from PIL import Image

img = Image.open("amplifier-icon-original.png")
new_size = img.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
new_size.save(f"amplifier-icon-{SIZE}.png")
```

## Usage in GitHub README

```markdown
![Amplifier](assets/branding/icons/amplifier-icon-64.png)
```

## Co-Author Attribution

When Amplifier assists with commits, use this co-author line:

```
Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>
```
