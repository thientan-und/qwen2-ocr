FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Note: We use pypdfium2 for PDF processing which doesn't require system dependencies
# If you need pdf2image instead, uncomment the following lines:
# RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils && \
#     apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application files
COPY app.py .
COPY ocr_app.py .
COPY templates/ templates/
COPY .env.example .env.example

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8080

# Environment variables (can be overridden)
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=8080
ENV FLASK_DEBUG=False

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health', timeout=5)"

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "--timeout", "300", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
