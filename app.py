#!/usr/bin/env python3
"""
Flask Web Application for OCR Testing
Provides a web interface to test OCR functionality with JSON output.
"""

import os
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from ocr_app import OCRApp

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration from environment variables
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '16'))
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_MB * 1024 * 1024
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')

# Ensure upload folder exists
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'pdf'}

# OCR App configuration from environment variables
API_URL = os.getenv('API_URL')
API_KEY = os.getenv('API_KEY')
MODEL = os.getenv('MODEL', 'qwen2-vl-32b-instruct-awq')

# Validate environment variables (warning only at startup)
if not API_URL or not API_KEY:
    print("=" * 60)
    print("⚠️  WARNING: Missing API Configuration!")
    print("=" * 60)
    print("API_URL and API_KEY environment variables are not set.")
    print("The application will start but OCR functionality will not work.")
    print("Please set these variables in your .env file or deployment platform.")
    print("=" * 60)


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint for Docker/Dokploy."""
    return jsonify({'status': 'healthy'}), 200


@app.route('/api/ocr', methods=['POST'])
def ocr():
    """
    OCR endpoint for processing uploaded files.

    Returns JSON response with OCR results.
    """
    # Check API configuration first
    if not API_URL or not API_KEY:
        return jsonify({
            'success': False,
            'error': 'API configuration missing. Please set API_URL and API_KEY environment variables.'
        }), 500

    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    try:
        # Save uploaded file with proper extension
        original_filename = file.filename
        filename = secure_filename(original_filename)

        # Ensure extension is preserved
        if not filename or '.' not in filename:
            # If secure_filename removed extension, restore it
            ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            if ext:
                filename = f"{filename or 'file'}.{ext}"

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        print(f"File saved: {filepath}")
        print(f"Original filename: {original_filename}")
        print(f"Secured filename: {filename}")

        # Get custom prompt if provided
        prompt = request.form.get('prompt', 'OCR this image and extract all text.')
        dpi = int(request.form.get('dpi', 200))

        # Initialize OCR app
        ocr_app = OCRApp(API_URL, API_KEY, MODEL)

        # Determine file type from extension
        file_ext = filename.lower().rsplit('.', 1)[1] if '.' in filename else ''

        # Process file
        if file_ext == 'pdf':
            # Process PDF
            print(f"Processing as PDF: {filepath}")
            results = ocr_app.process_pdf(filepath, prompt, dpi)
            response_data = {
                'success': True,
                'filename': filename,
                'type': 'pdf',
                'pages': len(results),
                'results': results
            }
        else:
            # Process single image
            print(f"Processing as image: {filepath}")
            result = ocr_app.ocr_image(filepath, prompt)
            response_data = {
                'success': True,
                'filename': filename,
                'type': 'image',
                'results': [{'page': 1, 'response': result}]
            }

        # Clean up uploaded file
        os.remove(filepath)

        return jsonify(response_data)

    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR in OCR processing:")
        print(error_trace)

        # Clean up file if it exists
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)

        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': error_trace if app.debug else None
        }), 500


@app.route('/api/config', methods=['GET'])
def config():
    """Get current API configuration."""
    return jsonify({
        'api_url': API_URL or 'NOT_CONFIGURED',
        'api_key_set': bool(API_KEY),
        'model': MODEL,
        'max_file_size': '16MB',
        'allowed_extensions': list(ALLOWED_EXTENSIONS),
        'status': 'ready' if (API_URL and API_KEY) else 'missing_config'
    })


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return jsonify({'error': f'File too large. Maximum size is {MAX_FILE_SIZE_MB}MB'}), 413


if __name__ == '__main__':
    # Get Flask configuration from environment variables
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    print("=" * 60)
    print("OCR Web Application")
    print("=" * 60)
    print(f"API Endpoint: {API_URL}")
    print(f"Model: {MODEL}")
    print(f"Allowed file types: {', '.join(ALLOWED_EXTENSIONS)}")
    print(f"Max file size: {MAX_FILE_SIZE_MB}MB")
    print("=" * 60)
    print(f"\nStarting server at http://{FLASK_HOST}:{FLASK_PORT}")
    print("Press Ctrl+C to stop\n")

    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)
