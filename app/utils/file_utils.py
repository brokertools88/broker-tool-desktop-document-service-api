"""
File utility functions for common file operations.

This module provides helper functions for file handling, validation, and processing.
"""

import os
import hashlib
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional, Tuple, BinaryIO, Any, Callable
from pathlib import Path
import tempfile
import shutil
import logging

logger = logging.getLogger(__name__)


def calculate_file_hash(
    content: bytes, 
    algorithm: str = "sha256",
    chunk_size: int = 8192,
    progress_callback: Optional[Callable[[float], None]] = None
) -> str:
    """
    Calculate hash of file content with streaming support for large files.
    
    Args:
        content: File binary content
        algorithm: Hash algorithm to use
        chunk_size: Chunk size for streaming calculation
        progress_callback: Optional progress callback for large files
        
    Returns:
        Hexadecimal hash string
    """
    hash_obj = hashlib.new(algorithm)
    
    if len(content) <= chunk_size:
        # Small file, process directly
        hash_obj.update(content)
        return hash_obj.hexdigest()
    
    # Large file, process in chunks with progress tracking
    total_size = len(content)
    processed = 0
    
    for i in range(0, len(content), chunk_size):
        chunk = content[i:i + chunk_size]
        hash_obj.update(chunk)
        processed += len(chunk)
        
        if progress_callback:
            progress = (processed / total_size) * 100
            progress_callback(progress)
    
    return hash_obj.hexdigest()


def get_file_extension(filename: str, compound_extensions: bool = True, normalize_case: bool = True) -> str:
    """
    Get file extension with support for compound extensions and case normalization.
    
    Args:
        filename: Filename to extract extension from
        compound_extensions: Whether to handle compound extensions (.tar.gz, etc.)
        normalize_case: Whether to normalize case to lowercase
        
    Returns:
        File extension string
    """
    path = Path(filename)
    
    if compound_extensions:
        # Handle compound extensions
        compound_exts = ['.tar.gz', '.tar.bz2', '.tar.xz', '.tar.Z']
        for ext in compound_exts:
            if filename.lower().endswith(ext):
                return ext.lower() if normalize_case else ext
    
    extension = path.suffix
    
    if normalize_case:
        extension = extension.lower()
    
    return extension


def get_file_mime_type(
    filename: str, 
    content: Optional[bytes] = None,
    custom_mappings: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """
    Get MIME type with content-based detection and custom mappings.
    
    Args:
        filename: Filename to determine MIME type for
        content: Optional file content for content-based detection
        custom_mappings: Custom MIME type mappings
        
    Returns:
        MIME type string or None if unknown
    """
    # Try custom mappings first
    if custom_mappings:
        ext = get_file_extension(filename, normalize_case=True)
        if ext in custom_mappings:
            return custom_mappings[ext]
    
    # Try filename-based detection
    mime_type, _ = mimetypes.guess_type(filename)
    
    if mime_type and not content:
        return mime_type
    
    # Content-based detection if content is provided
    if content:
        content_type = detect_mime_from_content(content)
        if content_type:
            # Prefer content-based detection over filename
            return content_type
    
    return mime_type


def detect_mime_from_content(content: bytes) -> Optional[str]:
    """
    Detect MIME type from file content using magic bytes.
    
    Args:
        content: File content bytes
        
    Returns:
        Detected MIME type or None
    """
    if not content:
        return None
    
    # Common file signatures
    signatures = {
        b'\x89PNG\r\n\x1a\n': 'image/png',
        b'\xff\xd8\xff': 'image/jpeg',
        b'GIF87a': 'image/gif',
        b'GIF89a': 'image/gif',
        b'%PDF': 'application/pdf',
        b'PK\x03\x04': 'application/zip',
        b'PK\x05\x06': 'application/zip',
        b'Rar!': 'application/x-rar-compressed',
        b'\x1f\x8b': 'application/gzip',
        b'BZ': 'application/x-bzip2',
        b'\x00\x00\x01\x00': 'image/x-icon',
        b'RIFF': 'audio/wav',  # Could also be video, need more checking
    }
    
    for signature, mime_type in signatures.items():
        if content.startswith(signature):
            return mime_type
    
    # Check for text content
    try:
        content.decode('utf-8')
        return 'text/plain'
    except UnicodeDecodeError:
        pass
    
    return None


def is_safe_filename(
    filename: str, 
    os_specific: bool = True,
    check_reserved: bool = True,
    max_length: int = 255
) -> bool:
    """
    Check if filename is safe with OS-specific validation and length checking.
    
    Args:
        filename: Filename to validate
        os_specific: Whether to apply OS-specific rules
        check_reserved: Whether to check for reserved filenames
        max_length: Maximum allowed filename length
        
    Returns:
        True if filename is safe
    """
    if not filename or filename in ['.', '..']:
        return False
    
    # Length validation
    if len(filename) > max_length:
        return False
    
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Check for null bytes and control characters
    if '\x00' in filename or any(ord(c) < 32 for c in filename):
        return False
    
    if os_specific:
        import platform
        current_os = platform.system().lower()
        
        if current_os == 'windows':
            # Windows-specific restrictions
            reserved_chars = '<>:"/\\|?*'
            if any(char in filename for char in reserved_chars):
                return False
            
            # Windows reserved names
            if check_reserved:
                reserved_names = {
                    'CON', 'PRN', 'AUX', 'NUL',
                    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
                }
                name_part = filename.split('.')[0].upper()
                if name_part in reserved_names:
                    return False
            
            # Windows doesn't allow names ending with period or space
            if filename.endswith('.') or filename.endswith(' '):
                return False
        
        elif current_os in ['linux', 'darwin']:  # macOS is darwin
            # Unix-like systems are more permissive
            if filename.startswith('.') and len(filename) == 1:
                return False
    
    return True


def sanitize_filename(
    filename: str, 
    replacement: str = "_",
    os_specific: bool = True,
    preserve_extension: bool = True,
    max_length: int = 255,
    unicode_normalize: bool = True
) -> str:
    """
    Sanitize filename with OS-specific rules, length limits, and Unicode normalization.
    
    Args:
        filename: Filename to sanitize
        replacement: Character to replace dangerous characters with
        os_specific: Whether to apply OS-specific sanitization rules
        preserve_extension: Whether to preserve file extension when truncating
        max_length: Maximum filename length
        unicode_normalize: Whether to normalize Unicode characters
        
    Returns:
        Sanitized filename
    """
    import unicodedata
    import platform
    
    if not filename:
        return f"file{replacement}"
    
    # Unicode normalization
    if unicode_normalize:
        filename = unicodedata.normalize('NFKD', filename)
    
    # OS-specific character replacement
    if os_specific:
        current_os = platform.system().lower()
        
        if current_os == 'windows':
            dangerous_chars = '<>:"/\\|?*'
        else:
            dangerous_chars = '/'  # Unix-like systems are more permissive
    else:
        dangerous_chars = '<>:"/\\|?*'
    
    sanitized = filename
    
    # Replace dangerous characters
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, replacement)
    
    # Remove control characters (ASCII 0-31)
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
    
    # Handle length truncation with extension preservation
    if len(sanitized) > max_length and preserve_extension:
        ext = get_file_extension(sanitized)
        if ext:
            # Reserve space for extension
            max_name_length = max_length - len(ext)
            name_part = sanitized[:-len(ext)]
            if max_name_length > 0:
                sanitized = name_part[:max_name_length] + ext
            else:
                # Extension is too long, truncate everything
                sanitized = sanitized[:max_length]
        else:
            sanitized = sanitized[:max_length]
    elif len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Ensure filename is not empty or just dots/replacement chars
    clean_check = sanitized.replace('.', '').replace(replacement, '').strip()
    if not clean_check:
        ext = get_file_extension(filename) if preserve_extension else ""
        sanitized = f"file{replacement}{ext}"
    
    # Final safety check
    if not is_safe_filename(sanitized, os_specific=os_specific):
        # Fallback to safe default
        ext = get_file_extension(filename) if preserve_extension else ""
        sanitized = f"safe_file{replacement}{ext}"
    
    return sanitized


def create_temp_file(
    content: bytes, 
    suffix: Optional[str] = None,
    auto_cleanup: bool = False,
    secure: bool = True,
    progress_callback: Optional[Callable[[float], None]] = None
) -> str:
    """
    Create temporary file with automatic cleanup and security options.
    
    Args:
        content: Content to write to file
        suffix: File suffix/extension
        auto_cleanup: Whether to schedule automatic cleanup
        secure: Whether to use secure temporary file creation
        progress_callback: Progress callback for large files
        
    Returns:
        Path to temporary file
    """
    import atexit
    
    # Use secure temporary file creation
    if secure:
        # Set restrictive permissions (owner only)
        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        try:
            with os.fdopen(fd, 'wb') as temp_file:
                if len(content) > 1024 * 1024 and progress_callback:
                    # Write in chunks with progress for large files
                    chunk_size = 64 * 1024
                    written = 0
                    total_size = len(content)
                    
                    for i in range(0, len(content), chunk_size):
                        chunk = content[i:i + chunk_size]
                        temp_file.write(chunk)
                        written += len(chunk)
                        progress_callback((written / total_size) * 100)
                else:
                    temp_file.write(content)
        except Exception:
            # Clean up on error
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise
    else:
        # Standard temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
    
    # Schedule automatic cleanup if requested
    if auto_cleanup:
        atexit.register(cleanup_temp_file, temp_path)
    
    return temp_path


def cleanup_temp_file(file_path: str, secure_delete: bool = False, max_retries: int = 3) -> bool:
    """
    Clean up temporary file with secure deletion and retry logic.
    
    Args:
        file_path: Path to file to delete
        secure_delete: Whether to perform secure deletion for sensitive files
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if file was successfully deleted
    """
    import time
    
    if not os.path.exists(file_path):
        return True
    
    for attempt in range(max_retries):
        try:
            if secure_delete:
                # Overwrite file with random data before deletion
                file_size = os.path.getsize(file_path)
                with open(file_path, 'r+b') as f:
                    # Overwrite with random data
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
            
            os.unlink(file_path)
            return True
            
        except OSError as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to cleanup temp file {file_path} after {max_retries} attempts: {str(e)}")
            else:
                # Wait before retry (file might be locked)
                time.sleep(0.1 * (attempt + 1))
        except Exception as e:
            logger.error(f"Unexpected error cleaning up temp file {file_path}: {str(e)}")
            break
    
    return False


def get_file_size_human_readable(size_bytes: int) -> str:
    """
    Convert file size to human readable format.
    
    TODO:
    - Add different unit systems (binary vs decimal)
    - Implement precision control
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    size = size_bytes
    unit_index = 0
    
    while size >= 1024 and unit_index < len(size_names) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.1f} {size_names[unit_index]}"


def split_file_into_chunks(content: bytes, chunk_size: int = 1024 * 1024) -> List[bytes]:
    """
    Split file content into chunks.
    
    TODO:
    - Add streaming chunk processing
    - Implement memory-efficient chunking for large files
    - Add chunk validation and checksums
    """
    chunks = []
    for i in range(0, len(content), chunk_size):
        chunks.append(content[i:i + chunk_size])
    return chunks


def validate_file_signature(content: bytes, expected_mime_type: str) -> bool:
    """
    Validate file signature against expected MIME type.
    
    TODO:
    - Implement comprehensive signature database
    - Add support for compound file formats
    - Implement polyglot detection
    """
    # Common file signatures
    signatures = {
        'application/pdf': [b'%PDF'],
        'image/jpeg': [b'\xff\xd8\xff'],
        'image/png': [b'\x89PNG\r\n\x1a\n'],
        'image/gif': [b'GIF87a', b'GIF89a'],
        'image/bmp': [b'BM'],
        'image/tiff': [b'II*\x00', b'MM\x00*'],
        'application/zip': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],
        'text/plain': []  # Text files don't have a specific signature
    }
    
    if expected_mime_type not in signatures:
        return True  # Unknown type, assume valid
    
    expected_sigs = signatures[expected_mime_type]
    if not expected_sigs:  # No signature required
        return True
    
    return any(content.startswith(sig) for sig in expected_sigs)


def extract_metadata_from_content(
    content: bytes, 
    filename: str,
    extract_exif: bool = True,
    extract_pdf_info: bool = True,
    extract_text_preview: bool = False
) -> Dict[str, Any]:
    """
    Extract comprehensive metadata from file content.
    
    Args:
        content: File content bytes
        filename: Original filename
        extract_exif: Whether to extract EXIF data from images
        extract_pdf_info: Whether to extract PDF metadata
        extract_text_preview: Whether to extract text preview
        
    Returns:
        Dictionary containing file metadata
    """
    metadata = {
        'size': len(content),
        'filename': filename,
        'extension': get_file_extension(filename),
        'mime_type': get_file_mime_type(filename, content),
        'hash_sha256': calculate_file_hash(content, 'sha256'),
        'hash_md5': calculate_file_hash(content, 'md5'),
        'created_at': datetime.utcnow().isoformat(),
        'is_binary': is_binary_content(content)
    }
    
    mime_type = metadata['mime_type']
    
    # Extract type-specific metadata
    if mime_type and mime_type.startswith('image/') and extract_exif:
        try:
            metadata.update(extract_image_metadata(content))
        except Exception as e:
            logger.warning(f"Failed to extract image metadata: {str(e)}")
    
    elif mime_type == 'application/pdf' and extract_pdf_info:
        try:
            metadata.update(extract_pdf_metadata(content))
        except Exception as e:
            logger.warning(f"Failed to extract PDF metadata: {str(e)}")
    
    elif mime_type and mime_type.startswith('text/') and extract_text_preview:
        try:
            text_content = content.decode('utf-8', errors='ignore')
            metadata['text_preview'] = text_content[:500]  # First 500 chars
            metadata['line_count'] = text_content.count('\n') + 1
            metadata['word_count'] = len(text_content.split())
        except Exception as e:
            logger.warning(f"Failed to extract text metadata: {str(e)}")
    
    return metadata


def is_binary_content(content: bytes, sample_size: int = 1024) -> bool:
    """
    Determine if content is binary by checking for null bytes and non-printable characters.
    
    Args:
        content: Content to check
        sample_size: Number of bytes to sample for checking
        
    Returns:
        True if content appears to be binary
    """
    if not content:
        return False
    
    # Sample the beginning of the file
    sample = content[:sample_size]
    
    # Check for null bytes (strong indicator of binary)
    if b'\x00' in sample:
        return True
    
    # Check ratio of printable characters
    printable_chars = sum(1 for byte in sample if 32 <= byte <= 126 or byte in [9, 10, 13])
    printable_ratio = printable_chars / len(sample)
    
    # If less than 80% printable characters, consider it binary
    return printable_ratio < 0.8


def extract_image_metadata(content: bytes) -> Dict[str, Any]:
    """
    Extract metadata from image files.
    
    TODO:
    - Implement EXIF data extraction
    - Add image dimension detection
    - Implement color profile information
    - Add GPS data extraction
    """
    metadata = {}
    
    # TODO: Use PIL/Pillow to extract image metadata
    # try:
    #     from PIL import Image
    #     from PIL.ExifTags import TAGS
    #     
    #     with Image.open(io.BytesIO(content)) as img:
    #         metadata['width'] = img.width
    #         metadata['height'] = img.height
    #         metadata['mode'] = img.mode
    #         
    #         # Extract EXIF data
    #         exifdata = img.getexif()
    #         for tag_id in exifdata:
    #             tag = TAGS.get(tag_id, tag_id)
    #             data = exifdata.get(tag_id)
    #             metadata[f'exif_{tag}'] = data
    # except Exception as e:
    #     logger.warning(f"Failed to extract image metadata: {str(e)}")
    
    return metadata


def extract_pdf_metadata(content: bytes) -> Dict[str, Any]:
    """
    Extract metadata from PDF files.
    
    TODO:
    - Implement PDF metadata extraction
    - Add page count detection
    - Extract document properties
    - Add text extraction for analysis
    """
    metadata = {}
    
    # TODO: Use PyPDF2 or similar to extract PDF metadata
    # try:
    #     import PyPDF2
    #     
    #     pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
    #     metadata['pages'] = len(pdf_reader.pages)
    #     
    #     if pdf_reader.metadata:
    #         metadata['title'] = pdf_reader.metadata.get('/Title', '')
    #         metadata['author'] = pdf_reader.metadata.get('/Author', '')
    #         metadata['subject'] = pdf_reader.metadata.get('/Subject', '')
    #         metadata['creator'] = pdf_reader.metadata.get('/Creator', '')
    # except Exception as e:
    #     logger.warning(f"Failed to extract PDF metadata: {str(e)}")
    
    return metadata


def compress_content(content: bytes, compression_type: str = 'gzip') -> bytes:
    """
    Compress file content.
    
    TODO:
    - Implement multiple compression algorithms
    - Add compression level control
    - Implement streaming compression for large files
    """
    if compression_type == 'gzip':
        import gzip
        return gzip.compress(content)
    elif compression_type == 'bz2':
        import bz2
        return bz2.compress(content)
    else:
        raise ValueError(f"Unsupported compression type: {compression_type}")


def decompress_content(content: bytes, compression_type: str = 'gzip') -> bytes:
    """
    Decompress file content.
    
    TODO:
    - Add automatic compression type detection
    - Implement streaming decompression
    - Add decompression bomb protection
    """
    if compression_type == 'gzip':
        import gzip
        return gzip.decompress(content)
    elif compression_type == 'bz2':
        import bz2
        return bz2.decompress(content)
    else:
        raise ValueError(f"Unsupported compression type: {compression_type}")


class FileProcessor:
    """
    File processor for batch operations, transformations, and progress tracking.
    """
    
    def __init__(self):
        self.processors = {}
        self.error_handlers = {}
        self.progress_callbacks = []
        self.recovery_strategies = {}
    
    def register_processor(self, file_type: str, processor_func: Callable[[bytes], bytes]):
        """Register file processor for specific type."""
        self.processors[file_type] = processor_func
    
    def register_error_handler(self, error_type: str, handler_func: Callable[[Exception, bytes], bytes]):
        """Register error handler for specific error types."""
        self.error_handlers[error_type] = handler_func
    
    def register_progress_callback(self, callback: Callable[[str, float], None]):
        """Register progress tracking callback."""
        self.progress_callbacks.append(callback)
    
    def _notify_progress(self, operation: str, progress: float):
        """Notify all registered progress callbacks."""
        for callback in self.progress_callbacks:
            try:
                callback(operation, progress)
            except Exception as e:
                logger.warning(f"Progress callback failed: {str(e)}")
    
    def process_file(self, content: bytes, file_type: str, filename: str = "") -> bytes:
        """Process single file with error handling and recovery."""
        try:
            if file_type in self.processors:
                self._notify_progress(f"Processing {filename}", 0.0)
                result = self.processors[file_type](content)
                self._notify_progress(f"Processing {filename}", 100.0)
                return result
            return content
        except Exception as e:
            # Try error handlers
            error_type = type(e).__name__
            if error_type in self.error_handlers:
                try:
                    return self.error_handlers[error_type](e, content)
                except Exception as recovery_error:
                    logger.error(f"Error handler failed: {str(recovery_error)}")
            
            logger.error(f"File processing failed for {filename}: {str(e)}")
            return content  # Return original content as fallback
    
    def process_batch(
        self, 
        files: List[Tuple[bytes, str, str]], 
        parallel: bool = False,
        max_workers: Optional[int] = None
    ) -> List[Tuple[bytes, bool, Optional[str]]]:
        """
        Process multiple files in batch with parallel processing support.
        
        Args:
            files: List of (content, file_type, filename) tuples
            parallel: Whether to use parallel processing
            max_workers: Maximum number of worker threads
            
        Returns:
            List of (processed_content, success, error_message) tuples
        """
        results = []
        total_files = len(files)
        
        if parallel and total_files > 1:
            # Parallel processing
            import concurrent.futures
            max_workers = max_workers or min(4, total_files)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_file = {
                    executor.submit(self._process_single_with_error_handling, content, file_type, filename): 
                    (content, file_type, filename)
                    for content, file_type, filename in files
                }
                
                # Collect results
                completed = 0
                for future in concurrent.futures.as_completed(future_to_file):
                    content, file_type, filename = future_to_file[future]
                    try:
                        processed_content = future.result()
                        results.append((processed_content, True, None))
                    except Exception as e:
                        logger.error(f"Batch processing failed for {filename}: {str(e)}")
                        results.append((content, False, str(e)))
                    
                    completed += 1
                    self._notify_progress("Batch processing", (completed / total_files) * 100)
        else:
            # Sequential processing
            for i, (content, file_type, filename) in enumerate(files):
                try:
                    processed_content = self.process_file(content, file_type, filename)
                    results.append((processed_content, True, None))
                except Exception as e:
                    logger.error(f"Batch processing failed for {filename}: {str(e)}")
                    results.append((content, False, str(e)))
                
                self._notify_progress("Batch processing", ((i + 1) / total_files) * 100)
        
        return results
    
    def _process_single_with_error_handling(self, content: bytes, file_type: str, filename: str) -> bytes:
        """Helper method for processing single file with error handling."""
        return self.process_file(content, file_type, filename)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            'registered_processors': len(self.processors),
            'registered_error_handlers': len(self.error_handlers),
            'progress_callbacks': len(self.progress_callbacks),
            'supported_types': list(self.processors.keys())
        }
