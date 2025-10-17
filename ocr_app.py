#!/usr/bin/env python3
"""
OCR Application using Qwen2-VL API
Supports local/remote images, multi-page documents, and PDF files.
"""

import argparse
import base64
import io
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

import requests
from PIL import Image
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# PDF conversion libraries
try:
    import pypdfium2 as pdfium
    PDF_BACKEND = 'pypdfium2'
except ImportError:
    try:
        from pdf2image import convert_from_path
        PDF_BACKEND = 'pdf2image'
    except ImportError:
        PDF_BACKEND = None


class OCRApp:
    """OCR application using Qwen2-VL vision-language model."""

    def __init__(self, api_url: str, api_key: str, model: str = "qwen2-vl-32b-instruct-awq"):
        """
        Initialize OCR app.

        Args:
            api_url: API endpoint URL
            api_key: Bearer token for authentication
            model: Model name to use
        """
        self.api_url = api_url
        self.api_key = api_key
        self.model = model

    def pdf_to_images(self, pdf_path: str, dpi: int = 200) -> List[Image.Image]:
        """
        Convert PDF to list of PIL Images.

        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for conversion (default: 200)

        Returns:
            List of PIL Image objects
        """
        if PDF_BACKEND is None:
            raise ImportError(
                "No PDF library available. Install either:\n"
                "  pip install pypdfium2\n"
                "or:\n"
                "  pip install pdf2image\n"
                "  (pdf2image also requires poppler-utils)"
            )

        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if PDF_BACKEND == 'pypdfium2':
            pdf = pdfium.PdfDocument(pdf_path)
            images = []
            for page_num in range(len(pdf)):
                page = pdf[page_num]
                bitmap = page.render(scale=dpi/72)
                pil_image = bitmap.to_pil()
                images.append(pil_image)
            return images

        elif PDF_BACKEND == 'pdf2image':
            return convert_from_path(pdf_path, dpi=dpi)

    def resize_image_if_needed(self, image: Image.Image, max_width: int = 1024, max_height: int = 1024) -> Image.Image:
        """
        Resize image if it exceeds maximum dimensions to reduce token usage.

        Args:
            image: PIL Image object
            max_width: Maximum width in pixels
            max_height: Maximum height in pixels

        Returns:
            Resized PIL Image object
        """
        width, height = image.size

        if width <= max_width and height <= max_height:
            return image

        # Calculate aspect ratio
        ratio = min(max_width / width, max_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)

        print(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def image_to_base64(self, image: Image.Image, format: str = 'PNG') -> str:
        """
        Convert PIL Image to base64 data URL with auto-resize.

        Args:
            image: PIL Image object
            format: Image format (PNG, JPEG, etc.)

        Returns:
            Base64 encoded data URL
        """
        # Resize image if needed to reduce token count
        image = self.resize_image_if_needed(image)

        buffered = io.BytesIO()
        # Use JPEG for better compression if format allows
        if format.upper() in ['PNG', 'BMP']:
            image.save(buffered, format='JPEG', quality=85)
            mime_type = 'image/jpeg'
        else:
            image.save(buffered, format=format, quality=85 if format.upper() == 'JPEG' else None)
            mime_type = f'image/{format.lower()}'

        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return f"data:{mime_type};base64,{img_str}"

    def encode_image_base64(self, image_path: str) -> str:
        """
        Encode local image to base64 data URL with auto-resize for large images.

        Args:
            image_path: Path to local image file

        Returns:
            Base64 encoded data URL
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Load image with PIL and resize if needed
        try:
            image = Image.open(image_path)

            # Convert RGBA to RGB if needed
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            # Resize if needed to reduce token count
            image = self.resize_image_if_needed(image)

            # Convert to JPEG with good quality for smaller size
            buffered = io.BytesIO()
            image.save(buffered, format='JPEG', quality=85)
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

            return f"data:image/jpeg;base64,{img_str}"

        except Exception as e:
            raise Exception(f"Failed to process image {image_path}: {e}")

    def ocr_image(self, image_source: str, prompt: str = "OCR this image and summarize key fields.") -> Dict[str, Any]:
        """
        Perform OCR on a single image.

        Args:
            image_source: URL or local file path to image
            prompt: Custom prompt for OCR task

        Returns:
            API response as dictionary
        """
        # Determine if source is URL or local file
        if image_source.startswith(('http://', 'https://')):
            image_url = image_source
        else:
            # Local file - encode to base64
            image_url = self.encode_image_base64(image_source)

        # Prepare API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ]
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=300)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status_code": getattr(e.response, 'status_code', None)}

    def ocr_multiple_images(self, images: List[str], prompt: str = "OCR this image and extract all text.") -> List[Dict[str, Any]]:
        """
        Perform OCR on multiple images.

        Args:
            images: List of image URLs or PIL Image objects
            prompt: Custom prompt for OCR task

        Returns:
            List of API responses
        """
        results = []
        for idx, img in enumerate(images, 1):
            print(f"Processing image {idx}/{len(images)}...")

            if isinstance(img, Image.Image):
                # Convert PIL Image to base64
                image_url = self.image_to_base64(img)
            else:
                # String path or URL
                if img.startswith(('http://', 'https://')):
                    image_url = img
                else:
                    image_url = self.encode_image_base64(img)

            # Prepare API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            page_prompt = f"{prompt} (Page {idx}/{len(images)})"
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": page_prompt},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ]
            }

            try:
                response = requests.post(self.api_url, headers=headers, json=payload, timeout=300)
                response.raise_for_status()
                results.append({"page": idx, "response": response.json()})
            except requests.exceptions.RequestException as e:
                results.append({
                    "page": idx,
                    "response": {"error": str(e), "status_code": getattr(e.response, 'status_code', None)}
                })

        return results

    def process_pdf(self, pdf_path: str, prompt: str = "OCR this image and extract all text.", dpi: int = 200) -> List[Dict[str, Any]]:
        """
        Process a PDF file and perform OCR on all pages.

        Args:
            pdf_path: Path to PDF file
            prompt: Custom prompt for OCR task
            dpi: Resolution for PDF conversion

        Returns:
            List of API responses for each page
        """
        print(f"Converting PDF to images (DPI: {dpi})...")
        images = self.pdf_to_images(pdf_path, dpi=dpi)
        print(f"Found {len(images)} page(s)")
        return self.ocr_multiple_images(images, prompt)

    def extract_text(self, api_response: Dict[str, Any]) -> str:
        """
        Extract OCR text from API response.

        Args:
            api_response: Raw API response

        Returns:
            Extracted text content
        """
        if "error" in api_response:
            return f"Error: {api_response['error']}"

        try:
            return api_response['choices'][0]['message']['content']
        except (KeyError, IndexError) as e:
            return f"Error parsing response: {e}\nRaw response: {json.dumps(api_response, indent=2)}"


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='OCR application using Qwen2-VL API with PDF and multi-page support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # OCR from remote URL
  python ocr_app.py https://example.com/image.png

  # OCR from local file
  python ocr_app.py /path/to/image.jpg

  # OCR from PDF file
  python ocr_app.py document.pdf

  # OCR multiple files
  python ocr_app.py image1.jpg image2.png document.pdf

  # Custom prompt
  python ocr_app.py image.png --prompt "Extract all text from this invoice"

  # High resolution PDF processing
  python ocr_app.py document.pdf --dpi 300
        """
    )

    # Get default values from environment variables
    default_api_url = os.getenv('API_URL', '')
    default_api_key = os.getenv('API_KEY', '')
    default_model = os.getenv('MODEL', 'qwen2-vl-32b-instruct-awq')
    default_dpi = int(os.getenv('DEFAULT_DPI', '200'))

    parser.add_argument('files', nargs='+', help='Image URLs, image files, or PDF files (can specify multiple)')
    parser.add_argument('--prompt', '-p',
                       default='OCR this image and extract all text.',
                       help='Custom OCR prompt (default: "OCR this image and extract all text.")')
    parser.add_argument('--api-url',
                       default=default_api_url,
                       help=f'API endpoint URL (default: {default_api_url})')
    parser.add_argument('--api-key',
                       default=default_api_key,
                       help='API authentication key')
    parser.add_argument('--model',
                       default=default_model,
                       help=f'Model name to use (default: {default_model})')
    parser.add_argument('--output', '-o',
                       help='Save OCR result to file')
    parser.add_argument('--json', action='store_true',
                       help='Output full JSON response')
    parser.add_argument('--dpi',
                       type=int,
                       default=default_dpi,
                       help=f'DPI for PDF conversion (default: {default_dpi})')
    parser.add_argument('--separate-pages', action='store_true',
                       help='Show results separated by page')

    args = parser.parse_args()

    # Initialize OCR app
    app = OCRApp(args.api_url, args.api_key, args.model)

    print(f"Processing {len(args.files)} file(s)")
    print(f"Using model: {args.model}")
    print("=" * 60)

    all_results = []

    for file_idx, file_path in enumerate(args.files, 1):
        print(f"\n[File {file_idx}/{len(args.files)}]: {file_path}")
        print("-" * 60)

        try:
            # Check if it's a PDF
            if file_path.lower().endswith('.pdf') and not file_path.startswith(('http://', 'https://')):
                # Process PDF
                results = app.process_pdf(file_path, args.prompt, args.dpi)
                all_results.extend(results)
            else:
                # Single image
                response = app.ocr_image(file_path, args.prompt)
                all_results.append({"file": file_path, "response": response})
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            all_results.append({"file": file_path, "response": {"error": str(e)}})

    # Format and display output
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    output_lines = []

    for idx, result in enumerate(all_results, 1):
        if args.json:
            output_lines.append(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if 'page' in result:
                # Multi-page result
                page_num = result['page']
                text = app.extract_text(result['response'])
                if args.separate_pages:
                    output_lines.append(f"\n--- Page {page_num} ---")
                    output_lines.append(text)
                else:
                    output_lines.append(text)
            else:
                # Single file result
                file_name = result.get('file', f'Result {idx}')
                text = app.extract_text(result['response'])
                if len(args.files) > 1:
                    output_lines.append(f"\n--- {file_name} ---")
                output_lines.append(text)

    output = '\n'.join(output_lines)
    print(output)

    # Save to file if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\nResult saved to: {args.output}")

    # Return error code if any errors occurred
    has_errors = any('error' in r.get('response', {}) for r in all_results)
    return 1 if has_errors else 0


if __name__ == '__main__':
    sys.exit(main())
