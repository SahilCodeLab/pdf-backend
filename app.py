"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   PREMIUM ACADEMIC PDF GENERATOR v2.1                        ║
║                   🚀 Optimized with Fast Manual Parser 🚀                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

Fast, reliable PDF generation with intelligent manual parsing.
No API dependencies - works offline!
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from weasyprint import HTML, CSS
import os
import io
import json
import time
import re
from datetime import datetime
import markdown
from dotenv import load_dotenv
import logging
import traceback

load_dotenv()

# ══════════════════════════════════════════════════════════════════════════════
# LOGGING CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] ═ %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('premium_pdf_generator.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ══════════════════════════════════════════════════════════════════════════════
# GEMINI AI CLIENT - OPTIONAL (DISABLED BY DEFAULT FOR SPEED)
# ══════════════════════════════════════════════════════════════════════════════
GEMINI_AVAILABLE = False
USE_GEMINI = os.getenv("USE_GEMINI", "false").lower() == "true"

try:
    if USE_GEMINI:
        from google import genai
        from google.genai import types
        from google.genai.errors import APIError
        
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            logger.warning("⚠️ GEMINI_API_KEY not found")
        else:
            client = genai.Client(api_key=GEMINI_API_KEY)
            GEMINI_AVAILABLE = True
            logger.info("✅ Gemini AI enabled and ready")
    else:
        logger.info("🚀 Gemini AI disabled - Using fast manual parser")
except ImportError:
    logger.info("🚀 Google Generative AI not installed - Using manual parser")
except Exception as e:
    logger.info(f"🚀 Gemini unavailable - Using manual parser: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# PREMIUM DESIGN THEMES
# ══════════════════════════════════════════════════════════════════════════════
class PremiumTheme:
    """Premium theme configurations for different document styles"""
    
    CLASSIC_ACADEMIC = {
        "name": "Classic Academic",
        "primary": "#1a365d",
        "secondary": "#2c5282",
        "accent": "#c53030",
        "gold": "#b7791f",
        "text": "#1a202c",
        "heading": "#0d1b2a",
        "subheading": "#2d3748",
        "border": "#a0aec0",
        "footer_text": "#718096",
        "code_bg": "#f7fafc",
        "quote_bg": "#edf2f7",
        "highlight_bg": "#fefcbf",
        "table_alt": "#f7fafc",
        "font_family": "Georgia, 'Times New Roman', serif",
        "heading_font": "Georgia, serif",
        "code_font": "'Courier New', Courier, monospace",
    }
    
    MODERN_CORPORATE = {
        "name": "Modern Corporate",
        "primary": "#1e3a5f",
        "secondary": "#2563eb",
        "accent": "#059669",
        "gold": "#d97706",
        "text": "#111827",
        "heading": "#0f172a",
        "subheading": "#334155",
        "border": "#e2e8f0",
        "footer_text": "#64748b",
        "code_bg": "#f1f5f9",
        "quote_bg": "#f8fafc",
        "highlight_bg": "#fef3c7",
        "table_alt": "#f8fafc",
        "font_family": "'Helvetica Neue', Helvetica, Arial, sans-serif",
        "heading_font": "'Helvetica Neue', Arial, sans-serif",
        "code_font": "'Courier New', monospace",
    }
    
    ELEGANT_LEGAL = {
        "name": "Elegant Legal",
        "primary": "#1c1917",
        "secondary": "#44403c",
        "accent": "#7c2d12",
        "gold": "#a16207",
        "text": "#292524",
        "heading": "#1c1917",
        "subheading": "#57534e",
        "border": "#d6d3d1",
        "footer_text": "#78716c",
        "code_bg": "#fafaf9",
        "quote_bg": "#f5f5f4",
        "highlight_bg": "#fef9c3",
        "table_alt": "#fafaf9",
        "font_family": "'Book Antiqua', 'Palatino Linotype', Georgia, serif",
        "heading_font": "'Book Antiqua', Palatino, serif",
        "code_font": "'Courier New', Courier, monospace",
    }
    
    EXECUTIVE_LUXURY = {
        "name": "Executive Luxury",
        "primary": "#18181b",
        "secondary": "#3f3f46",
        "accent": "#b45309",
        "gold": "#ca8a04",
        "text": "#27272a",
        "heading": "#09090b",
        "subheading": "#3f3f46",
        "border": "#71717a",
        "footer_text": "#a1a1aa",
        "code_bg": "#fafafa",
        "quote_bg": "#f4f4f5",
        "highlight_bg": "#fef08a",
        "table_alt": "#fafafa",
        "font_family": "Didot, 'Bodoni MT', 'Times New Roman', serif",
        "heading_font": "Didot, Georgia, serif",
        "code_font": "'Courier New', monospace",
    }
    
    SCIENTIFIC_JOURNAL = {
        "name": "Scientific Journal",
        "primary": "#0c4a6e",
        "secondary": "#0369a1",
        "accent": "#be185d",
        "gold": "#ca8a04",
        "text": "#1e293b",
        "heading": "#0f172a",
        "subheading": "#334155",
        "border": "#94a3b8",
        "footer_text": "#64748b",
        "code_bg": "#f1f5f9",
        "quote_bg": "#e0f2fe",
        "highlight_bg": "#dcfce7",
        "table_alt": "#f8fafc",
        "font_family": "'Times New Roman', Georgia, serif",
        "heading_font": "'Times New Roman', Georgia, serif",
        "code_font": "'Courier New', monospace",
    }
    
    @classmethod
    def get_theme(cls, theme_name):
        themes = {
            'classic': cls.CLASSIC_ACADEMIC,
            'corporate': cls.MODERN_CORPORATE,
            'legal': cls.ELEGANT_LEGAL,
            'luxury': cls.EXECUTIVE_LUXURY,
            'scientific': cls.SCIENTIFIC_JOURNAL,
            'default': cls.CLASSIC_ACADEMIC
        }
        return themes.get(theme_name.lower(), cls.CLASSIC_ACADEMIC)


# ══════════════════════════════════════════════════════════════════════════════
# ⚡ FAST INTELLIGENT TEXT PARSER (OPTIMIZED FOR SPEED)
# ══════════════════════════════════════════════════════════════════════════════
class FastTextParser:
    """Lightning-fast intelligent text parser - no API calls needed!"""
    
    def __init__(self, theme):
        self.theme = theme
    
    def parse_inline_styles(self, text):
        """Convert markdown-style formatting to HTML"""
        # Bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
        # Italic
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
        # Code
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        return text
    
    def detect_document_type(self, text):
        """Detect document type for better parsing"""
        text_lower = text.lower()
        scores = {
            'academic_paper': sum(1 for kw in ['abstract', 'introduction', 'methodology', 'references'] if kw in text_lower),
            'business_report': sum(1 for kw in ['executive summary', 'revenue', 'quarterly'] if kw in text_lower),
            'technical': sum(1 for kw in ['syntax', 'parameter', 'configuration', 'api'] if kw in text_lower),
            'legal': sum(1 for kw in ['whereas', 'hereby', 'clause'] if kw in text_lower),
        }
        return max(scores, key=scores.get) if max(scores.values()) > 0 else 'general'
    
    def parse(self, text):
        """Ultra-fast document parsing - no external calls"""
        lines = text.strip().split('\n')
        sections = []
        title = ""
        metadata = {'author': '', 'date': '', 'version': '', 'institution': ''}
        
        current_list = None
        list_type = None
        
        for i, line in enumerate(lines):
            original_line = line
            line = line.strip()
            
            if not line:
                if current_list:
                    sections.append({"type": list_type, "items": current_list})
                    current_list = None
                    list_type = None
                continue
            
            line_parsed = self.parse_inline_styles(line)
            
            # Title detection
            if not title and len(line) < 120:
                if line.startswith('# ') or (line.isupper() and len(line.split()) <= 15):
                    title = line.replace('#', '').strip()
                    continue
            
            # Metadata
            for pattern, key in [
                (r'(?:Author|By)[:\s]+(.+)', 'author'),
                (r'(?:Date|Published)[:\s]+(.+)', 'date'),
                (r'(?:Version|Rev)[:\s]+(.+)', 'version'),
            ]:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    metadata[key] = match.group(1).strip()
                    break
            
            # Headings
            if line.startswith('#'):
                if current_list:
                    sections.append({"type": list_type, "items": current_list})
                    current_list = None
                    list_type = None
                level = len(re.match(r'^(#+)\s', line).group(1)) if line.startswith('#') else 1
                clean = re.sub(r'^#+\s*', '', line).strip()
                sections.append({"type": "heading", "text": self.parse_inline_styles(clean), "level": level})
                continue
            
            # Questions
            if line.endswith('?') or re.match(r'^(What|How|Why|When|Where|Who|Which|Explain)', line, re.I):
                sections.append({"type": "question", "text": line_parsed})
                continue
            
            # Answers
            if re.match(r'^(Answer:|Solution:|=>|→)', line):
                clean = re.sub(r'^(Answer:|Solution:|=>|→)\s*', '', line)
                sections.append({"type": "answer", "text": self.parse_inline_styles(clean)})
                continue
            
            # Blockquotes
            if line.startswith(('>', 'Note:', 'Important:', '⚠️', '📌', '💡')):
                clean = re.sub(r'^[>\s]*(Note:|Important:|⚠️|📌|💡)\s*', '', line)
                sections.append({"type": "blockquote", "text": self.parse_inline_styles(clean)})
                continue
            
            # Tables
            if '|' in line and line.count('|') >= 2:
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if not all(re.match(r'^[-:]+$', c) for c in cells if c):
                    if sections and sections[-1].get('type') == 'table':
                        sections[-1]['rows'].append(cells)
                    else:
                        sections.append({"type": "table", "headers": cells, "rows": []})
                continue
            
            # Bullet lists
            if re.match(r'^[\-\*\•\→➤✦]\s+', line):
                if not current_list or list_type != "bullet_list":
                    if current_list:
                        sections.append({"type": list_type, "items": current_list})
                    current_list = []
                    list_type = "bullet_list"
                match = re.match(r'^[\-\*\•\→➤✦]\s+(.+)', line)
                current_list.append(self.parse_inline_styles(match.group(1)))
                continue
            
            # Numbered lists
            numbered_match = re.match(r'^(\d+)[.)]\s+(.+)', line)
            if numbered_match:
                if not current_list or list_type != "numbered_list":
                    if current_list:
                        sections.append({"type": list_type, "items": current_list})
                    current_list = []
                    list_type = "numbered_list"
                current_list.append(self.parse_inline_styles(numbered_match.group(2)))
                continue
            
            # Roman numerals
            roman_match = re.match(r'^([IVX]+)[.)]\s+(.+)', line)
            if roman_match:
                if not current_list or list_type != "numbered_list":
                    if current_list:
                        sections.append({"type": list_type, "items": current_list})
                    current_list = []
                    list_type = "numbered_list"
                current_list.append(self.parse_inline_styles(roman_match.group(2)))
                continue
            
            # Paragraphs
            if sections and sections[-1]['type'] == 'paragraph' and len(sections[-1]['text'].split()) < 60:
                sections[-1]['text'] += ' ' + line_parsed
            else:
                if current_list:
                    sections.append({"type": list_type, "items": current_list})
                    current_list = None
                    list_type = None
                sections.append({"type": "paragraph", "text": line_parsed})
        
        if current_list:
            sections.append({"type": list_type, "items": current_list})
        
        return {
            "title": title or "Premium Document",
            "sections": sections,
            "metadata": metadata,
            "doc_type": self.detect_document_type(text)
        }


# ══════════════════════════════════════════════════════════════════════════════
# PREMIUM HTML BUILDER - CLEAN CSS (NO WARNINGS)
# ══════════════════════════════════════════════════════════════════════════════
class PremiumHTMLBuilder:
    """Build premium-quality HTML with WeasyPrint-compatible CSS"""
    
    def __init__(self, theme, options=None):
        self.theme = theme
        self.options = options or {}
        self.has_cover = self.options.get('cover_page', True)
        self.has_toc = self.options.get('table_of_contents', True)
        self.quality = self.options.get('quality', 'high')
    
    def build_css(self):
        """Generate WeasyPrint-compatible CSS"""
        theme = self.theme
        
        sizes = {
            'standard': {'base': '11pt', 'h1': '16pt', 'h2': '14pt'},
            'high': {'base': '12pt', 'h1': '18pt', 'h2': '15pt'},
            'premium': {'base': '13pt', 'h1': '20pt', 'h2': '17pt'}
        }
        s = sizes.get(self.quality, sizes['high'])
        
        return f"""
@page {{
    size: A4;
    margin: 2.5cm 2cm 2.5cm 2.5cm;
}}

@page :first {{
    margin: 2cm;
}}

body {{
    font-family: {theme['font_family']};
    font-size: {s['base']};
    color: {theme['text']};
    line-height: 1.7;
}}

/* Cover Page */
.cover-page {{
    text-align: center;
    padding-top: 100px;
    page-break-after: always;
}}

.cover-badge {{
    display: inline-block;
    background-color: {theme['primary']};
    color: white;
    padding: 5px 18px;
    font-size: 9pt;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 25px;
}}

.cover-title {{
    font-family: {theme['heading_font']};
    font-size: 26pt;
    font-weight: bold;
    color: {theme['heading']};
    margin-bottom: 12px;
}}

.cover-subtitle {{
    font-size: 13pt;
    color: {theme['subheading']};
    margin-bottom: 40px;
    font-style: italic;
}}

.cover-divider {{
    width: 100px;
    height: 2px;
    background-color: {theme['accent']};
    margin: 30px auto;
}}

.cover-meta {{
    margin-top: 50px;
    font-size: 10pt;
    color: {theme['footer_text']};
}}

.cover-meta p {{
    margin: 4px 0;
    text-indent: 0;
    text-align: center;
}}

/* TOC Page */
.toc-page {{
    page-break-after: always;
}}

.toc-header {{
    font-family: {theme['heading_font']};
    font-size: 20pt;
    color: {theme['heading']};
    text-align: center;
    margin-bottom: 40px;
    padding-bottom: 15px;
    border-bottom: 2px solid {theme['heading']};
}}

.toc-list {{
    list-style: none;
    padding: 0;
}}

.toc-item {{
    display: flex;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px dotted {theme['border']};
    font-size: 11pt;
}}

.toc-item-title {{
    color: {theme['text']};
}}

.toc-section {{
    padding-left: 25px;
    font-size: 10pt;
    color: {theme['subheading']};
}}

/* Main Header */
.doc-header {{
    text-align: center;
    font-size: 13pt;
    font-weight: bold;
    margin-bottom: 40px;
    letter-spacing: 2px;
    color: {theme['heading']};
    border-bottom: 2px double {theme['heading']};
    padding-bottom: 12px;
    text-transform: uppercase;
}}

/* Headings */
h1 {{
    font-family: {theme['heading_font']};
    font-size: {s['h1']};
    font-weight: bold;
    color: {theme['heading']};
    margin-top: 35px;
    margin-bottom: 18px;
    page-break-after: avoid;
    border-left: 4px solid {theme['accent']};
    padding-left: 12px;
}}

h2 {{
    font-family: {theme['heading_font']};
    font-size: {s['h2']};
    font-weight: bold;
    color: {theme['subheading']};
    margin-top: 28px;
    margin-bottom: 14px;
    page-break-after: avoid;
}}

/* Paragraphs */
p {{
    margin-top: 0;
    margin-bottom: 14px;
    text-align: justify;
    text-indent: 2em;
}}

p:first-of-type {{
    text-indent: 0;
}}

strong {{
    color: {theme['heading']};
    font-weight: bold;
}}

em {{
    font-style: italic;
}}

code {{
    font-family: {theme['code_font']};
    background-color: {theme['code_bg']};
    padding: 1px 5px;
    font-size: 0.9em;
    color: {theme['accent']};
}}

/* Lists */
ul, ol {{
    margin: 12px 0 20px 28px;
    padding: 0;
}}

ul li {{
    list-style-type: disc;
    margin-bottom: 8px;
}}

ol li {{
    list-style-type: decimal;
    margin-bottom: 8px;
}}

/* Q&A */
.question {{
    font-weight: bold;
    color: {theme['heading']};
    margin-top: 25px;
    margin-bottom: 10px;
    padding: 12px 18px;
    background-color: {theme['quote_bg']};
    border-left: 4px solid {theme['accent']};
    page-break-after: avoid;
}}

.answer {{
    margin-bottom: 16px;
    padding-left: 18px;
    border-left: 2px solid {theme['border']};
}}

/* Blockquotes */
blockquote {{
    margin: 20px 0;
    padding: 15px 20px;
    background-color: {theme['quote_bg']};
    border-left: 4px solid {theme['accent']};
    font-style: italic;
}}

blockquote p {{
    margin-bottom: 0;
    text-indent: 0;
    text-align: left;
}}

/* Code Blocks */
pre {{
    font-family: {theme['code_font']};
    background-color: {theme['code_bg']};
    padding: 15px;
    border: 1px solid {theme['border']};
    border-left: 4px solid {theme['secondary']};
    font-size: 10pt;
    margin: 20px 0;
    page-break-inside: avoid;
}}

pre code {{
    background: none;
    padding: 0;
}}

.code-language {{
    display: inline-block;
    background-color: {theme['secondary']};
    color: white;
    padding: 2px 8px;
    font-size: 8pt;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}}

/* Tables */
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 25px 0;
    font-size: 10pt;
    page-break-inside: avoid;
}}

th {{
    background-color: {theme['primary']};
    color: white;
    font-weight: bold;
    padding: 12px 14px;
    text-align: left;
    border: 1px solid {theme['secondary']};
}}

td {{
    border: 1px solid {theme['border']};
    padding: 10px 12px;
    text-align: left;
}}

tr:nth-child(even) {{
    background-color: {theme['table_alt']};
}}

.table-caption {{
    font-size: 9pt;
    color: {theme['footer_text']};
    text-align: center;
    margin-top: -18px;
    margin-bottom: 18px;
    font-style: italic;
}}

/* Dividers */
.divider {{
    border: none;
    border-top: 2px solid {theme['border']};
    margin: 35px 0;
}}

/* Key Points */
.key-point {{
    background-color: {theme['highlight_bg']};
    border-left: 3px solid {theme['gold']};
    padding: 12px 18px;
    margin: 20px 0;
    font-weight: bold;
}}
"""
    
    def build_cover_page(self, doc):
        """Generate premium cover page"""
        metadata = doc.get('metadata', {})
        
        meta_html = ""
        if metadata.get('author'):
            meta_html += f'<p><strong>Author:</strong> {metadata["author"]}</p>'
        if metadata.get('date'):
            meta_html += f'<p><strong>Date:</strong> {metadata["date"]}</p>'
        else:
            meta_html += f'<p><strong>Date:</strong> {datetime.now().strftime("%B %d, %Y")}</p>'
        if metadata.get('version'):
            meta_html += f'<p><strong>Version:</strong> {metadata["version"]}</p>'
        if metadata.get('institution'):
            meta_html += f'<p><strong>Organization:</strong> {metadata["institution"]}</p>'
        
        return f"""
<div class="cover-page">
    <div class="cover-badge">Premium Edition</div>
    <div class="cover-title">{doc.get('title', 'DOCUMENT')}</div>
    <div class="cover-subtitle">{doc.get('subtitle', '')}</div>
    <div class="cover-divider"></div>
    <div class="cover-meta">{meta_html}</div>
</div>
"""
    
    def build_toc(self, doc):
        """Generate table of contents"""
        sections = doc.get('sections', [])
        headings = [s for s in sections if s.get('type') in ['heading', 'subheading']]
        
        if not headings:
            return ""
        
        html = '<div class="toc-page"><div class="toc-header">Table of Contents</div><ol class="toc-list">'
        
        for section in headings:
            text = section.get('text', '')
            level = section.get('level', 1)
            cls = 'toc-section' if level > 1 else 'toc-item'
            html += f'<li class="{cls}"><span class="toc-item-title">{text}</span></li>'
        
        html += '</ol></div>'
        return html
    
    def build_element(self, section):
        """Build HTML for a section"""
        stype = section.get('type', 'paragraph')
        text = section.get('text', '')
        items = section.get('items', [])
        
        if stype == 'heading':
            level = section.get('level', 1)
            tag = 'h1' if level == 1 else 'h2'
            return f'<{tag}>{text}</{tag}>'
        
        elif stype == 'subheading':
            return f'<h2>{text}</h2>'
        
        elif stype == 'paragraph':
            return f'<p>{text}</p>'
        
        elif stype == 'question':
            return f'<div class="question">{text}</div>'
        
        elif stype == 'answer':
            return f'<div class="answer"><p>{text}</p></div>'
        
        elif stype == 'blockquote':
            return f'<blockquote><p>{text}</p></blockquote>'
        
        elif stype == 'code_block':
            lang = section.get('language', 'code')
            return f'<div class="code-language">{lang}</div><pre><code>{text}</code></pre>'
        
        elif stype == 'bullet_list':
            html = '<ul>'
            for item in items:
                html += f'<li>{item}</li>'
            html += '</ul>'
            return html
        
        elif stype == 'numbered_list':
            html = '<ol>'
            for item in items:
                html += f'<li>{item}</li>'
            html += '</ol>'
            return html
        
        elif stype == 'table':
            headers = section.get('headers', [])
            rows = section.get('rows', [])
            
            html = '<table><thead><tr>'
            for header in headers:
                html += f'<th>{header}</th>'
            html += '</tr></thead><tbody>'
            
            for row in rows:
                html += '<tr>'
                for cell in row:
                    html += f'<td>{cell}</td>'
                html += '</tr>'
            
            html += '</tbody></table>'
            
            if section.get('caption'):
                html += f'<p class="table-caption">{section["caption"]}</p>'
            
            return html
        
        elif stype == 'divider':
            return '<hr class="divider">'
        
        else:
            return f'<p>{text}</p>'
    
    def build(self, doc):
        """Build complete HTML document"""
        title = doc.get('title', 'PREMIUM DOCUMENT').upper()
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
    {self.build_css()}
    </style>
</head>
<body>
"""
        
        if self.has_cover:
            html += self.build_cover_page(doc)
        
        if self.has_toc:
            html += self.build_toc(doc)
        
        html += f'<div class="doc-header">{title}</div>'
        
        for section in doc.get('sections', []):
            html += self.build_element(section)
        
        html += """
</body>
</html>"""
        
        return html


# ══════════════════════════════════════════════════════════════════════════════
# PDF GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
class PremiumPDFGenerator:
    """Premium PDF generation engine"""
    
    def __init__(self, theme_name='classic', options=None):
        self.theme = PremiumTheme.get_theme(theme_name)
        self.options = options or {}
        self.parser = FastTextParser(self.theme)
        self.builder = PremiumHTMLBuilder(self.theme, self.options)
    
    def generate(self, text, output_path=None):
        """Generate premium PDF"""
        logger.info(f"📄 Generating PDF - Theme: {self.theme['name']}")
        
        # Parse document
        doc = self.parser.parse(text)
        sections_count = len(doc.get('sections', []))
        logger.info(f"✅ Parsed {sections_count} sections")
        
        # Build HTML
        html_content = self.builder.build(doc)
        
        # Generate PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
            logger.info(f"💾 PDF saved: {output_path}")
        
        return pdf_bytes
    
    def generate_to_bytes(self, text):
        """Generate PDF and return bytes"""
        pdf_bytes = self.generate(text)
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_file.seek(0)
        return pdf_file


# ══════════════════════════════════════════════════════════════════════════════
# FLASK API ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/", methods=["GET"])
def index():
    """Health check"""
    return jsonify({
        "status": "✅ Premium PDF Generator v2.1 Running",
        "speed": "⚡ Fast Manual Parser (No API calls)",
        "gemini": "Enabled" if GEMINI_AVAILABLE else "Disabled",
        "themes": ["classic", "corporate", "legal", "luxury", "scientific"],
        "endpoints": {
            "POST /generate_pdf": "Generate PDF",
            "POST /generate_premium_pdf": "Generate with options",
            "GET /themes": "List themes"
        }
    })

@app.route("/themes", methods=["GET"])
def list_themes():
    """List available themes"""
    return jsonify({
        "themes": {
            "classic": "Classic Academic - Traditional scholarly style",
            "corporate": "Modern Corporate - Professional business",
            "legal": "Elegant Legal - Formal legal documents",
            "luxury": "Executive Luxury - Premium executive",
            "scientific": "Scientific Journal - Research papers"
        }
    })

@app.route("/generate_pdf", methods=["POST"])
def generate_pdf():
    """Generate premium PDF"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
        
        bulk_text = data.get("bulk_text", "")
        if not bulk_text.strip():
            return jsonify({"error": "bulk_text is missing"}), 400
        
        filename = data.get("filename", "document")
        theme_name = data.get("theme", "classic")
        
        logger.info(f"📝 Processing: {filename}")
        
        generator = PremiumPDFGenerator(theme_name)
        pdf_bytes = generator.generate(bulk_text)
        
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_file.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return send_file(
            pdf_file,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{filename}_{timestamp}.pdf"
        )
        
    except Exception as e:
        logger.error(f"❌ Error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.route("/generate_premium_pdf", methods=["POST"])
def generate_premium_pdf():
    """Generate PDF with full options"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
        
        bulk_text = data.get("bulk_text", "")
        if not bulk_text.strip():
            return jsonify({"error": "bulk_text is missing"}), 400
        
        premium_options = {
            'theme': data.get('theme', 'classic'),
            'cover_page': data.get('cover_page', True),
            'table_of_contents': data.get('table_of_contents', True),
            'quality': data.get('quality', 'high'),
            'header_text': data.get('header_text', 'DOCUMENT'),
            'footer_text': data.get('footer_text', ''),
        }
        
        logger.info(f"✨ Premium request: {data.get('filename', 'document')}")
        
        generator = PremiumPDFGenerator(premium_options['theme'], premium_options)
        pdf_bytes = generator.generate(bulk_text)
        
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_file.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return send_file(
            pdf_file,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{data.get('filename', 'document')}_{timestamp}.pdf"
        )
        
    except Exception as e:
        logger.error(f"❌ Error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ══════════════════════════════════════════════════════════════════════════════
# RUN SERVER
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║     ██████╗ ██╗   ██╗███╗   ██╗ ██████╗ ███████╗ ██████╗ ███╗   ██╗
    ║     ██╔══██╗██║   ██║████╗  ██║██╔════╝ ██╔════╝██╔═══██╗████╗  ██║
    ║     ██████╔╝██║   ██║██╔██╗ ██║██║  ███╗█████╗  ██║   ██║██╔██╗ ██║
    ║     ██╔══██╗██║   ██║██║╚██╗██║██║   ██║██╔══╝  ██║   ██║██║╚██╗██║
    ║     ██████╔╝╚██████╔╝██║ ╚████║╚██████╔╝███████╗╚██████╔╝██║ ╚████║
    ║     ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
    ║                      v2.1 - SPEED OPTIMIZED
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    logger.info(f"🚀 Server: http://0.0.0.0:{port}")
    logger.info(f"⚡ Manual Parser: Active (No API delays)")
    logger.info(f"🤖 Gemini: {'Enabled' if GEMINI_AVAILABLE else 'Disabled'}")
    
    app.run(host="0.0.0.0", port=port, debug=debug)
