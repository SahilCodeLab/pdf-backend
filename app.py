import os
import io
import subprocess  # External tools ke liye
import tempfile    # Temporary files ke liye
import shutil      # Directory operations ke liye
from flask import Flask, request, send_file, jsonify, make_response
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter # PDF to Word
from flask_cors import CORS
from PIL import Image # JPG to PDF
from reportlab.pdfgen import canvas # Page numbers / Watermark
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import grey # Watermark color
from pdf2image import convert_from_bytes # PDF to JPG (Needs Poppler)
import zipfile # PDF to JPG (multiple images)

app = Flask(__name__)
CORS(app)

# --- Helper Functions ---
def create_temp_file(file_stream, suffix):
    # Ek temporary file banata hai aur uska path return karta hai
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp.write(file_stream.read())
        return temp.name

def cleanup_files(files_list):
    # Temporary files ko delete karta hai
    for f in files_list:
        if f and os.path.exists(f):
            os.remove(f)

def cleanup_dir(dir_path):
    # Temporary directory ko delete karta hai
    if dir_path and os.path.exists(dir_path):
        shutil.rmtree(dir_path)

# --- Feature 1: Merge PDF ---
@app.route('/api/merge', methods=['POST'])
def merge_pdf():
    if 'files' not in request.files: return jsonify({"error": "No files found"}), 400
    files = request.files.getlist('files')
    if len(files) < 2: return jsonify({"error": "Upload at least 2 files"}), 400
    merger = PdfMerger()
    try:
        for file in files:
            if file.filename.endswith('.pdf'): merger.append(file.stream)
            else: return jsonify({"error": f"File '{file.filename}' is not a PDF"}), 400
        output_stream = io.BytesIO()
        merger.write(output_stream)
        merger.close()
        output_stream.seek(0)
        return send_file(output_stream, as_attachment=True, download_name='merged.pdf', mimetype='application/pdf')
    except Exception as e: return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# --- Feature 2: Split PDF ---
@app.route('/api/split', methods=['POST'])
def split_pdf():
    if 'file' not in request.files: return jsonify({"error": "No file found"}), 400
    file = request.files['file']
    start_page = request.form.get('start_page', type=int)
    end_page = request.form.get('end_page', type=int)
    if not start_page or not end_page or start_page < 1 or end_page < start_page:
        return jsonify({"error": "Invalid page range"}), 400
    try:
        reader = PdfReader(file.stream)
        writer = PdfWriter()
        if end_page > len(reader.pages): return jsonify({"error": "End page exceeds total pages"}), 400
        for i in range(start_page - 1, end_page): writer.add_page(reader.pages[i])
        output_stream = io.BytesIO()
        writer.write(output_stream)
        writer.close()
        output_stream.seek(0)
        return send_file(output_stream, as_attachment=True, download_name='split.pdf', mimetype='application/pdf')
    except Exception as e: return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# --- Feature 3: PDF to Word ---
@app.route('/api/pdf-to-word', methods=['POST'])
def pdf_to_word():
    if 'file' not in request.files: return jsonify({"error": "No file found"}), 400
    file = request.files['file']
    if not file.filename.endswith('.pdf'): return jsonify({"error": "File is not a PDF"}), 400
    temp_pdf_path, temp_docx_path = None, None
    try:
        temp_pdf_path = create_temp_file(file.stream, ".pdf")
        temp_docx_path = temp_pdf_path.replace(".pdf", ".docx")
        cv = Converter(temp_pdf_path)
        cv.convert(temp_docx_path, start=0, end=None)
        cv.close()
        return send_file(temp_docx_path, as_attachment=True, download_name='converted.docx')
    except Exception as e: return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally: cleanup_files([temp_pdf_path, temp_docx_path])

# --- Feature 4: Compress PDF (Requires Ghostscript) ---
@app.route('/api/compress', methods=['POST'])
def compress_pdf():
    if 'file' not in request.files: return jsonify({"error": "No file found"}), 400
    file = request.files['file']
    if not file.filename.endswith('.pdf'): return jsonify({"error": "File is not a PDF"}), 400
    temp_input_path, temp_output_path = None, None
    try:
        temp_input_path = create_temp_file(file.stream, ".pdf")
        temp_output_path = temp_input_path.replace(".pdf", "_compressed.pdf")
        # NOTE: 'gs' command (Ghostscript) server par install hona chahiye
        command = ['gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4', '-dPDFSETTINGS=/ebook',
                   '-dNOPAUSE', '-dQUIET', '-dBATCH', f'-sOutputFile={temp_output_path}', temp_input_path]
        subprocess.run(command, check=True)
        return send_file(temp_output_path, as_attachment=True, download_name='compressed.pdf')
    except FileNotFoundError: return jsonify({"error": "Ghostscript is not installed"}), 500
    except Exception as e: return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally: cleanup_files([temp_input_path, temp_output_path])

# --- Feature 5: JPG to PDF ---
@app.route('/api/jpg-to-pdf', methods=['POST'])
def jpg_to_pdf():
    if 'files' not in request.files: return jsonify({"error": "No image files found"}), 400
    files = request.files.getlist('files')
    image_list = []
    try:
        for file in files:
            if file.mimetype.startswith('image/'):
                img = Image.open(file.stream).convert('RGB')
                image_list.append(img)
            else: return jsonify({"error": f"File '{file.filename}' is not an image"}), 400
        if not image_list: return jsonify({"error": "No valid images to convert"}), 400
        output_stream = io.BytesIO()
        image_list[0].save(output_stream, "PDF", resolution=100.0, save_all=True, append_images=image_list[1:])
        output_stream.seek(0)
        return send_file(output_stream, as_attachment=True, download_name='converted.pdf', mimetype='application/pdf')
    except Exception as e: return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# --- Feature 6: Rotate PDF ---
@app.route('/api/rotate', methods=['POST'])
def rotate_pdf():
    if 'file' not in request.files: return jsonify({"error": "No file found"}), 400
    file = request.files['file']
    angle = request.form.get('angle', type=int)
    if angle not in [90, 180, 270]:
        return jsonify({"error": "Invalid rotation angle. Must be 90, 180, or 270"}), 400
    try:
        reader = PdfReader(file.stream)
        writer = PdfWriter()
        for page in reader.pages:
            page.rotate(angle)
            writer.add_page(page)
        output_stream = io.BytesIO()
        writer.write(output_stream)
        writer.close()
        output_stream.seek(0)
        return send_file(output_stream, as_attachment=True, download_name='rotated.pdf', mimetype='application/pdf')
    except Exception as e: return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# --- Feature 7: Protect PDF ---
@app.route('/api/protect', methods=['POST'])
def protect_pdf():
    if 'file' not in request.files: return jsonify({"error": "No file found"}), 400
    file = request.files['file']
    password = request.form.get('password')
    if not password: return jsonify({"error": "Password not provided"}), 400
    try:
        reader = PdfReader(file.stream)
        writer = PdfWriter()
        for page in reader.pages: writer.add_page(page)
        writer.encrypt(password) # Password lagana
        output_stream = io.BytesIO()
        writer.write(output_stream)
        writer.close()
        output_stream.seek(0)
        return send_file(output_stream, as_attachment=True, download_name='protected.pdf', mimetype='application/pdf')
    except Exception as e: return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# --- Feature 8: Add Page Numbers ---
@app.route('/api/add-page-numbers', methods=['POST'])
def add_page_numbers():
    if 'file' not in request.files: return jsonify({"error": "No file found"}), 400
    file = request.files['file']
    try:
        input_pdf = PdfReader(file.stream)
        output_writer = PdfWriter()
        for i, page in enumerate(input_pdf.pages):
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            can.drawString(275, 30, str(i + 1)) # Page number position
            can.save()
            packet.seek(0)
            watermark_pdf = PdfReader(packet)
            page.merge_page(watermark_pdf.pages[0])
            output_writer.add_page(page)
        output_stream = io.BytesIO()
        output_writer.write(output_stream)
        output_writer.close()
        output_stream.seek(0)
        return send_file(output_stream, as_attachment=True, download_name='page_numbered.pdf', mimetype='application/pdf')
    except Exception as e: return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# --- Feature 9: Add Watermark (New) ---
@app.route('/api/add-watermark', methods=['POST'])
def add_watermark():
    if 'file' not in request.files: return jsonify({"error": "No file found"}), 400
    
    file = request.files['file']
    watermark_text = request.form.get('text')
    if not watermark_text: return jsonify({"error": "Watermark text not provided"}), 400
    
    try:
        input_pdf = PdfReader(file.stream)
        output_writer = PdfWriter()
        
        # Watermark ka PDF banana
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.setFont("Helvetica", 50) # Font size
        can.setFillColor(grey, alpha=0.3) # Color aur transparency
        can.saveState()
        can.translate(300, 450) # Position
        can.rotate(45) # Angle
        can.drawCentredString(0, 0, watermark_text)
        can.restoreState()
        can.save()
        packet.seek(0)
        watermark_pdf = PdfReader(packet)
        watermark_page = watermark_pdf.pages[0]

        for page in input_pdf.pages:
            page.merge_page(watermark_page) # Har page par watermark merge karna
            output_writer.add_page(page)

        output_stream = io.BytesIO()
        output_writer.write(output_stream)
        output_writer.close()
        output_stream.seek(0)
        
        return send_file(output_stream, as_attachment=True, download_name='watermarked.pdf', mimetype='application/pdf')
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# --- Feature 10: Remove Pages (New) ---
@app.route('/api/remove-pages', methods=['POST'])
def remove_pages():
    if 'file' not in request.files: return jsonify({"error": "No file found"}), 400
    
    file = request.files['file']
    # Pages to remove, comma-separated (e.g., "1,3,5-7")
    pages_to_remove_str = request.form.get('pages')
    if not pages_to_remove_str: return jsonify({"error": "Pages to remove not specified"}), 400

    try:
        # Page string ko parse karna (e.g., "1,3,5-7" -> {1, 3, 5, 6, 7})
        pages_to_remove = set()
        for part in pages_to_remove_str.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages_to_remove.update(range(start, end + 1))
            else:
                pages_to_remove.add(int(part))
        
        reader = PdfReader(file.stream)
        writer = PdfWriter()
        
        for i in range(len(reader.pages)):
            if (i + 1) not in pages_to_remove: # Page number 1-based hota hai
                writer.add_page(reader.pages[i])

        if len(writer.pages) == 0:
            return jsonify({"error": "Cannot remove all pages"}), 400
            
        output_stream = io.BytesIO()
        writer.write(output_stream)
        writer.close()
        output_stream.seek(0)
        
        return send_file(output_stream, as_attachment=True, download_name='pages_removed.pdf', mimetype='application/pdf')
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# --- Feature 11: PDF to JPG (Requires Poppler) (New) ---
@app.route('/api/pdf-to-jpg', methods=['POST'])
def pdf_to_jpg():
    if 'file' not in request.files: return jsonify({"error": "No file found"}), 400
    file = request.files['file']
    
    temp_dir = None
    try:
        # NOTE: 'poppler' library server par install honi chahiye
        images = convert_from_bytes(file.read())
        
        if not images:
            return jsonify({"error": "Could not convert PDF to images"}), 500

        # Agar ek hi image hai, toh direct bhej do
        if len(images) == 1:
            img_io = io.BytesIO()
            images[0].save(img_io, format='JPEG')
            img_io.seek(0)
            return send_file(img_io, as_attachment=True, download_name='converted.jpg', mimetype='image/jpeg')

        # Agar multiple images hain, toh ZIP file banao
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, 'w') as zf:
            for i, image in enumerate(images):
                img_io = io.BytesIO()
                image.save(img_io, format='JPEG')
                img_io.seek(0)
                zf.writestr(f'page_{i+1}.jpg', img_io.getvalue())
        
        zip_io.seek(0)
        return send_file(zip_io, as_attachment=True, download_name='converted_images.zip', mimetype='application/zip')
        
    except Exception as e:
        # Poppler install nahi hone par bhi yahaan error aa sakta hai
        return jsonify({"error": f"An error occurred. Is Poppler installed? Error: {str(e)}"}), 500

# --- Feature 12: Unlock PDF (Requires QPDF) (New) ---
@app.route('/api/unlock', methods=['POST'])
def unlock_pdf():
    if 'file' not in request.files: return jsonify({"error": "No file found"}), 400
    file = request.files['file']
    password = request.form.get('password', '') # Password optional hai

    temp_input_path, temp_output_path = None, None
    try:
        temp_input_path = create_temp_file(file.stream, ".pdf")
        temp_output_path = temp_input_path.replace(".pdf", "_unlocked.pdf")
        
        # NOTE: 'qpdf' command server par install hona chahiye
        command = [
            'qpdf',
            '--decrypt',
            f'--password={password}',
            temp_input_path,
            temp_output_path
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            if "invalid password" in result.stderr:
                return jsonify({"error": "Invalid password"}), 400
            return jsonify({"error": f"QPDF error: {result.stderr}"}), 500
        
        return send_file(temp_output_path, as_attachment=True, download_name='unlocked.pdf')
    
    except FileNotFoundError:
        return jsonify({"error": "QPDF is not installed on the server"}), 500
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally:
        cleanup_files([temp_input_path, temp_output_path])

# --- Office to PDF Features (Requires LibreOffice) ---
# Yeh sabse complex features hain. Server par LibreOffice install hona zaroori hai.

def office_to_pdf_converter(file, input_suffix):
    temp_input_path, temp_output_dir = None, None
    try:
        temp_input_path = create_temp_file(file.stream, input_suffix)
        temp_output_dir = tempfile.mkdtemp() # Output ke liye ek directory
        
        # NOTE: 'libreoffice' command server par install hona chahiye
        command = [
            'libreoffice',
            '--headless', # Bina UI ke chalao
            '--convert-to', 'pdf',
            '--outdir', temp_output_dir,
            temp_input_path
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            return None, f"LibreOffice error: {result.stderr}"

        # Output file ka naam dhoondna
        output_filename = os.path.splitext(os.path.basename(temp_input_path))[0] + '.pdf'
        output_pdf_path = os.path.join(temp_output_dir, output_filename)
        
        if not os.path.exists(output_pdf_path):
            return None, "Converted file not found"
        
        return output_pdf_path, None # Success
    
    except FileNotFoundError:
        return None, "LibreOffice is not installed on the server"
    except subprocess.TimeoutExpired:
        return None, "Conversion timed out (30 seconds)"
    except Exception as e:
        return None, f"An error occurred: {str(e)}"
    finally:
        # Input file delete karna, output directory (aur file) ko nahi
        cleanup_files([temp_input_path]) 

# --- Feature 13: Word to PDF (Requires LibreOffice) (New) ---
@app.route('/api/word-to-pdf', methods=['POST'])
def word_to_pdf():
    if 'file' not in request.files: return jsonify({"error": "No file found"}), 400
    file = request.files['file']
    if not file.filename.endswith(('.doc', '.docx')):
        return jsonify({"error": "File is not a Word document"}), 400
    
    output_pdf_path, error = office_to_pdf_converter(file, ".docx")
    
    if error:
        return jsonify({"error": error}), 500
    
    try:
        return send_file(output_pdf_path, as_attachment=True, download_name='converted.pdf')
    finally:
        cleanup_dir(os.path.dirname(output_pdf_path)) # Poori directory delete karna

# --- Feature 14: Excel to PDF (Requires LibreOffice) (New) ---
@app.route('/api/excel-to-pdf', methods=['POST'])
def excel_to_pdf():
    if 'file' not in request.files: return jsonify({"error": "No file found"}), 400
    file = request.files['file']
    if not file.filename.endswith(('.xls', '.xlsx')):
        return jsonify({"error": "File is not an Excel document"}), 400
    
    output_pdf_path, error = office_to_pdf_converter(file, ".xlsx")
    
    if error:
        return jsonify({"error": error}), 500
    
    try:
        return send_file(output_pdf_path, as_attachment=True, download_name='converted.pdf')
    finally:
        cleanup_dir(os.path.dirname(output_pdf_path))

# --- Feature 15: PPT to PDF (Requires LibreOffice) (New) ---
@app.route('/api/ppt-to-pdf', methods=['POST'])
def ppt_to_pdf():
    if 'file' not in request.files: return jsonify({"error": "No file found"}), 400
    file = request.files['file']
    if not file.filename.endswith(('.ppt', '.pptx')):
        return jsonify({"error": "File is not a PowerPoint document"}), 400
    
    output_pdf_path, error = office_to_pdf_converter(file, ".pptx")
    
    if error:
        return jsonify({"error": error}), 500
    
    try:
        return send_file(output_pdf_path, as_attachment=True, download_name='converted.pdf')
    finally:
        cleanup_dir(os.path.dirname(output_pdf_path))

# --- Server ko Run Karna ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
