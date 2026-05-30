from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from weasyprint import HTML
from google import genai
from google.genai import types
import os
import io
import json
from datetime import datetime
from dotenv import load_dotenv
import logging
import traceback

# Load environment variables
load_dotenv()

# ------------------------------------------------------------
# LOGGER SETUP
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# =========================
# Gemini Setup (NEW SDK)
# =========================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("❌ GEMINI_API_KEY not found")
    raise ValueError("❌ GEMINI_API_KEY not found")

# New SDK client
client = genai.Client(api_key=GEMINI_API_KEY)
logger.info("✅ Gemini client initialized")

# =========================
# Premium Themes
# =========================
THEMES = {
    "modern_professional": {
        "name": "Modern Professional",
        "primary": "#2563eb",
        "secondary": "#3b82f6",
        "accent": "#f59e0b",
        "bg": "#ffffff",
        "text": "#1e293b",
        "heading": "#1e40af",
        "subheading": "#334155",
        "border": "#e2e8f0",
        "cover_gradient_start": "#2563eb",
        "cover_gradient_end": "#7c3aed",
        "question_bg": "#eff6ff",
        "question_border": "#3b82f6",
        "footer_text": "#94a3b8",
        "font_heading": "Georgia, serif",
        "font_body": "Segoe UI, Arial, sans-serif",
        "watermark_opacity": "0.03"
    },
    "corporate_premium": {
        "name": "Corporate Premium",
        "primary": "#1e40af",
        "secondary": "#3b82f6",
        "accent": "#dc2626",
        "bg": "#ffffff",
        "text": "#111827",
        "heading": "#1e3a8a",
        "subheading": "#374151",
        "border": "#e5e7eb",
        "cover_gradient_start": "#1e40af",
        "cover_gradient_end": "#312e81",
        "question_bg": "#f8fafc",
        "question_border": "#1e40af",
        "footer_text": "#6b7280",
        "font_heading": "Cambria, serif",
        "font_body": "Calibri, sans-serif",
        "watermark_opacity": "0.04"
    },
    "elegant_minimal": {
        "name": "Elegant Minimal",
        "primary": "#059669",
        "secondary": "#34d399",
        "accent": "#f59e0b",
        "bg": "#ffffff",
        "text": "#1f2937",
        "heading": "#065f46",
        "subheading": "#374151",
        "border": "#d1d5db",
        "cover_gradient_start": "#059669",
        "cover_gradient_end": "#34d399",
        "question_bg": "#ecfdf5",
        "question_border": "#059669",
        "footer_text": "#9ca3af",
        "font_heading": "Playfair Display, serif",
        "font_body": "Lato, sans-serif",
        "watermark_opacity": "0.02"
    },
    "dark_executive": {
        "name": "Dark Executive",
        "primary": "#f59e0b",
        "secondary": "#d97706",
        "accent": "#3b82f6",
        "bg": "#0f172a",
        "text": "#e2e8f0",
        "heading": "#fbbf24",
        "subheading": "#cbd5e1",
        "border": "#334155",
        "cover_gradient_start": "#f59e0b",
        "cover_gradient_end": "#ef4444",
        "question_bg": "#1e293b",
        "question_border": "#f59e0b",
        "footer_text": "#64748b",
        "font_heading": "Trebuchet MS, sans-serif",
        "font_body": "Verdana, sans-serif",
        "watermark_opacity": "0.05"
    },
    "creative_vibrant": {
        "name": "Creative Vibrant",
        "primary": "#7c3aed",
        "secondary": "#a78bfa",
        "accent": "#f97316",
        "bg": "#faf5ff",
        "text": "#4c1d95",
        "heading": "#5b21b6",
        "subheading": "#6d28d9",
        "border": "#ddd6fe",
        "cover_gradient_start": "#7c3aed",
        "cover_gradient_end": "#ec4899",
        "question_bg": "#f5f3ff",
        "question_border": "#7c3aed",
        "footer_text": "#a78bfa",
        "font_heading": "Montserrat, sans-serif",
        "font_body": "Open Sans, sans-serif",
        "watermark_opacity": "0.03"
    }
}

# =========================
# Health Check
# =========================
@app.route("/")
def home():
    return jsonify({
        "status": "OK",
        "message": "DocCraft AI Premium Backend Running",
        "themes_available": list(THEMES.keys()),
        "version": "3.0.0",
        "sdk": "google-genai (new)"
    })

# =========================
# Get Themes
# =========================
@app.route("/themes", methods=["GET"])
def get_themes():
    themes_info = {}
    for theme_id, theme in THEMES.items():
        themes_info[theme_id] = {
            "name": theme["name"],
            "primary_color": theme["primary"],
            "preview_colors": [theme["primary"], theme["secondary"], theme["accent"]]
        }
    return jsonify(themes_info)

# =========================
# Analyze Document (NEW SDK)
# =========================
def analyze_document(text):
    logger.info(f"📝 Analyzing text ({len(text)} chars)")
    
    prompt = f"""You are a professional document structure parser.

Analyze this text and return ONLY valid JSON. No markdown, no code blocks.

Schema:
{{
  "document_type": "",
  "title": "",
  "author": "",
  "sections": [
    {{
      "type": "",
      "text": "",
      "items": []
    }}
  ],
  "metadata": {{
    "keywords": [],
    "reading_time_minutes": 0,
    "complexity": "basic"
  }}
}}

Section types: heading, subheading, paragraph, bullet_list, numbered_list, question, answer, quote, callout, divider

Document types: academic_notes, assignment, business_report, meeting_notes, research_paper, resume, blog_article, whitepaper, general_document

Text:
{text}"""
    
    try:
        logger.info("🤖 Calling Gemini API (new SDK)...")
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=4096,
            )
        )
        
        raw = response.text.strip()
        logger.info(f"📄 Response received ({len(raw)} chars)")
        
        # Clean any markdown
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        
        parsed = json.loads(raw)
        logger.info(f"✅ Parsed: {parsed.get('document_type')}, {len(parsed.get('sections', []))} sections")
        return parsed
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parse error: {e}")
        logger.error(f"Raw: {raw[:500]}")
        raise
    except Exception as e:
        logger.error(f"❌ Gemini error: {e}")
        raise

# =========================
# Manual Parse (Fallback)
# =========================
def manual_parse_document(text, title="Document"):
    """Fallback parser agar Gemini fail ho jaye"""
    lines = text.strip().split('\n')
    sections = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if len(line) < 50 and (line.isupper() or line.startswith('Chapter')):
            sections.append({"type": "heading", "text": line})
        elif line.endswith('?') or line.startswith(('What', 'How', 'Why', 'When', 'Where')):
            sections.append({"type": "question", "text": line})
        elif line.startswith(('- ', '* ', '• ')):
            sections.append({"type": "bullet_list", "items": [line[2:]]})
        elif line[0].isdigit() and '. ' in line[:4]:
            sections.append({"type": "numbered_list", "items": [line.split('. ', 1)[1]]})
        else:
            sections.append({"type": "paragraph", "text": line})
    
    word_count = len(text.split())
    
    return {
        "document_type": "general_document",
        "title": title,
        "author": "",
        "sections": sections or [{"type": "paragraph", "text": text}],
        "metadata": {
            "keywords": [],
            "reading_time_minutes": max(1, word_count // 200),
            "complexity": "basic"
        }
    }

# =========================
# Cover Page
# =========================
def generate_cover_page(title, doc_type, theme, author=""):
    return f"""
    <div style="page-break-after:always; height:100vh; display:flex; align-items:center; justify-content:center; 
                background:linear-gradient(135deg, {theme['cover_gradient_start']}15, {theme['cover_gradient_end']}15); position:relative;">
        <div style="position:absolute; top:0; left:0; right:0; height:6px; 
                    background:linear-gradient(90deg, {theme['cover_gradient_start']}, {theme['cover_gradient_end']});"></div>
        <div style="text-align:center; z-index:2; max-width:80%;">
            <div style="font-size:13px; text-transform:uppercase; letter-spacing:6px; color:{theme['primary']}; 
                        margin-bottom:30px; font-family:{theme['font_body']};">
                {doc_type.replace('_', ' ').title()}
            </div>
            <h1 style="font-size:42px; font-family:{theme['font_heading']}; color:{theme['heading']}; 
                       margin-bottom:30px; line-height:1.2; font-weight:bold;">{title}</h1>
            <div style="width:80px; height:3px; background:linear-gradient(90deg, {theme['cover_gradient_start']}, 
                        {theme['cover_gradient_end']}); margin:30px auto;"></div>
            <div style="font-size:12px; color:{theme['footer_text']}; font-family:{theme['font_body']}; margin-top:30px;">
                <p style="margin:5px 0;">{author if author else ''}</p>
                <p style="margin:5px 0;">{datetime.now().strftime('%B %d, %Y')}</p>
                <p style="margin:10px 0; font-weight:bold; color:{theme['primary']};">Powered by DocCraft AI</p>
            </div>
        </div>
    </div>
    """

# =========================
# Build HTML
# =========================
def build_premium_html(doc, theme_id="modern_professional"):
    theme = THEMES.get(theme_id, THEMES["modern_professional"])
    title = doc.get("title", "Document")
    document_type = doc.get("document_type", "general_document")
    author = doc.get("author", "")
    sections = doc.get("sections", [])
    metadata = doc.get("metadata", {})
    keywords = metadata.get("keywords", [])
    reading_time = metadata.get("reading_time_minutes", 0)
    complexity = metadata.get("complexity", "basic")
    
    cover = generate_cover_page(title, document_type, theme, author)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title} - DocCraft AI</title>
    <style>
        @page {{ size:A4; margin:1.8cm; @bottom-center {{ content:"Page " counter(page); font-size:9px; color:{theme['footer_text']}; }} }}
        @page :first {{ margin:0; @bottom-center {{ content:none; }} }}
        body {{ font-family:{theme['font_body']}; color:{theme['text']}; line-height:1.8; background:{theme['bg']}; font-size:12px; }}
        h1 {{ font-family:{theme['font_heading']}; font-size:26px; color:{theme['heading']}; margin-top:30px; margin-bottom:15px; border-bottom:2px solid {theme['primary']}; padding-bottom:10px; }}
        h2 {{ font-family:{theme['font_heading']}; font-size:20px; color:{theme['heading']}; margin-top:25px; margin-bottom:12px; }}
        p {{ font-size:12px; margin-bottom:12px; text-align:justify; }}
        .quote-box {{ background:linear-gradient(135deg, {theme['primary']}08, {theme['secondary']}08); border-left:4px solid {theme['primary']}; padding:15px; margin:20px 0; font-style:italic; border-radius:0 8px 8px 0; }}
        .question-box {{ background:{theme['question_bg']}; border-left:4px solid {theme['question_border']}; padding:12px; margin:20px 0; font-weight:600; border-radius:0 6px 6px 0; }}
        .answer-box {{ margin:10px 0 20px 20px; padding:10px; border-bottom:1px dashed {theme['border']}; }}
        ul, ol {{ margin:10px 0 10px 25px; }}
        li {{ margin:6px 0; font-size:12px; }}
        ul li {{ list-style-type:none; position:relative; }}
        ul li::before {{ content:"▸"; color:{theme['primary']}; position:absolute; left:-20px; font-size:10px; }}
        ol {{ counter-reset:item; }}
        ol li {{ counter-increment:item; list-style-type:none; position:relative; }}
        ol li::before {{ content:counter(item); background:{theme['primary']}; color:white; border-radius:50%; width:18px; height:18px; display:inline-flex; align-items:center; justify-content:center; font-size:9px; position:absolute; left:-28px; top:2px; }}
        .divider {{ text-align:center; margin:30px 0; color:{theme['primary']}; font-size:20px; letter-spacing:15px; }}
        .info-bar {{ display:flex; justify-content:space-between; background:{theme['bg']}; border:1px solid {theme['border']}; border-radius:8px; padding:12px; margin:20px 0; font-size:11px; }}
        .footer-note {{ margin-top:40px; padding-top:15px; border-top:2px solid {theme['border']}; text-align:center; color:{theme['footer_text']}; font-size:10px; }}
    </style>
</head>
<body>
    {cover}
    <div class="info-bar">
        <span>📄 {document_type.replace('_', ' ').title()}</span>
        <span>⏱️ {reading_time} min read</span>
        <span>📅 {datetime.now().strftime('%b %d, %Y')}</span>
        <span style="background:{theme['primary']}; color:white; padding:3px 12px; border-radius:20px; font-size:10px; font-weight:bold;">{complexity.upper()}</span>
    </div>
"""
    
    # Keywords
    if keywords:
        html += '<div style="margin:15px 0;">'
        for kw in keywords[:8]:
            html += f'<span style="display:inline-block; background:{theme["primary"]}15; color:{theme["primary"]}; padding:2px 10px; border-radius:12px; font-size:10px; margin:2px;">#{kw}</span>'
        html += '</div>'
    
    # Sections
    for section in sections:
        stype = section.get("type", "paragraph")
        text = section.get("text", "")
        items = section.get("items", [])
        
        if stype == "heading":
            html += f'<h1>{text}</h1>'
        elif stype == "subheading":
            html += f'<h2>{text}</h2>'
        elif stype == "question":
            html += f'<div class="question-box">❓ {text}</div>'
        elif stype == "answer":
            html += f'<div class="answer-box">{text}</div>'
        elif stype == "quote":
            html += f'<div class="quote-box">💬 {text}</div>'
        elif stype == "callout":
            html += f'<div style="background:{theme["primary"]}10; border:2px solid {theme["primary"]}30; border-radius:10px; padding:15px; margin:20px 0;">📌 {text}</div>'
        elif stype == "divider":
            html += f'<div class="divider">✦ ✦ ✦</div>'
        elif stype == "bullet_list":
            html += '<ul>'
            for item in items:
                html += f'<li>{item}</li>'
            html += '</ul>'
        elif stype == "numbered_list":
            html += '<ol>'
            for item in items:
                html += f'<li>{item}</li>'
            html += '</ol>'
        else:
            html += f'<p>{text}</p>'
    
    # Footer
    html += f"""
    <div class="footer-note">
        <p>© {datetime.now().year} DocCraft AI • Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        <p>Theme: {theme['name']} • Premium Document Generation</p>
    </div>
</body>
</html>"""
    
    return html

# =========================
# Generate PDF Endpoint
# =========================
@app.route("/generate_pdf", methods=["POST"])
def generate_pdf():
    try:
        data = request.get_json()
        logger.info(f"📥 Request: {list(data.keys()) if data else 'None'}")
        
        subject = data.get("subject", "Document")
        filename = data.get("filename", "document")
        bulk_text = data.get("bulk_text", "")
        theme_id = data.get("theme", "modern_professional")
        author = data.get("author", "")
        
        if not bulk_text.strip():
            return jsonify({"error": "bulk_text is empty"}), 400
        
        if theme_id not in THEMES:
            theme_id = "modern_professional"
        
        # Step 1: Analyze (with fallback)
        try:
            doc = analyze_document(bulk_text)
        except Exception as e:
            logger.warning(f"Gemini failed, using manual parse: {e}")
            doc = manual_parse_document(bulk_text, subject)
        
        if not doc.get("title"):
            doc["title"] = subject
        if author:
            doc["author"] = author
        
        # Step 2: Build HTML
        html_content = build_premium_html(doc, theme_id)
        
        # Step 3: Generate PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_file.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_name = f"{filename}_{timestamp}_{theme_id}.pdf"
        
        logger.info(f"✅ PDF generated: {download_name} ({len(pdf_bytes)} bytes)")
        
        return send_file(
            pdf_file,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=download_name
        )
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500

# =========================
# Test Endpoint
# =========================
@app.route("/test_pdf", methods=["GET"])
def test_pdf():
    try:
        doc = {
            "document_type": "test",
            "title": "Test Document",
            "author": "DocCraft AI",
            "sections": [
                {"type": "heading", "text": "Welcome to DocCraft AI"},
                {"type": "paragraph", "text": "This test confirms PDF generation is working."},
                {"type": "subheading", "text": "Available Themes"},
                {"type": "bullet_list", "items": ["Modern Professional", "Corporate Premium", "Elegant Minimal", "Dark Executive", "Creative Vibrant"]},
                {"type": "divider", "text": ""},
                {"type": "quote", "text": "Simplicity is the ultimate sophistication."}
            ],
            "metadata": {"keywords": ["test"], "reading_time_minutes": 1, "complexity": "basic"}
        }
        
        html_content = build_premium_html(doc, "modern_professional")
        pdf_bytes = HTML(string=html_content).write_pdf()
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_file.seek(0)
        
        return send_file(
            pdf_file,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="test_document.pdf"
        )
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
        return jsonify({"error": str(e)}), 500

# =========================
# Preview Endpoint
# =========================
@app.route("/preview", methods=["POST"])
def preview():
    try:
        data = request.get_json()
        bulk_text = data.get("bulk_text", "")
        theme_id = data.get("theme", "modern_professional")
        
        if not bulk_text.strip():
            return jsonify({"error": "Empty content"}), 400
        
        try:
            doc = analyze_document(bulk_text)
        except:
            doc = manual_parse_document(bulk_text)
        
        return jsonify({
            "document_type": doc.get("document_type"),
            "title": doc.get("title"),
            "sections_count": len(doc.get("sections", [])),
            "metadata": doc.get("metadata", {}),
            "theme": THEMES.get(theme_id, THEMES["modern_professional"])["name"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================
# Run
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Starting DocCraft AI v3.0 on port {port}")
    app.run(host="0.0.0.0", port=port)
