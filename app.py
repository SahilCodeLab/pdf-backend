import os
import io
import subprocess
import tempfile
import shutil
import zipfile
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pypdf import PdfMerger, PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# Helper Functions
def create_temp_file(file_stream, suffix):
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp.write(file_stream.read())
        return temp.name

def cleanup_files(files_list):
    for f in files_list:
        if f and os.path.exists(f):
            os.remove(f)

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

@app.route('/api/compress-pdf', methods=['POST'])
def compress_pdf():
    """Compress PDF using Ghostscript"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    
    temp_input = None
    temp_output = None
    
    try:
        temp_input = create_temp_file(file, '.pdf')
        temp_output = temp_input.replace('.pdf', '_compressed.pdf')
        
        command = [
            'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
            '-dPDFSETTINGS=/ebook', '-dNOPAUSE', '-dQUIET', '-dBATCH',
            f'-sOutputFile={temp_output}', temp_input
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            return jsonify({"error": f"Ghostscript error: {result.stderr}"}), 500
        
        return send_file(temp_output, as_attachment=True, download_name='compressed.pdf')
    
    except Exception as e:
        return jsonify({"error": f"Compression failed: {str(e)}"}), 500
    finally:
        cleanup_files([temp_input, temp_output])

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
            can.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.3)  # Gray with transparency
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
            can.drawString(300, 20, str(page_num + 1))  # Bottom center
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

# === SECURITY TOOLS ===

@app.route('/api/encrypt-file', methods=['POST'])
def encrypt_file():
    """Encrypt any file with AES"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    password = request.form.get('password', '')
    
    if not password:
        return jsonify({"error": "Password required"}), 400
    
    try:
        file_data = file.read()
        
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        fernet = Fernet(key)
        
        encrypted_data = fernet.encrypt(file_data)
        final_data = salt + encrypted_data
        
        output_stream = io.BytesIO(final_data)
        output_stream.seek(0)
        
        return send_file(output_stream, as_attachment=True, download_name=f'encrypted_{file.filename}')
    
    except Exception as e:
        return jsonify({"error": f"Encryption failed: {str(e)}"}), 500

@app.route('/api/decrypt-file', methods=['POST'])
def decrypt_file():
    """Decrypt AES encrypted file"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    password = request.form.get('password', '')
    
    if not password:
        return jsonify({"error": "Password required"}), 400
    
    try:
        file_data = file.read()
        
        salt = file_data[:16]
        encrypted_data = file_data[16:]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        fernet = Fernet(key)
        
        decrypted_data = fernet.decrypt(encrypted_data)
        
        output_stream = io.BytesIO(decrypted_data)
        output_stream.seek(0)
        
        return send_file(output_stream, as_attachment=True, download_name=f'decrypted_{file.filename}')
    
    except Exception as e:
        return jsonify({"error": f"Decryption failed: {str(e)}"}), 500

# === HEALTH CHECK ===

@app.route('/')
def home():
    return jsonify({
        "message": "PDF Tools API is running!",
        "version": "3.0",
        "status": "healthy",
        "endpoints": {
            "pdf_tools": [
                "/api/merge-pdf - Merge PDFs",
                "/api/split-pdf - Split PDF", 
                "/api/compress-pdf - Compress PDF",
                "/api/protect-pdf - Password Protect PDF",
                "/api/remove-password - Remove PDF Password",
                "/api/rotate-pdf - Rotate PDF",
                "/api/add-watermark - Add Watermark",
                "/api/add-page-numbers - Add Page Numbers"
            ],
            "security": [
                "/api/encrypt-file - Encrypt File",
                "/api/decrypt-file - Decrypt File"
            ]
        }
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "PDF Tools API"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
