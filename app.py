"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   PREMIUM ACADEMIC PDF GENERATOR v2.0                        ║
║                        ✨ Elite Document Processing ✨                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

Enhanced Flask application for generating premium quality PDF documents
with AI-powered parsing, multiple themes, and professional typesetting.
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
# GEMINI AI CLIENT SETUP WITH ADVANCED RESILIENCE
# ══════════════════════════════════════════════════════════════════════════════
try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError
    
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("❌ GEMINI_API_KEY not found in environment variables")
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    GEMINI_AVAILABLE = True
    logger.info("✅ Gemini AI Client initialized successfully")
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("⚠️ Google Generative AI not installed. Using advanced manual parsing.")
except Exception as e:
    GEMINI_AVAILABLE = False
    logger.warning(f"⚠️ Gemini initialization failed: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# PREMIUM DESIGN THEMES
# ══════════════════════════════════════════════════════════════════════════════
class PremiumTheme:
    """Premium theme configurations for different document styles"""
    
    # ══════════════════════════════════════════════════════════════════════════
    # Theme 1: Classic Academic (Default)
    # ══════════════════════════════════════════════════════════════════════════
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
        "font_family": "'Georgia', 'Times New Roman', serif",
        "heading_font": "'Georgia', serif",
        "code_font": "'Courier New', Courier, monospace",
    }
    
    # ══════════════════════════════════════════════════════════════════════════
    # Theme 2: Modern Corporate
    # ══════════════════════════════════════════════════════════════════════════
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
        "code_font": "'Fira Code', 'Consolas', monospace",
    }
    
    # ══════════════════════════════════════════════════════════════════════════
    # Theme 3: Elegant Legal
    # ══════════════════════════════════════════════════════════════════════════
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
    
    # ══════════════════════════════════════════════════════════════════════════
    # Theme 4: Executive Luxury
    # ══════════════════════════════════════════════════════════════════════════
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
        "font_family": "'Didot', 'Bodoni MT', 'Times New Roman', serif",
        "heading_font": "'Didot', Georgia, serif",
        "code_font": "'SF Mono', 'Monaco', monospace",
    }
    
    # ══════════════════════════════════════════════════════════════════════════
    # Theme 5: Scientific Journal
    # ══════════════════════════════════════════════════════════════════════════
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
        "font_family": "'Computer Modern', 'Times New Roman', serif",
        "heading_font": "'Computer Modern', Georgia, serif",
        "code_font": "'Fira Code', 'Consolas', monospace",
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
            'default': cls.CLASSIC_ACADEMIC
        }
        return themes.get(theme_name.lower(), cls.CLASSIC_ACADEMIC)


# ══════════════════════════════════════════════════════════════════════════════
# ADVANCED TEXT PARSER WITH MULTI-STAGE INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════
class PremiumTextParser:
    """Intelligent text parser using Gemini AI and Markdown engine"""
    
    def __init__(self, theme):
        self.theme = theme

    def parse(self, text):
        """
        1. AI se raw text ko structured Markdown mein convert karwaye.
        2. Markdown ko library ki madad se HTML mein convert kare.
        """
        print("🤖 Parsing and Formatting with Gemini...")
        
        # AI Prompt: Ye instruction AI ko raw text ko sahi formatting dene par majboor karegi
        prompt = f"""
        Convert the following raw text into structured, professional Markdown format. 
        - Use # for Titles, ## for Sections, ### for Subsections.
        - Organize data into Markdown tables where applicable.
        - Use - for bullets, 1. for numbered lists.
        - Use **bold** and *italic* as needed.
        - Ensure all content is preserved without summarization.
        
        Raw Text:
        {text}
        """
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            markdown_text = response.text
            
            # Markdown library ko HTML mein convert karne ke liye use karein
            # 'tables' aur 'fenced_code' extensions zaroori hain
            html_content = markdown.markdown(
                markdown_text, 
                extensions=['tables', 'fenced_code']
            )
            return html_content
            
        except Exception as e:
            print(f"❌ Error in parsing: {e}")
            # Agar AI fail ho, toh fallback mein simple text ko HTML paragraph bana do
            return f"<p>{text}</p>"
    
    def detect_document_type(self, text):
        """Detect the type of document for specialized parsing"""
        indicators = {
            'academic_paper': ['abstract', 'introduction', 'methodology', 'references', 'doi'],
            'legal_document': ['whereas', 'hereby', 'party', 'agreement', 'clause', 'herein'],
            'technical_manual': ['syntax', 'parameter', 'configuration', 'installation', 'api'],
            'business_report': ['executive summary', 'revenue', 'fiscal', 'quarterly', 'kpi'],
            'resume': ['experience', 'education', 'skills', 'certifications', 'objective'],
            'scientific': ['abstract', 'hypothesis', 'methodology', 'results', 'conclusion', 'figure'],
        }
        
        text_lower = text.lower()
        scores = {}
        
        for doc_type, keywords in indicators.items():
            scores[doc_type] = sum(1 for kw in keywords if kw in text_lower)
        
        return max(scores, key=scores.get) if max(scores.values()) > 0 else 'general'
    
    def parse_structure(self, text):
        """Advanced structural parsing with context awareness"""
        lines = text.strip().split('\n')
        sections = []
        title = ""
        
        # Document metadata
        metadata = {
            'author': '',
            'date': '',
            'version': '',
            'institution': ''
        }
        
        current_list = None
        list_type = None
        section_context = []
        
        for i, line in enumerate(lines):
            original_line = line
            line = line.strip()
            
            if not line:
                if current_list:
                    sections.append({"type": list_type, "items": current_list})
                    current_list = None
                    list_type = None
                continue
            
            # Parse inline styles
            line_parsed = self.parse_inline_styles(line)
            
            # TITLE DETECTION
            if not title and len(line) < 120:
                if (
                    line.startswith('# ') or 
                    line.isupper() and len(line.split()) <= 15 or
                    re.match(r'^[A-Z][A-Za-z\s\-:]+$', line)
                ):
                    title = line.replace('#', '').strip()
                    # Check for subtitle
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if len(next_line) < 80 and not next_line.startswith('#'):
                            sections.append({
                                "type": "subtitle",
                                "text": self.parse_inline_styles(next_line)
                            })
                    continue
            
            # METADATA DETECTION
            metadata_patterns = [
                (r'(?:Author|By|Writer)[:\s]+(.+)', 'author'),
                (r'(?:Date|Published|Date)[:\s]+(.+)', 'date'),
                (r'(?:Version|Rev)[:\s]+(.+)', 'version'),
                (r'(?:Institution|Organization|Company)[:\s]+(.+)', 'institution'),
            ]
            
            for pattern, key in metadata_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    metadata[key] = match.group(1).strip()
                    break
            
            # HEADING DETECTION
            heading_patterns = [
                r'^#{1,6}\s+(.+)',
                r'^(CHAPTER|SECTION|PART|UNIT)\s+\d+[:.\s]+(.+)',
                r'^(Chapter|Section|Part|Unit)\s+\d+',
                r'^[IVXLC]+\.\s+[A-Z]',
                r'^\d+\.\d+\s+[A-Z]',
            ]
            
            is_heading = False
            for pattern in heading_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    if current_list:
                        sections.append({"type": list_type, "items": current_list})
                        current_list = None
                        list_type = None
                    
                    clean_heading = re.sub(r'^#+\s*', '', line).strip()
                    sections.append({
                        "type": "heading",
                        "text": self.parse_inline_styles(clean_heading),
                        "level": len(re.match(r'^(#+)\s', line).group(1)) if line.startswith('#') else 1
                    })
                    is_heading = True
                    break
            
            if is_heading:
                continue
            
            # QUESTION DETECTION
            question_patterns = [
                r'^(What|How|Why|When|Where|Who|Which|Explain|Describe|Define|Compare|Analyze)',
                r'^\d+[.)]\s*(What|How|Why|When|Where|Who|Which)',
                r'\?$'
            ]
            
            for pattern in question_patterns:
                if re.match(pattern, line, re.IGNORECASE) or (line.endswith('?') and len(line) < 200):
                    sections.append({
                        "type": "question",
                        "text": line_parsed
                    })
                    break
            
            # ANSWER/DEFINITION DETECTION
            if line.startswith(('Answer:', 'Solution:', 'Definition:', '=>', '→', 'A:', 'S:')):
                clean_answer = re.sub(r'^(Answer:|Solution:|Definition:|=>|→|A:|S:)\s*', '', line)
                sections.append({
                    "type": "answer",
                    "text": self.parse_inline_styles(clean_answer)
                })
                continue
            
            # BLOCKQUOTE/NOTE DETECTION
            if line.startswith(('>', 'Note:', 'Important:', '⚠️', '📌', '💡', 'NB:', 'NOTE:')):
                clean_quote = re.sub(r'^[>\s]*(Note:|Important:|⚠️|📌|💡|NB:|NOTE:)\s*', '', line)
                sections.append({
                    "type": "blockquote",
                    "text": self.parse_inline_styles(clean_quote),
                    "note_type": "important" if any(x in line for x in ['Important', '⚠️', 'NB']) else "note"
                })
                continue
            
            # CODE BLOCK DETECTION
            if line.startswith(('```', '    ', '\t')) or re.match(r'^\s*(def |class |function |const |var |let |import |using )', line):
                code_content = original_line
                if line.startswith('```'):
                    code_content = re.sub(r'^```\w*\s*', '', line)
                
                sections.append({
                    "type": "code_block",
                    "text": self.parse_inline_styles(code_content.strip()),
                    "language": self.detect_language(code_content)
                })
                continue
            
            # TABLE DETECTION
            if '|' in line and line.count('|') >= 2:
                cells = [c.strip() for c in line.split('|')[1:-1]]
                
                if all(re.match(r'^[-:]+$', c) for c in cells if c):
                    continue
                
                if sections and sections[-1].get('type') == 'table':
                    sections[-1]['rows'].append(cells)
                else:
                    sections.append({
                        "type": "table",
                        "headers": cells if i > 0 else cells,
                        "rows": []
                    })
                continue
            
            # BULLET LIST DETECTION
            bullet_patterns = [
                r'^[\-\*\•\◦\▪]\s+(.+)',
                r'^→\s+(.+)',
                r'^➤\s+(.+)',
                r'^✦\s+(.+)',
            ]
            
            for pattern in bullet_patterns:
                match = re.match(pattern, line)
                if match:
                    if not current_list or list_type != "bullet_list":
                        if current_list:
                            sections.append({"type": list_type, "items": current_list})
                        current_list = []
                        list_type = "bullet_list"
                    current_list.append(self.parse_inline_styles(match.group(1)))
                    break
            
            if match:
                continue
            
            # NUMBERED LIST DETECTION
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
            
            # PARAGRAPH (DEFAULT)
            if sections and sections[-1]['type'] == 'paragraph' and len(sections[-1]['text'].split()) < 50:
                sections[-1]['text'] += ' ' + line_parsed
            else:
                if current_list:
                    sections.append({"type": list_type, "items": current_list})
                    current_list = None
                    list_type = None
                
                sections.append({
                    "type": "paragraph",
                    "text": line_parsed
                })
        
        # Final cleanup
        if current_list:
            sections.append({"type": list_type, "items": current_list})
        
        return {
            "title": title or "Premium Document",
            "sections": sections,
            "metadata": metadata,
            "doc_type": self.detect_document_type(text)
        }
    
    def detect_language(self, code):
        """Detect programming language from code content"""
        patterns = {
            'python': [r'\bdef\s+\w+\(', r'\bimport\s+\w+', r'\bprint\s*\(', r':\s*$'],
            'javascript': [r'\bfunction\s+\w+\(', r'\bconst\s+\w+\s*=', r'\bconsole\.log', r'=>'],
            'java': [r'\bpublic\s+class', r'\bSystem\.out\.print', r'\bvoid\s+main'],
            'c': [r'#include\s*<', r'\bint\s+main\(', r'\bprintf\s*\('],
            'html': [r'<html', r'<div', r'<span', r'</\w+>'],
            'css': [r'\{\s*[\w-]+\s*:', r'\bmargin\b', r'\bpadding\b', r'\.class'],
            'sql': [r'\bSELECT\b', r'\bFROM\b', r'\bWHERE\b', r'\bINSERT\b'],
            'json': [r'^\s*"[\w]+"\s*:', r'^\s*[\[\{]', r'^\s*\}'],
        }
        
        for lang, lang_patterns in patterns.items():
            if sum(1 for p in lang_patterns if re.search(p, code, re.IGNORECASE)) >= 2:
                return lang
        
        return 'plaintext'
    
    def parse(self, text):
        """Main parsing method - tries Gemini first, falls back to manual"""
        if GEMINI_AVAILABLE:
            try:
                logger.info("🤖 Attempting AI-powered document analysis...")
                return self.parse_with_gemini(text)
            except Exception as e:
                logger.warning(f"⚠️ Gemini parsing failed: {e}")
                logger.info("🔄 Falling back to intelligent manual parser...")
        
        return self.parse_structure(text)
    
    def parse_with_gemini(self, text):
        """Parse document using Gemini AI for intelligent structure detection"""
        prompt = f"""You are an expert document typesetter specializing in premium academic and professional document formatting.

CRITICAL REQUIREMENTS:
1. Preserve EVERY SINGLE WORD, sentence, and data point - NO summarization
2. Detect and preserve all formatting: bold, italic, code, links
3. Identify document structure accurately
4. Separate questions from answers cleanly
5. Preserve all list items and table data

Return ONLY a valid JSON object with this exact schema:

{{
  "title": "Exact document title (uppercase if major heading)",
  "subtitle": "Optional subtitle if present",
  "sections": [
    {{
      "type": "heading|subheading|paragraph|question|answer|blockquote|code_block|table|bullet_list|numbered_list|image|divider",
      "text": "Full text content (for standard types)",
      "items": ["List item 1", "List item 2"] (for lists),
      "headers": ["Col 1", "Col 2"] (for tables),
      "rows": [["Row 1 Cell 1", "Row 1 Cell 2"]] (for tables),
      "language": "python|javascript|etc" (for code blocks),
      "level": 1-6 (for headings),
      "alt_text": "Description" (for images)
    }}
  ],
  "metadata": {{
    "author": "Author name if found",
    "date": "Date if found",
    "version": "Version if found",
    "institution": "Institution if found"
  }}
}}

Document to analyze:
{text[:8000]}"""

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=8192,
                        response_mime_type="application/json"
                    )
                )
                
                result = json.loads(response.text.strip())
                logger.info("✅ AI parsing successful")
                return result
                
            except APIError as e:
                if e.code == 429 and attempt < 2:
                    wait_time = (attempt + 1) * 3
                    logger.warning(f"⏳ Rate limit hit. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                raise
            except Exception as e:
                raise


# ══════════════════════════════════════════════════════════════════════════════
# PREMIUM HTML BUILDER - ADVANCED TYPESETTING ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class PremiumHTMLBuilder:
    """Build premium-quality HTML documents with sophisticated styling"""
    
    def __init__(self, theme, options=None):
        self.theme = theme
        self.options = options or {}
        self.has_cover = self.options.get('cover_page', True)
        self.has_toc = self.options.get('table_of_contents', True)
        self.has_page_numbers = self.options.get('page_numbers', True)
        self.has_headers = self.options.get('headers', True)
        self.quality = self.options.get('quality', 'high')
    
    def build_css(self):
        """Generate premium CSS with all styling"""
        theme = self.theme
        
        sizes = {
            'standard': {'base': '11pt', 'h1': '16pt', 'h2': '14pt', 'h3': '12pt'},
            'high': {'base': '12pt', 'h1': '18pt', 'h2': '15pt', 'h3': '13pt'},
            'premium': {'base': '13pt', 'h1': '20pt', 'h2': '17pt', 'h3': '14pt'}
        }
        s = sizes.get(self.quality, sizes['high'])
        
        return f"""
        /* ═══════════════════════════════════════════════════════════════════
           PREMIUM PDF STYLESHEET
           Theme: {theme['name']}
           Quality: {self.quality.upper()}
           ═══════════════════════════════════════════════════════════════════ */
        
        @page {{
            size: A4;
            margin: 2.5cm 2cm 2.5cm 2.5cm;
            
            @top-center {{
                content: "{self.options.get('header_text', 'PREMIUM DOCUMENT')}";
                font-size: 8pt;
                color: {theme['footer_text']};
                font-family: {theme['font_family']};
                letter-spacing: 1.5px;
                text-transform: uppercase;
                border-bottom: 0.5px solid {theme['border']};
                padding-bottom: 12px;
                width: 100%;
            }}
            
            @bottom-right {{
                content: counter(page) " | " counter(pages);
                font-size: 9pt;
                color: {theme['footer_text']};
                font-family: {theme['font_family']};
            }}
            
            @bottom-left {{
                content: "{self.options.get('footer_text', 'Confidential')}";
                font-size: 8pt;
                color: {theme['footer_text']};
                font-family: {theme['font_family']};
            }}
        }}
        
        /* ═══════════════════════════════════════════════════════════════════
           BASE TYPOGRAPHY
           ═══════════════════════════════════════════════════════════════════ */
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: {theme['font_family']};
            font-size: {s['base']};
            color: {theme['text']};
            line-height: 1.8;
            text-rendering: optimizeLegibility;
            -webkit-font-smoothing: antialiased;
        }}
        
        /* ═══════════════════════════════════════════════════════════════════
           COVER PAGE STYLING
           ═══════════════════════════════════════════════════════════════════ */
        .cover-page {{
            text-align: center;
            padding-top: 120px;
            page-break-after: always;
            background: linear-gradient(180deg, {theme['code_bg']} 0%, white 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }}
        
        .cover-badge {{
            display: inline-block;
            background: {theme['primary']};
            color: white;
            padding: 6px 20px;
            font-size: 9pt;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 30px;
            border-radius: 2px;
        }}
        
        .cover-title {{
            font-family: {theme['heading_font']};
            font-size: 28pt;
            font-weight: 700;
            color: {theme['heading']};
            margin-bottom: 15px;
            line-height: 1.3;
            letter-spacing: -0.5px;
        }}
        
        .cover-subtitle {{
            font-size: 14pt;
            color: {theme['subheading']};
            margin-bottom: 50px;
            font-style: italic;
            max-width: 500px;
        }}
        
        .cover-divider {{
            width: 120px;
            height: 3px;
            background: {theme['accent']};
            margin: 40px auto;
        }}
        
        .cover-meta {{
            margin-top: 60px;
            font-size: 10pt;
            color: {theme['footer_text']};
            line-height: 2;
        }}
        
        .cover-meta span {{
            display: block;
        }}
        
        .cover-watermark {{
            position: absolute;
            bottom: 50px;
            right: 50px;
            opacity: 0.1;
            font-size: 80pt;
            font-weight: 700;
            color: {theme['primary']};
        }}
        
        /* ═══════════════════════════════════════════════════════════════════
           TABLE OF CONTENTS
           ═══════════════════════════════════════════════════════════════════ */
        .toc-page {{
            page-break-after: always;
        }}
        
        .toc-header {{
            font-family: {theme['heading_font']};
            font-size: 22pt;
            color: {theme['heading']};
            text-align: center;
            margin-bottom: 50px;
            padding-bottom: 20px;
            border-bottom: 2px solid {theme['heading']};
        }}
        
        .toc-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        
        .toc-item {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px dotted {theme['border']};
            font-size: 11pt;
        }}
        
        .toc-item-title {{
            color: {theme['text']};
            font-weight: 500;
        }}
        
        .toc-item-page {{
            color: {theme['footer_text']};
            font-family: {theme['code_font']};
        }}
        
        .toc-section {{
            padding-left: 20px;
            font-size: 10pt;
            color: {theme['subheading']};
        }}
        
        /* ═══════════════════════════════════════════════════════════════════
           MAIN CONTENT HEADINGS
           ═══════════════════════════════════════════════════════════════════ */
        .doc-header {{
            text-align: center;
            font-size: 14pt;
            font-weight: bold;
            margin-bottom: 50px;
            letter-spacing: 2px;
            color: {theme['heading']};
            border-bottom: 3px double {theme['heading']};
            padding-bottom: 15px;
            text-transform: uppercase;
        }}
        
        h1, .heading-1 {{
            font-family: {theme['heading_font']};
            font-size: {s['h1']};
            font-weight: 700;
            color: {theme['heading']};
            margin-top: 40px;
            margin-bottom: 20px;
            page-break-after: avoid;
            letter-spacing: 0.3px;
            border-left: 4px solid {theme['accent']};
            padding-left: 15px;
        }}
        
        h2, .heading-2 {{
            font-family: {theme['heading_font']};
            font-size: {s['h2']};
            font-weight: 600;
            color: {theme['subheading']};
            margin-top: 30px;
            margin-bottom: 15px;
            page-break-after: avoid;
        }}
        
        h3, .heading-3 {{
            font-family: {theme['heading_font']};
            font-size: {s['h3']};
            font-weight: 600;
            color: {theme['subheading']};
            margin-top: 24px;
            margin-bottom: 12px;
            page-break-after: avoid;
        }}
        
        /* ═══════════════════════════════════════════════════════════════════
           PARAGRAPHS & TEXT
           ═══════════════════════════════════════════════════════════════════ */
        p, .paragraph {{
            margin-top: 0;
            margin-bottom: 18px;
            text-align: justify;
            text-indent: 2em;
        }}
        
        p:first-of-type {{
            text-indent: 0;
        }}
        
        strong, b {{
            color: {theme['heading']};
            font-weight: 700;
        }}
        
        em, i {{
            font-style: italic;
            color: {theme['subheading']};
        }}
        
        code {{
            font-family: {theme['code_font']};
            background-color: {theme['code_bg']};
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
            color: {theme['accent']};
        }}
        
        /* ═══════════════════════════════════════════════════════════════════
           LISTS
           ═══════════════════════════════════════════════════════════════════ */
        ul, ol {{
            margin: 15px 0 25px 30px;
            padding: 0;
        }}
        
        ul li {{
            list-style-type: disc;
            margin-bottom: 10px;
            padding-left: 10px;
            text-align: left;
        }}
        
        ol li {{
            list-style-type: decimal;
            margin-bottom: 10px;
            padding-left: 10px;
        }}
        
        ul ul, ol ol, ul ol, ol ul {{
            margin-top: 8px;
            margin-bottom: 8px;
        }}
        
        /* ═══════════════════════════════════════════════════════════════════
           Q&A SECTIONS
           ═══════════════════════════════════════════════════════════════════ */
        .question {{
            font-weight: 700;
            color: {theme['heading']};
            margin-top: 30px;
            margin-bottom: 12px;
            padding: 15px 20px;
            background: linear-gradient(90deg, {theme['quote_bg']} 0%, transparent 100%);
            border-left: 4px solid {theme['accent']};
            page-break-after: avoid;
        }}
        
        .answer {{
            margin-bottom: 20px;
            padding-left: 20px;
            border-left: 2px dashed {theme['border']};
        }}
        
        /* ═══════════════════════════════════════════════════════════════════
           BLOCKQUOTES & NOTES
           ═══════════════════════════════════════════════════════════════════ */
        blockquote, .note {{
            margin: 25px 0;
            padding: 18px 25px;
            background-color: {theme['quote_bg']};
            border-left: 4px solid {theme['accent']};
            border-right: 1px solid {theme['border']};
            font-style: italic;
            page-break-inside: avoid;
        }}
        
        blockquote p {{
            margin-bottom: 0;
            text-indent: 0;
        }}
        
        .note-important {{
            background-color: {theme['highlight_bg']};
            border-left-color: {theme['gold']};
            border-left-width: 5px;
        }}
        
        .note::before {{
            content: "📌 ";
            font-style: normal;
        }}
        
        .note-important::before {{
            content: "⚠️ ";
        }}
        
        /* ═══════════════════════════════════════════════════════════════════
           CODE BLOCKS
           ═══════════════════════════════════════════════════════════════════ */
        pre, .code-block {{
            font-family: {theme['code_font']};
            background-color: {theme['code_bg']};
            padding: 20px;
            border: 1px solid {theme['border']};
            border-left: 4px solid {theme['secondary']};
            font-size: 10pt;
            margin: 25px 0;
            overflow-x: auto;
            page-break-inside: avoid;
            white-space: pre-wrap;
            line-height: 1.6;
        }}
        
        pre code {{
            background: none;
            padding: 0;
            color: {theme['text']};
        }}
        
        .code-language {{
            display: inline-block;
            background: {theme['secondary']};
            color: white;
            padding: 3px 10px;
            font-size: 9pt;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
            border-radius: 2px 2px 0 0;
        }}
        
        /* ═══════════════════════════════════════════════════════════════════
           TABLES
           ═══════════════════════════════════════════════════════════════════ */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 30px 0;
            font-size: 10pt;
            page-break-inside: avoid;
        }}
        
        th {{
            background: linear-gradient(180deg, {theme['primary']} 0%, {theme['secondary']} 100%);
            color: white;
            font-weight: 600;
            padding: 14px 16px;
            text-align: left;
            border: 1px solid {theme['secondary']};
            letter-spacing: 0.5px;
        }}
        
        td {{
            border: 1px solid {theme['border']};
            padding: 12px 14px;
            text-align: left;
            vertical-align: top;
        }}
        
        tr:nth-child(even) {{
            background-color: {theme['table_alt']};
        }}
        
        tr:hover {{
            background-color: {theme['quote_bg']};
        }}
        
        .table-caption {{
            font-size: 10pt;
            color: {theme['footer_text']};
            text-align: center;
            margin-top: -20px;
            margin-bottom: 20px;
            font-style: italic;
        }}
        
        /* ═══════════════════════════════════════════════════════════════════
           IMAGES & FIGURES
           ═══════════════════════════════════════════════════════════════════ */
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 25px auto;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .figure {{
            text-align: center;
            margin: 30px 0;
            page-break-inside: avoid;
        }}
        
        .figure-caption {{
            font-size: 10pt;
            color: {theme['footer_text']};
            margin-top: 12px;
            font-style: italic;
        }}
        
        /* ═══════════════════════════════════════════════════════════════════
           HIGHLIGHTS & SPECIAL ELEMENTS
           ═══════════════════════════════════════════════════════════════════ */
        .highlight {{
            background-color: {theme['highlight_bg']};
            padding: 2px 6px;
            border-radius: 2px;
        }}
        
        .key-point {{
            background: linear-gradient(90deg, {theme['highlight_bg']} 0%, transparent 100%);
            border-left: 3px solid {theme['gold']};
            padding: 15px 20px;
            margin: 25px 0;
            font-weight: 600;
        }}
        
        .divider {{
            border: none;
            border-top: 2px solid {theme['border']};
            margin: 40px 0;
        }}
        
        .section-number {{
            display: inline-block;
            background: {theme['primary']};
            color: white;
            width: 30px;
            height: 30px;
            line-height: 30px;
            text-align: center;
            border-radius: 50%;
            margin-right: 12px;
            font-size: 14pt;
            font-weight: 700;
        }}
        
        /* ═══════════════════════════════════════════════════════════════════
           RESPONSIVE ADJUSTMENTS
           ═══════════════════════════════════════════════════════════════════ */
        @media print {{
            body {{
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            
            .page-break {{
                page-break-before: always;
            }}
            
            .no-break {{
                page-break-inside: avoid;
            }}
        }}
        """
    
    def build_cover_page(self, doc):
        """Generate premium cover page HTML"""
        metadata = doc.get('metadata', {})
        theme = self.theme
        
        return f"""
        <div class="cover-page">
            <div class="cover-badge">Premium Edition</div>
            <div class="cover-title">{doc.get('title', 'DOCUMENT')}</div>
            <div class="cover-subtitle">{doc.get('subtitle', '')}</div>
            <div class="cover-divider"></div>
            <div class="cover-meta">
                {"<span><strong>Author:</strong> " + metadata.get('author', 'Not specified') + "</span>" if metadata.get('author') else ""}
                {"<span><strong>Date:</strong> " + metadata.get('date', datetime.now().strftime('%B %d, %Y')) + "</span>" if not metadata.get('date') else f"<span><strong>Date:</strong> {metadata.get('date')}</span>"}
                {"<span><strong>Version:</strong> " + metadata.get('version', '1.0') + "</span>" if metadata.get('version') else ""}
                {"<span><strong>Organization:</strong> " + metadata.get('institution', '') + "</span>" if metadata.get('institution') else ""}
            </div>
            <div class="cover-watermark">PREMIUM</div>
        </div>
        """
    
    def build_toc(self, doc):
        """Generate table of contents"""
        sections = doc.get('sections', [])
        headings = [(i, s) for i, s in enumerate(sections) if s.get('type') in ['heading', 'subheading']]
        
        if not headings:
            return ""
        
        html = '<div class="toc-page"><div class="toc-header">Table of Contents</div><ol class="toc-list">'
        
        for idx, section in headings:
            text = section.get('text', '')
            level = section.get('level', 1)
            
            if level > 1:
                html += f'<li class="toc-item toc-section"><span class="toc-item-title">{text}</span></li>'
            else:
                html += f'<li class="toc-item"><span class="toc-item-title">{text}</span></li>'
        
        html += '</ol></div>'
        return html
    
    def build_element(self, section, index):
        """Build HTML for a single section element"""
        stype = section.get('type', 'paragraph')
        text = section.get('text', '')
        items = section.get('items', [])
        theme = self.theme
        
        lang_badge = f'<div class="code-language">{section.get("language", "code")}</div>' if stype == 'code_block' else ''
        
        if stype == 'heading':
            level = section.get('level', 1)
            if level == 1:
                return f'<h1>{text}</h1>'
            else:
                return f'<h{level + 1}>{text}</h{level + 1}>'
        
        elif stype == 'subheading':
            return f'<h2>{text}</h2>'
        
        elif stype == 'paragraph':
            return f'<p>{text}</p>'
        
        elif stype == 'question':
            return f'<div class="question">{text}</div>'
        
        elif stype == 'answer':
            return f'<div class="answer"><p>{text}</p></div>'
        
        elif stype == 'blockquote':
            note_class = 'note-important' if section.get('note_type') == 'important' else ''
            return f'<blockquote class="note {note_class}"><p>{text}</p></blockquote>'
        
        elif stype == 'code_block':
            return f'{lang_badge}<pre><code>{text}</code></pre>'
        
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
                html += f'<p class="table-caption">{section.get("caption")}</p>'
            
            return html
        
        elif stype == 'divider':
            return '<hr class="divider">'
        
        elif stype == 'image':
            return f'''
            <div class="figure">
                <img src="{section.get('src', '')}" alt="{section.get('alt_text', '')}">
                <p class="figure-caption">{section.get('alt_text', '')}</p>
            </div>
            '''
        
        else:
            return f'<p>{text}</p>'
    
    def build(self, doc):
        """Build complete premium HTML document"""
        title = doc.get('title', 'PREMIUM DOCUMENT').upper()
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
        
        # Add main content header
        html += f'<div class="doc-header">{title}</div>'
        
        # Add all sections
        for idx, section in enumerate(doc.get('sections', [])):
            html += self.build_element(section, idx)
        
        html += """
</body>
</html>"""
        
        return html


# ══════════════════════════════════════════════════════════════════════════════
# ADVANCED PDF GENERATOR ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class PremiumPDFGenerator:
    """Premium PDF generation with advanced features"""
    
    def __init__(self, theme_name='classic', options=None):
        self.theme = PremiumTheme.get_theme(theme_name)
        self.options = options or {}
        self.parser = PremiumTextParser(self.theme)
        self.builder = PremiumHTMLBuilder(self.theme, self.options)
    
    def generate(self, text, output_path=None):
        """Generate premium PDF from text"""
        logger.info(f"📄 Generating premium PDF with {self.theme['name']} theme...")
        
        # Parse document structure
        doc = self.parser.parse(text)
        logger.info(f"✅ Document parsed: {len(doc.get('sections', []))} sections detected")
        
        # Build HTML
        html_content = self.builder.build(doc)
        
        # Generate PDF with WeasyPrint
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
            logger.info(f"✅ PDF saved to: {output_path}")
        
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
        "status": "✅ Premium PDF Generator is running",
        "version": "2.0",
        "gemini_available": GEMINI_AVAILABLE,
        "available_themes": ["classic", "corporate", "legal", "luxury", "scientific"],
        "endpoints": {
            "POST /generate_pdf": "Generate PDF from text",
            "POST /generate_premium_pdf": "Generate with advanced options",
            "POST /parse_document": "Parse document structure only",
            "GET /themes": "List available themes"
        }
    })

@app.route("/themes", methods=["GET"])
def list_themes():
    """List all available themes"""
    themes = {
        "classic": "Classic Academic - Traditional scholarly style",
        "corporate": "Modern Corporate - Professional business look",
        "legal": "Elegant Legal - Formal legal document style",
        "luxury": "Executive Luxury - Premium executive documents",
        "scientific": "Scientific Journal - Academic research style"
    }
    return jsonify({"themes": themes})

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
        
        # Get options
        filename = data.get("filename", "premium_document")
        theme_name = data.get("theme", "classic")
        options = data.get("options", {})
        
        logger.info(f"📝 Processing request for: {filename}")
        
        # Generate PDF
        generator = PremiumPDFGenerator(theme_name, options)
        pdf_bytes = generator.generate(bulk_text)
        
        # Prepare response
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_file.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_name = f"{filename}_{timestamp}.pdf"
        
        logger.info(f"✅ PDF generated successfully: {download_name}")
        
        return send_file(
            pdf_file,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=download_name
        )
        
    except Exception as e:
        logger.error(f"❌ Error generating PDF: {traceback.format_exc()}")
        return jsonify({
            "error": str(e),
            "message": "Failed to generate PDF",
            "details": traceback.format_exc()
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
            'page_numbers': data.get('page_numbers', True),
            'headers': data.get('headers', True),
            'quality': data.get('quality', 'high'),
            'header_text': data.get('header_text', 'PREMIUM DOCUMENT'),
            'footer_text': data.get('footer_text', 'Confidential'),
            'filename': data.get('filename', 'premium_document'),
            'custom_css': data.get('custom_css', '')
        }
        
        logger.info(f"✨ Processing premium request: {premium_options['filename']}")
        
        generator = PremiumPDFGenerator(premium_options['theme'], premium_options)
        pdf_bytes = generator.generate(bulk_text)
        
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_file.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return send_file(
            pdf_file,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{premium_options['filename']}_{timestamp}.pdf"
        )
        
    except Exception as e:
        logger.error(f"❌ Premium PDF generation failed: {traceback.format_exc()}")
        return jsonify({
            "error": str(e),
            "message": "Premium PDF generation failed"
        }), 500


@app.route("/parse_document", methods=["POST"])
def parse_document():
    """Parse document structure without generating PDF"""
    try:
        data = request.get_json()
        
        if not data or not data.get('bulk_text'):
            return jsonify({"error": "bulk_text is required"}), 400
        
        text = data['bulk_text']
        theme_name = data.get('theme', 'classic')
        
        parser = PremiumTextParser(PremiumTheme.get_theme(theme_name))
        doc = parser.parse(text)
        
        return jsonify({
            "success": True,
            "document": doc,
            "stats": {
                "total_sections": len(doc.get('sections', [])),
                "title": doc.get('title'),
                "doc_type": doc.get('doc_type'),
                "has_metadata": bool(doc.get('metadata'))
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Document parsing failed: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route("/preview_html", methods=["POST"])
def preview_html():
    """Generate HTML preview (without PDF conversion)"""
    try:
        data = request.get_json()
        
        if not data or not data.get('bulk_text'):
            return jsonify({"error": "bulk_text is required"}), 400
        
        text = data['bulk_text']
        theme_name = data.get('theme', 'classic')
        options = data.get('options', {})
        
        parser = PremiumTextParser(PremiumTheme.get_theme(theme_name))
        builder = PremiumHTMLBuilder(PremiumTheme.get_theme(theme_name), options)
        
        doc = parser.parse(text)
        html = builder.build(doc)
        
        return jsonify({
            "success": True,
            "html": html,
            "document": doc
        })
        
    except Exception as e:
        logger.error(f"❌ HTML preview generation failed: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


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
    
    logger.info("""
    ╔════════════════════════════════════════════════════════════════════════════╗
    ║                                                                            ║
    ║     ██████╗ ██╗   ██╗███╗   ██╗ ██████╗ ███████╗ ██████╗ ███╗   ██╗       ║
    ║     ██╔══██╗██║   ██║████╗  ██║██╔════╝ ██╔════╝██╔═══██╗████╗  ██║       ║
    ║     ██████╔╝██║   ██║██╔██╗ ██║██║  ███╗█████╗  ██║   ██║██╔██╗ ██║       ║
    ║     ██╔══██╗██║   ██║██║╚██╗██║██║   ██║██╔══╝  ██║   ██║██║╚██╗██║       ║
    ║     ██████╔╝╚██████╔╝██║ ╚████║╚██████╔╝███████╗╚██████╔╝██║ ╚████║       ║
    ║     ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝       ║
    ║                                                                            ║
    ║                    PREMIUM PDF GENERATOR v2.0                              ║
    ║                                                                            ║
    ╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    logger.info(f"🚀 Server starting on port {port}")
    logger.info(f"🔧 Debug mode: {debug}")
    logger.info(f"🤖 Gemini AI: {'Enabled' if GEMINI_AVAILABLE else 'Disabled (Manual parsing)'}")
    logger.info("📌 Available endpoints:")
    logger.info("   POST /generate_pdf - Generate basic premium PDF")
    logger.info("   POST /generate_premium_pdf - Generate with full options")
    logger.info("   POST /parse_document - Parse document structure")
    logger.info("   POST /preview_html - Preview HTML output")
    logger.info("   GET /themes - List available themes")
    
    app.run(host="0.0.0.0", port=port, debug=debug)
