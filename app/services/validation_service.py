"""
Validation Service for input validation and data sanitization.

This service provides comprehensive validation for API inputs, file uploads, and data processing.
"""

from typing import Dict, List, Optional, Any, Union
import re
import logging
from datetime import datetime
import mimetypes
from pathlib import Path
# TODO: Import python-magic when dependency is added
# import magic  # python-magic for file type detection

from app.core.config import settings
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Service for comprehensive input validation and data sanitization.
    
    TODO:
    - Implement all validation rules
    - Add custom validation decorators
    - Implement data sanitization
    - Add validation caching for performance
    - Implement validation reporting and analytics
    """
    
    def __init__(self):
        self.settings = settings
        # TODO: Initialize validation rules and patterns
        self._init_validation_rules()
    
    def _init_validation_rules(self) -> None:
        """
        Initialize validation rules and patterns.
        
        Define validation patterns for different data types
        Load custom validation rules from configuration
        Initialize file type validation rules
        """
        # Email validation patterns
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.disposable_email_domains = {
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email'
        }
        
        # Phone validation patterns
        self.phone_pattern = re.compile(r'^\+?[\d\s\-\(\)]{10,}$')
        self.international_phone_pattern = re.compile(r'^\+[1-9]\d{1,14}$')
        
        # Filename validation patterns
        self.filename_pattern = re.compile(r'^[a-zA-Z0-9._\-\s]+$')
        self.reserved_filenames = {
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
            'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
            'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        # File type validation
        self.allowed_file_types = {
            'image/jpeg', 'image/png', 'image/tiff', 'image/bmp', 'image/gif',
            'application/pdf', 'text/plain', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        # Security patterns
        self.sql_injection_patterns = [
            re.compile(r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bDELETE\b|\bUPDATE\b)", re.IGNORECASE),
            re.compile(r"(\bDROP\b|\bALTER\b|\bCREATE\b|\bTRUNCATE\b)", re.IGNORECASE),
            re.compile(r"(--|\#|\;|\||`)", re.IGNORECASE)
        ]
        
        self.xss_patterns = [
            re.compile(r"<script[^>]*>", re.IGNORECASE),
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"on\w+\s*=", re.IGNORECASE)
        ]
        
        # Data size limits
        self.max_file_size = getattr(settings, 'MAX_FILE_SIZE', 100 * 1024 * 1024)  # 100MB
        self.max_filename_length = 255
        self.max_metadata_size = 10 * 1024  # 10KB
    
    def validate_email(self, email: str) -> bool:
        """
        Validate email address format with domain and disposable email detection.
        
        Add domain validation
        Implement disposable email detection
        Add custom email rules per organization
        """
        if not email or not isinstance(email, str):
            return False
        
        email = email.strip().lower()
        
        # Basic pattern validation
        if not self.email_pattern.match(email):
            return False
        
        # Check for disposable email domains
        domain = email.split('@')[1] if '@' in email else ''
        if domain in self.disposable_email_domains:
            return False
        
        # Additional domain validation
        if len(domain) < 3 or '.' not in domain:
            return False
        
        # Check for consecutive dots
        if '..' in email:
            return False
        
        return True
    
    def validate_phone(self, phone: str) -> bool:
        """
        Validate phone number format with international support.
        
        Add international format validation
        Implement country-specific validation
        Add phone number normalization
        """
        if not phone or not isinstance(phone, str):
            return False
        
        phone = phone.strip()
        
        # Remove common formatting characters
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Check international format first
        if phone.startswith('+'):
            return bool(self.international_phone_pattern.match(cleaned_phone))
        
        # Check general phone format
        if len(cleaned_phone) < 10 or len(cleaned_phone) > 15:
            return False
        
        # Must contain only digits after cleaning
        if not cleaned_phone.isdigit():
            return False
        
        return bool(self.phone_pattern.match(phone))
    
    def validate_filename(self, filename: str) -> bool:
        """
        Validate filename for security and compatibility with comprehensive checks.
        
        Add path traversal attack prevention
        Implement filename length validation
        Add OS-specific filename validation
        Check for reserved filenames
        """
        if not filename or not isinstance(filename, str):
            return False
        
        filename = filename.strip()
        
        # Check filename length
        if len(filename) > self.max_filename_length:
            return False
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check for reserved filenames (Windows)
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in self.reserved_filenames:
            return False
        
        # Check for control characters
        if any(ord(char) < 32 for char in filename):
            return False
        
        # Check for problematic characters
        forbidden_chars = '<>:"|?*'
        if any(char in filename for char in forbidden_chars):
            return False
        
        # Check basic pattern
        if not self.filename_pattern.match(filename):
            return False
        
        # Must have an extension
        if '.' not in filename:
            return False
        
        return True
        return True
    
    def validate_file_type(self, content: bytes, declared_type: str, filename: str) -> Dict[str, Any]:
        """
        Validate file type against content and security rules with deep inspection.
        
        Args:
            content: File binary content
            declared_type: MIME type declared by client
            filename: Original filename
            
        Returns:
            Validation result with detected type and security info
            
        Implement deep file content inspection
        Add malware detection integration
        Implement polyglot file detection
        Add file structure validation
        """
        result = {
            "is_valid": False,
            "detected_type": None,
            "declared_type": declared_type,
            "security_issues": [],
            "warnings": []
        }
        
        try:
            # Use fallback file type detection (TODO: Use python-magic for accurate detection)
            detected_type = self._detect_file_type_fallback(content, filename)
            result["detected_type"] = detected_type
            
            # Check if detected type matches declared type
            if detected_type != declared_type:
                result["warnings"].append(f"Type mismatch: declared {declared_type}, detected {detected_type}")
            
            # Check if file type is allowed
            if detected_type not in self.allowed_file_types:
                result["security_issues"].append(f"File type not allowed: {detected_type}")
                return result
            
            # Perform security checks
            security_issues = self._check_file_security(content, detected_type)
            result["security_issues"].extend(security_issues)
            
            # Additional content-based security checks
            if self._contains_suspicious_content(content):
                result["security_issues"].append("Suspicious content detected")
            
            # Check for polyglot files (files that are valid in multiple formats)
            if self._is_polyglot_file(content):
                result["security_issues"].append("Potential polyglot file detected")
            
            # File structure validation
            structure_issues = self._validate_file_structure(content, detected_type)
            result["security_issues"].extend(structure_issues)
            
            # Determine if file is valid
            result["is_valid"] = len(result["security_issues"]) == 0
            
            return result
            
        except Exception as e:
            logger.error(f"File type validation failed: {str(e)}")
            result["security_issues"].append(f"Validation error: {str(e)}")
            result["is_valid"] = False
        
        return result
    
    def validate_file_size(self, content: bytes, max_size: Optional[int] = None) -> bool:
        """
        Validate file size against limits.
        
        TODO:
        - Add user-specific size limits
        - Implement progressive size validation
        - Add size-based pricing validation
        """
        max_allowed = max_size or (self.settings.MAX_FILE_SIZE_MB * 1024 * 1024)
        return len(content) <= max_allowed
    
    def validate_api_input(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate API input against schema.
        
        Args:
            data: Input data to validate
            schema: Validation schema
            
        Returns:
            Validation result with errors and sanitized data
            
        TODO:
        - Implement comprehensive schema validation
        - Add data type coercion
        - Implement nested object validation
        - Add custom validation rules
        """
        result = {
            "is_valid": True,
            "errors": {},
            "sanitized_data": {},
            "warnings": []
        }
        
        try:
            # TODO: Implement schema-based validation
            for field, rules in schema.items():
                if field in data:
                    field_result = self._validate_field(data[field], rules)
                    if not field_result["is_valid"]:
                        result["errors"][field] = field_result["errors"]
                        result["is_valid"] = False
                    else:
                        result["sanitized_data"][field] = field_result["value"]
                elif rules.get("required", False):
                    result["errors"][field] = "Field is required"
                    result["is_valid"] = False
            
        except Exception as e:
            logger.error(f"API input validation failed: {str(e)}")
            result["is_valid"] = False
            result["errors"]["_general"] = "Validation failed"
        
        return result
    
    def sanitize_string(self, value: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Sanitize string input for security and consistency.
        
        Implement HTML/script tag removal
        Add SQL injection prevention
        Implement Unicode normalization
        Add profanity filtering option
        """
        if not isinstance(value, str):
            return str(value) if value is not None else ""
        
        options = options or {}
        sanitized = value
        
        # Remove HTML/XML tags
        if options.get('strip_html', True):
            sanitized = re.sub(r'<[^>]+>', '', sanitized)
        
        # Remove script content
        if options.get('remove_scripts', True):
            sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove SQL injection patterns
        if options.get('prevent_sql_injection', True):
            for pattern in self.sql_injection_patterns:
                sanitized = pattern.sub('', sanitized)
        
        # Remove XSS patterns
        if options.get('prevent_xss', True):
            for pattern in self.xss_patterns:
                sanitized = pattern.sub('', sanitized)
        
        # Unicode normalization
        if options.get('normalize_unicode', True):
            import unicodedata
            sanitized = unicodedata.normalize('NFKC', sanitized)
        
        # Trim whitespace
        if options.get('trim_whitespace', True):
            sanitized = sanitized.strip()
        
        # Limit length
        max_length = options.get('max_length')
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
        sanitized = value.strip()
        
        # TODO: Add more sanitization options
        if options.get("remove_html", True):
            sanitized = re.sub(r'<[^>]+>', '', sanitized)
        
        if options.get("max_length"):
            sanitized = sanitized[:options["max_length"]]
        
        return sanitized
    
    def validate_json_structure(self, data: Any, expected_structure: Dict[str, Any]) -> bool:
        """
        Validate JSON data structure.
        
        TODO:
        - Implement recursive structure validation
        - Add type checking for nested objects
        - Implement array validation
        - Add custom structure rules
        """
        # TODO: Implement JSON structure validation
        return True
    
    def _detect_file_type_fallback(self, content: bytes, filename: str) -> str:
        """
        Fallback file type detection when python-magic is not available.
        
        TODO:
        - Implement basic file signature detection
        - Add filename extension mapping
        - Improve accuracy of detection
        """
        # Check file signatures
        if content.startswith(b'%PDF'):
            return 'application/pdf'
        elif content.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        elif content.startswith(b'\x89PNG'):
            return 'image/png'
        
        # Fallback to filename extension
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
    
    def _check_file_security(self, content: bytes, file_type: str) -> List[str]:
        """
        Perform security checks on file content.
        
        TODO:
        - Implement virus scanning integration
        - Add embedded script detection
        - Implement malformed file detection
        - Add suspicious pattern detection
        """
        issues = []
        
        # TODO: Implement comprehensive security checks
        # Basic checks for now
        if len(content) == 0:
            issues.append("Empty file detected")
        
        # TODO: Add more security checks based on file type
        if file_type == 'application/pdf':
            issues.extend(self._check_pdf_security(content))
        elif file_type.startswith('image/'):
            issues.extend(self._check_image_security(content))
        
        return issues
    
    def _check_pdf_security(self, content: bytes) -> List[str]:
        """
        Security checks specific to PDF files.
        
        TODO:
        - Check for embedded JavaScript
        - Detect malformed PDF structure
        - Check for suspicious metadata
        - Validate PDF version compatibility
        """
        issues = []
        
        # Basic PDF security checks
        if b'/JavaScript' in content or b'/JS' in content:
            issues.append("PDF contains JavaScript code")
        
        return issues
    
    def _check_image_security(self, content: bytes) -> List[str]:
        """
        Security checks specific to image files.
        
        TODO:
        - Check for embedded scripts in metadata
        - Validate image structure
        - Check for polyglot attacks
        - Detect steganography indicators
        """
        issues = []
        
        # Basic image security checks
        if b'<script' in content.lower():
            issues.append("Image contains script tags")
        
        return issues
    
    def _contains_suspicious_content(self, content: bytes) -> bool:
        """Check for suspicious content patterns"""
        try:
            # Convert to string for pattern matching (first 1KB only for performance)
            text_content = content[:1024].decode('utf-8', errors='ignore').lower()
            
            # Check for script injections
            for pattern in self.xss_patterns:
                if pattern.search(text_content):
                    return True
            
            # Check for SQL injection patterns
            for pattern in self.sql_injection_patterns:
                if pattern.search(text_content):
                    return True
            
            # Check for embedded executables
            suspicious_signatures = [b'\x4d\x5a', b'\x7f\x45\x4c\x46']  # MZ (PE), ELF headers
            for sig in suspicious_signatures:
                if sig in content[:512]:
                    return True
            
            return False
        except Exception:
            return True  # If we can't check, assume suspicious
    
    def _is_polyglot_file(self, content: bytes) -> bool:
        """Check if file might be a polyglot (valid in multiple formats)"""
        if len(content) < 512:
            return False
        
        # Check for multiple file signatures in the same file
        signatures_found = 0
        
        # Common file signatures
        signatures = {
            b'\xff\xd8\xff': 'jpeg',
            b'\x89\x50\x4e\x47': 'png',
            b'\x25\x50\x44\x46': 'pdf',
            b'\x50\x4b\x03\x04': 'zip/office',
            b'\x4d\x5a': 'exe'
        }
        
        for sig in signatures.keys():
            if sig in content[:512] or sig in content[512:1024]:
                signatures_found += 1
        
        return signatures_found > 1
    
    def _validate_file_structure(self, content: bytes, file_type: str) -> List[str]:
        """Validate file structure based on type"""
        issues = []
        
        try:
            if file_type == 'application/pdf':
                # Basic PDF structure validation
                if not content.startswith(b'%PDF-'):
                    issues.append("Invalid PDF header")
                if b'%%EOF' not in content[-1024:]:
                    issues.append("Missing PDF EOF marker")
            
            elif file_type.startswith('image/'):
                # Basic image validation
                if file_type == 'image/jpeg' and not content.startswith(b'\xff\xd8\xff'):
                    issues.append("Invalid JPEG header")
                elif file_type == 'image/png' and not content.startswith(b'\x89\x50\x4e\x47'):
                    issues.append("Invalid PNG header")
            
            # Check for truncated files
            if len(content) < 512:
                issues.append("File appears to be truncated")
        
        except Exception as e:
            issues.append(f"Structure validation error: {str(e)}")
        
        return issues
    
    def _validate_field(self, value: Any, rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate individual field against rules.
        
        TODO:
        - Implement all validation rule types
        - Add custom validation functions
        - Implement conditional validation
        - Add validation rule composition
        """
        result = {
            "is_valid": True,
            "value": value,
            "errors": []
        }
        
        # TODO: Implement comprehensive field validation
        field_type = rules.get("type", "string")
        
        if field_type == "email":
            if not self.validate_email(str(value)):
                result["is_valid"] = False
                result["errors"].append("Invalid email format")
        elif field_type == "phone":
            if not self.validate_phone(str(value)):
                result["is_valid"] = False
                result["errors"].append("Invalid phone format")
        
        # TODO: Add more field type validations
        
        return result


# TODO: Add validation rule builder
class ValidationRuleBuilder:
    """
    Builder for creating custom validation rules.
    
    TODO:
    - Implement fluent validation rule API
    - Add rule composition and chaining
    - Implement conditional validation rules
    - Add rule serialization for storage
    """
    
    def __init__(self):
        self.rules = {}
    
    def required(self) -> 'ValidationRuleBuilder':
        """Mark field as required."""
        self.rules["required"] = True
        return self
    
    def min_length(self, length: int) -> 'ValidationRuleBuilder':
        """Set minimum length validation."""
        self.rules["min_length"] = length
        return self
    
    def max_length(self, length: int) -> 'ValidationRuleBuilder':
        """Set maximum length validation."""
        self.rules["max_length"] = length
        return self
    
    def pattern(self, regex: str) -> 'ValidationRuleBuilder':
        """Add regex pattern validation."""
        self.rules["pattern"] = regex
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build validation rules."""
        return self.rules.copy()


# TODO: Add validation middleware for FastAPI
class ValidationMiddleware:
    """
    Middleware for automatic request validation.
    
    TODO:
    - Implement FastAPI middleware integration
    - Add automatic validation based on route annotations
    - Implement validation error formatting
    - Add validation metrics and monitoring
    """
    
    def __init__(self, validation_service: ValidationService):
        self.validation_service = validation_service
    
    async def __call__(self, request, call_next):
        """Process request validation."""
        # TODO: Implement middleware logic
        response = await call_next(request)
        return response
