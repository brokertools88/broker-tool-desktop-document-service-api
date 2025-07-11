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
        # Initialize comprehensive validation rules and patterns
        self._init_validation_rules()
        self._setup_security_patterns()
        self._setup_file_type_validators()
    
    def _init_validation_rules(self) -> None:
        """
        Initialize validation rules and patterns with comprehensive coverage.
        
        Define validation patterns for different data types
        Load custom validation rules from configuration
        Initialize file type validation rules
        """
        # Email validation patterns
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.disposable_email_domains = {
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com', 'trashmail.com'
        }
        
        # Phone validation patterns
        self.phone_patterns = {
            'us': re.compile(r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$'),
            'international': re.compile(r'^\+?[1-9]\d{1,14}$'),
            'generic': re.compile(r'^[\+\d\s\-\(\)\.]{10,}$')
        }
        
        # Additional validation patterns
        self.validation_patterns = {
            'zipcode_us': re.compile(r'^\d{5}(?:-\d{4})?$'),
            'url': re.compile(r'^https?://[^\s/$.?#].[^\s]*$'),
            'uuid': re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'),
            'credit_card': re.compile(r'^(?:\d{4}[-\s]?){3}\d{4}$'),
            'ssn': re.compile(r'^\d{3}-?\d{2}-?\d{4}$')
        }
    
    def _setup_security_patterns(self):
        """Initialize comprehensive security threat detection patterns."""
        self.security_patterns = {
            'sql_injection': [
                re.compile(r'(\bUNION\b.*\bSELECT\b)', re.IGNORECASE),
                re.compile(r'(\bDROP\b.*\bTABLE\b)', re.IGNORECASE),
                re.compile(r'(\bINSERT\b.*\bINTO\b)', re.IGNORECASE),
                re.compile(r'(--|\#|\/\*)', re.IGNORECASE),
                re.compile(r'(\'\s*OR\s*\')', re.IGNORECASE),
                re.compile(r'(\bEXEC\b|\bEXECUTE\b)', re.IGNORECASE)
            ],
            'xss': [
                re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
                re.compile(r'javascript:', re.IGNORECASE),
                re.compile(r'on\w+\s*=', re.IGNORECASE),
                re.compile(r'<iframe[^>]*>', re.IGNORECASE),
                re.compile(r'<object[^>]*>', re.IGNORECASE),
                re.compile(r'<embed[^>]*>', re.IGNORECASE)
            ],
            'command_injection': [
                re.compile(r'[;&|`]'),
                re.compile(r'\$\([^)]*\)'),
                re.compile(r'`[^`]*`'),
                re.compile(r'\|\s*\w+'),
                re.compile(r'>\s*/dev/null')
            ],
            'path_traversal': [
                re.compile(r'\.\.[\\/]'),
                re.compile(r'[\\/]\.\.'),
                re.compile(r'%2e%2e'),
                re.compile(r'\.\.%2f'),
                re.compile(r'%2f\.\.%2f')
            ]
        }
    
    def _setup_file_type_validators(self):
        """Initialize file type specific validators with comprehensive signatures."""
        self.file_signatures = {
            'application/pdf': [b'%PDF'],
            'image/jpeg': [b'\xff\xd8\xff'],
            'image/png': [b'\x89PNG\r\n\x1a\n'],
            'image/gif': [b'GIF87a', b'GIF89a'],
            'image/bmp': [b'BM'],
            'image/tiff': [b'II*\x00', b'MM\x00*'],
            'application/zip': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],
            'application/msword': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': [b'PK\x03\x04'],
            'text/plain': []  # No specific signature required
        }
        
        # Maximum file sizes by type (in bytes)
        self.max_file_sizes = {
            'image/jpeg': 10 * 1024 * 1024,  # 10MB
            'image/png': 10 * 1024 * 1024,   # 10MB
            'application/pdf': 50 * 1024 * 1024,  # 50MB
            'text/plain': 5 * 1024 * 1024,   # 5MB
            'default': 25 * 1024 * 1024       # 25MB default
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
        """
        result = {
            "is_valid": True,
            "errors": {},
            "sanitized_data": {},
            "warnings": []
        }
        
        try:
            # Validate required fields
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in data or data[field] is None:
                    result["errors"][field] = f"Field '{field}' is required"
                    result["is_valid"] = False
            
            # Validate each field in the data
            field_schemas = schema.get("properties", {})
            for field_name, field_value in data.items():
                if field_name in field_schemas:
                    field_schema = field_schemas[field_name]
                    field_result = self._validate_field(field_name, field_value, field_schema)
                    
                    if not field_result["is_valid"]:
                        result["errors"][field_name] = field_result["error"]
                        result["is_valid"] = False
                    else:
                        result["sanitized_data"][field_name] = field_result["sanitized_value"]
                        if field_result.get("warning"):
                            result["warnings"].append(f"{field_name}: {field_result['warning']}")
                else:
                    # Unknown field - may be allowed or rejected based on schema
                    if schema.get("additionalProperties", True):
                        result["sanitized_data"][field_name] = field_value
                    else:
                        result["warnings"].append(f"Unknown field '{field_name}' ignored")
            
        except Exception as e:
            logger.error(f"API input validation failed: {str(e)}")
            result["is_valid"] = False
            result["errors"]["validation_error"] = f"Validation failed: {str(e)}"
        
        return result
    
    def _validate_field(self, field_name: str, value: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single field against its schema"""
        result = {
            "is_valid": True,
            "error": None,
            "sanitized_value": value,
            "warning": None
        }
        
        try:
            # Type validation
            expected_type = schema.get("type")
            if expected_type:
                if expected_type == "string" and not isinstance(value, str):
                    if value is not None:
                        result["sanitized_value"] = str(value)
                        result["warning"] = "Value was converted to string"
                elif expected_type == "integer" and not isinstance(value, int):
                    try:
                        result["sanitized_value"] = int(value)
                        result["warning"] = "Value was converted to integer"
                    except (ValueError, TypeError):
                        result["is_valid"] = False
                        result["error"] = "Value must be an integer"
                        return result
                elif expected_type == "boolean" and not isinstance(value, bool):
                    if isinstance(value, str):
                        if value.lower() in ["true", "1", "yes"]:
                            result["sanitized_value"] = True
                        elif value.lower() in ["false", "0", "no"]:
                            result["sanitized_value"] = False
                        else:
                            result["is_valid"] = False
                            result["error"] = "Value must be a boolean"
                            return result
            
            # Length validation for strings
            if isinstance(result["sanitized_value"], str):
                min_length = schema.get("minLength")
                max_length = schema.get("maxLength")
                
                if min_length and len(result["sanitized_value"]) < min_length:
                    result["is_valid"] = False
                    result["error"] = f"Value must be at least {min_length} characters"
                    return result
                    
                if max_length and len(result["sanitized_value"]) > max_length:
                    result["is_valid"] = False
                    result["error"] = f"Value must be no more than {max_length} characters"
                    return result
            
            # Enum validation
            enum_values = schema.get("enum")
            if enum_values and result["sanitized_value"] not in enum_values:
                result["is_valid"] = False
                result["error"] = f"Value must be one of: {', '.join(map(str, enum_values))}"
                return result
            
            # Pattern validation for strings
            if isinstance(result["sanitized_value"], str):
                pattern = schema.get("pattern")
                if pattern:
                    import re
                    if not re.match(pattern, result["sanitized_value"]):
                        result["is_valid"] = False
                        result["error"] = "Value does not match required pattern"
                        return result
            
        except Exception as e:
            result["is_valid"] = False
            result["error"] = f"Validation error: {str(e)}"
        
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
    
    def validate_json_structure(self, data: Any, expected_structure: Dict[str, Any]) -> bool:
        """
        Validate JSON data structure.
        
        Args:
            data: Data to validate
            expected_structure: Expected structure definition
            
        Returns:
            True if structure matches, False otherwise
        """
        try:
            return self._validate_structure_recursive(data, expected_structure)
        except Exception as e:
            logger.error(f"JSON structure validation failed: {str(e)}")
            return False
    
    def _validate_structure_recursive(self, data: Any, structure: Dict[str, Any]) -> bool:
        """Recursively validate data structure"""
        if not isinstance(structure, dict):
            return True
            
        # Check required fields
        required_fields = structure.get("required", [])
        if isinstance(data, dict):
            for field in required_fields:
                if field not in data:
                    return False
        else:
            return len(required_fields) == 0
        
        # Check field types and structures
        properties = structure.get("properties", {})
        if isinstance(data, dict):
            for field_name, field_structure in properties.items():
                if field_name in data:
                    field_type = field_structure.get("type")
                    field_value = data[field_name]
                    
                    # Type validation
                    if field_type == "object" and not isinstance(field_value, dict):
                        return False
                    elif field_type == "array" and not isinstance(field_value, list):
                        return False
                    elif field_type == "string" and not isinstance(field_value, str):
                        return False
                    elif field_type == "number" and not isinstance(field_value, (int, float)):
                        return False
                    elif field_type == "boolean" and not isinstance(field_value, bool):
                        return False
                    
                    # Recursive validation for objects
                    if field_type == "object" and "properties" in field_structure:
                        if not self._validate_structure_recursive(field_value, field_structure):
                            return False
                    
                    # Array item validation
                    if field_type == "array" and "items" in field_structure and isinstance(field_value, list):
                        item_structure = field_structure["items"]
                        for item in field_value:
                            if not self._validate_structure_recursive(item, item_structure):
                                return False
        
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
        Perform comprehensive security checks on file content.
        
        Implements:
        - Malicious pattern detection
        - Embedded script detection
        - Malformed file detection
        - Suspicious content analysis
        """
        issues = []
        
        # Implement comprehensive security checks
        # Basic file integrity checks
        if len(content) == 0:
            issues.append("Empty file detected")
            return issues
        
        # Check for common malicious patterns
        malicious_patterns = [
            (b'<script', "Embedded JavaScript detected"),
            (b'<?php', "PHP code detected"),
            (b'#!/bin/', "Shell script detected"),
            (b'\x4d\x5a', "Potential executable file"),
            (b'%!PS-Adobe', "PostScript detected in non-PS file"),
            (b'javascript:', "JavaScript URL detected")
        ]
        
        for pattern, message in malicious_patterns:
            if pattern in content[:2048]:  # Check first 2KB
                issues.append(message)
        
        # Check for suspicious file size patterns
        if len(content) > 100 * 1024 * 1024:  # 100MB
            issues.append("File size unusually large")
        
        # File type specific security checks
        if file_type == 'application/pdf':
            issues.extend(self._check_pdf_security(content))
        elif file_type.startswith('image/'):
            issues.extend(self._check_image_security(content))
        elif file_type == 'text/plain':
            issues.extend(self._check_text_security(content))
        
        # Check for polyglot files (files that are valid in multiple formats)
        if self._is_potential_polyglot(content):
            issues.append("Potential polyglot file detected")
        
        # Check for hidden data in file
        if self._has_hidden_data(content, file_type):
            issues.append("File may contain hidden data")
        
        return issues
    
    def _check_pdf_security(self, content: bytes) -> List[str]:
        """
        Security checks specific to PDF files with comprehensive analysis.
        """
        issues = []
        
        # Check for PDF header
        if not content.startswith(b'%PDF'):
            issues.append("Invalid PDF header")
            return issues
        
        # Check for JavaScript in PDF
        if b'/JavaScript' in content or b'/JS' in content:
            issues.append("PDF contains JavaScript")
        
        # Check for forms and actions
        if b'/Action' in content:
            issues.append("PDF contains actions")
        
        # Check for external references
        if b'/URI' in content or b'http://' in content or b'https://' in content:
            issues.append("PDF contains external references")
        
        # Check for embedded files
        if b'/EmbeddedFile' in content:
            issues.append("PDF contains embedded files")
        
        # Check for suspicious objects
        suspicious_objects = [b'/Launch', b'/ImportData', b'/SubmitForm']
        for obj in suspicious_objects:
            if obj in content:
                issues.append(f"PDF contains suspicious object: {obj.decode()}")
        
        return issues
    
    def _check_image_security(self, content: bytes) -> List[str]:
        """
        Security checks specific to image files.
        """
        issues = []
        
        # Check for executable code in EXIF data
        if b'<?php' in content or b'<script' in content:
            issues.append("Image contains embedded code")
        
        # Check for unusual metadata size
        if len(content) > 50 * 1024 * 1024:  # 50MB for images is large
            issues.append("Image file unusually large")
        
        # Check for steganography indicators
        if self._check_steganography_indicators(content):
            issues.append("Image may contain hidden data")
        
        return issues
    
    def _check_text_security(self, content: bytes) -> List[str]:
        """
        Security checks for text files.
        """
        issues = []
        
        try:
            text = content.decode('utf-8', errors='ignore')
            
            # Check for suspicious patterns using our security patterns
            for threat_type, patterns in self.security_patterns.items():
                for pattern in patterns:
                    if pattern.search(text):
                        issues.append(f"Potential {threat_type} detected")
                        break
        
        except Exception:
            issues.append("Text encoding issues detected")
        
        return issues
    
    def _is_potential_polyglot(self, content: bytes) -> bool:
        """
        Check if file could be valid in multiple formats (polyglot attack).
        """
        # Check for multiple valid file signatures
        signatures_found = 0
        
        for file_type, signatures in self.file_signatures.items():
            for signature in signatures:
                if signature and content.startswith(signature):
                    signatures_found += 1
                    if signatures_found > 1:
                        return True
        
        # Check for mixed content patterns
        if (b'%PDF' in content[:100] and 
            (b'<script' in content or b'<?php' in content)):
            return True
        
        return False
    
    def _has_hidden_data(self, content: bytes, file_type: str) -> bool:
        """
        Check for hidden data in file based on type.
        """
        # Check for trailing data after expected end markers
        end_markers = {
            'application/pdf': b'%%EOF',
            'image/jpeg': b'\xff\xd9',
            'image/png': b'IEND\xaeB`\x82'
        }
        
        if file_type in end_markers:
            marker = end_markers[file_type]
            marker_pos = content.rfind(marker)
            if marker_pos != -1:
                trailing_data = content[marker_pos + len(marker):]
                # Allow small amount of trailing whitespace
                if len(trailing_data.strip()) > 10:
                    return True
        
        return False
    
    def _check_steganography_indicators(self, content: bytes) -> bool:
        """
        Check for potential steganography in image files.
        """
        # Basic heuristics for steganography detection
        # This is a simplified check - real steganography detection is complex
        
        # Check for unusual data patterns in image
        if len(content) < 1000:
            return False
        
        # Sample random bytes and check for entropy
        import random
        sample_size = min(1000, len(content) // 10)
        sample = random.sample(list(content), sample_size)
        
        # Calculate byte frequency distribution
        byte_counts = {}
        for byte in sample:
            byte_counts[byte] = byte_counts.get(byte, 0) + 1
        
        # High entropy might indicate hidden data
        entropy = 0
        for count in byte_counts.values():
            p = count / sample_size
            if p > 0:
                entropy -= p * (p.bit_length() - 1)
        
        # Threshold for suspicious entropy (this is a rough heuristic)
        return entropy > 7.5
    
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


# Validation rule builder implementation
class ValidationRuleBuilder:
    """
    Builder for creating custom validation rules with fluent API.
    
    Implements:
    - Fluent validation rule API
    - Rule composition and chaining
    - Conditional validation rules
    - Rule serialization for storage
    """
    
    def __init__(self):
        self.rules = {}
        self.conditions = []
        self.custom_validators = []
    
    def required(self) -> 'ValidationRuleBuilder':
        """Mark field as required."""
        self.rules["required"] = True
        return self
    
    def optional(self) -> 'ValidationRuleBuilder':
        """Mark field as optional."""
        self.rules["required"] = False
        return self
    
    def min_length(self, length: int) -> 'ValidationRuleBuilder':
        """Set minimum length validation."""
        self.rules["min_length"] = length
        return self
    
    def max_length(self, length: int) -> 'ValidationRuleBuilder':
        """Set maximum length validation."""
        self.rules["max_length"] = length
        return self
    
    def pattern(self, regex: str, message: Optional[str] = None) -> 'ValidationRuleBuilder':
        """Add regex pattern validation."""
        self.rules["pattern"] = {"regex": regex, "message": message}
        return self
    
    def email(self) -> 'ValidationRuleBuilder':
        """Add email validation."""
        self.rules["type"] = "email"
        return self
    
    def phone(self, format: str = "international") -> 'ValidationRuleBuilder':
        """Add phone number validation."""
        self.rules["type"] = "phone"
        self.rules["phone_format"] = format
        return self
    
    def numeric(self, min_val: Optional[float] = None, max_val: Optional[float] = None) -> 'ValidationRuleBuilder':
        """Add numeric validation."""
        self.rules["type"] = "numeric"
        if min_val is not None:
            self.rules["min_value"] = min_val
        if max_val is not None:
            self.rules["max_value"] = max_val
        return self
    
    def date(self, format: str = "%Y-%m-%d") -> 'ValidationRuleBuilder':
        """Add date validation."""
        self.rules["type"] = "date"
        self.rules["date_format"] = format
        return self
    
    def custom(self, validator_func, message: Optional[str] = None) -> 'ValidationRuleBuilder':
        """Add custom validation function."""
        self.custom_validators.append({
            "function": validator_func,
            "message": message or "Custom validation failed"
        })
        return self
    
    def when(self, condition_field: str, condition_value: Any) -> 'ValidationRuleBuilder':
        """Add conditional validation."""
        self.conditions.append({
            "field": condition_field,
            "value": condition_value
        })
        return self
    
    def in_list(self, allowed_values: List[Any]) -> 'ValidationRuleBuilder':
        """Validate value is in allowed list."""
        self.rules["allowed_values"] = allowed_values
        return self
    
    def not_in_list(self, forbidden_values: List[Any]) -> 'ValidationRuleBuilder':
        """Validate value is not in forbidden list."""
        self.rules["forbidden_values"] = forbidden_values
        return self
    
    def unique(self, check_function) -> 'ValidationRuleBuilder':
        """Add uniqueness validation."""
        self.rules["unique_check"] = check_function
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build validation rules into dictionary."""
        final_rules = self.rules.copy()
        
        if self.conditions:
            final_rules["conditions"] = self.conditions
        
        if self.custom_validators:
            final_rules["custom_validators"] = self.custom_validators
        
        return final_rules
    
    def build_json(self) -> str:
        """Build validation rules as JSON string for storage."""
        import json
        rules = self.build()
        
        # Remove non-serializable functions
        serializable_rules = {}
        for key, value in rules.items():
            if key != "custom_validators" and key != "unique_check":
                serializable_rules[key] = value
        
        return json.dumps(serializable_rules, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ValidationRuleBuilder':
        """Create ValidationRuleBuilder from JSON string."""
        import json
        rules = json.loads(json_str)
        
        builder = cls()
        builder.rules = rules
        return builder
    
    def validate(self, value: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate a value against the built rules."""
        errors = []
        context = context or {}
        
        # Check conditions first
        if self.conditions:
            condition_met = False
            for condition in self.conditions:
                field_value = context.get(condition["field"])
                if field_value == condition["value"]:
                    condition_met = True
                    break
            
            if not condition_met:
                return {"valid": True, "errors": []}
        
        # Required check
        if self.rules.get("required", False) and (value is None or value == ""):
            errors.append("Field is required")
            return {"valid": False, "errors": errors}
        
        # If optional and empty, skip other validations
        if not self.rules.get("required", False) and (value is None or value == ""):
            return {"valid": True, "errors": []}
        
        # Type-specific validations
        field_type = self.rules.get("type")
        if field_type == "email":
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(value)):
                errors.append("Invalid email format")
        
        elif field_type == "phone":
            phone_format = self.rules.get("phone_format", "international")
            if phone_format == "us":
                if not re.match(r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$', str(value)):
                    errors.append("Invalid US phone number format")
            else:
                if not re.match(r'^\+?[1-9]\d{1,14}$', str(value)):
                    errors.append("Invalid international phone number format")
        
        elif field_type == "numeric":
            try:
                num_value = float(value)
                min_val = self.rules.get("min_value")
                max_val = self.rules.get("max_value")
                
                if min_val is not None and num_value < min_val:
                    errors.append(f"Value must be at least {min_val}")
                if max_val is not None and num_value > max_val:
                    errors.append(f"Value must be at most {max_val}")
            except (ValueError, TypeError):
                errors.append("Value must be numeric")
        
        # Length validations
        if isinstance(value, str):
            min_len = self.rules.get("min_length")
            max_len = self.rules.get("max_length")
            
            if min_len is not None and len(value) < min_len:
                errors.append(f"Minimum length is {min_len}")
            if max_len is not None and len(value) > max_len:
                errors.append(f"Maximum length is {max_len}")
        
        # Pattern validation
        pattern_rule = self.rules.get("pattern")
        if pattern_rule and isinstance(value, str):
            regex = pattern_rule["regex"] if isinstance(pattern_rule, dict) else pattern_rule
            if not re.match(regex, value):
                message = pattern_rule.get("message", "Pattern validation failed") if isinstance(pattern_rule, dict) else "Pattern validation failed"
                errors.append(message)
        
        # Custom validators
        for validator in self.custom_validators:
            try:
                if not validator["function"](value, context):
                    errors.append(validator["message"])
            except Exception as e:
                errors.append(f"Custom validation error: {str(e)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }


# Validation middleware for FastAPI implementation
class ValidationMiddleware:
    """
    Middleware for automatic request validation with comprehensive FastAPI integration.
    
    Implements:
    - FastAPI middleware integration
    - Automatic validation based on route annotations
    - Validation error formatting
    - Validation metrics and monitoring
    """
    
    def __init__(self, validation_service: ValidationService):
        self.validation_service = validation_service
        self.validation_stats = {
            "total_requests": 0,
            "validation_errors": 0,
            "validation_successes": 0,
            "error_types": {}
        }
    
    async def __call__(self, request, call_next):
        """Process request validation with comprehensive error handling."""
        # Increment request counter
        self.validation_stats["total_requests"] += 1
        
        try:
            # Extract request data for validation
            request_data = await self._extract_request_data(request)
            
            # Determine validation rules based on route
            validation_rules = self._get_validation_rules(request)
            
            # Perform validation if rules exist
            if validation_rules:
                validation_result = await self._validate_request(request_data, validation_rules)
                
                if not validation_result["valid"]:
                    self.validation_stats["validation_errors"] += 1
                    self._update_error_stats(validation_result["errors"])
                    
                    # Return validation error response
                    return self._create_validation_error_response(validation_result["errors"])
                
                self.validation_stats["validation_successes"] += 1
            
            # Continue with request processing
            response = await call_next(request)
            
            # Add validation headers if needed
            if hasattr(request, 'validation_metadata'):
                response.headers["X-Validation-Status"] = "passed"
            
            return response
            
        except Exception as e:
            # Log validation middleware errors
            logger.error(f"Validation middleware error: {str(e)}")
            
            # Continue with request processing (fail open)
            response = await call_next(request)
            response.headers["X-Validation-Status"] = "error"
            return response
    
    async def _extract_request_data(self, request) -> Dict[str, Any]:
        """Extract data from request for validation."""
        request_data = {}
        
        # Extract query parameters
        if hasattr(request, 'query_params'):
            request_data["query"] = dict(request.query_params)
        
        # Extract path parameters
        if hasattr(request, 'path_params'):
            request_data["path"] = dict(request.path_params)
        
        # Extract headers
        if hasattr(request, 'headers'):
            request_data["headers"] = dict(request.headers)
        
        # Extract body for POST/PUT requests
        if hasattr(request, 'method') and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                # This is a simplified approach - in real implementation,
                # you'd need to handle different content types properly
                if hasattr(request, '_body'):
                    import json
                    body = await request.body()
                    if body:
                        request_data["body"] = json.loads(body.decode('utf-8'))
            except Exception as e:
                logger.warning(f"Failed to parse request body: {str(e)}")
        
        return request_data
    
    def _get_validation_rules(self, request) -> Optional[Dict[str, Any]]:
        """Get validation rules for the current route."""
        # This would be implemented based on your routing system
        # For now, return basic rules based on request method and path
        
        if not hasattr(request, 'url'):
            return None
        
        path = str(request.url.path)
        method = getattr(request, 'method', 'GET')
        
        # Example rules based on common API patterns
        rules = {}
        
        # Document upload validation
        if '/documents' in path and method == 'POST':
            rules = {
                "body": {
                    "filename": ValidationRuleBuilder().required().min_length(1).max_length(255).build(),
                    "content_type": ValidationRuleBuilder().required().pattern(r'^[a-zA-Z0-9/\-]+$').build()
                }
            }
        
        # User creation validation
        elif '/users' in path and method == 'POST':
            rules = {
                "body": {
                    "email": ValidationRuleBuilder().required().email().build(),
                    "name": ValidationRuleBuilder().required().min_length(2).max_length(100).build()
                }
            }
        
        # Query parameter validation for list endpoints
        elif method == 'GET' and any(keyword in path for keyword in ['/documents', '/users', '/files']):
            rules = {
                "query": {
                    "limit": ValidationRuleBuilder().optional().numeric(1, 100).build(),
                    "offset": ValidationRuleBuilder().optional().numeric(0, float('inf')).build()
                }
            }
        
        return rules if rules else None
    
    async def _validate_request(self, request_data: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate request data against rules."""
        all_errors = []
        
        for section, section_rules in rules.items():
            section_data = request_data.get(section, {})
            
            for field_name, field_rules in section_rules.items():
                field_value = section_data.get(field_name)
                
                # Create validator from rules
                validator = ValidationRuleBuilder()
                validator.rules = field_rules
                
                # Validate field
                result = validator.validate(field_value, section_data)
                
                if not result["valid"]:
                    for error in result["errors"]:
                        all_errors.append({
                            "field": f"{section}.{field_name}",
                            "message": error,
                            "value": field_value
                        })
        
        return {
            "valid": len(all_errors) == 0,
            "errors": all_errors
        }
    
    def _create_validation_error_response(self, errors: List[Dict[str, Any]]):
        """Create standardized validation error response."""
        from fastapi import HTTPException
        from fastapi.responses import JSONResponse
        
        error_response = {
            "error": "Validation failed",
            "message": "Request validation failed",
            "details": errors,
            "error_count": len(errors),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(
            status_code=422,
            content=error_response
        )
    
    def _update_error_stats(self, errors: List[Dict[str, Any]]):
        """Update error statistics for monitoring."""
        for error in errors:
            error_type = error.get("field", "unknown")
            self.validation_stats["error_types"][error_type] = (
                self.validation_stats["error_types"].get(error_type, 0) + 1
            )
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics for monitoring."""
        total_requests = self.validation_stats["total_requests"]
        error_rate = (
            (self.validation_stats["validation_errors"] / total_requests * 100)
            if total_requests > 0 else 0
        )
        
        return {
            "total_requests": total_requests,
            "validation_errors": self.validation_stats["validation_errors"],
            "validation_successes": self.validation_stats["validation_successes"],
            "error_rate_percent": round(error_rate, 2),
            "error_types": self.validation_stats["error_types"],
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def reset_stats(self):
        """Reset validation statistics."""
        self.validation_stats = {
            "total_requests": 0,
            "validation_errors": 0,
            "validation_successes": 0,
            "error_types": {}
        }
