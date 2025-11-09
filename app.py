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

def generate_html_content(subject, qa_pairs):
    """Generate beautiful HTML content"""
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 40px;
                color: #333;
            }}
            .header {{
                text-align: center;
                border-bottom: 3px solid #2c3e50;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .title {{
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }}
            .timestamp {{
                color: #7f8c8d;
                font-size: 14px;
            }}
            .qa-section {{
                margin-bottom: 30px;
            }}
            .question {{
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
                padding: 15px;
                background: #f8f9fa;
                border-left: 5px solid #3498db;
                border-radius: 5px;
            }}
            .answer {{
                font-size: 16px;
                color: #555;
                margin-bottom: 20px;
                padding: 0 15px;
                line-height: 1.8;
            }}
            .page-break {{
                page-break-before: always;
            }}
            .footer {{
                text-align: center;
                margin-top: 50px;
                padding-top: 20px;
                border-top: 1px solid #bdc3c7;
                color: #7f8c8d;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="title">{subject}</div>
            <div class="timestamp">Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</div>
        </div>
    """
    
    # Add Q&A pairs
    for i, (question, answer) in enumerate(qa_pairs, 1):
        # Add page break every 5 questions
        if i > 1 and i % 5 == 1:
            html_template += '<div class="page-break"></div>'
        
        html_template += f"""
        <div class="qa-section">
            <div class="question">{i}. {question}</div>
            <div class="answer">{answer}</div>
        </div>
        """
    
    # Add footer
    html_template += f"""
        <div class="footer">
            Page <span class="pageNumber"></span> • Generated with AI PDF Maker
        </div>
    </body>
    </html>
    """
    
    return html_template

@app.route('/')
def home():
    return jsonify({
        "status": "OK", 
        "message": "PDF Backend is running!",
        "version": "WeasyPrint Edition",
        "features": ["Unicode Support", "Beautiful Formatting", "Page Breaks"]
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
            return jsonify({"error": "No questions detected. Try: 1. Question?\\nAnswer..."}), 400
        
        # Generate HTML content
        html_content = generate_html_content(subject, qa_pairs)
        
        # Create PDF from HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        # Create file-like object
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_file.seek(0)
        
        return send_file(
            pdf_file,
            as_attachment=True,
            download_name=f"{filename}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)