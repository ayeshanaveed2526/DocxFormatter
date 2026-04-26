import os
import json
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from document_processor import process_document

app = Flask(__name__)
# Allow requests from any origin (covers Vercel frontend + local dev)
CORS(app, origins="*")

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

@app.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200

@app.route('/api/format', methods=['POST'])
def format_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        rules_json = request.form.get('rules', '{}')
        rules = json.loads(rules_json)
    except Exception:
        rules = {}

    if file and file.filename.endswith('.docx'):
        import time
        ts = int(time.time())
        filename    = f"{ts}_{secure_filename(file.filename)}"
        input_path  = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)

        output_filename = f"formatted_{filename}"
        output_path     = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        try:
            process_document(input_path, output_path, rules)
            
            # Use a helper to send file and then cleanup
            response = send_file(
                output_path,
                as_attachment=True,
                download_name=output_filename,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            
            # Clean up input file immediately
            if os.path.exists(input_path):
                os.remove(input_path)
                
            return response
        except Exception as e:
            if os.path.exists(input_path): os.remove(input_path)
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Invalid file format. Only .docx is supported.'}), 400

@app.after_request
def cleanup_outputs(response):
    """
    Optional: You could add logic here to periodically clean the OUTPUT_FOLDER 
    if you don't delete them immediately.
    """
    return response

if __name__ == '__main__':
    # Use environment variable for port (Render provides $PORT)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
