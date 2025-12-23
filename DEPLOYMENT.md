# Deployment Instructions

## Quick Start

### Prerequisites
- Python 3.8+
- Tesseract OCR
- Git

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd image-text-extractor
   ```

2. **Install system dependencies:**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install tesseract-ocr tesseract-ocr-eng python3-pip

   # Set Tesseract environment
   export TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata \
   PYTHONPATH=/path/to/image-text-extractor \
   python3 -m uvicorn main:app --host 0.0.0.0 --port 8080
   ```

### Docker Deployment

1. **Build and run with Docker:**
   ```bash
   docker-compose up --build
   ```

2. **Or build manually:**
   ```bash
   docker build -t image-text-extractor .
   docker run -p 8080:8080 image-text-extractor
   ```

### API Usage

**Extract text from image:**
```bash
curl -X POST "http://localhost:8080/api/v1/text/extract" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_image.png" \
  -F "ocr_engine=tesseract" \
  -F "confidence_threshold=0.3"
```

**Health check:**
```bash
curl http://localhost:8080/api/v1/health/status
```

### API Documentation

- Swagger UI: `http://localhost:8080/api/v1/docs`
- ReDoc: `http://localhost:8080/api/v1/redoc`

## Production Deployment

### Environment Variables
Copy `.env.example` to `.env` and configure:

```env
# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=Image Text Extraction API
VERSION=1.0.0

# Server Settings
HOST=0.0.0.0
PORT=8080
DEBUG=false

# OCR Settings
TESSERACT_CONFIG=--oem 3 --psm 3
DEFAULT_LANGUAGE=eng
MAX_FILE_SIZE=10485760

# Upload Settings
UPLOAD_DIR=./uploads
ALLOWED_EXTENSIONS=png,jpg,jpeg,gif,bmp,tiff,webp

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Key Features

✅ **Production Ready**
- Layered architecture with dependency injection
- Comprehensive error handling and logging
- Input validation and security
- Docker containerization
- Health checks and monitoring

✅ **OCR Excellence**
- Intelligent text spacing correction
- Word splitting for merged text
- Position-based spacing analysis
- Multiple confidence thresholds
- Language detection

✅ **Developer Friendly**
- Auto-generated API documentation
- Comprehensive test structure
- Clean code architecture
- Type hints and validation
- Detailed logging and debugging

## Troubleshooting

**Tesseract not found:**
```bash
# Check installation
tesseract --version

# Set correct environment
export TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
```

**Port already in use:**
```bash
# Check what's using the port
sudo lsof -i :8080

# Kill the process
sudo kill -9 <PID>
```

**Import errors:**
```bash
# Make sure PYTHONPATH is set
export PYTHONPATH=/path/to/image-text-extractor
```