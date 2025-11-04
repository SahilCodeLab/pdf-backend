
import os
import io
import json
import fitz  # PyMuPDF - Powerful PDF manipulation
import subprocess
import tempfile
import shutil
import zipfile
from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
from werkzeug.utils import secure_filename
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.colors import Color, grey, red, blue
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
import pytesseract
from cryptography.fernet import Fernet
import base64

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'}

# Initialize encryption
def generate_key():
    return Fernet.generate_key()

fernet = Fernet(generate_key())

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper Functions
def create_temp_file(file_stream, suffix):
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp.write(file_stream.read())
        return temp.name

def cleanup_files(files_list):
    for f in files_list:
        if f and os.path.exists(f):
            os.remove(f)

def cleanup_dir(dir_path):
    if dir_path and os.path.exists(dir_path):
        shutil.rmtree(dir_path)

def pdf_to_images(pdf_bytes):
    """Convert PDF to list of PIL Images"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Higher resolution
        img_data = pix.tobytes("ppm")
        img = Image.open(io.BytesIO(img_data))
        images.append(img)
    doc.close()
    return images

# === PDF MANIPULATION TOOLS ===

@app.route('/api/merge-pdf', methods=['POST'])
def merge_pdf():
    """Merge multiple PDF files"""
    if 'files' not in request.files:
        return jsonify({"error": "No files uploaded"}), 400
    
    files = request.files.getlist('files')
    if len(files) < 2:
        return jsonify({"error": "At least 2 PDF files required"}), 400

    merger = fitz.open()
    temp_files = []
    
    try:
        for file in files:
            if file and allowed_file(file.filename) and file.filename.lower().endswith('.pdf'):
                temp_path = create_temp_file(file, '.pdf')
                temp_files.append(temp_path)
                doc = fitz.open(temp_path)
                merger.insert_pdf(doc)
                doc.close()
            else:
                return jsonify({"error": f"Invalid file: {file.filename}"}), 400
        
        output_stream = io.BytesIO()
        merger.save(output_stream)
        merger.close()
        output_stream.seek(0)
        
        return send_file(output_stream, as_attachment=True, download_name='merged.pdf', mimetype='application/pdf')
    
    except Exception as e:
        return jsonify({"error": f"Merge failed: {str(e)}"}), 500
    finally:
        cleanup_files(temp_files)

@app.route('/api/split-pdf', methods=['POST'])
def split_pdf():
    """Split PDF into multiple files or extract pages"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    split_type = request.form.get('type', 'range')  # range, even_odd, multiple
    pages = request.form.get('pages', '')
    
    try:
        pdf_bytes = file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        
        if split_type == 'range':
            # Split by page range (e.g., "1-3,5-7")
            page_ranges = []
            for part in pages.split(','):
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    page_ranges.append((start-1, end-1))
                else:
                    page_num = int(part) - 1
                    page_ranges.append((page_num, page_num))
            
            output_stream = io.BytesIO()
            new_doc = fitz.open()
            
            for start, end in page_ranges:
                for page_num in range(start, end + 1):
                    if 0 <= page_num < total_pages:
                        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            
            new_doc.save(output_stream)
            new_doc.close()
            output_stream.seek(0)
            return send_file(output_stream, as_attachment=True, download_name='split.pdf')
        
        elif split_type == 'even_odd':
            # Create ZIP with even and odd pages
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                # Even pages
                even_doc = fitz.open()
                for page_num in range(1, total_pages, 2):  # 1-indexed even
                    even_doc.insert_pdf(doc, from_page=page_num-1, to_page=page_num-1)
                even_stream = io.BytesIO()
                even_doc.save(even_stream)
                even_doc.close()
                zip_file.writestr('even_pages.pdf', even_stream.getvalue())
                
                # Odd pages
                odd_doc = fitz.open()
                for page_num in range(0, total_pages, 2):  # 0-indexed odd
                    odd_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                odd_stream = io.BytesIO()
                odd_doc.save(odd_stream)
                odd_doc.close()
                zip_file.writestr('odd_pages.pdf', odd_stream.getvalue())
            
            zip_buffer.seek(0)
            return send_file(zip_buffer, as_attachment=True, download_name='split_pages.zip')
        
        elif split_type == 'multiple':
            # Split into individual pages
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                for page_num in range(total_pages):
                    single_doc = fitz.open()
                    single_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                    page_stream = io.BytesIO()
                    single_doc.save(page_stream)
                    single_doc.close()
                    zip_file.writestr(f'page_{page_num+1}.pdf', page_stream.getvalue())
            
            zip_buffer.seek(0)
            return send_file(zip_buffer, as_attachment=True, download_name='individual_pages.zip')
        
        doc.close()
        
    except Exception as e:
        return jsonify({"error": f"Split failed: {str(e)}"}), 500

@app.route('/api/compress-pdf', methods=['POST'])
def compress_pdf():
    """Compress PDF with different quality levels"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    quality = request.form.get('quality', 'medium')  # low, medium, high
    
    try:
        # Using Ghostscript for compression
        temp_input = create_temp_file(file, '.pdf')
        temp_output = temp_input.replace('.pdf', '_compressed.pdf')
        
        quality_map = {
            'low': '/screen',
            'medium': '/ebook', 
            'high': '/printer'
        }
        
        command = [
            'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
            f'-dPDFSETTINGS={quality_map.get(quality, "/ebook")}',
            '-dNOPAUSE', '-dQUIET', '-dBATCH',
            f'-sOutputFile={temp_output}', temp_input
        ]
        
        subprocess.run(command, check=True, capture_output=True)
        
        return send_file(temp_output, as_attachment=True, download_name='compressed.pdf')
    
    except Exception as e:
        return jsonify({"error": f"Compression failed: {str(e)}"}), 500
    finally:
        cleanup_files([temp_input, temp_output])

# === PDF CONVERSION TOOLS ===

@app.route('/api/pdf-to-word', methods=['POST'])
def pdf_to_word():
    """Convert PDF to Word document"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    
    try:
        # Using PyMuPDF for text extraction
        pdf_bytes = file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        text_content = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text_content.append(page.get_text())
        
        doc.close()
        
        # Create simple Word document (for complex conversion, use python-docx)
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        
        docx_stream = io.BytesIO()
        doc = SimpleDocTemplate(docx_stream, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        for text in text_content:
            story.append(Paragraph(text.replace('\n', '<br/>'), styles['Normal']))
        
        doc.build(story)
        docx_stream.seek(0)
        
        return send_file(docx_stream, as_attachment=True, download_name='converted.docx')
    
    except Exception as e:
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500

@app.route('/api/pdf-to-images', methods=['POST'])
def pdf_to_images_api():
    """Convert PDF to images (JPG/PNG)"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    format_type = request.form.get('format', 'jpg')  # jpg or png
    dpi = int(request.form.get('dpi', 150))
    
    try:
        pdf_bytes = file.read()
        images = pdf_to_images(pdf_bytes)
        
        if len(images) == 1:
            # Single image
            img_stream = io.BytesIO()
            images[0].save(img_stream, format=format_type.upper(), quality=95)
            img_stream.seek(0)
            return send_file(img_stream, as_attachment=True, download_name=f'converted.{format_type}')
        else:
            # Multiple images - create ZIP
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                for i, img in enumerate(images):
                    img_stream = io.BytesIO()
                    img.save(img_stream, format=format_type.upper(), quality=95)
                    zip_file.writestr(f'page_{i+1}.{format_type}', img_stream.getvalue())
            
            zip_buffer.seek(0)
            return send_file(zip_buffer, as_attachment=True, download_name='converted_pages.zip')
    
    except Exception as e:
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500

@app.route('/api/images-to-pdf', methods=['POST'])
def images_to_pdf():
    """Convert multiple images to PDF"""
    if 'files' not in request.files:
        return jsonify({"error": "No files uploaded"}), 400
    
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No valid images"}), 400
    
    try:
        images = []
        for file in files:
            if file and allowed_file(file.filename):
                img = Image.open(file.stream)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                images.append(img)
        
        if not images:
            return jsonify({"error": "No valid images found"}), 400
        
        # Create PDF
        pdf_stream = io.BytesIO()
        images[0].save(pdf_stream, "PDF", resolution=100.0, save_all=True, 
                      append_images=images[1:])
        pdf_stream.seek(0)
        
        return send_file(pdf_stream, as_attachment=True, download_name='converted.pdf')
    
    except Exception as e:
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500

# === PDF SECURITY TOOLS ===

@app.route('/api/protect-pdf', methods=['POST'])
def protect_pdf():
    """Add password protection to PDF"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    password = request.form.get('password', '')
    owner_password = request.form.get('owner_password', '')
    permissions = int(request.form.get('permissions', 0))  # Bitmask for permissions
    
    if not password:
        return jsonify({"error": "Password required"}), 400
    
    try:
        pdf_bytes = file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Set encryption
        encrypt_meth = 1  # PDF 1.4 encryption
        perm = permissions  # Permissions bitmask
        
        doc.save(None, encryption=encrypt_meth, user_pw=password, 
                owner_pw=owner_password or None, permissions=perm)
        
        output_stream = io.BytesIO()
        doc.save(output_stream)
        doc.close()
        output_stream.seek(0)
        
        return send_file(output_stream, as_attachment=True, download_name='protected.pdf')
    
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
        pdf_bytes = file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        if doc.is_encrypted:
            if not doc.authenticate(password):
                return jsonify({"error": "Invalid password"}), 401
        
        output_stream = io.BytesIO()
        doc.save(output_stream)
        doc.close()
        output_stream.seek(0)
        
        return send_file(output_stream, as_attachment=True, download_name='unlocked.pdf')
    
    except Exception as e:
        return jsonify({"error": f"Password removal failed: {str(e)}"}), 500

@app.route('/api/encrypt-file', methods=['POST'])
def encrypt_file():
    """Encrypt any file with AES encryption"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    password = request.form.get('password', '')
    
    if not password:
        return jsonify({"error": "Password required"}), 400
    
    try:
        file_data = file.read()
        
        # Derive key from password
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        import os
        
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
        
        # Combine salt + encrypted data
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
        
        # Extract salt and encrypted data
        salt = file_data[:16]
        encrypted_data = file_data[16:]
        
        # Derive key from password
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        
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

# === IMAGE TOOLS ===

@app.route('/api/compress-image', methods=['POST'])
def compress_image():
    """Compress image with quality control"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    quality = int(request.form.get('quality', 85))
    format_type = request.form.get('format', 'JPEG')
    
    try:
        img = Image.open(file.stream)
        
        # Convert to RGB if necessary
        if format_type.upper() == 'JPEG' and img.mode != 'RGB':
            img = img.convert('RGB')
        
        output_stream = io.BytesIO()
        img.save(output_stream, format=format_type, quality=quality, optimize=True)
        output_stream.seek(0)
        
        return send_file(output_stream, as_attachment=True, download_name=f'compressed.{format_type.lower()}')
    
    except Exception as e:
        return jsonify({"error": f"Compression failed: {str(e)}"}), 500

@app.route('/api/resize-image', methods=['POST'])
def resize_image():
    """Resize image with different modes"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    width = int(request.form.get('width', 0))
    height = int(request.form.get('height', 0))
    maintain_ratio = request.form.get('maintain_ratio', 'true').lower() == 'true'
    resize_mode = request.form.get('mode', 'fit')  # fit, fill, crop
    
    try:
        img = Image.open(file.stream)
        original_width, original_height = img.size
        
        if width <= 0 and height <= 0:
            return jsonify({"error": "Invalid dimensions"}), 400
        
        if maintain_ratio:
            if width > 0 and height > 0:
                # Maintain aspect ratio
                ratio = min(width/original_width, height/original_height)
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
            elif width > 0:
                ratio = width / original_width
                new_height = int(original_height * ratio)
                new_width = width
            else:
                ratio = height / original_height
                new_width = int(original_width * ratio)
                new_height = height
        else:
            new_width = width if width > 0 else original_width
            new_height = height if height > 0 else original_height
        
        if resize_mode == 'crop':
            # Crop to exact dimensions
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            left = (new_width - width) / 2
            top = (new_height - height) / 2
            right = (new_width + width) / 2
            bottom = (new_height + height) / 2
            img = img.crop((left, top, right, bottom))
        else:
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        output_stream = io.BytesIO()
        img.save(output_stream, format=img.format or 'JPEG', quality=95)
        output_stream.seek(0)
        
        return send_file(output_stream, as_attachment=True, download_name='resized_image.jpg')
    
    except Exception as e:
        return jsonify({"error": f"Resize failed: {str(e)}"}), 500

@app.route('/api/convert-image', methods=['POST'])
def convert_image():
    """Convert image between different formats"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    target_format = request.form.get('format', 'JPEG').upper()
    
    try:
        img = Image.open(file.stream)
        
        # Handle format-specific conversions
        if target_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        elif target_format == 'PNG' and img.mode == 'RGB':
            img = img.convert('RGBA')
        
        output_stream = io.BytesIO()
        img.save(output_stream, format=target_format, quality=95)
        output_stream.seek(0)
        
        ext_map = {'JPEG': 'jpg', 'PNG': 'png', 'BMP': 'bmp', 'TIFF': 'tiff', 'WEBP': 'webp'}
        ext = ext_map.get(target_format, target_format.lower())
        
        return send_file(output_stream, as_attachment=True, download_name=f'converted.{ext}')
    
    except Exception as e:
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500

# === ADVANCED PDF TOOLS ===

@app.route('/api/add-watermark', methods=['POST'])
def add_watermark():
    """Add text or image watermark to PDF"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    watermark_type = request.form.get('type', 'text')  # text or image
    text = request.form.get('text', 'CONFIDENTIAL')
    opacity = float(request.form.get('opacity', 0.3))
    position = request.form.get('position', 'center')  # center, diagonal, etc.
    
    try:
        pdf_bytes = file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            if watermark_type == 'text':
                # Add text watermark
                rect = page.rect
                font_size = 60
                
                # Calculate position
                if position == 'diagonal':
                    # Diagonal across page
                    points = [(rect.width * 0.1, rect.height * 0.1), 
                             (rect.width * 0.9, rect.height * 0.9)]
                else:  # center
                    points = [(rect.width / 2, rect.height / 2)]
                
                for x, y in points:
                    page.insert_text(
                        (x, y), text, fontsize=font_size, 
                        color=(0.5, 0.5, 0.5),  # Gray color
                        rotate=45,  # Diagonal text
                        overlay=True
                    )
            elif watermark_type == 'image' and 'watermark_file' in request.files:
                # Add image watermark
                watermark_file = request.files['watermark_file']
                img = Image.open(watermark_file.stream)
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                
                # Calculate position
                rect = page.rect
                if position == 'center':
                    x = (rect.width - img.width) / 2
                    y = (rect.height - img.height) / 2
                else:
                    x, y = 50, 50  # Top-left
                
                page.insert_image(
                    fitz.Rect(x, y, x + img.width, y + img.height),
                    stream=img_bytes.getvalue()
                )
        
        output_stream = io.BytesIO()
        doc.save(output_stream)
        doc.close()
        output_stream.seek(0)
        
        return send_file(output_stream, as_attachment=True, download_name='watermarked.pdf')
    
    except Exception as e:
        return jsonify({"error": f"Watermark failed: {str(e)}"}), 500

@app.route('/api/extract-text', methods=['POST'])
def extract_text():
    """Extract text from PDF or images (OCR)"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    use_ocr = request.form.get('ocr', 'false').lower() == 'true'
    
    try:
        if file.filename.lower().endswith('.pdf'):
            # PDF text extraction
            pdf_bytes = file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            text_data = {}
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                text_data[f"page_{page_num + 1}"] = text
            
            doc.close()
            
            return jsonify({
                "success": True,
                "total_pages": len(text_data),
                "text": text_data
            })
        
        else:
            # Image OCR
            img = Image.open(file.stream)
            
            if use_ocr:
                # Use Tesseract OCR
                try:
                    text = pytesseract.image_to_string(img)
                    return jsonify({
                        "success": True,
                        "text": text,
                        "method": "ocr"
                    })
                except:
                    return jsonify({"error": "OCR failed. Tesseract not installed."}), 500
            else:
                return jsonify({"error": "OCR required for image text extraction"}), 400
    
    except Exception as e:
        return jsonify({"error": f"Text extraction failed: {str(e)}"}), 500

@app.route('/api/repair-pdf', methods=['POST'])
def repair_pdf():
    """Attempt to repair corrupted PDF"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    
    try:
        # Method 1: Try to open and save with PyMuPDF
        pdf_bytes = file.read()
        
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            output_stream = io.BytesIO()
            doc.save(output_stream)
            doc.close()
            output_stream.seek(0)
            
            return send_file(output_stream, as_attachment=True, download_name='repaired.pdf')
        
        except:
            # Method 2: Use Ghostscript for repair
            temp_input = create_temp_file(io.BytesIO(pdf_bytes), '.pdf')
            temp_output = temp_input.replace('.pdf', '_repaired.pdf')
            
            command = [
                'gs', '-o', temp_output, '-sDEVICE=pdfwrite', 
                '-dPDFSETTINGS=/prepress', temp_input
            ]
            
            subprocess.run(command, check=True, capture_output=True)
            
            return send_file(temp_output, as_attachment=True, download_name='repaired.pdf')
    
    except Exception as e:
        return jsonify({"error": f"Repair failed: {str(e)}"}), 500
    finally:
        cleanup_files([temp_input, temp_output])

# === UTILITY ENDPOINTS ===

@app.route('/')
def home():
    return jsonify({
        "message": "Ultimate PDF & Image Tools API",
        "version": "2.0",
        "endpoints": {
            "pdf_tools": [
                "/api/merge-pdf", "/api/split-pdf", "/api/compress-pdf",
                "/api/protect-pdf", "/api/remove-password", "/api/add-watermark",
                "/api/repair-pdf", "/api/extract-text"
            ],
            "conversion": [
                "/api/pdf-to-word", "/api/pdf-to-images", "/api/images-to-pdf"
            ],
            "security": [
                "/api/encrypt-file", "/api/decrypt-file"
            ],
            "image_tools": [
                "/api/compress-image", "/api/resize-image", "/api/convert-image"
            ]
        }
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "PDF Tools API"})

# Error handlers
@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum size is 100MB"}), 413

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
