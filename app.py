from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from fpdf import FPDF
import os
import io
import google.generativeai as genai
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Gemini API - Environment variable se lega
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class AdvancedPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def add_qa_section(self, number, question, answer):
        """Smart QA section addition"""
        # Question
        self.set_font('Arial', 'B', 13)
        self.set_text_color(0, 0, 139)  # Dark blue for questions
        self.multi_cell(0, 9, f"{number}. {question}")
        self.ln(2)
        
        # Answer
        self.set_font('Arial', '', 11)
        self.set_text_color(0, 0, 0)  # Black for answers
        self.multi_cell(0, 7, answer)
        self.ln(8)

def intelligent_text_parser(text):
    """
    GEMINI AI - Smart text parser
    Jo bhi format mein text ho, automatically detect karega
    """
    try:
        if not GEMINI_API_KEY:
            return fallback_parser(text)
            
        model = genai.GenerativeModel('gemini-pro')
        
        advanced_prompt = f"""
        ROLE: You are an EXPERT educational content parser with 20 years experience.
        
        TASK: Analyze ANY text format and extract ALL question-answer pairs intelligently.
        
        INPUT TEXT:
        {text}
        
        CRITICAL THINKING:
        1. First understand the CONTEXT and STRUCTURE
        2. Identify patterns - numbered lists, Q/A format, bullet points, paragraphs
        3. Detect implicit questions even without numbers
        4. Handle mixed formats, messy text, incomplete structures
        5. Preserve original meaning while cleaning
        
        SMART DETECTION STRATEGIES:
        - Numbered items (1., 2., etc.)
        - Q: A: format
        - Question/Answer headings
        - Sentences ending with ? 
        - Bullet points with questions
        - Paragraphs containing Q&A
        - Mixed languages (English/Hindi)
        - Incomplete numbering
        - Multi-line answers
        
        OUTPUT FORMAT (STRICT JSON):
        {{
            "qa_pairs": [
                {{
                    "question": "cleaned question text",
                    "answer": "cleaned answer text" 
                }}
            ],
            "analysis": {{
                "total_questions": 5,
                "format_detected": "numbered_list",
                "confidence_score": 0.95
            }}
        }}
        
        RULES:
        - Be CREATIVE in detection
        - Handle ANY text format
        - Don't miss ANY questions
        - Clean but preserve meaning
        - Split long answers logically
        - Return VALID JSON only
        """
        
        response = model.generate_content(advanced_prompt)
        result_text = response.text.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            import json
            result_data = json.loads(json_match.group())
            qa_pairs = [(q['question'], q['answer']) for q in result_data['qa_pairs']]
            
            print(f"🎯 GEMINI ANALYSIS: {result_data['analysis']}")
            return qa_pairs
        else:
            return fallback_parser(text)
            
    except Exception as e:
        print(f"🤖 Gemini Error: {e}")
        return fallback_parser(text)

def fallback_parser(text):
    """Advanced fallback parser when Gemini fails"""
    qa_pairs = []
    lines = text.split('\n')
    
    current_q = ""
    current_a = []
    q_patterns = [
        r'^(\d+[\.\)])\s*(.+)',  # 1. Question
        r'^(Q\d*[:\.]?)\s*(.+)',  # Q1: Question
        r'^(Question\s*\d*[:\.]?)\s*(.+)',  # Question 1:
        r'^([•\-*])\s*(.+\?)',  # • Question?
        r'^(.+\?)$',  # Anything ending with ?
    ]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        is_question = False
        clean_line = line
        
        # Multiple question detection patterns
        for pattern in q_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                is_question = True
                clean_line = match.group(2) if match.lastindex >= 2 else line
                break
        
        if is_question:
            # Save previous QA
            if current_q and current_a:
                qa_pairs.append((
                    clean_text(current_q), 
                    clean_text(' '.join(current_a))
                ))
            current_q = clean_line
            current_a = []
        else:
            # Answer content
            current_a.append(line)
    
    # Final QA pair
    if current_q and current_a:
        qa_pairs.append((
            clean_text(current_q), 
            clean_text(' '.join(current_a))
        ))
    
    return qa_pairs

def clean_text(text):
    """Intelligent text cleaning"""
    if not text:
        return ""
    
    # Preserve meaning while cleaning
    text = re.sub(r'\n+', ' ', text)  # Newlines to spaces
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
    text = text.strip()
    
    # Smart truncation
    if len(text) > 2000:
        # Don't cut in middle of sentence
        last_period = text[:1800].rfind('.')
        if last_period > 0:
            text = text[:last_period+1] + " [Content optimized]"
        else:
            text = text[:1800] + "... [Content optimized]"
    
    return text

@app.route('/')
def home():
    return jsonify({
        "status": "OK", 
        "message": "AI PDF Backend is running!",
        "features": ["Gemini AI Integration", "Smart Text Parsing", "Auto Format Detection"]
    })

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        subject = data.get('subject', 'AI Generated Notes')
        filename = data.get('filename', f'notes_{datetime.now().strftime("%H%M%S")}')
        bulk_text = data.get('bulk_text', '')
        
        if not bulk_text.strip():
            return jsonify({"error": "Please provide some text content"}), 400
        
        # 🎯 AI-POWERED PARSING
        print("🤖 Starting AI Text Analysis...")
        qa_pairs = intelligent_text_parser(bulk_text)
        
        if not qa_pairs:
            return jsonify({"error": "No questions detected. Try different formatting."}), 400
        
        # Create PDF
        pdf = AdvancedPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Header
        pdf.set_font('Arial', 'B', 18)
        pdf.set_text_color(0, 0, 128)  # Navy blue
        pdf.cell(0, 15, "AI-GENERATED STUDY NOTES", 0, 1, 'C')
        
        pdf.set_font('Arial', 'B', 16)
        pdf.set_text_color(0, 100, 0)  # Green
        pdf.cell(0, 12, subject.upper(), 0, 1, 'C')
        pdf.ln(8)
        
        # Add AI-processed content
        pdf.set_font('Arial', 'I', 10)
        pdf.set_text_color(100, 100, 100)  # Gray
        pdf.cell(0, 8, f"Processed by AI • {len(qa_pairs)} questions detected • {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, 'C')
        pdf.ln(10)
        
        # Smart content addition
        for i, (question, answer) in enumerate(qa_pairs, 1):
            if pdf.get_y() > 240:
                pdf.add_page()
            
            pdf.add_qa_section(i, question, answer)
        
        # Save to memory
        output = io.BytesIO()
        pdf.output(output)
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f"{filename}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({"error": f"AI Processing Failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)