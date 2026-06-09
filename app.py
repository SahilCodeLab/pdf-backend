"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   PREMIUM ACADEMIC PDF GENERATOR v2.1                        ║
║                   🚀 Optimized with Fast Manual Parser 🚀                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

Fast, reliable PDF generation with intelligent manual parsing.
No API dependencies - works offline!

Author: Premium PDF Generator
Version: 2.1
"""

# ══════════════════════════════════════════════════════════════════════════════
# IMPORTS
# ══════════════════════════════════════════════════════════════════════════════
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from weasyprint import HTML, CSS
import os
import io
import json
import time
import re
from datetime import datetime
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
    
    # Theme 1: Classic Academic - Traditional scholarly style
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
    
    # Theme 2: Modern Corporate - Professional business look
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
    
    # Theme 3: Elegant Legal - Formal legal documents
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
    
    # Theme 4: Executive Luxury - Premium executive documents
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
    
    # Theme 6: Vintage Paper - Classic look with vintage paper background
    VINTAGE = {
        "name": "Vintage Paper",
        "primary": "#5b4636",
        "secondary": "#a67c52",
        "accent": "#c49e71",
        "gold": "#d4af37",
        "text": "#3e2723",
        "heading": "#3e2723",
        "subheading": "#5d4037",
        "border": "#8d6e63",
        "footer_text": "#6d4c41",
        "code_bg": "#f5f1e6",
        "quote_bg": "#f1e7d0",
        "highlight_bg": "#fff9c4",
        "table_alt": "#faf3e0",
        "font_family": "'Georgia', 'Times New Roman', serif",
        "heading_font": "'Georgia', serif",
        "code_font": "'Courier New', monospace",
        "background_image": "url('vintage-paper.jpg')",
        "bg_color": "#ffffff",
        "extra_body_css": ""
    }

    # Theme 7: Corporate Vibe - Modern professional look
    CORPORATE_VIBE = {
        "name": "Corporate Vibe",
        "primary": "#0d47a1",
        "secondary": "#1976d2",
        "accent": "#64b5f6",
        "gold": "#ffb300",
        "text": "#212121",
        "heading": "#0d47a1",
        "subheading": "#1565c0",
        "border": "#90a4ae",
        "footer_text": "#607d8b",
        "code_bg": "#eceff1",
        "quote_bg": "#e3f2fd",
        "highlight_bg": "#fff9c4",
        "table_alt": "#f5f5f5",
        "font_family": "'Helvetica Neue', Helvetica, Arial, sans-serif",
        "heading_font": "'Helvetica Neue', Arial, sans-serif",
        "code_font": "'Courier New', monospace",
        "bg_color": "#ffffff",
        "extra_body_css": ""
    }

    # Theme 5: Scientific Journal - Academic research papers
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
        "bg_color": "#ffffff",
        "extra_body_css": ""
    }

    # Theme 8: Modern Minimalist - Clean zinc/gray design
    MINIMALIST = {
        "name": "Modern Minimalist",
        "primary": "#09090b",
        "secondary": "#27272a",
        "accent": "#71717a",
        "gold": "#a1a1aa",
        "text": "#18181b",
        "heading": "#09090b",
        "subheading": "#27272a",
        "border": "#e4e4e7",
        "footer_text": "#71717a",
        "code_bg": "#f4f4f5",
        "quote_bg": "#fafafa",
        "highlight_bg": "#f4f4f5",
        "table_alt": "#fafafa",
        "font_family": "'Inter', 'Segoe UI', Arial, sans-serif",
        "heading_font": "'Inter', 'Segoe UI', Arial, sans-serif",
        "code_font": "'Courier New', monospace",
        "bg_color": "#ffffff",
        "extra_body_css": "",
        "gradient": "",
        "background_image": ""
    }

    # Theme 9: Midnight Tech - Dark slate design with blue accents
    MIDNIGHT = {
        "name": "Midnight Tech",
        "primary": "#38bdf8",
        "secondary": "#0ea5e9",
        "accent": "#f43f5e",
        "gold": "#fbbf24",
        "text": "#cbd5e1",
        "heading": "#f8fafc",
        "subheading": "#38bdf8",
        "border": "#334155",
        "footer_text": "#64748b",
        "code_bg": "#1e293b",
        "quote_bg": "#1e293b",
        "highlight_bg": "#334155",
        "table_alt": "#1e293b",
        "font_family": "'Inter', 'Segoe UI', Arial, sans-serif",
        "heading_font": "'Inter', 'Segoe UI', Arial, sans-serif",
        "code_font": "'Courier New', monospace",
        "bg_color": "#0f172a",
        "extra_body_css": "",
        "gradient": "",
        "background_image": ""
    }

    # Theme 10: Cyberpunk Creative - Neon pink and cyan details on dark background
    CYBERPUNK = {
        "name": "Cyberpunk Creative",
        "primary": "#ec4899",
        "secondary": "#06b6d4",
        "accent": "#facc15",
        "gold": "#facc15",
        "text": "#cbd5e1",
        "heading": "#fdf2f8",
        "subheading": "#ec4899",
        "border": "#4b5563",
        "footer_text": "#9ca3af",
        "code_bg": "#111827",
        "quote_bg": "#1f2937",
        "highlight_bg": "#ec4899",
        "table_alt": "#1f2937",
        "font_family": "'Consolas', 'Courier New', Courier, monospace",
        "heading_font": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
        "code_font": "'Courier New', monospace",
        "bg_color": "#090d16",
        "extra_body_css": "",
        "gradient": "",
        "background_image": ""
    }
    
    @classmethod
    def get_theme(cls, theme_name):
        """Get theme by name with fallback to default"""
        themes = {
            'classic': cls.CLASSIC_ACADEMIC,
            'corporate': cls.MODERN_CORPORATE,
            'legal': cls.ELEGANT_LEGAL,
            'luxury': cls.EXECUTIVE_LUXURY,
            'scientific': cls.SCIENTIFIC_JOURNAL,
            'vintage': cls.VINTAGE,
            'corporate_vibe': cls.CORPORATE_VIBE,
            'minimalist': cls.MINIMALIST,
            'midnight': cls.MIDNIGHT,
            'cyberpunk': cls.CYBERPUNK,
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
        # Bold patterns
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
        
        # Italic patterns
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
        
        # Code patterns
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
            
            # Metadata detection
            metadata_patterns = [
                (r'(?:Author|By)[:\s]+(.+)', 'author'),
                (r'(?:Date|Published)[:\s]+(.+)', 'date'),
                (r'(?:Version|Rev)[:\s]+(.+)', 'version'),
                (r'(?:Institution|Organization|Company)[:\s]+(.+)', 'institution'),
            ]
            
            for pattern, key in metadata_patterns:
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
                sections.append({
                    "type": "heading",
                    "text": self.parse_inline_styles(clean),
                    "level": level
                })
                continue
            
            # Questions
            if line.endswith('?') or re.match(r'^(What|How|Why|When|Where|Who|Which|Explain|Describe|Define|Compare|Analyze)', line, re.I):
                sections.append({"type": "question", "text": line_parsed})
                continue
            
            # Answers
            if re.match(r'^(Answer:|Solution:|Definition:|=>|→|A:|S:)', line):
                clean = re.sub(r'^(Answer:|Solution:|Definition:|=>|→|A:|S:)\s*', '', line)
                sections.append({"type": "answer", "text": self.parse_inline_styles(clean)})
                continue
            
            # Blockquotes / Notes
            if line.startswith(('>', 'Note:', 'Important:', '⚠️', '📌', '💡', 'NB:', 'WARNING:')):
                clean = re.sub(r'^[>\s]*(Note:|Important:|⚠️|📌|💡|NB:|WARNING:)\s*', '', line)
                sections.append({
                    "type": "blockquote",
                    "text": self.parse_inline_styles(clean),
                    "note_type": "important" if any(x in line for x in ['Important', '⚠️', 'NB', 'WARNING']) else "note"
                })
                continue
            
            # Tables
            if '|' in line and line.count('|') >= 2:
                cells = [c.strip() for c in line.split('|')[1:-1]]
                
                # Skip separator rows
                if all(re.match(r'^[-:]+$', c) for c in cells if c):
                    continue
                
                if sections and sections[-1].get('type') == 'table':
                    sections[-1]['rows'].append(cells)
                else:
                    sections.append({
                        "type": "table",
                        "headers": cells,
                        "rows": []
                    })
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
            
            # Roman numeral lists
            roman_match = re.match(r'^([IVX]+)[.)]\s+(.+)', line)
            if roman_match:
                if not current_list or list_type != "numbered_list":
                    if current_list:
                        sections.append({"type": list_type, "items": current_list})
                    current_list = []
                    list_type = "numbered_list"
                current_list.append(self.parse_inline_styles(roman_match.group(2)))
                continue
            
            # Paragraphs - handle continuation
            if sections and sections[-1]['type'] == 'paragraph' and len(sections[-1]['text'].split()) < 60:
                sections[-1]['text'] += ' ' + line_parsed
            else:
                if current_list:
                    sections.append({"type": list_type, "items": current_list})
                    current_list = None
                    list_type = None
                sections.append({"type": "paragraph", "text": line_parsed})
        
        # Final cleanup
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
        """Generate WeasyPrint-compatible CSS customized per theme"""
        theme = self.theme
        theme_id = theme['name'].lower().replace(' ', '-')
        
        sizes = {
            'standard': {'base': '11pt', 'h1': '16pt', 'h2': '13pt'},
            'high': {'base': '12pt', 'h1': '18pt', 'h2': '15pt'},
            'premium': {'base': '13pt', 'h1': '20pt', 'h2': '17pt'}
        }
        s = sizes.get(self.quality, sizes['high'])
        
        # 1. BASE COMMON CSS RULES (Reset & Defaults)
        base_css = f"""
        * {{
            box-sizing: border-box;
        }}
        html, body {{
            margin: 0;
            padding: 0;
            background-color: {theme['bg_color']};
        }}
        body {{
            font-family: {theme['font_family']};
            font-size: {s['base']};
            color: {theme['text']};
            line-height: 1.7;
        }}
        ul, ol {{
            margin: 12px 0 20px 28px;
            padding: 0;
        }}
        ul li {{
            list-style-type: disc;
            margin-bottom: 6px;
        }}
        ol li {{
            list-style-type: decimal;
            margin-bottom: 6px;
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
            padding: 2px 5px;
            font-size: 0.9em;
            color: {theme['accent']};
            border-radius: 3px;
        }}
        pre {{
            font-family: {theme['code_font']};
            background-color: {theme['code_bg']};
            padding: 15px;
            border: 1px solid {theme['border']};
            border-left: 4px solid {theme['secondary']};
            font-size: 10pt;
            margin: 20px 0;
            page-break-inside: avoid;
            border-radius: 4px;
            color: {theme['text']};
        }}
        pre code {{
            background: none;
            padding: 0;
            color: inherit;
        }}
        .code-language {{
            display: inline-block;
            background-color: {theme['secondary']};
            color: white;
            padding: 2px 8px;
            font-size: 8pt;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: -15px;
            border-radius: 3px 3px 0 0;
            font-family: {theme['code_font']};
        }}
        .table-caption {{
            font-size: 9pt;
            color: {theme['footer_text']};
            text-align: center;
            margin-top: -15px;
            margin-bottom: 18px;
            font-style: italic;
        }}
        .divider {{
            border: none;
            border-top: 1px solid {theme['border']};
            margin: 35px 0;
        }}
        """

        # 2. THEME-SPECIFIC LAYOUT OVERRIDES
        layout_css = ""
        
        if theme_id == "classic-academic":
            layout_css = f"""
            @page {{
                size: A4;
                margin: 3.5cm 2.5cm 3cm 2.5cm;
                @top-center {{
                    content: "{theme['name'].upper()}";
                    font-family: {theme['heading_font']};
                    font-size: 8.5pt;
                    color: {theme['footer_text']};
                    border-bottom: 0.5px solid {theme['border']};
                    padding-bottom: 6px;
                    margin-bottom: 15px;
                }}
                @bottom-center {{
                    content: counter(page);
                    font-family: {theme['font_family']};
                    font-size: 10pt;
                    color: {theme['text']};
                }}
            }}
            @page :first {{
                margin: 0cm;
                @top-center {{ content: normal; }}
                @bottom-center {{ content: normal; }}
            }}
            
            /* Cover Page - Classic Academic */
            .cover-classic-academic {{
                text-align: center;
                padding: 120px 40px;
                height: 100%;
                page-break-after: always;
                background-color: #ffffff;
            }}
            .cover-classic-academic .cover-badge {{
                display: inline-block;
                border: 1px solid {theme['border']};
                background: none;
                color: {theme['primary']};
                font-weight: bold;
                letter-spacing: 3px;
                padding: 8px 20px;
                text-transform: uppercase;
                font-size: 9pt;
                margin-bottom: 40px;
            }}
            .cover-classic-academic .cover-title {{
                font-family: {theme['heading_font']};
                font-size: 28pt;
                font-weight: normal;
                color: {theme['heading']};
                margin: 30px auto;
                line-height: 1.3;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .cover-classic-academic .cover-subtitle {{
                font-family: {theme['font_family']};
                font-size: 13pt;
                color: {theme['subheading']};
                margin-top: 15px;
                font-style: italic;
            }}
            .cover-classic-academic .cover-divider {{
                width: 120px;
                height: 1px;
                background-color: {theme['primary']};
                margin: 40px auto;
            }}
            .cover-classic-academic .cover-meta {{
                margin-top: 100px;
                font-family: {theme['font_family']};
                font-size: 11pt;
                color: {theme['text']};
                line-height: 2;
            }}
            
            /* Main Content - Classic Academic */
            .main-classic-academic {{
                font-family: {theme['font_family']};
            }}
            .main-classic-academic .doc-header {{
                font-family: {theme['heading_font']};
                font-size: 10pt;
                text-align: center;
                border-bottom: 1px double {theme['border']};
                padding-bottom: 10px;
                margin-bottom: 40px;
                letter-spacing: 2px;
                color: {theme['primary']};
            }}
            .main-classic-academic h1 {{
                font-family: {theme['heading_font']};
                font-size: {s['h1']};
                color: {theme['heading']};
                text-align: center;
                margin-top: 45px;
                margin-bottom: 25px;
                border-bottom: 1px solid {theme['border']};
                padding-bottom: 8px;
                page-break-after: avoid;
            }}
            .main-classic-academic h2 {{
                font-family: {theme['heading_font']};
                font-size: {s['h2']};
                color: {theme['secondary']};
                margin-top: 30px;
                margin-bottom: 15px;
                page-break-after: avoid;
            }}
            .main-classic-academic p {{
                text-align: justify;
                text-indent: 1.8em;
                margin-bottom: 14px;
            }}
            .main-classic-academic p:first-of-type {{
                text-indent: 0;
            }}
            .main-classic-academic blockquote {{
                margin: 25px 2cm;
                padding: 0;
                border-left: none;
                font-style: italic;
                background: none;
                text-align: justify;
                line-height: 1.6;
            }}
            .main-classic-academic table {{
                border-top: 2px solid {theme['primary']};
                border-bottom: 2px solid {theme['primary']};
                margin: 30px 0;
            }}
            .main-classic-academic th {{
                background-color: transparent;
                color: {theme['heading']};
                border-bottom: 1px solid {theme['primary']};
                font-weight: bold;
                padding: 10px;
            }}
            .main-classic-academic td {{
                border: none;
                border-bottom: 0.5px solid {theme['border']};
                padding: 10px;
            }}
            .main-classic-academic tr:nth-child(even) {{
                background-color: transparent;
            }}
            .main-classic-academic .key-point {{
                background-color: {theme['highlight_bg']};
                border: 1px solid {theme['border']};
                padding: 15px;
                margin: 20px 0;
            }}
            """
            
        elif theme_id == "modern-corporate" or theme_id == "corporate-vibe" or theme_id == "corporate":
            layout_css = f"""
            @page {{
                size: A4;
                margin: 2.8cm 2.2cm 2.5cm 2.2cm;
                border-top: 8px solid {theme['primary']};
                @bottom-right {{
                    content: "Page " counter(page) " of " counter(pages);
                    font-family: {theme['font_family']};
                    font-size: 8pt;
                    color: {theme['footer_text']};
                }}
                @bottom-left {{
                    content: "CONFIDENTIAL REPORT";
                    font-family: {theme['font_family']};
                    font-size: 8pt;
                    color: {theme['footer_text']};
                    font-weight: bold;
                }}
            }}
            @page :first {{
                margin: 0cm;
                border-top: none;
                @bottom-right {{ content: normal; }}
                @bottom-left {{ content: normal; }}
            }}
            
            /* Cover Page - Corporate */
            .cover-{theme_id} {{
                text-align: left;
                padding: 0;
                height: 100%;
                page-break-after: always;
                background-color: #ffffff;
                position: relative;
            }}
            .cover-{theme_id}::before {{
                content: "";
                display: block;
                height: 220px;
                background-color: {theme['primary']};
                margin-bottom: 60px;
            }}
            .cover-{theme_id} .cover-badge {{
                display: inline-block;
                background-color: {theme['accent']};
                color: white;
                font-weight: bold;
                letter-spacing: 1px;
                padding: 6px 14px;
                text-transform: uppercase;
                font-size: 8pt;
                margin-left: 50px;
            }}
            .cover-{theme_id} .cover-title {{
                font-family: {theme['heading_font']};
                font-size: 32pt;
                font-weight: bold;
                color: {theme['primary']};
                margin: 30px 50px;
                line-height: 1.2;
            }}
            .cover-{theme_id} .cover-subtitle {{
                font-family: {theme['font_family']};
                font-size: 14pt;
                color: {theme['subheading']};
                margin: 0 50px 40px 50px;
            }}
            .cover-{theme_id} .cover-divider {{
                width: 100px;
                height: 4px;
                background-color: {theme['accent']};
                margin: 0 50px;
            }}
            .cover-{theme_id} .cover-meta {{
                margin-top: 100px;
                padding-left: 50px;
                font-family: {theme['font_family']};
                font-size: 10pt;
                color: {theme['text']};
                line-height: 1.8;
                border-left: 3px solid {theme['border']};
                margin-left: 50px;
            }}
            
            /* Main Content - Corporate */
            .main-{theme_id} {{
                font-family: {theme['font_family']};
            }}
            .main-{theme_id} .doc-header {{
                font-family: {theme['heading_font']};
                font-size: 9pt;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: {theme['secondary']};
                border-bottom: 2px solid {theme['border']};
                padding-bottom: 8px;
                margin-bottom: 40px;
                font-weight: bold;
            }}
            .main-{theme_id} h1 {{
                font-family: {theme['heading_font']};
                font-size: {s['h1']};
                color: {theme['primary']};
                margin-top: 35px;
                margin-bottom: 18px;
                border-bottom: 2px solid {theme['border']};
                padding-bottom: 5px;
                page-break-after: avoid;
            }}
            .main-{theme_id} h2 {{
                font-family: {theme['heading_font']};
                font-size: {s['h2']};
                color: {theme['secondary']};
                margin-top: 25px;
                margin-bottom: 12px;
                page-break-after: avoid;
            }}
            .main-{theme_id} p {{
                margin-bottom: 16px;
                text-align: left;
                line-height: 1.65;
            }}
            .main-{theme_id} blockquote {{
                background-color: {theme['quote_bg']};
                border-left: 4px solid {theme['primary']};
                padding: 15px 20px;
                margin: 20px 0;
            }}
            .main-{theme_id} table {{
                border-top: 2px solid {theme['primary']};
                border-bottom: 2px solid {theme['primary']};
                margin: 25px 0;
            }}
            .main-{theme_id} th {{
                background-color: {theme['primary']};
                color: white;
                font-weight: bold;
                padding: 10px 12px;
            }}
            .main-{theme_id} td {{
                border-bottom: 1px solid {theme['border']};
                padding: 10px 12px;
            }}
            .main-{theme_id} tr:nth-child(even) {{
                background-color: {theme['table_alt']};
            }}
            .main-{theme_id} .key-point {{
                background-color: {theme['highlight_bg']};
                border-left: 4px solid {theme['gold']};
                padding: 15px;
                margin: 20px 0;
            }}
            """
            
        elif theme_id == "elegant-legal":
            layout_css = f"""
            @page {{
                size: A4;
                margin: 2.5cm 2.5cm 2.5cm 3.5cm;
                border-left: 2px solid #8c1d1d;
                @bottom-center {{
                    content: "Page " counter(page);
                    font-family: {theme['font_family']};
                    font-size: 10pt;
                    color: {theme['text']};
                }}
            }}
            @page :first {{
                margin: 0cm;
                border-left: none;
                @bottom-center {{ content: normal; }}
            }}
            
            /* Cover Page - Legal */
            .cover-elegant-legal {{
                text-align: center;
                padding: 150px 50px;
                height: 100%;
                page-break-after: always;
                background-color: #ffffff;
            }}
            .cover-elegant-legal .cover-badge {{
                display: none;
            }}
            .cover-elegant-legal .cover-title {{
                font-family: {theme['heading_font']};
                font-size: 24pt;
                font-weight: bold;
                color: #000000;
                text-transform: uppercase;
                margin: 40px auto;
                line-height: 1.4;
                border-top: 3px double #000000;
                border-bottom: 3px double #000000;
                padding: 20px 0;
            }}
            .cover-elegant-legal .cover-subtitle {{
                font-family: {theme['font_family']};
                font-size: 12pt;
                color: #333333;
                margin-top: 15px;
            }}
            .cover-elegant-legal .cover-divider {{
                display: none;
            }}
            .cover-elegant-legal .cover-meta {{
                margin-top: 150px;
                text-align: left;
                font-family: {theme['font_family']};
                font-size: 11pt;
                line-height: 2.2;
                margin-left: 40px;
            }}
            
            /* Main Content - Legal */
            .main-elegant-legal {{
                font-family: {theme['font_family']};
                line-height: 2.1;
            }}
            .main-elegant-legal .doc-header {{
                text-align: center;
                font-family: {theme['heading_font']};
                font-size: 11pt;
                font-weight: bold;
                text-transform: uppercase;
                border-bottom: 1px solid #000000;
                padding-bottom: 8px;
                margin-bottom: 45px;
            }}
            .main-elegant-legal h1 {{
                font-family: {theme['heading_font']};
                font-size: {s['h1']};
                color: #000000;
                text-transform: uppercase;
                text-align: center;
                margin-top: 40px;
                margin-bottom: 20px;
                page-break-after: avoid;
            }}
            .main-elegant-legal h2 {{
                font-family: {theme['heading_font']};
                font-size: {s['h2']};
                color: {theme['secondary']};
                margin-top: 30px;
                margin-bottom: 15px;
                page-break-after: avoid;
            }}
            .main-elegant-legal p {{
                text-align: justify;
                text-indent: 2.5em;
                margin-bottom: 0;
            }}
            .main-elegant-legal blockquote {{
                margin: 20px 1.5cm;
                border: 1px solid {theme['border']};
                padding: 15px;
                background-color: {theme['quote_bg']};
                font-style: italic;
            }}
            .main-elegant-legal table {{
                border: 1px solid #000000;
                margin: 25px 0;
            }}
            .main-elegant-legal th, .main-elegant-legal td {{
                border: 1px solid #000000;
                padding: 8px 12px;
            }}
            .main-elegant-legal th {{
                background-color: #f5f5f4;
                color: #000000;
            }}
            """
            
        elif theme_id == "executive-luxury":
            layout_css = f"""
            @page {{
                size: A4;
                margin: 3.2cm;
                border: 1px solid {theme['primary']};
                padding: 1.2cm;
                @bottom-center {{
                    content: "—  " counter(page) "  —";
                    font-family: {theme['heading_font']};
                    font-size: 10pt;
                    color: {theme['primary']};
                    letter-spacing: 1px;
                }}
            }}
            @page :first {{
                margin: 0cm;
                border: none;
                @bottom-center {{ content: normal; }}
            }}
            
            /* Cover Page - Luxury */
            .cover-executive-luxury {{
                text-align: center;
                padding: 140px 50px;
                height: 100%;
                page-break-after: always;
                background-color: #ffffff;
                border: 1px solid {theme['primary']};
                margin: 2.5cm;
                box-sizing: border-box;
            }}
            .cover-executive-luxury .cover-badge {{
                display: inline-block;
                background-color: transparent;
                border: 1px solid {theme['primary']};
                color: {theme['primary']};
                font-weight: bold;
                letter-spacing: 4px;
                padding: 5px 20px;
                text-transform: uppercase;
                font-size: 8pt;
                margin-bottom: 50px;
            }}
            .cover-executive-luxury .cover-title {{
                font-family: {theme['heading_font']};
                font-size: 26pt;
                font-weight: normal;
                color: {theme['heading']};
                letter-spacing: 3px;
                text-transform: uppercase;
                line-height: 1.4;
                margin: 30px auto;
            }}
            .cover-executive-luxury .cover-subtitle {{
                font-family: {theme['font_family']};
                font-size: 12pt;
                color: {theme['subheading']};
                letter-spacing: 1px;
                font-style: italic;
            }}
            .cover-executive-luxury .cover-divider {{
                width: 140px;
                height: 1px;
                background-color: {theme['primary']};
                margin: 35px auto;
            }}
            .cover-executive-luxury .cover-meta {{
                margin-top: 100px;
                font-family: {theme['font_family']};
                font-size: 9.5pt;
                color: {theme['text']};
                line-height: 2;
                letter-spacing: 0.5px;
            }}
            
            /* Main Content - Luxury */
            .main-executive-luxury {{
                font-family: {theme['font_family']};
            }}
            .main-executive-luxury .doc-header {{
                text-align: center;
                font-family: {theme['heading_font']};
                font-size: 11pt;
                font-weight: normal;
                text-transform: uppercase;
                letter-spacing: 3px;
                color: {theme['primary']};
                border-bottom: 1px solid {theme['primary']};
                padding-bottom: 12px;
                margin-bottom: 45px;
            }}
            .main-executive-luxury h1 {{
                font-family: {theme['heading_font']};
                font-size: {s['h1']};
                color: {theme['heading']};
                text-transform: uppercase;
                letter-spacing: 2px;
                text-align: center;
                margin-top: 45px;
                margin-bottom: 25px;
                border-bottom: 1px solid {theme['primary']};
                padding-bottom: 10px;
                page-break-after: avoid;
            }}
            .main-executive-luxury h2 {{
                font-family: {theme['heading_font']};
                font-size: {s['h2']};
                color: {theme['secondary']};
                letter-spacing: 1px;
                text-align: center;
                margin-top: 30px;
                margin-bottom: 15px;
                page-break-after: avoid;
            }}
            .main-executive-luxury p {{
                text-align: justify;
                line-height: 1.8;
                margin-bottom: 16px;
            }}
            .main-executive-luxury blockquote {{
                margin: 25px 0;
                padding: 15px 25px;
                background-color: {theme['quote_bg']};
                border-left: 2px solid {theme['primary']};
                font-style: italic;
                color: {theme['secondary']};
            }}
            .main-executive-luxury table {{
                border-top: 1px solid {theme['primary']};
                border-bottom: 1px solid {theme['primary']};
                margin: 30px 0;
            }}
            .main-executive-luxury th {{
                background-color: transparent;
                color: {theme['heading']};
                border-bottom: 1.5px solid {theme['primary']};
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .main-executive-luxury td {{
                border: none;
                border-bottom: 1px solid #f4f4f5;
                padding: 10px;
            }}
            """
            
        elif theme_id == "scientific-journal":
            layout_css = f"""
            @page {{
                size: A4;
                margin: 2cm;
                @bottom-center {{
                    content: counter(page);
                    font-family: {theme['font_family']};
                    font-size: 9pt;
                    color: {theme['text']};
                }}
            }}
            @page :first {{
                margin: 0cm;
                @bottom-center {{ content: normal; }}
            }}
            
            /* Cover Page - Scientific */
            .cover-scientific-journal {{
                text-align: center;
                padding: 160px 60px;
                height: 100%;
                page-break-after: always;
                background-color: #ffffff;
            }}
            .cover-scientific-journal .cover-badge {{
                display: none;
            }}
            .cover-scientific-journal .cover-title {{
                font-family: {theme['heading_font']};
                font-size: 22pt;
                font-weight: bold;
                color: {theme['heading']};
                margin: 20px auto;
                line-height: 1.3;
            }}
            .cover-scientific-journal .cover-subtitle {{
                font-family: {theme['font_family']};
                font-size: 13pt;
                color: {theme['subheading']};
                margin-top: 10px;
            }}
            .cover-scientific-journal .cover-divider {{
                width: 80px;
                height: 2px;
                background-color: {theme['primary']};
                margin: 30px auto;
            }}
            .cover-scientific-journal .cover-meta {{
                margin-top: 120px;
                font-family: {theme['font_family']};
                font-size: 10pt;
                color: {theme['text']};
                line-height: 2;
            }}
            
            /* Main Content - Scientific (Dual Column) */
            .main-scientific-journal {{
                column-count: 2;
                column-gap: 1.2cm;
                font-family: {theme['font_family']};
            }}
            .main-scientific-journal .doc-header {{
                column-span: all;
                font-family: {theme['heading_font']};
                font-size: 12pt;
                font-weight: bold;
                text-align: center;
                border-bottom: 2px solid #000000;
                padding-bottom: 12px;
                margin-bottom: 30px;
                text-transform: uppercase;
            }}
            
            /* CSS Counters for auto section numbering */
            .main-scientific-journal {{
                counter-reset: h1counter;
            }}
            .main-scientific-journal h1 {{
                column-span: all;
                counter-reset: h2counter;
                font-family: {theme['heading_font']};
                font-size: 13pt;
                font-weight: bold;
                color: {theme['heading']};
                margin-top: 30px;
                margin-bottom: 12px;
                border-bottom: 1px solid #000000;
                padding-bottom: 3px;
                page-break-after: avoid;
                text-transform: uppercase;
                border-left: none;
                padding-left: 0;
            }}
            .main-scientific-journal h1::before {{
                counter-increment: h1counter;
                content: counter(h1counter) ". ";
            }}
            .main-scientific-journal h2 {{
                font-family: {theme['heading_font']};
                font-size: 10.5pt;
                font-weight: bold;
                color: {theme['subheading']};
                margin-top: 18px;
                margin-bottom: 8px;
                page-break-after: avoid;
            }}
            .main-scientific-journal h2::before {{
                counter-increment: h2counter;
                content: counter(h1counter) "." counter(h2counter) " ";
            }}
            .main-scientific-journal p {{
                font-size: 9.5pt;
                line-height: 1.45;
                text-align: justify;
                text-indent: 1.5em;
                margin-bottom: 6px;
            }}
            .main-scientific-journal p:first-of-type {{
                text-indent: 0;
            }}
            .main-scientific-journal blockquote {{
                column-span: all;
                background-color: {theme['quote_bg']};
                border-left: 3px solid {theme['primary']};
                padding: 10px 15px;
                margin: 15px 0;
                font-size: 9.5pt;
            }}
            .main-scientific-journal table {{
                column-span: all;
                border-top: 1.5px solid #000;
                border-bottom: 1.5px solid #000;
                margin: 20px 0;
                font-size: 9pt;
            }}
            .main-scientific-journal th {{
                background-color: transparent;
                color: #000;
                border-bottom: 1px solid #000;
                font-weight: bold;
                padding: 6px;
            }}
            .main-scientific-journal td {{
                border: none;
                padding: 6px;
            }}
            .main-scientific-journal tr:nth-child(even) {{
                background-color: transparent;
            }}
            .main-scientific-journal .key-point {{
                background-color: {theme['highlight_bg']};
                border: 1px solid {theme['border']};
                padding: 10px;
                margin: 15px 0;
                font-size: 9.5pt;
            }}
            """
            
        elif theme_id == "vintage-paper":
            layout_css = f"""
            @page {{
                size: A4;
                margin: 2.8cm 2.4cm;
                @bottom-right {{
                    content: "Folio " counter(page);
                    font-family: {theme['font_family']};
                    font-size: 9pt;
                    font-style: italic;
                    color: {theme['footer_text']};
                }}
            }}
            @page :first {{
                margin: 0cm;
                @bottom-right {{ content: normal; }}
            }}
            
            body {{
                background-image: url('vintage-paper.jpg');
                background-size: cover;
                background-repeat: no-repeat;
                background-position: center;
            }}
            
            /* Cover Page - Vintage */
            .cover-vintage-paper {{
                text-align: center;
                padding: 120px 50px;
                height: 100%;
                page-break-after: always;
                background-image: url('vintage-paper.jpg');
                background-size: cover;
                border: 4px double {theme['primary']};
                margin: 2cm;
                box-sizing: border-box;
            }}
            .cover-vintage-paper .cover-badge {{
                display: inline-block;
                background: none;
                border: 1px dashed {theme['primary']};
                color: {theme['primary']};
                font-family: {theme['font_family']};
                padding: 5px 15px;
                font-style: italic;
                font-size: 9pt;
                margin-bottom: 40px;
            }}
            .cover-vintage-paper .cover-title {{
                font-family: {theme['heading_font']};
                font-size: 28pt;
                color: {theme['heading']};
                margin: 20px auto;
                line-height: 1.3;
            }}
            .cover-vintage-paper .cover-subtitle {{
                font-size: 13pt;
                color: {theme['subheading']};
                margin-top: 10px;
                font-style: italic;
            }}
            .cover-vintage-paper .cover-divider {{
                width: 100px;
                height: 2px;
                background-color: {theme['primary']};
                margin: 30px auto;
            }}
            .cover-vintage-paper .cover-meta {{
                margin-top: 100px;
                font-family: {theme['font_family']};
                font-size: 10pt;
                color: {theme['text']};
                line-height: 2;
            }}
            
            /* Main Content - Vintage */
            .main-vintage-paper {{
                font-family: {theme['font_family']};
            }}
            .main-vintage-paper .doc-header {{
                text-align: center;
                font-size: 11pt;
                font-family: {theme['heading_font']};
                border-bottom: 1px dashed {theme['primary']};
                padding-bottom: 10px;
                margin-bottom: 40px;
                color: {theme['primary']};
            }}
            .main-vintage-paper h1 {{
                font-family: {theme['heading_font']};
                font-size: {s['h1']};
                color: {theme['heading']};
                text-align: center;
                border-bottom: 1px dashed {theme['primary']};
                padding-bottom: 8px;
                margin-top: 40px;
                page-break-after: avoid;
                border-left: none;
                padding-left: 0;
            }}
            .main-vintage-paper h2 {{
                font-family: {theme['heading_font']};
                font-size: {s['h2']};
                color: {theme['subheading']};
                margin-top: 30px;
                page-break-after: avoid;
            }}
            .main-vintage-paper p {{
                line-height: 1.8;
                text-indent: 2.2em;
                color: {theme['text']};
                text-align: justify;
            }}
            .main-vintage-paper p:first-of-type {{
                text-indent: 0;
            }}
            .main-vintage-paper blockquote {{
                background-color: rgba(241, 231, 208, 0.5);
                border: none;
                border-left: 3px double {theme['primary']};
                padding: 12px 20px;
                font-style: italic;
                margin: 25px 15px;
            }}
            .main-vintage-paper table {{
                border-top: 1px solid {theme['primary']};
                border-bottom: 1px solid {theme['primary']};
                margin: 25px 0;
            }}
            .main-vintage-paper th {{
                background-color: transparent;
                color: {theme['heading']};
                border-bottom: 1px solid {theme['primary']};
                font-weight: bold;
                padding: 10px;
            }}
            .main-vintage-paper td {{
                border: none;
                border-bottom: 1px dotted {theme['border']};
                padding: 10px;
                color: {theme['text']};
            }}
            .main-vintage-paper tr:nth-child(even) {{
                background-color: rgba(241, 231, 208, 0.2);
            }}
            .main-vintage-paper .key-point {{
                background-color: {theme['highlight_bg']};
                border-left: 3px solid {theme['primary']};
                padding: 12px 18px;
            }}
            """
            
        elif theme_id == "modern-minimalist":
            layout_css = f"""
            @page {{
                size: A4;
                margin: 3.5cm 2.5cm;
                @bottom-left {{
                    content: counter(page);
                    font-family: {theme['font_family']};
                    font-size: 9.5pt;
                    color: {theme['footer_text']};
                }}
            }}
            @page :first {{
                margin: 0cm;
                @bottom-left {{ content: normal; }}
            }}
            
            /* Cover Page - Minimalist */
            .cover-modern-minimalist {{
                text-align: left;
                padding: 160px 60px;
                height: 100%;
                page-break-after: always;
                background-color: #ffffff;
            }}
            .cover-modern-minimalist .cover-badge {{
                display: none;
            }}
            .cover-modern-minimalist .cover-title {{
                font-family: {theme['heading_font']};
                font-size: 34pt;
                font-weight: 200;
                letter-spacing: -1px;
                color: {theme['heading']};
                margin-bottom: 20px;
                line-height: 1.2;
            }}
            .cover-modern-minimalist .cover-subtitle {{
                font-family: {theme['font_family']};
                font-size: 13pt;
                color: {theme['subheading']};
                margin-top: 10px;
            }}
            .cover-modern-minimalist .cover-divider {{
                display: none;
            }}
            .cover-modern-minimalist .cover-meta {{
                margin-top: 150px;
                font-family: {theme['font_family']};
                font-size: 10pt;
                color: {theme['text']};
                line-height: 1.8;
                border-top: 1px solid {theme['border']};
                padding-top: 30px;
            }}
            
            /* Main Content - Minimalist */
            .main-modern-minimalist {{
                font-family: {theme['font_family']};
            }}
            .main-modern-minimalist .doc-header {{
                font-family: {theme['heading_font']};
                font-size: 9pt;
                color: {theme['footer_text']};
                border-bottom: 1px solid {theme['border']};
                padding-bottom: 10px;
                margin-bottom: 50px;
                font-weight: 400;
            }}
            .main-modern-minimalist h1 {{
                font-family: {theme['heading_font']};
                font-size: {s['h1']};
                font-weight: 300;
                letter-spacing: -0.5px;
                color: {theme['heading']};
                margin-top: 45px;
                margin-bottom: 20px;
                border-bottom: none;
                padding-left: 0;
                page-break-after: avoid;
            }}
            .main-modern-minimalist h2 {{
                font-family: {theme['heading_font']};
                font-size: {s['h2']};
                font-weight: 400;
                color: {theme['subheading']};
                margin-top: 30px;
                page-break-after: avoid;
            }}
            .main-modern-minimalist p {{
                font-size: 11pt;
                line-height: 1.75;
                color: {theme['text']};
                text-indent: 0;
                margin-bottom: 20px;
            }}
            .main-modern-minimalist blockquote {{
                background-color: transparent;
                border-left: 2px solid {theme['primary']};
                padding: 10px 0 10px 20px;
                margin: 25px 0;
                font-style: normal;
                color: {theme['accent']};
            }}
            .main-modern-minimalist table {{
                border: none;
                margin: 30px 0;
            }}
            .main-modern-minimalist th {{
                background-color: transparent;
                color: {theme['heading']};
                border-bottom: 2px solid {theme['primary']};
                font-weight: 600;
                padding: 12px 6px;
            }}
            .main-modern-minimalist td {{
                border: none;
                border-bottom: 1px solid {theme['border']};
                padding: 12px 6px;
            }}
            .main-modern-minimalist tr:nth-child(even) {{
                background-color: transparent;
            }}
            .main-modern-minimalist .key-point {{
                background-color: {theme['highlight_bg']};
                border: none;
                border-top: 1px solid {theme['border']};
                border-bottom: 1px solid {theme['border']};
                padding: 15px 0;
            }}
            """
            
        elif theme_id == "midnight-tech":
            layout_css = f"""
            @page {{
                size: A4;
                margin: 2.5cm 2cm;
                @bottom-right {{
                    content: "SYS_STATUS: ACTIVE // PAGE " counter(page);
                    font-family: {theme['code_font']};
                    font-size: 8pt;
                    color: {theme['footer_text']};
                }}
            }}
            @page :first {{
                margin: 0cm;
                @bottom-right {{ content: normal; }}
            }}
            
            body {{
                background-color: {theme['bg_color']};
                color: {theme['text']};
            }}
            
            /* Cover Page - Midnight */
            .cover-midnight-tech {{
                text-align: center;
                padding: 140px 40px;
                height: 100%;a
                page-break-after: always;
                background-color: {theme['bg_color']};
            }}
            .cover-midnight-tech .cover-badge {{
                display: inline-block;
                background-color: {theme['secondary']};
                color: white;
                font-family: {theme['code_font']};
                font-size: 8pt;
                letter-spacing: 2px;
                padding: 6px 14px;
                border-radius: 4px;
                margin-bottom: 30px;
            }}
            .cover-midnight-tech .cover-title {{
                font-family: {theme['heading_font']};
                font-size: 28pt;
                color: {theme['heading']};
                margin-bottom: 15px;
                line-height: 1.3;
            }}
            .cover-midnight-tech .cover-subtitle {{
                font-size: 13pt;
                color: {theme['subheading']};
                margin-bottom: 40px;
                font-family: {theme['code_font']};
            }}
            .cover-midnight-tech .cover-divider {{
                width: 120px;
                height: 2px;
                background-color: {theme['primary']};
                margin: 30px auto;
            }}
            .cover-midnight-tech .cover-meta {{
                margin-top: 100px;
                font-family: {theme['code_font']};
                font-size: 9.5pt;
                color: {theme['footer_text']};
                line-height: 2;
                text-align: left;
                display: inline-block;
                border: 1px solid {theme['border']};
                padding: 20px 40px;
                border-radius: 6px;
                background-color: {theme['code_bg']};
            }}
            
            /* Main Content - Midnight */
            .main-midnight-tech .doc-header {{
                font-family: {theme['code_font']};
                font-size: 8.5pt;
                color: {theme['primary']};
                border-bottom: 1px solid {theme['border']};
                padding-bottom: 10px;
                margin-bottom: 40px;
                letter-spacing: 1px;
            }}
            .main-midnight-tech h1 {{
                font-family: {theme['heading_font']};
                font-size: {s['h1']};
                color: {theme['heading']};
                border-bottom: 2px solid {theme['primary']};
                padding-bottom: 6px;
                margin-top: 35px;
                page-break-after: avoid;
                border-left: none;
                padding-left: 0;
            }}
            .main-midnight-tech h2 {{
                font-family: {theme['heading_font']};
                font-size: {s['h2']};
                color: {theme['subheading']};
                margin-top: 25px;
                page-break-after: avoid;
            }}
            .main-midnight-tech p {{
                line-height: 1.65;
                color: {theme['text']};
                text-indent: 0;
                margin-bottom: 15px;
            }}
            .main-midnight-tech blockquote {{
                background-color: {theme['quote_bg']};
                border-left: 4px solid {theme['primary']};
                border-radius: 4px;
                padding: 15px 20px;
                margin: 20px 0;
            }}
            .main-midnight-tech .question {{
                background-color: {theme['quote_bg']};
                border: 1px solid {theme['border']};
                border-left: 4px solid {theme['accent']};
                padding: 15px;
                border-radius: 4px;
                color: {theme['heading']};
            }}
            .main-midnight-tech .answer {{
                border-left: 2px solid {theme['border']};
                background-color: {theme['bg_color']};
                padding: 15px;
                margin-top: 5px;
                border-radius: 0 4px 4px 0;
            }}
            .main-midnight-tech table {{
                border: 1px solid {theme['border']};
                border-radius: 6px;
                overflow: hidden;
            }}
            .main-midnight-tech th {{
                background-color: {theme['code_bg']};
                color: {theme['primary']};
                border: 1px solid {theme['border']};
            }}
            .main-midnight-tech td {{
                border: 1px solid {theme['border']};
                background-color: {theme['bg_color']};
                color: {theme['text']};
            }}
            .main-midnight-tech tr:nth-child(even) td {{
                background-color: {theme['table_alt']};
            }}
            .main-midnight-tech .key-point {{
                background-color: {theme['highlight_bg']};
                border: 1px solid {theme['border']};
                border-left: 4px solid {theme['gold']};
                padding: 15px;
                border-radius: 4px;
            }}
            """
            
        elif theme_id == "cyberpunk-creative":
            layout_css = f"""
            @page {{
                size: A4;
                margin: 2.8cm 2cm;
                @bottom-right {{
                    content: "▼ NET_SECURE // PAGE " counter(page);
                    font-family: {theme['code_font']};
                    font-weight: bold;
                    font-size: 8pt;
                    color: {theme['primary']};
                }}
            }}
            @page :first {{
                margin: 0cm;
                @bottom-right {{ content: normal; }}
            }}
            
            body {{
                background-color: {theme['bg_color']};
                color: {theme['text']};
                border: 3px solid {theme['primary']};
                box-sizing: border-box;
                height: 100%;
            }}
            
            /* Cover Page - Cyberpunk */
            .cover-cyberpunk-creative {{
                text-align: center;
                padding: 120px 40px;
                height: 100%;
                page-break-after: always;
                background-color: {theme['bg_color']};
                border: 2px dashed {theme['primary']};
                margin: 1.5cm;
                box-sizing: border-box;
            }}
            .cover-cyberpunk-creative .cover-badge {{
                display: inline-block;
                background-color: {theme['primary']};
                color: {theme['bg_color']};
                font-family: {theme['code_font']};
                font-weight: bold;
                letter-spacing: 2px;
                padding: 6px 14px;
                text-transform: uppercase;
                font-size: 8.5pt;
                margin-bottom: 40px;
                box-shadow: 0 0 10px {theme['primary']};
            }}
            .cover-cyberpunk-creative .cover-title {{
                font-family: {theme['code_font']};
                font-weight: bold;
                font-size: 26pt;
                color: {theme['primary']};
                text-shadow: 0 0 8px rgba(236, 72, 153, 0.6);
                margin-bottom: 15px;
                line-height: 1.3;
                text-transform: uppercase;
            }}
            .cover-cyberpunk-creative .cover-subtitle {{
                font-size: 13pt;
                color: {theme['secondary']};
                font-family: {theme['code_font']};
                text-transform: uppercase;
                margin-bottom: 40px;
            }}
            .cover-cyberpunk-creative .cover-divider {{
                width: 120px;
                height: 4px;
                background-color: {theme['accent']};
                margin: 30px auto;
                box-shadow: 0 0 8px {theme['accent']};
            }}
            .cover-cyberpunk-creative .cover-meta {{
                margin-top: 100px;
                font-family: {theme['code_font']};
                font-size: 9pt;
                color: {theme['text']};
                line-height: 2;
                text-align: left;
                display: inline-block;
                border: 1px solid {theme['border']};
                padding: 20px 30px;
                background-color: {theme['code_bg']};
            }}
            
            /* Main Content - Cyberpunk */
            .main-cyberpunk-creative .doc-header {{
                font-family: {theme['code_font']};
                font-size: 9pt;
                font-weight: bold;
                color: {theme['secondary']};
                border-bottom: 2px solid {theme['secondary']};
                padding-bottom: 10px;
                margin-bottom: 40px;
                letter-spacing: 2px;
                text-transform: uppercase;
            }}
            .main-cyberpunk-creative h1 {{
                font-family: {theme['code_font']};
                font-weight: bold;
                font-size: {s['h1']};
                color: {theme['primary']};
                text-shadow: 0 0 8px rgba(236, 72, 153, 0.5);
                border-bottom: 2px solid {theme['secondary']};
                padding-bottom: 8px;
                margin-top: 35px;
                text-transform: uppercase;
                border-left: none;
                padding-left: 0;
                page-break-after: avoid;
            }}
            .main-cyberpunk-creative h2 {{
                font-family: {theme['code_font']};
                font-size: {s['h2']};
                color: {theme['secondary']};
                text-shadow: 0 0 5px rgba(6, 182, 212, 0.3);
                text-transform: uppercase;
                margin-top: 25px;
                page-break-after: avoid;
            }}
            .main-cyberpunk-creative p {{
                font-family: {theme['code_font']};
                line-height: 1.6;
                color: {theme['text']};
                margin-bottom: 15px;
            }}
            .main-cyberpunk-creative blockquote {{
                background-color: {theme['quote_bg']};
                border: 1px solid {theme['border']};
                border-left: 4px solid {theme['accent']};
                color: {theme['accent']};
                padding: 15px 20px;
                margin: 20px 0;
            }}
            .main-cyberpunk-creative .question {{
                background-color: {theme['code_bg']};
                border: 2px solid {theme['primary']};
                color: {theme['heading']};
                font-family: {theme['code_font']};
                text-transform: uppercase;
                border-radius: 0;
            }}
            .main-cyberpunk-creative .answer {{
                background-color: {theme['quote_bg']};
                border: 1px dashed {theme['secondary']};
                padding: 15px;
                margin-top: 5px;
            }}
            .main-cyberpunk-creative table {{
                border: 2px solid {theme['secondary']};
                background-color: {theme['code_bg']};
            }}
            .main-cyberpunk-creative th {{
                background-color: {theme['primary']};
                color: {theme['bg_color']};
                font-weight: bold;
                border: 1px solid {theme['secondary']};
                text-transform: uppercase;
            }}
            .main-cyberpunk-creative td {{
                border: 1px solid {theme['secondary']};
                color: {theme['text']};
            }}
            .main-cyberpunk-creative tr:nth-child(even) td {{
                background-color: {theme['table_alt']};
            }}
            .main-cyberpunk-creative .key-point {{
                background-color: {theme['accent']};
                color: {theme['bg_color']};
                border-left: 5px solid {theme['primary']};
                padding: 15px;
                font-weight: bold;
            }}
            """
            
        else:
            layout_css = f"""
            @page {{
                size: A4;
                margin: 2.5cm;
                @bottom-right {{
                    content: "Page " counter(page);
                    font-family: {theme['font_family']};
                    font-size: 9pt;
                    color: {theme['footer_text']};
                }}
            }}
            h1 {{
                font-family: {theme['heading_font']};
                font-size: {s['h1']};
                color: {theme['heading']};
                margin-top: 30px;
                border-left: 4px solid {theme['accent']};
                padding-left: 10px;
            }}
            p {{
                line-height: 1.6;
            }}
            """
            
        return base_css + layout_css
"""
    
    def build_cover_page(self, doc):
        """Generate premium cover page"""
        metadata = doc.get('metadata', {})
        theme_name = self.theme['name'].lower().replace(' ', '-')
        
        meta_html = ""
        if metadata.get('author'):
            meta_html += f'<p class="meta-author"><strong>Author:</strong> {metadata["author"]}</p>'
        if metadata.get('date'):
            meta_html += f'<p class="meta-date"><strong>Date:</strong> {metadata["date"]}</p>'
        else:
            meta_html += f'<p class="meta-date"><strong>Date:</strong> {datetime.now().strftime("%B %d, %Y")}</p>'
        if metadata.get('version'):
            meta_html += f'<p class="meta-version"><strong>Version:</strong> {metadata["version"]}</p>'
        if metadata.get('institution'):
            meta_html += f'<p class="meta-inst"><strong>Organization:</strong> {metadata["institution"]}</p>'
        
        return f"""
<div class="cover-page cover-{theme_name}">
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
        """Build HTML for a single section element"""
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
        theme_name = self.theme['name'].lower().replace(' ', '-')
        
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
        
        # Add cover page
        if self.has_cover:
            html += self.build_cover_page(doc)
        
        # Add table of contents
        if self.has_toc:
            html += self.build_toc(doc)
        
        # Add main content wrap
        html += f'<div class="main-content main-{theme_name}">'
        
        # Add main content header
        html += f'<div class="doc-header">{title}</div>'
        
        # Add all sections
        for section in doc.get('sections', []):
            html += self.build_element(section)
            
        html += '</div>'
        
        html += """
</body>
</html>"""
        
        return html


# ══════════════════════════════════════════════════════════════════════════════
# PDF GENERATOR ENGINE
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
        
        # Parse document structure
        doc = self.parser.parse(text)
        sections_count = len(doc.get('sections', []))
        logger.info(f"✅ Parsed {sections_count} sections")
        
        # Build HTML
        html_content = self.builder.build(doc)
        
        # Generate PDF
        pdf_bytes = HTML(string=html_content, base_url=os.path.dirname(os.path.abspath(__file__))).write_pdf()
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
            logger.info(f"💾 PDF saved: {output_path}")
        
        return pdf_bytes
    
    def generate_to_bytes(self, text):
        """Generate PDF and return as bytes"""
        pdf_bytes = self.generate(text)
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_file.seek(0)
        return pdf_file


# ══════════════════════════════════════════════════════════════════════════════
# FLASK API ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/", methods=["GET"])
def index():
    """Health check endpoint"""
    return jsonify({
        "status": "✅ Premium PDF Generator v2.1 Running",
        "version": "2.1",
        "speed": "⚡ Fast Manual Parser (No API calls)",
        "gemini": "Enabled" if GEMINI_AVAILABLE else "Disabled",
        "themes": ["classic", "corporate", "legal", "luxury", "scientific", "vintage", "minimalist", "midnight", "cyberpunk"],
        "endpoints": {
            "GET /": "Health check",
            "GET /themes": "List available themes",
            "POST /generate_pdf": "Generate basic PDF",
            "POST /generate_premium_pdf": "Generate with full options"
        }
    })

@app.route("/themes", methods=["GET"])
def list_themes():
    """List all available themes"""
    return jsonify({
        "success": True,
        "themes": {
            "classic": "Classic Academic - Traditional scholarly style with serif fonts",
            "corporate": "Modern Corporate - Professional business documents",
            "legal": "Elegant Legal - Formal legal document styling",
            "luxury": "Executive Luxury - Premium executive documents",
            "scientific": "Scientific Journal - Academic research papers",
            "vintage": "Vintage Paper - Classic look with vintage paper background",
            "minimalist": "Modern Minimalist - Clean Zinc, sans-serif design",
            "midnight": "Midnight Tech - Dark Slate design with blue accents",
            "cyberpunk": "Cyberpunk Creative - Neon pink and cyan details on dark background"
        }
    })

@app.route("/generate_pdf", methods=["POST"])
def generate_pdf():
    """Generate premium PDF document"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
        
        bulk_text = data.get("bulk_text", "")
        if not bulk_text.strip():
            return jsonify({"error": "bulk_text content is missing"}), 400
        
        # Get parameters
        filename = data.get("filename", "document")
        theme_name = data.get("theme", "classic")
        
        logger.info(f"📝 Processing request for: {filename}")
        
        # Generate PDF
        generator = PremiumPDFGenerator(theme_name)
        pdf_bytes = generator.generate(bulk_text)
        
        # Prepare response
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_file.seek(0)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        logger.info(f"✅ PDF generated successfully: {filename}_{timestamp}.pdf")
        
        return send_file(
            pdf_file,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{filename}_{timestamp}.pdf"
        )
        
    except Exception as e:
        logger.error(f"❌ Error generating PDF: {traceback.format_exc()}")
        return jsonify({
            "error": str(e),
            "message": "Failed to generate PDF"
        }), 500

@app.route("/generate_premium_pdf", methods=["POST"])
def generate_premium_pdf():
    """Generate PDF with full premium options"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
        
        bulk_text = data.get("bulk_text", "")
        if not bulk_text.strip():
            return jsonify({"error": "bulk_text content is missing"}), 400
        
        # Full premium options
        premium_options = {
            'theme': data.get('theme', 'classic'),
            'cover_page': data.get('cover_page', True),
            'table_of_contents': data.get('table_of_contents', True),
            'quality': data.get('quality', 'high'),
            'header_text': data.get('header_text', 'DOCUMENT'),
            'footer_text': data.get('footer_text', ''),
        }
        
        logger.info(f"✨ Processing premium request: {data.get('filename', 'document')}")
        
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
        logger.error(f"❌ Premium PDF generation failed: {traceback.format_exc()}")
        return jsonify({
            "error": str(e),
            "message": "Premium PDF generation failed"
        }), 500


# ══════════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ══════════════════════════════════════════════════════════════════════════════
# APPLICATION LAUNCH
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    print("""
  
    
    logger.info(f"🚀 Server starting on http://0.0.0.0:{port}")
    logger.info(f"🔧 Debug mode: {debug}")
    logger.info(f"⚡ Manual Parser: Active (No API delays)")
    logger.info(f"🤖 Gemini AI: {'Enabled' if GEMINI_AVAILABLE else 'Disabled'}")
    logger.info("")
    logger.info("📌 Available Endpoints:")
    logger.info("   GET  /            - Health check")
    logger.info("   GET  /themes      - List themes")
    logger.info("   POST /generate_pdf - Generate PDF")
    logger.info("   POST /generate_premium_pdf - Full options")
    logger.info("")
    
    app.run(host="0.0.0.0", port=port, debug=debug)
