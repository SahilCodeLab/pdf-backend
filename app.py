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

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# =========================
# Gemini Setup
# =========================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found")

client = genai.Client(api_key=GEMINI_API_KEY)
logger.info("✅ Gemini client ready")

# =========================
# PROFESSIONAL THEME (SINGLE CLEAN THEME)
# =========================
THEME = {
    "primary": "#1a1a1a",
    "secondary": "#333333",
    "accent": "#0066cc",
    "bg": "#ffffff",
    "text": "#1a1a1a",
    "heading": "#000000",
    "subheading": "#333333",
    "border": "#e0e0e0",
    "question_bg": "#f8f9fa",
    "question_border": "#0066cc",
    "footer_text": "#888888",
    "font_heading": "Georgia, 'Times New Roman', serif",
    "font_body": "'Segoe UI', Arial, sans-serif",
}

# =========================
# Health Check
# =========================
@app.route("/")
def home():
    return jsonify({"status": "OK", "message": "DocCraft AI Running"})

# =========================
# Gemini Parser (Simple - Only Detect Structure)
# =========================
def analyze_document(text):
    prompt = f"""Analyze this text and return ONLY valid JSON. No markdown, no explanation.

JSON format:
{{
  "title": "main title from text",
  "sections": [
    {{"type": "heading", "text": "..."}},
    {{"type": "subheading", "text": "..."}},
    {{"type": "paragraph", "text": "..."}},
    {{"type": "question", "text": "..."}},
    {{"type": "answer", "text": "..."}},
    {{"type": "bullet_list", "items": ["item1", "item2"]}},
    {{"type": "numbered_list", "items": ["item1", "item2"]}}
  ]
}}

Rules:
- Detect actual headings (short lines, important topics)
- Detect questions (ending with ? or starting with What/How/Why/When/Where)
- Detect bullet points (starting with -, *, •)
- Detect numbered lists (starting with 1., 2., etc)
- Everything else = paragraph
- NO extra text, NO summaries, ONLY the JSON

Text:
{text}"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=4096)
        )
        
        raw = response.text.strip()
        # Clean JSON
        for prefix in ["```json", "```"]:
            if raw.startswith(prefix):
                raw = raw[len(prefix):]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        raise

# =========================
# Fallback Parser (No Gemini)
# =========================
def manual_parse(text):
    lines = text.strip().split('\n')
    sections = []
    title = ""
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # First non-empty line = title
        if not title and len(line) < 100:
            title = line
            continue
        
        # Heading detection
        if len(line) < 80 and (line.isupper() or 
            line.startswith(('Chapter', 'Part', 'Section', 'Unit')) or
            (i > 0 and not lines[i-1].strip() and not lines[i+1].strip() if i+1 < len(lines) else True)):
            sections.append({"type": "heading", "text": line})
        
        # Question detection
        elif line.endswith('?') or line.startswith(('What ', 'How ', 'Why ', 'When ', 'Where ', 'Who ')):
            sections.append({"type": "question", "text": line})
        
        # Bullet points
        elif line.startswith(('- ', '* ', '• ', '→ ', '▸ ')):
            sections.append({"type": "bullet_list", "items": [line[2:]]})
        
        # Numbered list
        elif line[0].isdigit() and '. ' in line[:5]:
            sections.append({"type": "numbered_list", "items": [line.split('. ', 1)[1]]})
        
        # Paragraph
        else:
            sections.append({"type": "paragraph", "text": line})
    
    return {
        "title": title or "Document",
        "sections": sections or [{"type": "paragraph", "text": text}]
    }

# =========================
# BUILD CLEAN PREMIUM HTML
# =========================
def build_html(doc):
    title = doc.get("title", "Document")
    sections = doc.get("sections", [])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
    @page {{
        size: A4;
        margin: 2.2cm 2cm 2.5cm 2cm;
        @bottom-center {{
            content: counter(page);
            font-size: 9px;
            color: {THEME['footer_text']};
            font-family: {THEME['font_body']};
        }}
    }}
    
    @page :first {{
        @bottom-center {{
            content: none;
        }}
    }}
    
    body {{
        font-family: {THEME['font_body']};
        color: {THEME['text']};
        line-height: 1.7;
        font-size: 11.5px;
    }}
    
    /* COVER PAGE */
    .cover {{
        text-align: center;
        padding-top: 35%;
        page-break-after: always;
    }}
    
    .cover-title {{
        font-family: {THEME['font_heading']};
        font-size: 36px;
        font-weight: bold;
        color: {THEME['heading']};
        letter-spacing: 1px;
        margin-bottom: 20px;
    }}
    
    .cover-line {{
        width: 60px;
        height: 2px;
        background: {THEME['accent']};
        margin: 0 auto 20px auto;
    }}
    
    .cover-date {{
        font-size: 12px;
        color: {THEME['footer_text']};
        letter-spacing: 2px;
        text-transform: uppercase;
    }}
    
    /* HEADINGS */
    h1 {{
        font-family: {THEME['font_heading']};
        font-size: 22px;
        font-weight: bold;
        color: {THEME['heading']};
        margin-top: 35px;
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 1px solid {THEME['border']};
        page-break-after: avoid;
    }}
    
    h2 {{
        font-family: {THEME['font_heading']};
        font-size: 17px;
        font-weight: bold;
        color: {THEME['subheading']};
        margin-top: 25px;
        margin-bottom: 10px;
        page-break-after: avoid;
    }}
    
    /* PARAGRAPH */
    p {{
        margin-bottom: 10px;
        text-align: justify;
    }}
    
    /* QUESTION & ANSWER */
    .question {{
        font-weight: 600;
        color: {THEME['heading']};
        margin-top: 20px;
        margin-bottom: 5px;
        font-size: 12px;
    }}
    
    .answer {{
        margin-left: 0;
        margin-bottom: 15px;
        padding-left: 0;
    }}
    
    /* LISTS */
    ul {{
        margin: 8px 0 12px 20px;
        padding: 0;
        list-style: none;
    }}
    
    ul li {{
        position: relative;
        padding-left: 15px;
        margin-bottom: 5px;
    }}
    
    ul li::before {{
        content: "—";
        position: absolute;
        left: 0;
        color: {THEME['accent']};
    }}
    
    ol {{
        margin: 8px 0 12px 20px;
        padding: 0;
    }}
    
    ol li {{
        margin-bottom: 5px;
    }}
    
    /* DIVIDER */
    .divider {{
        text-align: center;
        margin: 25px 0;
        color: {THEME['border']};
    }}
</style>
</head>
<body>
<div class="cover">
    <div class="cover-title">{title}</div>
    <div class="cover-line"></div>
    <div class="cover-date">{datetime.now().strftime('%B %d, %Y')}</div>
</div>
"""
    
    # CONTENT PAGES
    for section in sections:
        stype = section.get("type", "paragraph")
        text = section.get("text", "")
        items = section.get("items", [])
        
        if stype == "heading":
            html += f'<h1>{text}</h1>'
        elif stype == "subheading":
            html += f'<h2>{text}</h2>'
        elif stype == "question":
            html += f'<p class="question">{text}</p>'
        elif stype == "answer":
            html += f'<p class="answer">{text}</p>'
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
        elif stype == "divider":
            html += '<div class="divider">· · ·</div>'
        else:
            html += f'<p>{text}</p>'
    
    html += """
</body>
</html>"""
    
    return html

# =========================
# PDF Generation
# =========================
@app.route("/generate_pdf", methods=["POST"])
def generate_pdf():
    try:
        data = request.get_json()
        bulk_text = data.get("bulk_text", "")
        filename = data.get("filename", "document")
        
        if not bulk_text.strip():
            return jsonify({"error": "bulk_text is empty"}), 400
        
        # Analyze text
        try:
            doc = analyze_document(bulk_text)
        except Exception as e:
            logger.warning(f"Gemini failed, using manual: {e}")
            doc = manual_parse(bulk_text)
        
        # Build HTML & PDF
        html_content = build_html(doc)
        pdf_bytes = HTML(string=html_content).write_pdf()
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
        logger.error(f"Error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

# =========================
# Test PDF
# =========================
@app.route("/test_pdf", methods=["GET"])
def test_pdf():
    doc = {
        "title": "Sample Document",
        "sections": [
            {"type": "heading", "text": "Introduction"},
            {"type": "paragraph", "text": "This is a sample paragraph showing the clean professional formatting."},
            {"type": "subheading", "text": "Key Features"},
            {"type": "bullet_list", "items": ["Clean design", "Professional layout", "Auto page breaks", "Smart detection"]},
            {"type": "heading", "text": "Questions & Answers"},
            {"type": "question", "text": "What makes a document professional?"},
            {"type": "answer", "text": "A professional document has consistent formatting, clear hierarchy, and proper spacing."},
        ]
    }
    
    html_content = build_html(doc)
    pdf_bytes = HTML(string=html_content).write_pdf()
    pdf_file = io.BytesIO(pdf_bytes)
    pdf_file.seek(0)
    
    return send_file(pdf_file, mimetype="application/pdf", as_attachment=True, download_name="sample.pdf")

# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
