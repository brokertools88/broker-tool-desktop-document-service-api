# InsureCove Document Service

A secure, scalable document processing service with OCR capabilities using Mistral AI, built with FastAPI and AWS integration.

## 🚀 Features

- **Secure Document Upload**: Multi-format file upload with validation and virus scanning
- **OCR Processing**: Text extraction using Mistral AI OCR with confidence scoring
- **AWS S3 Integration**: Scalable cloud storage with lifecycle management
- **JWT Authentication**: Secure API access with role-based permissions
- **RESTful API**: Following 2024 API standards with comprehensive documentation
- **Async Processing**: Background task processing for large documents
- **Comprehensive Logging**: Structured logging with audit trails
- **Production Ready**: Docker containerization with monitoring and scaling

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+
- AWS Account with S3 access
- Mistral AI API access

## 🛠️ Installation

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd broker-tool-desktop-document-service-api
   ```

2. **Set up Python environment:**
   
   On **Windows**:
   ```powershell
   py -3 -m venv venv
   venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```
   
   On **Linux/Mac**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements-dev.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start services with Docker Compose:**
   ```bash
   docker-compose up -d postgres redis
   ```

5. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Start the development server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Docker Deployment

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

2. **Run migrations:**
   ```bash
   docker-compose exec document-api alembic upgrade head
   ```

## 📖 API Documentation

Once the service is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `AWS_ACCESS_KEY_ID` | AWS access key | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - |
| `S3_BUCKET_NAME` | S3 bucket for document storage | - |
| `JWT_SECRET_KEY` | JWT signing secret | - |
| `MISTRAL_API_KEY` | Mistral AI API key | - |
| `MAX_FILE_SIZE` | Maximum file size (bytes) | 50MB |
| `ALLOWED_FILE_TYPES` | Comma-separated MIME types | - |

### AWS Configuration

1. **Create S3 bucket:**
   ```bash
   aws s3 mb s3://your-document-bucket
   ```

2. **Set up IAM permissions:**
   - S3 read/write access
   - KMS encryption permissions (if using)

3. **Configure lifecycle policies** (see `docs/AWS_SECRET.md`)

## 🧪 Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# All tests with coverage
pytest --cov=app tests/

# Performance tests
pytest tests/performance/
```

### Test Coverage

```bash
coverage run -m pytest
coverage report
coverage html  # Generate HTML report
```

## 📊 Monitoring

### Health Checks

- **Application Health**: `GET /health`
- **Database Health**: `GET /health/db`
- **Redis Health**: `GET /health/redis`
- **S3 Health**: `GET /health/s3`

### Metrics

The service exposes Prometheus metrics at `/metrics`:

- Request rates and latencies
- Document processing metrics
- Storage utilization
- Error rates

### Logging

Structured JSON logging with correlation IDs:

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "INFO",
  "message": "Document uploaded successfully",
  "correlation_id": "req-123",
  "user_id": "user-456",
  "file_id": "doc-789"
}
```

## 🔒 Security

### Authentication

- **Auth Microservice Integration**: Uses the existing InsureCove authentication microservice
- **JWT Token Validation**: Validates tokens through the auth service API
- **Role-based Access Control (RBAC)**: User permissions managed by auth service
- **Service-to-Service Communication**: API key support for internal service calls

### File Security

- Content-type validation
- Virus scanning integration
- File size limits
- Malicious content detection

### Infrastructure Security

- HTTPS/TLS encryption
- Security headers
- Input validation and sanitization
- SQL injection prevention

## 🚀 Deployment

### Production Deployment

1. **Build production image:**
   ```bash
   docker build -t document-service:latest .
   ```

2. **Deploy with Docker Compose:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Set up monitoring:**
   ```bash
   docker-compose --profile monitoring up -d
   ```

### Kubernetes Deployment

See `deploy/kubernetes/` for Kubernetes manifests and Helm charts.

### AWS ECS Deployment

See `deploy/ecs/` for ECS task definitions and service configurations.

## 📚 API Usage Examples

### Upload Document

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
     -H "Authorization: Bearer <token>" \
     -F "file=@document.pdf"
```

### Process OCR

```bash
curl -X POST "http://localhost:8000/api/v1/ocr/process" \
     -H "Authorization: Bearer <token>" \
     -F "file=@document.pdf" \
     -F "language=en"
```

### Get OCR Result

```bash
curl -X GET "http://localhost:8000/api/v1/ocr/result/<task_id>" \
     -H "Authorization: Bearer <token>"
```

## 🛣️ Development Roadmap

### Phase 1: Core Implementation ✅
- [x] Project structure and design
- [ ] Core API endpoints
- [ ] AWS S3 integration
- [ ] Basic OCR integration

### Phase 2: Advanced Features
- [ ] Mistral OCR integration
- [ ] Advanced file validation
- [ ] Batch processing
- [ ] Caching layer

### Phase 3: Production Readiness
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Monitoring and alerting

### Phase 4: Enhancements
- [ ] Multi-language OCR
- [ ] Advanced analytics
- [ ] Machine learning improvements
- [ ] API versioning

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation
- Use meaningful commit messages
- Add type hints

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Full Documentation](docs/)
- **Issues**: [GitHub Issues](../../issues)
- **Discussions**: [GitHub Discussions](../../discussions)

## 🙏 Acknowledgments

- FastAPI team for the excellent framework
- Mistral AI for OCR capabilities
- AWS for cloud infrastructure
- The open-source community

---

**Built with ❤️ for InsureCove**
