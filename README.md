# Image Text Extraction API

A robust, production-ready FastAPI application for extracting text from images using Optical Character Recognition (OCR). Built with modern software engineering practices, featuring a clean layered architecture, comprehensive error handling, and extensive monitoring capabilities.

## 🌟 Features

### Core Functionality
- **Multi-Engine OCR**: Support for Tesseract and EasyOCR engines
- **Format Support**: JPEG, PNG, BMP, TIFF, WEBP, GIF
- **Image Preprocessing**: Advanced preprocessing pipeline for better OCR accuracy
- **Multi-Language**: Support for multiple languages
- **Confidence Scoring**: Detailed confidence metrics for extracted text
- **Bounding Boxes**: Precise text region localization

### Architecture & Design
- **Layered Architecture**: Clean separation between API, services, repositories, and utilities
- **Dependency Injection**: Proper IoC container pattern
- **SOLID Principles**: Following SOLID design principles
- **Error Handling**: Comprehensive exception handling with custom exceptions
- **Logging**: Structured logging with Loguru
- **Validation**: Input validation with Pydantic

### Production Features
- **Health Checks**: Kubernetes-ready health, readiness, and liveness probes
- **Monitoring**: Extraction statistics and usage analytics
- **Security**: CORS, security headers, input sanitization
- **Rate Limiting**: Built-in protection against abuse
- **File Management**: Automatic cleanup and storage management
- **Containerization**: Docker and docker-compose ready

## 🏗️ Architecture

```
app/
├── api/
│   └── v1/
│       ├── endpoints/         # API endpoint definitions
│       └── router.py          # API router aggregation
├── core/                      # Core application configuration
│   ├── config.py             # Settings and configuration
│   ├── exceptions.py         # Custom exception definitions
│   ├── middleware.py         # Custom middleware
│   └── logging_config.py     # Logging setup
├── models/                   # Pydantic models
│   └── text_extraction.py   # Request/response models
├── services/                 # Business logic layer
│   ├── text_extraction_service.py  # Main orchestration
│   ├── ocr_service.py              # OCR engine abstraction
│   ├── image_processing_service.py # Image preprocessing
│   └── file_service.py             # File handling
├── repositories/            # Data access layer
│   └── extraction_repository.py   # Result persistence
└── utils/                   # Utility functions
    ├── validators.py        # Input validation
    └── response_helpers.py  # Response formatting
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Tesseract OCR
- Docker (optional)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd image-text-extractor
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install Tesseract OCR**

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

5. **Configure environment**
```bash
cp .env.example .env
# Edit .env file with your settings
```

6. **Run the application**
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Docker Deployment

1. **Build and run with docker-compose**
```bash
docker-compose up -d
```

2. **Or build manually**
```bash
docker build -t image-text-extractor .
docker run -p 8000:8000 image-text-extractor
```

## 📖 API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/api/v1/docs`
- **ReDoc**: `http://localhost:8000/api/v1/redoc`
- **OpenAPI Spec**: `http://localhost:8000/api/v1/openapi.json`

### Main Endpoints

#### Text Extraction
```http
POST /api/v1/text/extract
```

**Parameters:**
- `file`: Image file (multipart/form-data)
- `ocr_engine`: OCR engine (`tesseract` or `easyocr`)
- `languages`: Comma-separated language codes
- `preprocess`: Enable image preprocessing
- `confidence_threshold`: Minimum confidence (0.0-1.0)

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/text/extract" \
     -F "file=@image.jpg" \
     -F "ocr_engine=tesseract" \
     -F "languages=en" \
     -F "preprocess=true" \
     -F "confidence_threshold=0.5"
```

#### Health Checks
```http
GET /health                    # Basic health check
GET /api/v1/health/detailed    # Detailed system health
GET /api/v1/health/readiness   # Kubernetes readiness probe
GET /api/v1/health/liveness    # Kubernetes liveness probe
```

#### System Information
```http
GET /api/v1/text/capabilities  # Supported features
GET /api/v1/text/stats        # Usage statistics
GET /api/v1/text/history      # Recent extractions
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Performance Tests**: Load and stress testing

## 📊 Monitoring

### Health Monitoring
The application provides comprehensive health checks:

- **Basic Health**: Service availability
- **Detailed Health**: System resources, dependencies
- **Readiness**: Service ready to handle requests
- **Liveness**: Service is alive and responsive

### Usage Analytics
Built-in analytics track:
- Extraction success/failure rates
- Processing times
- Engine usage patterns
- Language detection statistics
- File format distribution

### Logging
Structured logging with multiple levels:
- Request/response logging
- Error tracking
- Performance metrics
- Security events

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|--------|
| `API_V1_STR` | API version prefix | `/api/v1` |
| `MAX_FILE_SIZE` | Maximum upload size (bytes) | `10485760` |
| `DEFAULT_OCR_ENGINE` | Default OCR engine | `tesseract` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DEBUG` | Debug mode | `False` |

### OCR Configuration

**Tesseract:**
- `TESSERACT_CONFIG`: OCR configuration string
- Languages: Install additional language packs

**EasyOCR:**
- `EASYOCR_LANGUAGES`: Supported languages list
- GPU support: Automatic detection

## 🚦 Production Deployment

### Performance Optimization
1. **Use production ASGI server**:
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Enable caching**: Redis for result caching

3. **Load balancing**: Multiple worker instances

4. **Resource limits**: Set memory/CPU limits

### Security Checklist
- [ ] Change default secret key
- [ ] Configure CORS properly
- [ ] Set up HTTPS/TLS
- [ ] Implement rate limiting
- [ ] Set up monitoring/alerting
- [ ] Regular security updates

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: image-text-extractor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: image-text-extractor
  template:
    spec:
      containers:
      - name: api
        image: image-text-extractor:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /api/v1/health/liveness
            port: 8000
        readinessProbe:
          httpGet:
            path: /api/v1/health/readiness
            port: 8000
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Set up pre-commit hooks
pre-commit install

# Run code quality checks
black .
flake8 .
mypy .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Documentation**: API docs at `/api/v1/docs`

## 🔄 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

---

**Built with ❤️ using FastAPI, Tesseract, and modern Python practices.**