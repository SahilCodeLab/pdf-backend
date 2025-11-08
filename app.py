from flask import Flask, request, jsonify, send_file
from fpdf import FPDF
import re
import os
from datetime import datetime

app = Flask(__name__)

class SmartPDF(FPDF):
    def footer(self):
        # Page number
        self.set_y(-15)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def parse_bulk_text(text):
    """Bulk text ko automatically parse karega"""
    qa_pairs = []
    
    # Multiple formats handle karega
    patterns = [
        r'(\d+)[\.\)]\s*(.*?)\n(.*?)(?=\n\d+[\.\)]|\Z)',  # 1. Question\nAnswer
        r'Q\d*[:\.]?\s*(.*?)\nA\d*[:\.]?\s*(.*?)(?=\nQ|\Z)',  # Q1: Question\nA1: Answer
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            for match in matches:
                if len(match) >= 2:
                    if pattern == patterns[0]:  # Number. Format
                        q_num = match[0]
                        question = match[1].strip()
                        answer = match[2].strip() if len(match) > 2 else ""
                    else:  # Q/A Format
                        question = match[0].strip()
                        answer = match[1].strip() if len(match) > 1 else ""
                    
                    # Clean text
                    answer = re.sub(r'\n+', ' ', answer)
                    answer = re.sub(r'\s+', ' ', answer).strip()
                    
                    if question and answer:
                        qa_pairs.append((question, answer))
            break
    
    return qa_pairs

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.json
        subject = data.get('subject', 'Study Notes')
        filename = data.get('filename', 'notes')
        bulk_text = data.get('bulk_text', '')
        individual_qa = data.get('individual_qa', [])
        
        # PDF banaye
        pdf = SmartPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        
        # Title
        pdf.cell(200, 10, txt=f"{subject}", ln=True, align='C')
        pdf.ln(10)
        
        # Data process karega
        if bulk_text:
            # Bulk text process karega
            qa_pairs = parse_bulk_text(bulk_text)
        else:
            # Individual Q/A use karega
            qa_pairs = individual_qa
        
        if not qa_pairs:
            return jsonify({'error': 'No valid questions found'}), 400
        
        # Content add karega
        for i, (question, answer) in enumerate(qa_pairs, 1):
            # Page break check
            if pdf.get_y() > 250:
                pdf.add_page()
            
            # Question (Bold)
            pdf.set_font("Arial", "B", 12)
            if not question.startswith(str(i)):
                question = f"{i}. {question}"
            pdf.multi_cell(0, 10, question)
            
            # Answer (Normal)
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 8, answer)
            pdf.ln(5)
        
        # Save karega
        file_path = f"generated_pdfs/{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf.output(file_path)
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # YEH LINE FIX KARO - PROPER INDENTATION
    if not os.path.exists('generated_pdfs'):
        os.makedirs('generated_pdfs')
    app.run(debug=True)
