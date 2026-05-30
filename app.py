from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from weasyprint import HTML
import google.generativeai as genai
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
# Gemini Setup
# =========================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("❌ GEMINI_API_KEY not found in environment variables")
    raise ValueError("❌ GEMINI_API_KEY not found in environment variables")

logger.info("✅ GEMINI_API_KEY loaded successfully")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')  # Updated model name
logger.info("✅ Gemini model initialized")

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
    logger.info("Health check requested")
    return jsonify({
        "status": "OK",
        "message": "DocCraft AI Premium Backend Running",
        "themes_available": list(THEMES.keys()),
        "version": "2.0.0"
    })

# =========================
# Get Themes Endpoint
# =========================
@app.route("/themes", methods=["GET"])
def get_themes():
    logger.info("Themes list requested")
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
    logger.info("📝 Starting document analysis with Gemini...")
    logger.info(f"📝 Text length: {len(text)} characters")
    
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
    
    try:
        logger.info("🤖 Calling Gemini API...")
        response = model.generate_content(prompt)
        logger.info("✅ Gemini API response received")
        
        raw = response.text.strip()
        logger.info(f"📄 Raw response (first 200 chars): {raw[:200]}...")
        
        # Clean JSON response
        if raw.startswith("```json"):
            logger.info("🔄 Cleaning JSON markdown wrapper")
            raw = raw.replace("```json", "").replace("```", "")
        elif raw.startswith("```"):
            raw = raw.replace("```", "")
        
        parsed = json.loads(raw)
        logger.info(f"✅ Document parsed successfully. Type: {parsed.get('document_type')}, Sections: {len(parsed.get('sections', []))}")
        return parsed
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON Parse Error: {str(e)}")
        logger.error(f"❌ Raw response: {raw}")
        raise
    except Exception as e:
        logger.error(f"❌ Gemini API Error: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# =========================
# Generate Cover Page
# =========================
def generate_cover_page(title, doc_type, theme, author=""):
    return f"""
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
                <p style="margin: 5px 0;">{author if author else ''}</p>
                <p style="margin: 5px 0;">{datetime.now().strftime('%B %d, %Y')}</p>
                <p style="margin: 10px 0; font-weight: bold; color: {theme['primary']};">Powered by DocCraft AI</p>
            </div>
        </div>
    </div>
    """

# =========================
# Build Premium HTML
# =========================
def build_premium_html(doc, theme_id="modern_professional"):
    logger.info(f"🎨 Building HTML with theme: {theme_id}")
    theme = THEMES.get(theme_id, THEMES["modern_professional"])
    title = doc.get("title", "Document")
    document_type = doc.get("document_type", "general_document")
    author = doc.get("author", "")
    sections = doc.get("sections", [])
    metadata = doc.get("metadata", {})
    keywords = metadata.get("keywords", [])
    reading_time = metadata.get("reading_time_minutes", 0)
    complexity = metadata.get("complexity", "basic")
    
    logger.info(f"📊 Doc info - Type: {document_type}, Sections: {len(sections)}, Theme: {theme['name']}")
    
    cover = generate_cover_page(title, document_type, theme, author)
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="keywords" content="{', '.join(keywords)}">
        <title>{title} - DocCraft AI</title>
        <style>
            @page {{
                size: A4;
                margin: 1.8cm;
                @bottom-center {{
                    content: "Page " counter(page);
                    font-size: 9px;
                    color: {theme['footer_text']};
                    font-family: {theme['font_body']};
                }}
            }}
            
            @page :first {{
                margin: 0;
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
            
            .quote-box {{
                background: linear-gradient(135deg, {theme['primary']}08, {theme['secondary']}08);
                border-left: 5px solid {theme['primary']};
                padding: 20px;
                margin: 20px 0;
                font-style: italic;
                border-radius: 0 8px 8px 0;
            }}
            
            .question-box {{
                background: {theme['question_bg']};
                border-left: 4px solid {theme['question_border']};
                padding: 15px;
                margin: 20px 0;
                font-weight: 600;
                border-radius: 0 6px 6px 0;
            }}
            
            .answer-box {{
                margin: 10px 0 20px 20px;
                padding: 10px;
                border-bottom: 1px dashed {theme['border']};
            }}
            
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
            
            .divider {{
                text-align: center;
                margin: 30px 0;
                color: {theme['primary']};
                font-size: 20px;
                letter-spacing: 15px;
            }}
            
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
            
            .footer-note {{
                margin-top: 40px;
                padding-top: 15px;
                border-top: 2px solid {theme['border']};
                text-align: center;
                color: {theme['footer_text']};
                font-size: 10px;
            }}
        </style>
    </head>
    <body>
        {cover}
        
        <div class="info-bar">
            <span>📄 {document_type.replace('_', ' ').title()}</span>
            <span>⏱️ {reading_time} min read</span>
            <span>📅 {datetime.now().strftime('%b %d, %Y')}</span>
        </div>
    """
    
    # Process Sections
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
            html += f'<div class="quote-box">{text}</div>'
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
    
    # Footer
    html += f"""
        <div class="footer-note">
            <p>© {datetime.now().year} DocCraft AI • Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p>Theme: {theme['name']} • Premium Document Generation</p>
        </div>
    </body>
    </html>
    """
    
    logger.info("✅ HTML built successfully")
    return html

# =========================
# Generate PDF Endpoint
# =========================
@app.route("/generate_pdf", methods=["POST"])
def generate_pdf():
    try:
        data = request.get_json()
        logger.info("📥 Received /generate_pdf request")
        logger.info(f"📥 Payload keys: {list(data.keys()) if data else 'None'}")
        
        # Extract fields
        subject = data.get("subject", "Document")
        filename = data.get("filename", "document")
        bulk_text = data.get("bulk_text", "")
        theme_id = data.get("theme", "modern_professional")
        author = data.get("author", "")
        
        logger.info(f"📝 Subject: '{subject}', Filename: '{filename}', Theme: '{theme_id}'")
        logger.info(f"📝 Author: '{author}', Text length: {len(bulk_text)}")
        
        # Validate theme
        if theme_id not in THEMES:
            logger.warning(f"⚠️ Invalid theme '{theme_id}', using default")
            theme_id = "modern_professional"
        
        # Validate bulk_text
        if not bulk_text.strip():
            logger.warning("❌ Empty bulk_text received")
            return jsonify({
                "error": "bulk_text is empty",
                "code": "EMPTY_CONTENT"
            }), 400
        
        # Step 1: Analyze document
        logger.info("🔍 Step 1/3: Analyzing document...")
        doc = analyze_document(bulk_text)
        logger.info(f"✅ Analysis complete. Document type: {doc.get('document_type')}")
        
        # Set defaults
        if not doc.get("title"):
            doc["title"] = subject
            logger.info(f"📌 Using subject as title: '{subject}'")
        
        if author:
            doc["author"] = author
        
        # Step 2: Build HTML
        logger.info("🎨 Step 2/3: Building HTML...")
        html_content = build_premium_html(doc, theme_id)
        logger.info(f"✅ HTML built ({len(html_content)} characters)")
        
        # Step 3: Generate PDF
        logger.info("📄 Step 3/3: Generating PDF...")
        pdf_bytes = HTML(string=html_content).write_pdf()
        logger.info(f"✅ PDF generated ({len(pdf_bytes)} bytes)")
        
        # Create file object
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_file.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_name = f"{filename}_{timestamp}_{theme_id}.pdf"
        
        logger.info(f"✅ Sending PDF: {download_name}")
        
        return send_file(
            pdf_file,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=download_name
        )
    
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON Parse Error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": "Failed to parse document structure",
            "details": str(e),
            "code": "JSON_PARSE_ERROR"
        }), 500
    
    except Exception as e:
        logger.error(f"❌ Unexpected Error: {str(e)}")
        logger.error(f"❌ Error Type: {type(e).__name__}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "type": type(e).__name__,
            "code": "GENERAL_ERROR"
        }), 500

# =========================
# Test Endpoint (No Gemini)
# =========================
@app.route("/test_pdf", methods=["GET"])
def test_pdf():
    try:
        logger.info("🧪 Test PDF endpoint called")
        
        doc = {
            "document_type": "test_document",
            "title": "Test Document",
            "author": "DocCraft AI",
            "sections": [
                {"type": "heading", "text": "Welcome to DocCraft AI"},
                {"type": "paragraph", "text": "This is a test document to verify PDF generation is working correctly."},
                {"type": "subheading", "text": "Features"},
                {"type": "bullet_list", "items": ["Premium Themes", "AI Analysis", "Professional Formatting", "Instant Download"]},
                {"type": "subheading", "text": "How It Works"},
                {"type": "numbered_list", "items": ["Enter your text", "Choose a theme", "Click generate", "Download PDF"]},
                {"type": "divider", "text": ""},
                {"type": "quote", "text": "The art of communication is the language of leadership."},
            ],
            "metadata": {
                "keywords": ["test", "pdf", "docraft"],
                "reading_time_minutes": 1,
                "complexity": "basic"
            }
        }
        
        html_content = build_premium_html(doc, "modern_professional")
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_file.seek(0)
        
        logger.info(f"✅ Test PDF generated: {len(pdf_bytes)} bytes")
        
        return send_file(
            pdf_file,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="test_document.pdf"
        )
        
    except Exception as e:
        logger.error(f"❌ Test PDF Error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500

# =========================
# Run Server
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Starting DocCraft AI server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
