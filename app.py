from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from weasyprint import HTML
import google.generativeai as genai
import os
import io
import json
from datetime import datetime
import base64
from PIL import Image, ImageDraw, ImageFont
import textwrap

app = Flask(__name__)
CORS(app)

# =========================
# Gemini Setup
# =========================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

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
        "version": "2.0.0"
    })

# =========================
# Theme Endpoint
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
# Gemini Parser
# =========================
def analyze_document(text):
    prompt = f"""
You are a professional document structure parser for premium document generation.

Analyze the following text and return ONLY valid JSON.

Schema:
{{
  "document_type": "",
  "title": "",
  "author": "",
  "sections": [
    {{
      "type": "",
      "text": "",
      "items": [],
      "level": 1
    }}
  ],
  "metadata": {{
    "keywords": [],
    "reading_time_minutes": 0,
    "complexity": "basic|intermediate|advanced"
  }}
}}

Allowed section types: heading, subheading, paragraph, bullet_list, numbered_list, question, answer, quote, callout, divider

Document types: academic_notes, assignment, business_report, meeting_notes, research_paper, resume, blog_article, whitepaper, general_document

Text:
{text}
"""
    
    response = model.generate_content(prompt)
    raw = response.text.strip()
    
    # Clean JSON response
    if raw.startswith("```json"):
        raw = raw.replace("```json", "").replace("```", "")
    elif raw.startswith("```"):
        raw = raw.replace("```", "")
    
    return json.loads(raw)

# =========================
# Generate Watermark SVG
# =========================
def generate_watermark_svg(theme):
    watermark_text = "DocCraft AI"
    opacity = theme.get("watermark_opacity", "0.03")
    
    return f"""
    <div style="
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-25deg);
        font-size: 120px;
        font-weight: bold;
        color: {theme['primary']};
        opacity: {opacity};
        pointer-events: none;
        white-space: nowrap;
        z-index: 1;
        letter-spacing: 20px;
        font-family: {theme['font_heading']};
    ">{watermark_text}</div>
    """

# =========================
# Cover Page Generator
# =========================
def generate_cover_page(title, doc_type, theme, author=""):
    cover = f"""
    <div class="cover-page" style="
        page-break-after: always;
        height: 100vh;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, {theme['cover_gradient_start']}15, {theme['cover_gradient_end']}15);
    ">
        <div style="
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 8px;
            background: linear-gradient(90deg, {theme['cover_gradient_start']}, {theme['cover_gradient_end']});
        "></div>
        
        <div style="
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-20deg);
            font-size: 200px;
            opacity: 0.03;
            color: {theme['primary']};
            font-weight: bold;
            pointer-events: none;
        ">DOC</div>
        
        <div class="cover-content" style="
            text-align: center;
            z-index: 2;
            max-width: 80%;
        ">
            <div style="
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 8px;
                color: {theme['primary']};
                margin-bottom: 30px;
                font-family: {theme['font_body']};
            ">{doc_type.replace('_', ' ').title()}</div>
            
            <h1 style="
                font-size: 48px;
                font-family: {theme['font_heading']};
                color: {theme['heading']};
                margin-bottom: 30px;
                line-height: 1.2;
                font-weight: bold;
            ">{title}</h1>
            
            <div style="
                width: 100px;
                height: 3px;
                background: linear-gradient(90deg, {theme['cover_gradient_start']}, {theme['cover_gradient_end']});
                margin: 30px auto;
            "></div>
            
            <div style="
                font-size: 12px;
                color: {theme['footer_text']};
                font-family: {theme['font_body']};
                margin-top: 30px;
            ">
                <p style="margin: 5px 0;">{author if author else ' '}</p>
                <p style="margin: 5px 0;">{datetime.now().strftime('%B %d, %Y')}</p>
                <p style="margin: 10px 0; font-weight: bold; color: {theme['primary']};">Powered by DocCraft AI</p>
            </div>
        </div>
    </div>
    """
    return cover

# =========================
# Premium HTML Builder
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
    
    # Generate watermark
    watermark = generate_watermark_svg(theme)
    
    # Generate cover page
    cover = generate_cover_page(title, document_type, theme, author)
    
    # Start building HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="keywords" content="{', '.join(keywords)}">
        <title>{title} - DocCraft AI</title>
        <style>
            @page {{
                size: A4;
                margin: 1.8cm;
                @top-center {{
                    content: element(header);
                }}
                @bottom-center {{
                    content: element(footer);
                }}
            }}
            
            @page :first {{
                margin: 0;
                @top-center {{
                    content: none;
                }}
                @bottom-center {{
                    content: none;
                }}
            }}
            
            body {{
                font-family: {theme['font_body']};
                color: {theme['text']};
                line-height: 1.8;
                background: {theme['bg']};
                font-size: 12px;
            }}
            
            /* Header & Footer */
            .running-header {{
                position: running(header);
                font-size: 9px;
                color: {theme['footer_text']};
                border-bottom: 1px solid {theme['border']};
                padding-bottom: 5px;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
            }}
            
            .running-footer {{
                position: running(footer);
                font-size: 8px;
                color: {theme['footer_text']};
                border-top: 1px solid {theme['border']};
                padding-top: 5px;
                text-align: center;
            }}
            
            /* Typography */
            h1 {{
                font-family: {theme['font_heading']};
                font-size: 28px;
                color: {theme['heading']};
                margin-top: 30px;
                margin-bottom: 15px;
                border-bottom: 2px solid {theme['primary']};
                padding-bottom: 10px;
            }}
            
            h2 {{
                font-family: {theme['font_heading']};
                font-size: 22px;
                color: {theme['heading']};
                margin-top: 25px;
                margin-bottom: 12px;
            }}
            
            h3 {{
                font-family: {theme['font_heading']};
                font-size: 18px;
                color: {theme['subheading']};
                margin-top: 20px;
                margin-bottom: 10px;
            }}
            
            p {{
                font-size: 12px;
                margin-bottom: 12px;
                text-align: justify;
            }}
            
            /* Special Elements */
            .quote-box {{
                background: linear-gradient(135deg, {theme['primary']}08, {theme['secondary']}08);
                border-left: 5px solid {theme['primary']};
                padding: 20px;
                margin: 20px 0;
                font-style: italic;
                border-radius: 0 8px 8px 0;
                position: relative;
            }}
            
            .quote-box::before {{
                content: '"';
                position: absolute;
                top: -10px;
                left: 10px;
                font-size: 60px;
                color: {theme['primary']};
                opacity: 0.3;
                font-family: Georgia, serif;
            }}
            
            .callout-box {{
                background: linear-gradient(135deg, {theme['primary']}10, {theme['accent']}10);
                border: 2px solid {theme['primary']};
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
                position: relative;
            }}
            
            .callout-box strong {{
                color: {theme['primary']};
            }}
            
            .question-box {{
                background: {theme['question_bg']};
                border-left: 4px solid {theme['question_border']};
                padding: 15px;
                margin: 20px 0;
                font-weight: 600;
                border-radius: 0 6px 6px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }}
            
            .answer-box {{
                margin: 10px 0 20px 20px;
                padding: 10px;
                border-bottom: 1px dashed {theme['border']};
            }}
            
            /* Lists */
            ul, ol {{
                margin: 10px 0 10px 25px;
                padding: 0;
            }}
            
            li {{
                margin: 8px 0;
                padding-left: 5px;
                font-size: 12px;
            }}
            
            ul li {{
                list-style-type: none;
                position: relative;
            }}
            
            ul li::before {{
                content: "▸";
                color: {theme['primary']};
                position: absolute;
                left: -20px;
                font-size: 10px;
            }}
            
            ol {{
                counter-reset: item;
            }}
            
            ol li {{
                counter-increment: item;
                list-style-type: none;
                position: relative;
            }}
            
            ol li::before {{
                content: counter(item);
                background: {theme['primary']};
                color: white;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 10px;
                position: absolute;
                left: -28px;
                top: 2px;
            }}
            
            /* Divider */
            .divider {{
                text-align: center;
                margin: 30px 0;
                color: {theme['primary']};
                font-size: 20px;
                letter-spacing: 15px;
            }}
            
            /* Tags */
            .keyword-tag {{
                display: inline-block;
                background: {theme['primary']}15;
                color: {theme['primary']};
                padding: 3px 10px;
                border-radius: 15px;
                font-size: 10px;
                margin: 3px;
                border: 1px solid {theme['primary']}30;
            }}
            
            /* Progress bar for complexity */
            .complexity-indicator {{
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 10px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 2px;
                background: {theme['primary']};
                color: white;
            }}
            
            /* Table of Contents */
            .toc {{
                background: {theme['bg']};
                border: 2px solid {theme['border']};
                border-radius: 12px;
                padding: 25px;
                margin: 30px 0;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }}
            
            .toc h2 {{
                font-family: {theme['font_heading']};
                color: {theme['primary']};
                border-bottom: 2px solid {theme['border']};
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            
            .toc-item {{
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px dotted {theme['border']};
                font-size: 11px;
            }}
            
            .toc-item:last-child {{
                border-bottom: none;
            }}
            
            /* Info bar */
            .info-bar {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: {theme['bg']};
                border: 1px solid {theme['border']};
                border-radius: 8px;
                padding: 15px;
                margin: 20px 0;
                font-size: 11px;
            }}
            
            .info-item {{
                display: flex;
                align-items: center;
                gap: 8px;
                color: {theme['subheading']};
            }}
            
            .info-icon {{
                font-size: 16px;
                color: {theme['primary']};
            }}
        </style>
    </head>
    <body>
        {watermark}
        {cover}
        
        <!-- Running Header -->
        <div class="running-header">
            <div style="font-weight: bold;">{title[:50]}{'...' if len(title) > 50 else ''}</div>
            <div>{theme['name']} Theme | DocCraft AI</div>
        </div>
        
        <!-- Running Footer -->
        <div class="running-footer">
            <div>DocCraft AI Premium | Generated: {datetime.now().strftime('%B %d, %Y %I:%M %p')} | Page <span class="page"></span></div>
        </div>
    """
    
    # Info Bar
    html += f"""
        <div class="info-bar" style="page-break-before: always;">
            <div class="info-item">
                <span class="info-icon">📄</span>
                <span>{document_type.replace('_', ' ').title()}</span>
            </div>
            <div class="info-item">
                <span class="info-icon">⏱️</span>
                <span>{reading_time} min read</span>
            </div>
            <div class="info-item">
                <span class="info-icon">📅</span>
                <span>{datetime.now().strftime('%b %d, %Y')}</span>
            </div>
            <div>
                <span class="complexity-indicator">{complexity.upper()}</span>
            </div>
        </div>
    """
    
    # Keywords
    if keywords:
        html += '<div style="margin: 20px 0;">'
        for kw in keywords:
            html += f'<span class="keyword-tag">#{kw}</span>'
        html += '</div>'
    
    # Generate TOC
    toc_items = []
    for i, section in enumerate(sections):
        if section['type'] in ['heading', 'subheading']:
            toc_items.append({
                'text': section['text'],
                'level': section['type'],
                'index': i
            })
    
    if toc_items:
        html += '<div class="toc"><h2>📑 Table of Contents</h2>'
        for item in toc_items:
            padding = '20px' if item['level'] == 'subheading' else '0px'
            html += f'''
            <div class="toc-item" style="padding-left: {padding};">
                <span>{item['text'][:80]}{'...' if len(item['text']) > 80 else ''}</span>
                <span style="color: {theme['footer_text']};">→</span>
            </div>
            '''
        html += '</div>'
    
    # Process Sections
    html += '<div class="content" style="position: relative; z-index: 2;">'
    
    for section in sections:
        section_type = section.get("type", "paragraph")
        text = section.get("text", "")
        items = section.get("items", [])
        
        if section_type == "heading":
            html += f'<h1>{text}</h1>'
        
        elif section_type == "subheading":
            html += f'<h2>{text}</h2>'
        
        elif section_type == "question":
            html += f'<div class="question-box">❓ {text}</div>'
        
        elif section_type == "answer":
            html += f'<div class="answer-box">{text}</div>'
        
        elif section_type == "quote":
            html += f'<div class="quote-box">💬 {text}</div>'
        
        elif section_type == "callout":
            html += f'<div class="callout-box">📌 {text}</div>'
        
        elif section_type == "divider":
            html += f'<div class="divider">✦ ✦ ✦</div>'
        
        elif section_type == "bullet_list":
            html += '<ul>'
            for item in items:
                html += f'<li>{item}</li>'
            html += '</ul>'
        
        elif section_type == "numbered_list":
            html += '<ol>'
            for item in items:
                html += f'<li>{item}</li>'
            html += '</ol>'
        
        else:
            html += f'<p>{text}</p>'
    
    html += '</div>'
    
    # Back cover
    html += f"""
        <div style="
            page-break-before: always;
            text-align: center;
            padding: 100px 0;
            background: linear-gradient(135deg, {theme['primary']}05, {theme['secondary']}05);
        ">
            <div style="
                font-size: 60px;
                color: {theme['primary']};
                opacity: 0.3;
                margin-bottom: 20px;
            ">✦</div>
            <h2 style="color: {theme['heading']};">Document Generated by</h2>
            <h1 style="
                font-size: 36px;
                color: {theme['primary']};
                border: none;
            ">DocCraft AI</h1>
            <p style="color: {theme['footer_text']}; margin-top: 20px;">
                Professional Document Generation Platform
            </p>
            <p style="color: {theme['footer_text']}; font-size: 10px; margin-top: 40px;">
                © {datetime.now().year} DocCraft AI. All rights reserved.
            </p>
        </div>
    </body>
    </html>
    """
    
    return html

# =========================
# PDF Generation Endpoint
# =========================
@app.route("/generate_pdf", methods=["POST"])
def generate_pdf():
    try:
        data = request.get_json()
        
        subject = data.get("subject", "Document")
        filename = data.get("filename", "document")
        bulk_text = data.get("bulk_text", "")
        theme_id = data.get("theme", "modern_professional")
        author = data.get("author", "")
        
        # Validate theme
        if theme_id not in THEMES:
            theme_id = "modern_professional"
        
        if not bulk_text.strip():
            return jsonify({
                "error": "bulk_text is empty",
                "code": "EMPTY_CONTENT"
            }), 400
        
        # Analyze document with Gemini
        doc = analyze_document(bulk_text)
        
        if not doc.get("title"):
            doc["title"] = subject
        
        if author:
            doc["author"] = author
        
        # Build premium HTML
        html_content = build_premium_html(doc, theme_id)
        
        # Generate PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_file.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return send_file(
            pdf_file,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{filename}_{timestamp}_{theme_id}.pdf"
        )
    
    except json.JSONDecodeError as e:
        return jsonify({
            "error": "Invalid JSON in Gemini response",
            "details": str(e),
            "code": "JSON_PARSE_ERROR"
        }), 500
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "code": "GENERAL_ERROR"
        }), 500

# =========================
# Quick Preview Endpoint
# =========================
@app.route("/preview", methods=["POST"])
def preview():
    try:
        data = request.get_json()
        bulk_text = data.get("bulk_text", "")
        theme_id = data.get("theme", "modern_professional")
        
        if not bulk_text.strip():
            return jsonify({"error": "Empty content"}), 400
        
        doc = analyze_document(bulk_text)
        
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
# Run Server
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
