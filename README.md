# Qwen2-VL OCR Application

A powerful Python CLI application for performing OCR (Optical Character Recognition) using the Qwen2-VL vision-language model API. Supports single/multiple images, multi-page documents, and PDF files.

## Features

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

### 1. Clone the repository:
```bash
git clone https://github.com/thientan-und/qwen2-ocr.git
cd qwen2-ocr
```

### 2. Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables:

**⚠️ IMPORTANT: You must create a `.env` file before running the application!**

Copy the example file:
```bash
cp .env.example .env
```

Edit `.env` and add your API credentials:
```env
API_URL=http://your-api-server/v1/chat/completions
API_KEY=your_api_key_here
MODEL=qwen2-vl-32b-instruct-awq
```

**Never commit your `.env` file to Git!** It contains sensitive API keys.

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

The default API configuration is:
- **Endpoint:** http://172.20.22.71/v1/chat/completions
- **Model:** qwen2-vl-32b-instruct-awq
- **Auth:** Bearer token authentication

You can override these defaults using command line arguments or by modifying the script.

## Output Formats

### Text Output (default)
Plain text extracted from images, optionally separated by page numbers.

### JSON Output
Full API response with metadata, useful for programmatic processing:
```bash
python ocr_app.py document.pdf --json > output.json
```

## Docker Deployment

### Using Docker Compose

**1. Create `.env` file (for local Docker):**
```bash
cp .env.example .env
# Edit .env with your API credentials
```

**2. Build and run:**
```bash
docker-compose up --build
```

The application will be available at `http://localhost:8080`

### Using Dokploy

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed Dokploy deployment instructions.

**Required Environment Variables in Dokploy:**
```
API_URL=http://your-api-server/v1/chat/completions
API_KEY=your-api-key-here
MODEL=qwen2-vl-32b-instruct-awq
```

**Optional Environment Variables:**
```
MAX_FILE_SIZE_MB=16
UPLOAD_FOLDER=uploads
DEFAULT_DPI=200
FLASK_DEBUG=False
```

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
- Increase timeout in the code (line 169, 221)

## License

MIT
