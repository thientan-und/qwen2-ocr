# Qwen2-VL OCR Application

A powerful Python CLI and Web application for performing OCR (Optical Character Recognition) using the Qwen2-VL vision-language model API. Supports single/multiple images, multi-page documents, and PDF files.

## Features

- **Web Interface** with modern UI for easy testing and visualization
- **Command Line Interface** for automation and batch processing
- Support for both local and remote images
- **PDF file processing** with configurable DPI
- **Multi-page document handling**
- **Batch processing** of multiple files
- Automatic base64 encoding for local images
- Custom OCR prompts
- JSON or text output formats
- Page-separated output option
- Save results to file
- Configurable API endpoint and authentication

## Installation

### 1. Clone or download the repository

### 2. Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables:

Copy the example environment file:
```bash
cp .env.example .env
```

Then edit `.env` file with your API credentials:
```bash
# Qwen2-VL API Configuration
API_URL=http://172.20.22.71/v1/chat/completions
API_KEY=your-api-key-here
MODEL=qwen2-vl-32b-instruct-awq

# Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True

# File Upload Configuration
MAX_FILE_SIZE_MB=16
UPLOAD_FOLDER=uploads

# PDF Processing
DEFAULT_DPI=200
```

**Important:** The `.env` file contains sensitive information. Never commit it to version control!

### 4. PDF Support (choose one):

**Option A - pypdfium2 (recommended, no external dependencies):**
```bash
pip install pypdfium2
```

**Option B - pdf2image (requires poppler):**
```bash
pip install pdf2image
```

For pdf2image on macOS:
```bash
brew install poppler
```

For pdf2image on Ubuntu/Debian:
```bash
sudo apt-get install poppler-utils
```

### 5. Make the script executable (optional):
```bash
chmod +x ocr_app.py
```

## Quick Start

### Web Interface (Recommended for Testing)

Start the web server:
```bash
python app.py
```

Then open your browser and go to: **http://localhost:5000**

The web interface provides:
- Drag-and-drop file upload
- Real-time OCR processing
- JSON output viewer with copy function
- Custom prompt and DPI configuration
- Support for images and PDF files

### Command Line Interface

For automation and batch processing, use the CLI:
```bash
python ocr_app.py your_file.pdf
```

## Usage

### Basic Usage

**OCR from remote URL:**
```bash
python ocr_app.py https://example.com/image.png
```

**OCR from local image:**
```bash
python ocr_app.py /path/to/image.jpg
```

**OCR from PDF file:**
```bash
python ocr_app.py document.pdf
```

**Process multiple files:**
```bash
python ocr_app.py image1.jpg image2.png document.pdf
```

### Advanced Usage

**Custom prompt:**
```bash
python ocr_app.py image.png --prompt "Extract all text from this invoice"
```

**High-resolution PDF processing:**
```bash
python ocr_app.py document.pdf --dpi 300
```

**Show page-separated results:**
```bash
python ocr_app.py document.pdf --separate-pages
```

**Save output to file:**
```bash
python ocr_app.py document.pdf --output result.txt
```

**Get full JSON response:**
```bash
python ocr_app.py image.png --json
```

**Custom API configuration:**
```bash
python ocr_app.py image.png \
  --api-url http://localhost:8000/v1/chat/completions \
  --api-key YOUR_API_KEY \
  --model qwen2-vl-32b-instruct-awq
```

## Command Line Options

```
positional arguments:
  files                 Image URLs, image files, or PDF files (can specify multiple)

options:
  -h, --help            Show help message
  --prompt, -p          Custom OCR prompt
  --api-url             API endpoint URL (default: http://172.20.22.71/v1/chat/completions)
  --api-key             API authentication key
  --model               Model name to use (default: qwen2-vl-32b-instruct-awq)
  --output, -o          Save OCR result to file
  --json                Output full JSON response
  --dpi                 DPI for PDF conversion (default: 200, higher = better quality)
  --separate-pages      Show results separated by page number
```

## Examples

### Single Image Processing

**Extract text from a screenshot:**
```bash
python ocr_app.py screenshot.png
```

**Process a document and save result:**
```bash
python ocr_app.py document.jpg --prompt "Extract all text exactly as shown" -o output.txt
```

**Get structured data from an invoice:**
```bash
python ocr_app.py invoice.png --prompt "Extract invoice number, date, total amount, and vendor name"
```

### PDF Processing

**Basic PDF OCR:**
```bash
python ocr_app.py contract.pdf
```

**High-quality PDF processing:**
```bash
python ocr_app.py scanned_document.pdf --dpi 300 --separate-pages
```

**Extract specific information from PDF:**
```bash
python ocr_app.py invoice.pdf --prompt "Extract all invoice line items with quantities and prices"
```

### Batch Processing

**Process multiple images:**
```bash
python ocr_app.py page1.jpg page2.jpg page3.jpg --separate-pages -o combined.txt
```

**Mixed file types:**
```bash
python ocr_app.py photo.jpg document.pdf screenshot.png
```

**Batch process with custom prompt:**
```bash
python ocr_app.py *.pdf --prompt "Summarize the main content" --separate-pages
```

## Supported File Formats

### Images
- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)
- WebP (.webp)

### Documents
- PDF (.pdf) - All pages processed automatically

## PDF Processing Details

The application supports two PDF backends:

1. **pypdfium2** (recommended):
   - No external dependencies
   - Fast and reliable
   - Automatically selected if installed

2. **pdf2image**:
   - Requires poppler-utils
   - Fallback option
   - Used if pypdfium2 is not available

### DPI Settings

- **Default: 200 DPI** - Good balance between quality and speed
- **150 DPI** - Faster processing, suitable for clean documents
- **300 DPI** - Higher quality, recommended for small text or scanned documents
- **400+ DPI** - Very high quality, slower processing

Example:
```bash
# Fast processing
python ocr_app.py document.pdf --dpi 150

# High quality
python ocr_app.py scanned_document.pdf --dpi 300
```

## API Configuration

The API configuration is managed through environment variables in the `.env` file:

- **API_URL:** API endpoint URL
- **API_KEY:** Bearer token for authentication
- **MODEL:** Model name to use
- **DEFAULT_DPI:** Default DPI for PDF processing

You can override these settings using command line arguments:
```bash
python ocr_app.py document.pdf --api-url http://custom-api/v1/chat/completions --api-key YOUR_KEY
```

Or by modifying the `.env` file directly.

## Output Formats

### Text Output (default)
Plain text extracted from images, optionally separated by page numbers.

### JSON Output
Full API response with metadata, useful for programmatic processing:
```bash
python ocr_app.py document.pdf --json > output.json
```

## 🚀 Deployment

### Docker / Dokploy

This application is ready for production deployment with Docker.

**Quick Deploy with Docker Compose:**
```bash
docker-compose up -d
```

**Deploy to Dokploy:**
1. Push to Git repository
2. Connect repository in Dokploy
3. Set environment variables
4. Deploy

**For detailed instructions**, see [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Step-by-step Dokploy deployment
- Docker setup
- VPS deployment
- Environment variables configuration
- Troubleshooting

### Environment Variables for Production

Set these in your deployment platform:
- `API_URL` - Vision API endpoint (required)
- `API_KEY` - API authentication key (required)
- `MODEL` - Model name (required)
- `FLASK_PORT` - Port to run on (default: 8080)
- `FLASK_DEBUG` - Set to `False` for production

## Troubleshooting

### PDF Import Error
If you see an error about PDF libraries:
```
ImportError: No PDF library available
```

Install one of the PDF backends:
```bash
pip install pypdfium2
# or
pip install pdf2image
```

### Low Quality OCR Results
- Increase DPI: `--dpi 300`
- Use high-resolution source images
- Ensure good image quality (contrast, brightness)

### Timeout Errors
For large PDFs or slow network:
- Process fewer pages at once
- Timeout is set to 5 minutes (300 seconds)

## 📁 Project Structure

```
qwen25-32b-ocr/
├── app.py                 # Flask web application
├── ocr_app.py            # CLI tool and OCR logic
├── templates/            # HTML templates
│   └── index.html
├── uploads/              # Temporary upload directory
├── .env                  # Environment variables (not in git)
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker container definition
├── docker-compose.yml    # Docker Compose configuration
├── .dockerignore         # Docker ignore patterns
├── .gitignore            # Git ignore patterns
├── README.md             # This file
└── DEPLOYMENT.md         # Deployment guide

## License

MIT
