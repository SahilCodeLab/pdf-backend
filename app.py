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
# PREMIUM ACADEMIC PUBLISHING THEME
# =========================
THEME = {
    "text": "#111111",
    "heading": "#000000",
    "subheading": "#222222",
    "border": "#cccccc",
    "footer_text": "#555555",
    "code_bg": "#f8f9fa",
    "quote_bg": "#fcfcfc",
    "font_family": "Georgia, 'Times New Roman', serif",
}

# =========================
# Health Check
# =========================
@app.route("/")
def home():
    return jsonify({"status": "OK", "message": "DocCraft AI Engine Active"})

# =========================
# Advanced Gemini Parser (Zero Data Loss)
# =========================
def analyze_document(text):
    prompt = f"""You are an expert document typesetter. Convert the following raw text into a highly accurate structured JSON format. 
CRITICAL RULE: You must preserve EVERY SINGLE WORD, sentence, and data point. Do NOT summarize, shorten, or paraphrase anything.

Analyze the structure and return ONLY a valid JSON object. No markdown wrapping.

JSON Schema:
{{
  "title": "Exact main title of the text",
  "sections": [
    {{
      "type": "heading" | "subheading" | "paragraph" | "question" | "answer" | "blockquote" | "code_block" | "table" | "bullet_list" | "numbered_list",
      "text": "The full exact text (applicable for standard types)",
      "items": ["Exact text of item 1", "Exact text of item 2"], // Only for bullet_list or numbered_list
      "headers": ["Col 1", "Col 2"], // Only for table
      "rows": [["Row 1 Col 1", "Row 1 Col 2"]] // Only for table
    }}
  ]
}}

Formatting Guidelines:
1. Retain inner emphasis: If specific words inside a paragraph are bold or crucial, wrap them in standard HTML tags like <strong>word</strong> or <em>word</em> inside the JSON text strings.
2. If text contains a Q&A format, cleanly separate them into 'question' and 'answer' types.
3. If it contains data comparisons, construct a proper 'table'.

Text to convert:
{text}"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0, # Lowest temperature for accurate extraction
                max_output_tokens=8192,
                response_mime_type="application/json" # Enforces pure JSON output safely
            )
        )
        
        return json.loads(response.text.strip())
    except Exception as e:
        logger.error(f"Gemini processing error, trying manual fallback: {e}")
        raise

# =========================
# Robust Manual Fallback Parser
# =========================
def manual_parse(text):
    lines = text.strip().split('\n')
    sections = []
    title = ""
    
    current_list = None
    list_type = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        if not title and len(line) < 100:
            title = line
            continue
            
        if current_list and not line.startswith(('-', '*', '•', '→', '1.', '2.', '3.')):
            sections.append({"type": list_type, "items": current_list})
            current_list = None
            list_type = None

        if len(line) < 90 and (line.isupper() or line.startswith(('Chapter', 'Part', 'Section', 'Unit', '6.', '7.', '8.', '9.'))):
            sections.append({"type": "heading", "text": line})
        elif line.endswith('?') or line.startswith(('What ', 'How ', 'Why ', 'When ', 'Where ', 'Who ', 'Explain ')):
            sections.append({"type": "question", "text": line})
        elif line.startswith(('- ', '* ', '• ', '→ ')):
            if not current_list or list_type != "bullet_list":
                if current_list: sections.append({"type": list_type, "items": current_list})
                current_list = []
                list_type = "bullet_list"
            current_list.append(line[2:].strip())
        elif line[0].isdigit() and '. ' in line[:5]:
            clean_item = line.split('. ', 1)[1].strip()
            if not current_list or list_type != "numbered_list":
                if current_list: sections.append({"type": list_type, "items": current_list})
                current_list = []
                list_type = "numbered_list"
            current_list.append(clean_item)
        elif line.startswith(('Note:', 'Important:', '>')):
            sections.append({"type": "blockquote", "text": line.replace('>', '').strip()})
        else:
            sections.append({"type": "paragraph", "text": line})
            
    if current_list:
        sections.append({"type": list_type, "items": current_list})
        
    return {
        "title": title or "Document Output",
        "sections": sections or [{"type": "paragraph", "text": text}]
    }

# =========================
# ADVANCED TYPESETTING HTML BUILDER
# =========================
def build_html(doc):
    title = doc.get("title", "DOCUMENT").upper()
    sections = doc.get("sections", [])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
    @page {{
        size: A4;
        margin: 3cm 2.2cm 2.8cm 2.2cm;
        
        @top-center {{
            content: "{title}";
            font-size: 9px;
            color: {THEME['footer_text']};
            font-family: {THEME['font_family']};
            letter-spacing: 1px;
            border-bottom: 0.5px solid {THEME['border']};
            padding-bottom: 8px;
            width: 100%;
        }}
        
        @bottom-right {{
            content: "Page " counter(page) " of " counter(pages);
            font-size: 10px;
            color: {THEME['footer_text']};
            font-family: {THEME['font_family']};
        }}
    }}
    
    body {{
        font-family: {THEME['font_family']};
        color: {THEME['text']};
        line-height: 1.7;
        font-size: 13px;
    }}
    
    .doc-main-header {{
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 40px;
        letter-spacing: 1px;
        color: {THEME['heading']};
        border-bottom: 2px solid #000000;
        padding-bottom: 10px;
    }}
    
    h1 {{
        font-size: 14.5px;
        font-weight: bold;
        color: {THEME['heading']};
        margin-top: 32px;
        margin-bottom: 14px;
        page-break-after: avoid;
        letter-spacing: 0.3px;
    }}
    
    h2 {{
        font-size: 13.5px;
        font-weight: bold;
        color: {THEME['subheading']};
        margin-top: 24px;
        margin-bottom: 12px;
        page-break-after: avoid;
    }}
    
    p {{
        margin-top: 0;
        margin-bottom: 16px;
        text-align: justify;
    }}
    
    .question {{
        font-weight: bold;
        color: {THEME['heading']};
        margin-top: 24px;
        margin-bottom: 8px;
    }}
    
    .answer {{
        margin-bottom: 16px;
    }}
    
    ul, ol {{
        margin: 5px 0 16px 24px;
        padding: 0;
    }}
    
    ul li, ol li {{
        margin-bottom: 6px;
        text-align: justify;
    }}
    
    blockquote {{
        margin: 18px 0;
        padding: 12px 22px;
        background-color: {THEME['quote_bg']};
        border-left: 3px solid #111111;
        font-style: italic;
    }}
    
    pre {{
        font-family: 'Courier New', Courier, monospace;
        background-color: {THEME['code_bg']};
        padding: 12px;
        border: 1px solid {THEME['border']};
        font-size: 11.5px;
        margin-bottom: 16px;
    }}
    
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 22px 0;
        font-size: 12px;
        page-break-inside: avoid;
    }}
    
    th, td {{
        border: 1px solid {THEME['border']};
        padding: 9px 12px;
        text-align: left;
    }}
    
    th {{
        background-color: #f5f5f5;
        font-weight: bold;
        color: {THEME['heading']};
    }}
    
    tr:nth-child(even) {{
        background-color: #fcfcfc;
    }}
</style>
</head>
<body>
    <div class="doc-main-header">{title}</div>
"""
    
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
        elif stype == "blockquote":
            html += f'blockquote><p>{text}</p></blockquote>'
        elif stype == "code_block":
            html += f'<pre><code>{text}</code></pre>'
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
        elif stype == "table":
            html += '<table><thead><tr>'
            for header in section.get("headers", []):
                html += f'<th>{header}</th>'
            html += '</tr></thead><tbody>'
            for row in section.get("rows", []):
                html += '<tr>'
                for cell in row:
                    html += f'<td>{cell}</td>'
                html += '</tr>'
            html += '</tbody></table>'
        else:
            html += f'<p>{text}</p>'
            
    html += """
</body>
</html>"""
    
    return html

# =========================
# API Endpoint
# =========================
@app.route("/generate_pdf", methods=["POST"])
def generate_pdf():
    try:
        data = request.get_json()
        bulk_text = data.get("bulk_text", "")
        filename = data.get("filename", "academic_document")
        
        if not bulk_text.strip():
            return jsonify({"error": "bulk_text content is missing"}), 400
        
        try:
            doc = analyze_document(bulk_text)
        except Exception as e:
            logger.warning(f"Advanced parse failed, initializing manual fallback: {e}")
            doc = manual_parse(bulk_text)
        
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
        logger.error(f"Critical Error Encountered: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
