# Slides Agent

Generate complete, visually polished HTML slide decks and export to PPTX.

## Description
Creates professional HTML presentations with modern design, then converts them to PowerPoint (.pptx) format. Supports themes, charts, images, and custom styling.

## Usage
```python
from skills.slides.skill import create_slide_deck, export_to_pptx

# Create presentation
deck = create_slide_deck(title="My Presentation", slides=[
    {"type": "title", "title": "Hello", "subtitle": "World"},
    {"type": "content", "title": "Key Points", "bullets": ["Point 1", "Point 2"]},
    {"type": "chart", "title": "Revenue", "chart_type": "bar", "data": {...}}
])

# Export to PPTX
pptx_path = export_to_pptx(deck, "output.pptx")
```

## Capabilities
- **HTML Slides**: Generate responsive HTML slides with CSS themes
- **Visual Design**: Typography, color palettes, layouts
- **Charts**: Embedded Chart.js or matplotlib charts
- **Images**: Support for background images and logos
- **Export**: Convert HTML to PPTX (via python-pptx)

## Requirements
- python-pptx, Pillow, jinja2

## Best Practices
- Use Google Fonts (Space Grotesk, Inter, etc.)
- Save images to assets/ directory
- Keep slides under 80% vertical space
- Include data sources for charts
