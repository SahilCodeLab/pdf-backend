from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from weasyprint import HTML
import io
from datetime import datetime

app = Flask(__name__)
CORS(app)   # Flutter (different origin) की अनुमति देता है

def parse_text(text: str):
    """Simple Q‑A splitter – हर दो लाइनों को Question / Answer मान लेता है."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    pairs = []
    for i in range(0, len(lines), 2):
        q = lines[i]
        a = lines[i + 1] if i + 1 < len(lines) else ''
        pairs.append((q, a))
    return pairs

def make_html(subject: str, qa_pairs):
    html = f"""<!doctype html>
<html><head>
<meta charset="UTF-8">
<style>
  body {{font-family: Arial, sans-serif; margin: 20px;}}
  .q {{font-weight: bold; margin-top: 15px;}}
  .a {{margin-left: 20px;}}
  @page {{size: A4; margin: 1.5cm;}}
</style>
</head><body>
<h2>{subject}</h2>
<p>Generated: {datetime.now().strftime('%d %b %Y %I:%M %p')}</p>
"""
    for q, a in qa_pairs:
        html += f'<div class="q">{q}</div>\n<div class="a">{a}</div>\n'
    html += "</body></html>"
    return html

@app.route('/')
def health():
    return jsonify({
        "status": "OK",
        "message": "PDF backend is live",
        "features": ["simple Q&A → PDF"]
    })

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    data = request.get_json()
    subject = data.get('subject', 'My Document')
    bulk   = data.get('bulk_text', '')

    if not bulk.strip():
        return jsonify({"error": "bulk_text empty"}), 400

    qa_pairs = parse_text(bulk)
    html = make_html(subject, qa_pairs)

    pdf_bytes = HTML(string=html).write_pdf()
    pdf_file = io.BytesIO(pdf_bytes)
    pdf_file.seek(0)

    filename = f"{data.get('filename','doc')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(
        pdf_file,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    # Render/Render‑Free में debug=False रखें
    app.run(host='0.0.0.0', port=5000, debug=False)
