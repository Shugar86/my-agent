# Docs Agent

Create formatted Word documents (.docx) and PDFs from outlines or raw content.

## Description
Generates professional documents from HTML content with custom styling. Supports A4 format, tables, charts, headers/footers, and multiple export formats (DOCX, PDF, Markdown).

## Usage
```python
from skills.docs.skill import create_document, convert_document

# Create document from HTML
doc = create_document(
    title="Quarterly Report",
    content="<h1>Report</h1><p>Content...</p>",
    format="html"
)

# Convert to DOCX
convert_document(doc, "output.docx", format="docx")

# Convert to PDF
convert_document(doc, "output.pdf", format="pdf")
```

## Capabilities
- **HTML Source**: Full styling control via HTML + CSS
- **DOCX Export**: Professional Word documents
- **PDF Export**: Print-ready PDFs
- **Markdown**: Simple text documents
- **Charts**: Embedded matplotlib charts as SVG
- **Tables**: Structured data tables

## Requirements
- python-docx, reportlab (for PDF), markdown

## Best Practices
- Use semantic HTML tags (h1, h2, p, table, ul)
- Set A4 page sizing in CSS @page
- Use pt units for print-accurate layout
- Avoid flex/grid/positioning in HTML (unsupported by converters)
- Keep sidebar layouts short (end where sidebar content ends)
