import os
import io
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pypdf import PdfMerger, PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# === PDF TOOLS ===

@app.route('/api/merge-pdf', methods=['POST'])
def merge_pdf():
    """Merge multiple PDF files"""
    if 'files' not in request.files:
        return jsonify({"error": "No files uploaded"}), 400
    
    files = request.files.getlist('files')
    if len(files) < 2:
        return jsonify({"error": "At least 2 PDF files required"}), 400

    merger = PdfMerger()
    
    try:
        for file in files:
            if file and file.filename.lower().endswith('.pdf'):
                merger.append(file.stream)
            else:
                return jsonify({"error": f"Invalid file: {file.filename}"}), 400
        
        output_stream = io.BytesIO()
        merger.write(output_stream)
        merger.close()
        output_stream.seek(0)
        
        return send_file(output_stream, as_attachment=True, download_name='merged.pdf', mimetype='application/pdf')
    
    except Exception as e:
        return jsonify({"error": f"Merge failed: {str(e)}"}), 500

@app.route('/api/split-pdf', methods=['POST'])
def split_pdf():
    """Split PDF by page range"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    start_page = request.form.get('start_page', type=int, default=1)
    end_page = request.form.get('end_page', type=int, default=1)
    
    try:
        reader = PdfReader(file.stream)
        total_pages = len(reader.pages)
        
        if start_page < 1 or end_page > total_pages or start_page > end_page:
            return jsonify({"error": f"Invalid page range. Total pages: {total_pages}"}), 400
        
        writer = PdfWriter()
        for i in range(start_page-1, end_page):
            writer.add_page(reader.pages[i])
        
        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)
        
        return send_file(output_stream, as_attachment=True, download_name='split.pdf', mimetype='application/pdf')
    
    except Exception as e:
        return jsonify({"error": f"Split failed: {str(e)}"}), 500

@app.route('/api/protect-pdf', methods=['POST'])
def protect_pdf():
    """Add password protection to PDF"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    password = request.form.get('password', '')
    
    if not password:
        return jsonify({"error": "Password required"}), 400
    
    try:
        reader = PdfReader(file.stream)
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        writer.encrypt(password)
        
        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)
        
        return send_file(output_stream, as_attachment=True, download_name='protected.pdf', mimetype='application/pdf')
    
    except Exception as e:
        return jsonify({"error": f"Protection failed: {str(e)}"}), 500

@app.route('/api/remove-password', methods=['POST'])
def remove_password():
    """Remove password protection from PDF"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    password = request.form.get('password', '')
    
    try:
        reader = PdfReader(file.stream)
        
        if reader.is_encrypted:
            if not reader.decrypt(password):
                return jsonify({"error": "Invalid password"}), 401
        
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        
        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)
        
        return send_file(output_stream, as_attachment=True, download_name='unlocked.pdf', mimetype='application/pdf')
    
    except Exception as e:
        return jsonify({"error": f"Password removal failed: {str(e)}"}), 500

@app.route('/api/rotate-pdf', methods=['POST'])
def rotate_pdf():
    """Rotate PDF pages"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    angle = request.form.get('angle', type=int, default=90)
    
    if angle not in [90, 180, 270]:
        return jsonify({"error": "Angle must be 90, 180, or 270"}), 400
    
    try:
        reader = PdfReader(file.stream)
        writer = PdfWriter()
        
        for page in reader.pages:
            page.rotate(angle)
            writer.add_page(page)
        
        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)
        
        return send_file(output_stream, as_attachment=True, download_name='rotated.pdf', mimetype='application/pdf')
    
    except Exception as e:
        return jsonify({"error": f"Rotation failed: {str(e)}"}), 500

@app.route('/api/add-watermark', methods=['POST'])
def add_watermark():
    """Add text watermark to PDF"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    watermark_text = request.form.get('text', 'CONFIDENTIAL')
    
    try:
        reader = PdfReader(file.stream)
        writer = PdfWriter()
        
        for page_num in range(len(reader.pages)):
            # Create watermark
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            can.setFont("Helvetica", 40)
            can.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.3)
            can.translate(300, 400)
            can.rotate(45)
            can.drawString(0, 0, watermark_text)
            can.save()
            
            packet.seek(0)
            watermark_reader = PdfReader(packet)
            watermark_page = watermark_reader.pages[0]
            
            # Merge with original page
            original_page = reader.pages[page_num]
            original_page.merge_page(watermark_page)
            writer.add_page(original_page)
        
        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)
        
        return send_file(output_stream, as_attachment=True, download_name='watermarked.pdf', mimetype='application/pdf')
    
    except Exception as e:
        return jsonify({"error": f"Watermark failed: {str(e)}"}), 500

@app.route('/api/add-page-numbers', methods=['POST'])
def add_page_numbers():
    """Add page numbers to PDF"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    
    try:
        reader = PdfReader(file.stream)
        writer = PdfWriter()
        
        for page_num in range(len(reader.pages)):
            # Create page number
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            can.setFont("Helvetica", 12)
            can.drawString(300, 20, str(page_num + 1))
            can.save()
            
            packet.seek(0)
            number_reader = PdfReader(packet)
            number_page = number_reader.pages[0]
            
            # Merge with original page
            original_page = reader.pages[page_num]
            original_page.merge_page(number_page)
            writer.add_page(original_page)
        
        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)
        
        return send_file(output_stream, as_attachment=True, download_name='numbered.pdf', mimetype='application/pdf')
    
    except Exception as e:
        return jsonify({"error": f"Page numbering failed: {str(e)}"}), 500

@app.route('/api/extract-text', methods=['POST'])
def extract_text():
    """Extract text from PDF"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    
    try:
        reader = PdfReader(file.stream)
        text_data = {}
        
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()
            text_data[f"page_{page_num + 1}"] = text
        
        return jsonify({
            "success": True,
            "total_pages": len(text_data),
            "text": text_data
        })
    
    except Exception as e:
        return jsonify({"error": f"Text extraction failed: {str(e)}"}), 500

@app.route('/api/get-pdf-info', methods=['POST'])
def get_pdf_info():
    """Get PDF information"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    
    try:
        reader = PdfReader(file.stream)
        
        info = {
            "total_pages": len(reader.pages),
            "is_encrypted": reader.is_encrypted,
            "metadata": reader.metadata
        }
        
        return jsonify({
            "success": True,
            "info": info
        })
    
    except Exception as e:
        return jsonify({"error": f"Info extraction failed: {str(e)}"}), 500

# === HEALTH CHECK ===

@app.route('/')
def home():
    return jsonify({
        "message": "PDF Tools API is running!",
        "version": "1.0",
        "status": "healthy",
        "endpoints": {
            "pdf_tools": [
                "POST /api/merge-pdf - Merge PDFs",
                "POST /api/split-pdf - Split PDF", 
                "POST /api/protect-pdf - Password Protect PDF",
                "POST /api/remove-password - Remove PDF Password",
                "POST /api/rotate-pdf - Rotate PDF",
                "POST /api/add-watermark - Add Watermark",
                "POST /api/add-page-numbers - Add Page Numbers",
                "POST /api/extract-text - Extract Text from PDF",
                "POST /api/get-pdf-info - Get PDF Information"
            ]
        }
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "PDF Tools API"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
