"""
Test configuration and fixtures.

This module provides common test configuration, fixtures, and utilities.
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator, Dict, List, Any
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
import tempfile
import os

from app.main import app
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create event loop for async tests.
    
    TODO:
    - Add event loop cleanup
    - Implement custom event loop policies
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """
    Create test client for FastAPI app.
    
    TODO:
    - Add test database configuration
    - Implement test authentication
    - Add test data seeding
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture
def test_settings() -> object:
    """
    Provide test configuration settings.
    
    TODO:
    - Override production settings
    - Add test-specific configuration
    - Implement environment isolation
    """
    test_settings = settings
    # TODO: Add proper test configuration when Settings supports modification
    # Override for testing
    # settings.TESTING = True
    # settings.DATABASE_URL = "sqlite:///./test.db"
    # settings.JWT_SECRET_KEY = "test-secret-key"
    return test_settings


@pytest.fixture
def mock_storage_service() -> AsyncMock:
    """
    Mock storage service for testing.
    
    TODO:
    - Add realistic mock responses
    - Implement state management
    - Add error simulation
    """
    mock = AsyncMock()
    mock.upload_file.return_value = {
        "file_id": "test-file-id",
        "filename": "test.pdf",
        "storage_url": "https://test-bucket.s3.amazonaws.com/test-file-id",
        "size": 1024,
        "content_type": "application/pdf"
    }
    return mock


@pytest.fixture
def mock_ocr_service() -> AsyncMock:
    """
    Mock OCR service for testing.
    
    TODO:
    - Add realistic OCR responses
    - Implement confidence scoring
    - Add language detection
    """
    mock = AsyncMock()
    mock.extract_text.return_value = {
        "text": "This is sample extracted text",
        "confidence": 0.95,
        "language": "en",
        "pages": 1,
        "processing_time": 2.5
    }
    return mock


@pytest.fixture
def mock_auth_service() -> AsyncMock:
    """
    Mock authentication service for testing.
    
    TODO:
    - Add token generation and validation
    - Implement user role simulation
    - Add permission testing
    """
    mock = AsyncMock()
    mock.verify_token.return_value = {
        "user_id": "test-user-id",
        "username": "testuser",
        "roles": ["user"],
        "permissions": ["read", "write"]
    }
    return mock


@pytest.fixture
def sample_pdf_content() -> bytes:
    """
    Provide sample PDF content for testing.
    
    TODO:
    - Add various PDF types
    - Include malformed PDFs for error testing
    - Add encrypted PDF samples
    """
    # Simple PDF header for testing
    return b"%PDF-1.4\n%Sample PDF content for testing"


@pytest.fixture
def sample_image_content() -> bytes:
    """
    Provide sample image content for testing.
    
    TODO:
    - Add various image formats
    - Include corrupted images for error testing
    - Add images with different resolutions
    """
    # Simple PNG header for testing
    return b"\x89PNG\r\n\x1a\n" + b"0" * 100


@pytest.fixture
def temp_file() -> Generator[str, None, None]:
    """
    Create temporary file for testing.
    
    TODO:
    - Add automatic cleanup
    - Support different file types
    - Add file content customization
    """
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test content")
        tmp_path = tmp.name
    
    yield tmp_path
    
    # Cleanup
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def test_user_data() -> dict[str, object]:
    """
    Provide test user data.
    
    TODO:
    - Add various user types
    - Include invalid user data
    - Add user permissions and roles
    """
    return {
        "user_id": "test-user-123",
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["user"],
        "permissions": ["read", "write"],
        "is_active": True
    }


@pytest.fixture
def test_document_data() -> dict[str, object]:
    """
    Provide test document data.
    
    TODO:
    - Add various document types
    - Include metadata examples
    - Add processing status variations
    """
    return {
        "id": "test-doc-123",
        "filename": "test-document.pdf",
        "content_type": "application/pdf",
        "size": 1024,
        "user_id": "test-user-123",
        "status": "uploaded",
        "metadata": {
            "pages": 1,
            "language": "en"
        }
    }


class MockDatabase:
    """
    Mock database for testing.
    
    TODO:
    - Implement CRUD operations
    - Add transaction support
    - Implement query simulation
    """
    
    def __init__(self) -> None:
        self.data: Dict[str, List[Dict[str, Any]]] = {}
    
    async def save(self, table: str, data: Dict[str, Any]) -> None:
        """Save data to mock table."""
        if table not in self.data:
            self.data[table] = []
        self.data[table].append(data)
    
    async def find(self, table: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find data in mock table."""
        if table not in self.data:
            return []
        return [item for item in self.data[table] if all(
            item.get(k) == v for k, v in query.items()
        )]


@pytest.fixture
def mock_database() -> MockDatabase:
    """Provide mock database instance."""
    return MockDatabase()


class TestHelpers:
    """
    Helper functions for testing.
    
    TODO:
    - Add data generation helpers
    - Implement assertion helpers
    - Add test utilities
    """
    
    @staticmethod
    def create_test_file(content: bytes, filename: str = "test.txt") -> str:
        """Create test file with content."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=filename) as tmp:
            tmp.write(content)
            return tmp.name
    
    @staticmethod
    def assert_response_format(response_data: Dict[str, Any]) -> None:
        """Assert standard response format."""
        assert "success" in response_data
        assert "message" in response_data
        assert "timestamp" in response_data
        assert "status_code" in response_data


# Performance testing fixtures
@pytest.fixture
def performance_test_data() -> Dict[str, Any]:
    """
    Provide data for performance testing.
    
    TODO:
    - Add large file samples
    - Include batch processing data
    - Add concurrent request simulation
    """
    return {
        "large_file_size": 10 * 1024 * 1024,  # 10MB
        "concurrent_requests": 50,
        "batch_size": 100
    }


# Security testing fixtures
@pytest.fixture
def security_test_data() -> Dict[str, List[str]]:
    """
    Provide data for security testing.
    
    TODO:
    - Add malicious file samples
    - Include injection attack vectors
    - Add authentication bypass attempts
    """
    return {
        "malicious_filenames": [
            "../../../etc/passwd",
            "<script>alert('xss')</script>.pdf",
            "file'; DROP TABLE documents; --"
        ],
        "invalid_tokens": [
            "invalid-jwt-token",
            "expired.jwt.token",
            ""
        ]
    }
