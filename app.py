from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from fpdf import FPDF
import re
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

class SmartPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def parse_bulk_text(text):
    qa_pairs = []
    
    patterns = [
        r'(\d+)[\.\)]\s*(.*?)\n(.*?)(?=\n\d+[\.\)]|\Z)',
        r'Q\d*[:\.]?\s*(.*?)\nA\d*[:\.]?\s*(.*?)(?=\nQ|\Z)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            for match in matches:
                if len(match) >= 2:
                    if pattern == patterns[0]:
                        question = match[1].strip()
                        answer = match[2].strip() if len(match) > 2 else ""
                    else:
                        question = match[0].strip()
                        answer = match[1].strip() if len(match) > 1 else ""
                    
                    answer = re.sub(r'\n+', ' ', answer)
                    answer = re.sub(r'\s+', ' ', answer).strip()
                    
                    if question and answer:
                        qa_pairs.append((question, answer))
            break
    
    return qa_pairs

@app.route('/')
def health_check():
    return jsonify({'status': 'OK', 'message': 'PDF Backend is running!'})

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.json
        subject = data.get('subject', 'Study Notes')
        filename = data.get('filename', 'notes')
        bulk_text = data.get('bulk_text', '')
        individual_qa = data.get('individual_qa', [])
        
        pdf = SmartPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        
        pdf.cell(200, 10, txt=f"{subject}", ln=True, align='C')
        pdf.ln(10)
        
        if bulk_text:
            qa_pairs = parse_bulk_text(bulk_text)
        else:
            qa_pairs = individual_qa
        
        if not qa_pairs:
            return jsonify({'error': 'No valid questions found'}), 400
        
        for i, (question, answer) in enumerate(qa_pairs, 1):
            if pdf.get_y() > 250:
                pdf.add_page()
            
            pdf.set_font("Arial", "B", 12)
            if not question.startswith(str(i)):
                question = f"{i}. {question}"
            pdf.multi_cell(0, 10, question)
            
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 8, answer)
            pdf.ln(5)
        
        file_path = f"generated_pdfs/{filename}.pdf"
        pdf.output(file_path)
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists('generated_pdfs'):
        os.makedirs('generated_pdfs')
    app.run(debug=True)
