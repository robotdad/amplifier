# PowerPoint Template Guide

This guide explains how the PPT Generator uses templates and placeholders for optimal slide generation.

## Quick Start

### Generate a Template
```bash
# Generate default template
make ppt-gen-template

# Generate with custom name
make ppt-gen-template OUTPUT=my_corporate_template.pptx
```

### Customize the Template
1. Open the generated template in PowerPoint
2. Go to **View → Slide Master**
3. Customize:
   - Colors and fonts
   - Company logos
   - Background designs
   - Footer information
4. Save the template

### Use Your Template
```bash
make ppt-gen CONTEXT="doc.md" DIRECTION="Create presentation" TEMPLATE=my_corporate_template.pptx
```

## How the Generator Uses Templates

### Smart Layout Selection

The generator automatically selects the best layout based on content:

| Content Type | Visual | Layout Used | Description |
|-------------|--------|-------------|-------------|
| Title slide | None | Layout 0 | Title Slide with title and subtitle |
| Text only | None | Layout 1 | Title and Content for bullet points |
| Text + Visual | Yes | Layout 3 | Two Content with side-by-side layout |
| Visual focus | Yes | Layout 8 | Picture with Caption (if available) |

### Placeholder System

The generator uses PowerPoint's placeholder system properly:

1. **Title Placeholder (idx=0)**: Always contains the slide title
2. **Content Placeholder (idx=1)**: Contains bullet points or main text
3. **Secondary Content (idx=2)**: Used for visuals in Two Content layout
4. **Picture Placeholders**: Uses `insert_picture()` for proper scaling

### Key Improvements

#### Before (Manual Positioning)
- Manually calculated positions with `Inches()`
- Images could overlap text
- Inconsistent spacing
- Didn't respect template design

#### After (Placeholder System)
- Uses template-defined positions
- Respects placeholder boundaries
- Maintains aspect ratios properly
- Honors template styling

## Template Layouts Explained

### Layout 0: Title Slide
- **Placeholder 0**: Title
- **Placeholder 1**: Subtitle
- **Usage**: Opening slide, section breaks, conclusions

### Layout 1: Title and Content
- **Placeholder 0**: Title
- **Placeholder 1**: Content (bullets/text)
- **Usage**: Text-only slides, key points

### Layout 3: Two Content
- **Placeholder 0**: Title
- **Placeholder 1**: Left content (text)
- **Placeholder 2**: Right content (visual)
- **Usage**: Slides with both text and visuals

### Layout 8: Picture with Caption
- **Placeholder 0**: Title
- **Placeholder 1**: Picture placeholder
- **Placeholder 2**: Caption text
- **Usage**: Visual-focused slides

## Best Practices

### Template Design
1. **Keep standard layouts**: Don't remove layouts 0, 1, 3, or 8
2. **Use picture placeholders**: Add proper picture placeholders for visuals
3. **Consistent styling**: Apply your brand colors to all layouts
4. **Test placeholders**: Verify all placeholders accept content

### Content Guidelines
1. **Clear titles**: Each slide needs a descriptive title
2. **Concise bullets**: Keep bullet points brief
3. **Visual balance**: Let the generator handle text/visual placement
4. **Speaker notes**: Add context in speaker notes, not on slides

## Advanced Customization

### Creating Custom Layouts

If you need additional layouts:

1. In Slide Master view, create new layout
2. Add placeholders:
   - Title at index 0
   - Content at index 1
   - Additional content at index 2+
3. Save template
4. The generator will use appropriate layouts based on content

### Multiple Templates

You can maintain multiple templates for different purposes:

```bash
# Corporate presentations
make ppt-gen-template OUTPUT=corporate.pptx

# Technical documentation
make ppt-gen-template OUTPUT=technical.pptx

# Sales pitches
make ppt-gen-template OUTPUT=sales.pptx
```

## Troubleshooting

### Images Not Appearing
- Ensure Layout 3 (Two Content) exists in template
- Check that picture placeholders are properly defined
- Verify image files were generated successfully

### Text Overlapping
- The generator now uses placeholders to prevent overlap
- If issues persist, check template placeholder positions

### Wrong Layout Selected
- The generator chooses layouts based on content type
- Ensure your template has the standard layouts (0, 1, 3, 8)

### Style Not Applied
- Customize styles in Slide Master, not individual slides
- Apply formatting to placeholder styles in master

## Technical Details

### Placeholder Access
```python
# The generator now uses index-based access
slide.placeholders[0].text = title  # Always title
slide.placeholders[1].text = content  # Main content
slide.placeholders[2]  # Secondary content/visual
```

### Picture Insertion
```python
# Proper way (respects placeholder bounds)
picture_placeholder.insert_picture(image_path)

# Old way (manual positioning, could overlap)
slide.shapes.add_picture(path, left, top, width, height)
```

### Visual Placement Logic
1. Check for picture placeholders first
2. Use placeholder 2 in Two Content layout
3. Fall back to manual positioning only if needed

## Example Workflow

1. **Generate template**:
   ```bash
   make ppt-gen-template OUTPUT=my_template.pptx
   ```

2. **Customize in PowerPoint**:
   - Open template
   - View → Slide Master
   - Apply branding
   - Save

3. **Generate presentation**:
   ```bash
   make ppt-gen CONTEXT="report.md data.txt" \
                DIRECTION="Create executive summary" \
                TEMPLATE=my_template.pptx \
                SLIDES=10
   ```

4. **Result**:
   - Professional presentation
   - Consistent branding
   - Optimal text/visual layout
   - No overlapping content

## Summary

The refactored PPT Generator now:
- ✅ Uses PowerPoint's placeholder system properly
- ✅ Respects template design and boundaries
- ✅ Automatically selects optimal layouts
- ✅ Prevents text/image overlap
- ✅ Maintains visual consistency
- ✅ Supports custom templates seamlessly

This approach ensures your presentations look professional and consistent while leveraging PowerPoint's built-in layout system.