from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from weasyprint import HTML
import os
import io
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)

def parse_text(text):
    """Smart text parser"""
    qa_pairs = []
    lines = text.split('\n')
    
    current_question = ""
    current_answer = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect question patterns
        is_question = (
            (line and line[0].isdigit() and ('.' in line or ')' in line)) or
            line.lower().startswith('q:') or
            line.lower().startswith('question') or
            line.lower().startswith('q.') or
            (len(line) < 150 and '?' in line and line.index('?') > 0)
        )
        
        if is_question:
            if current_question and current_answer:
                qa_pairs.append((current_question, ' '.join(current_answer)))
            current_question = line
            current_answer = []
        else:
            current_answer.append(line)
    
    if current_question and current_answer:
        qa_pairs.append((current_question, ' '.join(current_answer)))
    
    return qa_pairs

def estimate_content_height(question, answer):
    """Estimate how much space a Q&A pair will take"""
    # Rough estimation: 1 line = 20px, average characters per line = 80
    question_lines = max(1, len(question) // 80)
    answer_lines = max(1, len(answer) // 80)
    
    # Each line takes approx 25px in PDF with line height
    total_height = (question_lines + answer_lines) * 25 + 40  # 40px for margins
    return total_height

def generate_html_content(subject, qa_pairs, watermark_text=""):
    """Generate HTML with smart page breaks based on content length"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 1.5cm;
                
                @bottom-center {{
                    content: "Page " counter(page);
                    font-family: Arial, sans-serif;
                    font-size: 10px;
                    color: #666;
                }}
            }}
            
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 0;
                color: #333;
                text-align: justify;
                position: relative;
            }}
            
            .watermark {{
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-size: 60px;
                color: rgba(0, 0, 0, 0.08);
                font-weight: bold;
                z-index: -1;
                pointer-events: none;
                opacity: 0.7;
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 25px;
                padding-bottom: 15px;
                border-bottom: 2px solid #2c3e50;
            }}
            
            .title {{
                font-size: 22px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 5px;
            }}
            
            .subtitle {{
                font-size: 12px;
                color: #7f8c8d;
                margin-bottom: 3px;
            }}
            
            .qa-container {{
                margin: 0 auto;
            }}
            
            .qa-section {{
                margin-bottom: 20px;
                padding-bottom: 15px;
            }}
            
            .question {{
                font-size: 15px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 8px;
                padding: 10px;
                background: #f8f9fa;
                border-left: 4px solid #3498db;
                border-radius: 4px;
            }}
            
            .answer {{
                font-size: 13px;
                color: #555;
                padding: 0 10px;
                line-height: 1.5;
                text-align: justify;
            }}
            
            /* Smart page breaks */
            .qa-section {{
                page-break-inside: avoid;
            }}
            
            .page-break {{
                page-break-before: always;
            }}
            
            .footer {{
                text-align: center;
                margin-top: 25px;
                padding-top: 12px;
                border-top: 1px solid #bdc3c7;
                color: #7f8c8d;
                font-size: 10px;
            }}
        </style>
    </head>
    <body>
        <!-- Watermark on every page -->
        <div class="watermark">{watermark_text}</div>
        
        <div class="header">
            <div class="title">{subject}</div>
            <div class="subtitle">Generated on {datetime.now().strftime('%d %b %Y at %I:%M %p')}</div>
        </div>
        
        <div class="qa-container">
    """
    
    # Smart page breaking based on content length
    current_page_height = 400  # Header + initial margin height approx
    page_count = 1
    questions_on_current_page = 0
    
    for i, (question, answer) in enumerate(qa_pairs, 1):
        # Estimate content height for this Q&A
        content_height = estimate_content_height(question, answer)
        
        # If adding this content would exceed page, add page break
        if current_page_height + content_height > 1800:  # A4 page height approx
            html_content += '<div class="page-break"></div>'
            html_content += f"""
            <div class="header">
                <div class="title">{subject} (Continued)</div>
                <div class="subtitle">Page {page_count + 1}</div>
            </div>
            """
            current_page_height = 400  # Reset for new page
            page_count += 1
            questions_on_current_page = 0
        
        html_content += f"""
            <div class="qa-section">
                <div class="question">{i}. {question}</div>
                <div class="answer">{answer}</div>
            </div>
        """
        
        current_page_height += content_height
        questions_on_current_page += 1
    
    html_content += """
        </div>
        
        <div class="footer">
            Professional Document • Generated by sahilcodelab
        </div>
    </body>
    </html>
    """
    
    return html_content

@app.route('/')
def home():
    return jsonify({
        "status": "OK", 
        "message": "PDF Backend is running!",
        "features": ["Smart Page Breaks", "Content-based Layout", "Watermark", "Professional Formatting"]
    })

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()
        subject = data.get('subject', 'Study Notes')
        filename = data.get('filename', 'notes')
        bulk_text = data.get('bulk_text', '')
        
        if not bulk_text.strip():
            return jsonify({"error": "Please provide text content"}), 400
        
        # Parse text
        qa_pairs = parse_text(bulk_text)
        
        if not qa_pairs:
            return jsonify({"error": "No questions detected. Use format: 1. Question?\\nAnswer..."}), 400
        
        # Set watermark text
        watermark_text = "sahilcodelab"
        
        # Generate HTML content with smart page breaks
        html_content = generate_html_content(subject, qa_pairs, watermark_text)
        
        # Create PDF from HTML
        html = HTML(string=html_content)
        pdf_bytes = html.write_pdf()
        
        # Create dynamic filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{filename}_{timestamp}"
        
        # Create file-like object
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_file.seek(0)
        
        return send_file(
            pdf_file,
            as_attachment=True,
            download_name=f"{unique_filename}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
