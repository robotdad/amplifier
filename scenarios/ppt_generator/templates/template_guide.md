# Preparing PowerPoint Templates for PPT Generator

This guide explains how to create and prepare PowerPoint templates that work seamlessly with the PPT Generator tool.

## What is a Template?

A PowerPoint template is a pre-designed PPTX file that provides:

- **Corporate branding**: Logos, color schemes, fonts
- **Consistent styling**: Standardized text formatting
- **Pre-defined layouts**: Different slide types for various content
- **Master slides**: Base designs that all slides inherit from
- **Theme elements**: Background designs, graphics, watermarks

## Why Use Templates?

Templates ensure your generated presentations:
- Match your organization's brand guidelines
- Have professional, consistent appearance
- Include required legal/compliance elements
- Save time on manual formatting
- Look polished and presentation-ready

## How to Create a Template

### Step 1: Open PowerPoint

Start with a new blank presentation or modify an existing corporate template.

### Step 2: Access Slide Master

1. Go to **View** → **Slide Master**
2. You'll see the master slide hierarchy on the left
3. The top slide is the main master
4. Below are layout masters for different slide types

### Step 3: Design Your Master Slides

#### Main Master Slide
Configure universal elements that appear on all slides:

```
- Set background color/image
- Add company logo (usually top-right or bottom corner)
- Define default fonts:
  - Title: Bold, 44pt
  - Body: Regular, 24pt
  - Captions: Light, 18pt
- Set color scheme
- Add footer elements (page numbers, date, confidentiality)
```

#### Essential Layouts to Define

The PPT Generator expects these standard layouts:

1. **Title Slide**
   - Large title area (centered)
   - Subtitle area
   - Date/author fields (optional)
   - Company branding prominent

2. **Title and Content**
   - Title area at top
   - Content placeholder (bullets or text)
   - Room for 5-7 bullet points
   - Optional image placeholder

3. **Section Header**
   - Large section title (centered)
   - Optional subtitle
   - Minimal design for transitions

4. **Two Content**
   - Title area
   - Two columns for content
   - Good for comparisons

5. **Title Only**
   - Title at top
   - Rest of slide empty
   - For custom content/diagrams

6. **Blank**
   - No placeholders
   - For full-slide images/diagrams

### Step 4: Set Theme Colors

1. In Slide Master view, click **Colors** → **Customize Colors**
2. Define your palette:
   ```
   - Accent 1: Primary brand color
   - Accent 2: Secondary brand color
   - Accent 3: Highlight color
   - Accent 4-6: Supporting colors
   - Hyperlink: Link color
   - Followed Hyperlink: Visited link color
   ```

### Step 5: Configure Fonts

1. Click **Fonts** → **Customize Fonts**
2. Set:
   - Heading font: Your brand's heading font
   - Body font: Your brand's body text font

### Step 6: Add Placeholders

For each layout, add appropriate placeholders:

```python
# Content placeholders the generator expects:
- Title: For slide titles
- Content: For bullet points and text
- Picture: For images (optional)
- Chart: For diagrams (optional)
```

### Step 7: Save as Template

1. Exit Slide Master view
2. Save as a regular PPTX file (not POTX)
3. Name it descriptively: `company_template_2024.pptx`

## Best Practices

### 1. Keep It Simple

- **Don't over-design**: Clean templates work better with generated content
- **Leave space**: Generated content needs room to breathe
- **Avoid animations**: The generator won't preserve complex animations

### 2. Design for Flexibility

```
Good template characteristics:
✓ Clear hierarchy (title → subtitle → body)
✓ Sufficient white space
✓ Readable font sizes (min 18pt for body)
✓ High contrast (dark text on light or vice versa)
✓ Multiple layout options
```

### 3. Test Different Content Types

Before using with the generator, test your template with:
- Long bullet points (do they wrap well?)
- Technical content (is monospace font available?)
- Images (do they scale properly?)
- Tables (are they readable?)

### 4. Include Metadata

Add template information in File → Properties:
```
Title: Corporate Template v2.0
Subject: PPT Generator Compatible
Keywords: template, corporate, 2024
Comments: Optimized for AI generation
```

### 5. Version Control

- Keep template versions: `template_v1.pptx`, `template_v2.pptx`
- Document changes in a changelog
- Test new versions before deploying

## Using Templates with PPT Generator

### Basic Usage

```bash
amplifier ppt-generator \
  --context-dir ./content \
  --topic "Quarterly Review" \
  --template ./templates/corporate_template.pptx
```

### Template Location

Organize your templates:
```
templates/
├── corporate_standard.pptx     # Default corporate
├── corporate_tech.pptx         # Technical presentations
├── corporate_sales.pptx        # Sales decks
├── corporate_training.pptx     # Training materials
└── README.md                    # Template descriptions
```

### Selecting Templates

Choose templates based on content:
- **Technical content** → Use template with code-friendly fonts
- **Executive briefing** → Use minimal, elegant template
- **Training material** → Use template with clear sections
- **Sales pitch** → Use vibrant, engaging template

## Common Issues and Solutions

### Issue: Template Not Applied

**Problem**: Generated presentation doesn't use template styling

**Solutions**:
- Ensure you're using PPTX format (not POTX or PPT)
- Check template file isn't corrupted
- Verify template has required layouts
- Use `--verbose` flag to see template loading

### Issue: Fonts Not Displaying

**Problem**: Custom fonts don't appear in generated presentation

**Solutions**:
- Embed fonts in template: File → Options → Save → Embed fonts
- Use system fonts that are widely available
- Provide fallback font specifications

### Issue: Images Overlapping Text

**Problem**: Generated images cover text content

**Solutions**:
- Adjust placeholder sizes in template
- Leave more space between placeholders
- Set image placeholders to "fit" not "fill"

### Issue: Broken Layouts

**Problem**: Content doesn't fit in template layouts

**Solutions**:
- Make text placeholders larger
- Reduce font sizes slightly
- Increase slide margins
- Test with maximum content

## Advanced Template Features

### Dynamic Placeholders

Create smart placeholders that adapt:

```xml
<!-- In slide XML -->
<p:sp>
  <p:nvSpPr>
    <p:cNvPr id="3" name="Content Placeholder">
    <p:cNvSpPr>
      <a:spLocks noGrp="1"/>
    </p:cNvSpPr>
  </p:nvSpPr>
</p:sp>
```

### Conditional Formatting

Use slide master logic:
- Different headers for different sections
- Alternating color schemes
- Progressive disclosure layouts

### Custom Color Mapping

Map generator intents to your colors:
```python
color_mapping = {
    "primary": "Accent 1",
    "success": "Accent 3",
    "warning": "Accent 4",
    "error": "Accent 5"
}
```

## Template Validation

### Manual Checklist

Before using a template, verify:

- [ ] Company logo appears correctly
- [ ] Fonts are readable at distance
- [ ] Colors meet accessibility standards
- [ ] All required layouts exist
- [ ] Footer information is correct
- [ ] No broken links or missing images
- [ ] Template works on different screens

### Automated Testing

Test your template programmatically:

```python
from pptx import Presentation

def validate_template(template_path):
    """Validate template has required layouts"""
    prs = Presentation(template_path)

    required_layouts = [
        "Title Slide",
        "Title and Content",
        "Section Header",
        "Two Content",
        "Blank"
    ]

    layout_names = [layout.name for layout in prs.slide_layouts]

    for required in required_layouts:
        if required not in layout_names:
            print(f"Missing layout: {required}")
            return False

    print("Template valid!")
    return True

# Run validation
validate_template("corporate_template.pptx")
```

## Default Behavior

When no template is specified, the PPT Generator:

1. Creates a basic presentation with standard layouts
2. Uses system default fonts
3. Applies a simple, professional color scheme
4. Includes minimal formatting
5. Focuses on content over style

This default output is functional but generic. Templates add the professional polish and branding that make presentations stand out.

## Examples and Resources

### Sample Templates

The PPT Generator includes sample templates in `templates/examples/`:
- `minimal.pptx` - Clean, minimalist design
- `technical.pptx` - Code-friendly with monospace fonts
- `colorful.pptx` - Vibrant for creative content

### External Resources

- [Microsoft Template Guide](https://support.microsoft.com/office/templates)
- [PowerPoint Design Ideas](https://support.microsoft.com/designer)
- [Accessibility Guidelines](https://support.microsoft.com/accessibility)

### Community Templates

Share and find templates:
- GitHub: `amplifier-templates` repository
- Corporate: Check your organization's brand portal
- Design: Sites like SlidesCarnival, SlidesGo

## Troubleshooting Tips

### Debug Template Loading

Run with verbose output:
```bash
amplifier ppt-generator --verbose --template my_template.pptx ...
```

Look for:
- "Loading template from..."
- "Applied template successfully"
- "Using layout: [layout_name]"

### Inspect Generated PPTX

1. Rename `.pptx` to `.zip`
2. Extract and examine:
   - `ppt/slides/` - Individual slides
   - `ppt/slideLayouts/` - Applied layouts
   - `ppt/theme/` - Theme information

### Reset to Defaults

If templates cause issues:
```bash
# Generate without template to test
amplifier ppt-generator --context-dir ./content --topic "Test"

# Compare with template version
amplifier ppt-generator --context-dir ./content --topic "Test" --template template.pptx
```

## Conclusion

Well-designed templates transform AI-generated presentations from functional to professional. Invest time in creating good templates - they're reusable assets that ensure every generated presentation meets your standards.

Remember: The PPT Generator handles content creation; templates handle visual excellence. Together, they produce presentations that impress.