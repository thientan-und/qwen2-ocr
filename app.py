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

# Multiple Model Configurations
MODELS = {
    'qwen2-vl-32b': {
        'name': 'Qwen2-VL 32B (Local)',
        'api_url': os.getenv('API_URL'),
        'api_key': os.getenv('API_KEY'),
        'model': os.getenv('MODEL', 'qwen2-vl-32b-instruct-awq')
    },
    'qwen2.5-vl-7b': {
        'name': 'Qwen2.5-VL 7B (Hugging Face)',
        'api_url': os.getenv('HF_API_URL', 'https://router.huggingface.co/v1/chat/completions'),
        'api_key': os.getenv('HF_API_KEY'),
        'model': os.getenv('HF_MODEL', 'Qwen/Qwen2.5-VL-7B-Instruct:hyperbolic')
    }
}

# Validate configurations at startup
print("=" * 60)
print("Available Models:")
for model_id, config in MODELS.items():
    status = "✓" if config['api_key'] else "✗"
    print(f"  {status} {model_id}: {config['name']}")
    if not config['api_key']:
        print(f"    ⚠️  Missing API key for {config['name']}")
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
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    # Get selected model
    model_id = request.form.get('model_id', 'qwen2-vl-32b')

    if model_id not in MODELS:
        return jsonify({
            'success': False,
            'error': f'Invalid model_id: {model_id}. Available models: {", ".join(MODELS.keys())}'
        }), 400

    # Get model configuration
    model_config = MODELS[model_id]

    # Check if model is configured
    if not model_config['api_key']:
        return jsonify({
            'success': False,
            'error': f'Model {model_config["name"]} is not configured. Missing API key.'
        }), 500

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
        print(f"Using model: {model_config['name']}")

        # Get custom prompt if provided
        prompt = request.form.get('prompt', 'OCR this image and extract all text.')
        dpi = int(request.form.get('dpi', 200))

        # Initialize OCR app with selected model
        ocr_app = OCRApp(
            model_config['api_url'],
            model_config['api_key'],
            model_config['model']
        )

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
    """Get current API configuration and available models."""
    available_models = []
    for model_id, model_config in MODELS.items():
        available_models.append({
            'id': model_id,
            'name': model_config['name'],
            'configured': bool(model_config['api_key']),
            'api_url': model_config['api_url'] if model_config['api_key'] else 'NOT_CONFIGURED'
        })

    return jsonify({
        'models': available_models,
        'max_file_size': '16MB',
        'allowed_extensions': list(ALLOWED_EXTENSIONS),
        'status': 'ready' if any(m['configured'] for m in available_models) else 'missing_config'
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
    print(f"Allowed file types: {', '.join(ALLOWED_EXTENSIONS)}")
    print(f"Max file size: {MAX_FILE_SIZE_MB}MB")
    print(f"Configured models: {sum(1 for m in MODELS.values() if m['api_key'])}/{len(MODELS)}")
    print("=" * 60)
    print(f"\nStarting server at http://{FLASK_HOST}:{FLASK_PORT}")
    print("Press Ctrl+C to stop\n")

    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)
