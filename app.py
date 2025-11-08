from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from fpdf import FPDF
import os
import io
import re
from datetime import datetime

# Try Gemini import, but make it optional
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

app = Flask(__name__)
CORS(app)

# Gemini setup only if available
if GEMINI_AVAILABLE:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)

class SmartPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def intelligent_parser(text):
    """Smart parser that works with or without Gemini"""
    # Try Gemini first if available
    if GEMINI_AVAILABLE and os.getenv('GEMINI_API_KEY'):
        try:
            return parse_with_gemini(text)
        except:
            pass
    
    # Fallback to advanced regex parser
    return advanced_regex_parser(text)

def parse_with_gemini(text):
    """Gemini AI parsing"""
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"Extract questions and answers from: {text[:3000]}"
        response = model.generate_content(prompt)
        # Simple parsing logic here
        return advanced_regex_parser(response.text)
    except:
        return advanced_regex_parser(text)

def advanced_regex_parser(text):
    """Advanced regex-based parser"""
    qa_pairs = []
    lines = text.split('\n')
    
    current_q = ""
    current_a = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Multiple question patterns
        is_question = (
            (line and line[0].isdigit() and ('.' in line or ')' in line)) or
            line.lower().startswith('q:') or
            line.lower().startswith('question') or
            (len(line) < 100 and '?' in line and not line.startswith(' '))
        )
        
        if is_question:
            if current_q and current_a:
                qa_pairs.append((clean_text(current_q), clean_text(' '.join(current_a))))
            current_q = line
            current_a = []
        else:
            current_a.append(line)
    
    if current_q and current_a:
        qa_pairs.append((clean_text(current_q), clean_text(' '.join(current_a))))
    
    return qa_pairs

def clean_text(text):
    """Safe text cleaning"""
    if not text:
        return ""
    text = ' '.join(text.split())
    if len(text) > 1500:
        text = text[:1500] + "..."
    return text

@app.route('/')
def home():
    features = ["Smart Text Parsing", "Auto Format Detection"]
    if GEMINI_AVAILABLE and os.getenv('GEMINI_API_KEY'):
        features.append("Gemini AI Powered")
    
    return jsonify({
        "status": "OK", 
        "message": "PDF Backend is running!",
        "features": features
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
        
        # Smart parsing
        qa_pairs = intelligent_parser(bulk_text)
        
        if not qa_pairs:
            return jsonify({"error": "No questions detected. Try: 1. Question?\\nAnswer..."}), 400
        
        # Create PDF
        pdf = SmartPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Header
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, subject, 0, 1, 'C')
        pdf.ln(10)
        
        # Content
        for i, (question, answer) in enumerate(qa_pairs, 1):
            if pdf.get_y() > 250:
                pdf.add_page()
            
            # Question
            pdf.set_font('Arial', 'B', 12)
            display_q = question if question.startswith(str(i)) else f"{i}. {question}"
            pdf.multi_cell(0, 8, display_q)
            
            # Answer
            pdf.set_font('Arial', '', 11)
            pdf.multi_cell(0, 6, answer)
            pdf.ln(5)
        
        # Save
        output = io.BytesIO()
        pdf.output(output)
        output.seek(0)
        
        return send_file(output, as_attachment=True, download_name=f"{filename}.pdf")
        
    except Exception as e:
        return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)