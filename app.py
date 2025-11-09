from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from weasyprint import HTML
import os
import io
import re
from datetime import datetime
import uuid

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

def generate_html_content(subject, qa_pairs, user_name=""):
    """Generate beautiful HTML content with page numbers and full formatting"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 2cm;
                
                @bottom-center {{
                    content: "Page " counter(page);
                    font-family: Arial, sans-serif;
                    font-size: 10px;
                    color: #666;
                }}
                
                @top-center {{
                    content: "{subject}";
                    font-family: Arial, sans-serif;
                    font-size: 12px;
                    color: #666;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 10px;
                }}
            }}
            
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.8;
                margin: 0;
                padding: 0;
                color: #333;
                text-align: justify;
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 40px;
                padding-bottom: 20px;
                border-bottom: 3px solid #2c3e50;
            }}
            
            .title {{
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }}
            
            .subtitle {{
                font-size: 16px;
                color: #7f8c8d;
                margin-bottom: 5px;
            }}
            
            .user-info {{
                font-size: 14px;
                color: #3498db;
                font-style: italic;
            }}
            
            .qa-container {{
                margin: 0 auto;
                max-width: 100%;
            }}
            
            .qa-section {{
                margin-bottom: 30px;
                page-break-inside: avoid;
            }}
            
            .question {{
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 12px;
                padding: 15px;
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-left: 5px solid #3498db;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            
            .answer {{
                font-size: 16px;
                color: #555;
                padding: 0 15px;
                line-height: 1.8;
                text-align: justify;
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
            
            /* Ensure text uses full page width */
            .content-wrapper {{
                width: 100%;
                max-width: 100%;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="title">{subject}</div>
            <div class="subtitle">Generated on {datetime.now().strftime('%Y-%m-%d at %I:%M %p')}</div>
            {f'<div class="user-info">Created by: {user_name}</div>' if user_name else ''}
            <div class="subtitle">Total Questions: {len(qa_pairs)}</div>
        </div>
        
        <div class="content-wrapper">
            <div class="qa-container">
    """
    
    # Add Q&A pairs
    for i, (question, answer) in enumerate(qa_pairs, 1):
        # Add page break every 8 questions for better readability
        if i > 1 and i % 8 == 1:
            html_content += '<div class="page-break"></div>'
        
        html_content += f"""
                <div class="qa-section">
                    <div class="question">{i}. {question}</div>
                    <div class="answer">{answer}</div>
                </div>
        """
    
    html_content += """
            </div>
        </div>
        
        <div class="footer">
            Document generated automatically • All rights reserved
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
        "features": ["Page Numbers", "Full Justify", "Dynamic Filenames", "User Names"]
    })

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()
        subject = data.get('subject', 'Study Notes')
        filename = data.get('filename', 'notes')
        bulk_text = data.get('bulk_text', '')
        user_name = data.get('user_name', '')  # New field for user name
        
        if not bulk_text.strip():
            return jsonify({"error": "Please provide text content"}), 400
        
        # Parse text
        qa_pairs = parse_text(bulk_text)
        
        if not qa_pairs:
            return jsonify({"error": "No questions detected. Use format: 1. Question?\\nAnswer..."}), 400
        
        # Generate HTML content with user name
        html_content = generate_html_content(subject, qa_pairs, user_name)
        
        # Create PDF from HTML
        html = HTML(string=html_content)
        pdf_bytes = html.write_pdf()
        
        # Create dynamic filename with timestamp to avoid same name downloads
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
