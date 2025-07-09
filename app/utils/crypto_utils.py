"""
Cryptographic utility functions for security operations.

This module provides helper functions for encryption, hashing, and other crypto operations.
"""

import hashlib
import secrets
import base64
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Callable
import hmac
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


def generate_random_string(
    length: int = 32, 
    charset: str = "url_safe",
    encoding: str = "base64"
) -> str:
    """
    Generate cryptographically secure random string.
    
    Args:
        length: Length of the generated string
        charset: Character set to use ('url_safe', 'hex', 'alphanumeric', 'letters', 'digits')
        encoding: Encoding format ('base64', 'hex', 'raw')
        
    Returns:
        Cryptographically secure random string
    """
    if charset == "url_safe":
        return secrets.token_urlsafe(length)
    elif charset == "hex":
        return secrets.token_hex(length)
    elif charset == "alphanumeric":
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    elif charset == "letters":
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    elif charset == "digits":
        return ''.join(secrets.choice("0123456789") for _ in range(length))
    else:
        raise ValueError(f"Unsupported charset: {charset}")
    
    # Validate entropy (minimum 32 bits for security)
    min_entropy_bits = 32
    actual_entropy = length * 6  # Approximate for base64
    if actual_entropy < min_entropy_bits:
        logger.warning(f"Low entropy: {actual_entropy} bits (minimum recommended: {min_entropy_bits})")


def generate_random_bytes(
    length: int = 32, 
    entropy_source: Optional[str] = None
) -> bytes:
    """
    Generate cryptographically secure random bytes.
    
    Args:
        length: Number of bytes to generate
        entropy_source: Custom entropy source ('system', 'urandom', None for default)
        
    Returns:
        Cryptographically secure random bytes
    """
    # Validate entropy source
    if entropy_source and entropy_source not in ['system', 'urandom']:
        raise ValueError(f"Unsupported entropy source: {entropy_source}")
    
    if entropy_source == 'urandom':
        return os.urandom(length)
    elif entropy_source == 'system':
        # Use system random source if available
        try:
            with open('/dev/random', 'rb') as f:
                return f.read(length)
        except (FileNotFoundError, OSError):
            logger.warning("System random source not available, falling back to default")
    
    return secrets.token_bytes(length)


def hash_password(
    password: str, 
    salt: Optional[bytes] = None,
    iterations: int = 100000,
    algorithm: str = "sha256"
) -> Tuple[str, bytes]:
    """
    Hash password using PBKDF2 with salt.
    
    Args:
        password: Plain text password
        salt: Optional salt bytes
        iterations: Number of iterations (configurable)
        algorithm: Hash algorithm to use
        
    Returns:
        Tuple of (hashed_password, salt)
    """
    # Validate password strength
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    
    if salt is None:
        salt = generate_random_bytes(32)
    
    # Select algorithm
    hash_algorithm = {
        "sha256": hashes.SHA256(),
        "sha512": hashes.SHA512(),
        "sha1": hashes.SHA1()
    }.get(algorithm)
    
    if not hash_algorithm:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    kdf = PBKDF2HMAC(
        algorithm=hash_algorithm,
        length=32,
        salt=salt,
        iterations=iterations,
    )
    
    key = kdf.derive(password.encode('utf-8'))
    hashed = base64.b64encode(key).decode('utf-8')
    
    return hashed, salt


def verify_password(password: str, hashed_password: str, salt: bytes) -> bool:
    """
    Verify password against hash with timing attack protection.
    
    Args:
        password: Plain text password to verify
        hashed_password: Stored hash to compare against
        salt: Salt used for hashing
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Use constant-time comparison to prevent timing attacks
        new_hash, _ = hash_password(password, salt)
        return secrets.compare_digest(hashed_password.encode('utf-8'), new_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification failed: {str(e)}")
        return False


def generate_encryption_key(
    passphrase: Optional[str] = None,
    salt: Optional[bytes] = None,
    key_rotation_id: Optional[str] = None
) -> bytes:
    """
    Generate encryption key for Fernet.
    
    Args:
        passphrase: Optional passphrase for key derivation
        salt: Salt for key derivation (required if passphrase is provided)
        key_rotation_id: ID for key rotation support
        
    Returns:
        Encryption key bytes
    """
    if passphrase:
        if salt is None:
            salt = generate_random_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(passphrase.encode('utf-8'))
        # Fernet requires base64-encoded key
        return base64.urlsafe_b64encode(key)
    
    # Support for key rotation by logging the key generation
    if key_rotation_id:
        logger.info(f"Generated new encryption key with rotation ID: {key_rotation_id}")
    
    return Fernet.generate_key()


def encrypt_data(
    data: bytes, 
    key: bytes, 
    compress: bool = False,
    chunk_size: int = 1024 * 1024
) -> bytes:
    """
    Encrypt data using Fernet symmetric encryption.
    
    Args:
        data: Data to encrypt
        key: Encryption key
        compress: Whether to compress before encryption
        chunk_size: Chunk size for streaming encryption
        
    Returns:
        Encrypted data bytes
    """
    try:
        # Compress data if requested
        if compress:
            import gzip
            data = gzip.compress(data)
        
        fernet = Fernet(key)
        
        # For large data, implement streaming encryption
        if len(data) > chunk_size:
            logger.info(f"Encrypting large data ({len(data)} bytes) in chunks")
            encrypted_chunks = []
            
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]
                encrypted_chunk = fernet.encrypt(chunk)
                encrypted_chunks.append(encrypted_chunk)
            
            # Combine chunks with a delimiter
            delimiter = b"|||CHUNK|||"
            return delimiter.join(encrypted_chunks)
        
        return fernet.encrypt(data)
        
    except Exception as e:
        logger.error(f"Encryption failed: {str(e)}")
        raise


def decrypt_data(
    encrypted_data: bytes, 
    key: bytes, 
    decompress: bool = False,
    verify_integrity: bool = True
) -> bytes:
    """
    Decrypt data using Fernet symmetric encryption.
    
    Args:
        encrypted_data: Data to decrypt
        key: Decryption key
        decompress: Whether to decompress after decryption
        verify_integrity: Whether to verify data integrity
        
    Returns:
        Decrypted data bytes
    """
    try:
        fernet = Fernet(key)
        
        # Check if data was encrypted in chunks
        delimiter = b"|||CHUNK|||"
        if delimiter in encrypted_data:
            logger.info("Decrypting chunked data")
            encrypted_chunks = encrypted_data.split(delimiter)
            decrypted_chunks = []
            
            for chunk in encrypted_chunks:
                if chunk:  # Skip empty chunks
                    decrypted_chunk = fernet.decrypt(chunk)
                    decrypted_chunks.append(decrypted_chunk)
            
            data = b''.join(decrypted_chunks)
        else:
            data = fernet.decrypt(encrypted_data)
        
        # Verify integrity if requested
        if verify_integrity:
            # Fernet already provides integrity verification
            # Additional checks could be added here
            pass
        
        # Decompress if requested
        if decompress:
            import gzip
            data = gzip.decompress(data)
        
        return data
        
    except Exception as e:
        logger.error(f"Decryption failed: {str(e)}")
        raise


def encrypt_string(
    text: str, 
    key: bytes, 
    encoding: str = "utf-8",
    compress: bool = False
) -> str:
    """
    Encrypt string and return base64 encoded result.
    
    Args:
        text: Text to encrypt
        key: Encryption key
        encoding: Text encoding to use
        compress: Whether to compress text before encryption
        
    Returns:
        Base64 encoded encrypted string
    """
    # Validate encoding
    try:
        text_bytes = text.encode(encoding)
    except UnicodeEncodeError as e:
        logger.error(f"Text encoding failed: {str(e)}")
        raise
    
    encrypted_bytes = encrypt_data(text_bytes, key, compress=compress)
    return base64.b64encode(encrypted_bytes).decode('utf-8')


def decrypt_string(
    encrypted_text: str, 
    key: bytes, 
    encoding: str = "utf-8",
    decompress: bool = False
) -> str:
    """
    Decrypt base64 encoded string.
    
    Args:
        encrypted_text: Base64 encoded encrypted text
        key: Decryption key
        encoding: Text encoding to use
        decompress: Whether to decompress after decryption
        
    Returns:
        Decrypted string
    """
    # Validate base64 encoding
    try:
        encrypted_bytes = base64.b64decode(encrypted_text.encode('utf-8'))
    except Exception as e:
        logger.error(f"Base64 decoding failed: {str(e)}")
        raise
    
    decrypted_bytes = decrypt_data(encrypted_bytes, key, decompress=decompress)
    
    try:
        return decrypted_bytes.decode(encoding)
    except UnicodeDecodeError as e:
        logger.error(f"Text decoding failed: {str(e)}")
        raise


def calculate_hash(
    data: bytes, 
    algorithm: str = 'sha256',
    salt: Optional[bytes] = None,
    chunk_size: int = 8192
) -> str:
    """
    Calculate hash of data with streaming support.
    
    Args:
        data: Data to hash
        algorithm: Hash algorithm to use
        salt: Optional salt for hashing
        chunk_size: Chunk size for streaming calculation
        
    Returns:
        Hexadecimal hash string
    """
    # Validate algorithm
    try:
        hash_obj = hashlib.new(algorithm)
    except ValueError as e:
        logger.error(f"Unsupported hash algorithm: {algorithm}")
        raise
    
    # Add salt if provided
    if salt:
        hash_obj.update(salt)
    
    # Stream data in chunks for large data
    if len(data) > chunk_size:
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            hash_obj.update(chunk)
    else:
        hash_obj.update(data)
    
    return hash_obj.hexdigest()


def calculate_file_checksum(
    file_path: str, 
    algorithm: str = 'sha256',
    progress_callback: Optional[Callable[[float], None]] = None,
    chunk_size: int = 8192,
    verify_integrity: bool = True
) -> str:
    """
    Calculate checksum of file with progress tracking.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm to use
        progress_callback: Optional callback for progress updates
        chunk_size: Size of chunks to read
        verify_integrity: Whether to verify file integrity
        
    Returns:
        Hexadecimal checksum string
    """
    hash_obj = hashlib.new(algorithm)
    
    try:
        file_size = os.path.getsize(file_path) if progress_callback else 0
        bytes_read = 0
        
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                    
                hash_obj.update(chunk)
                bytes_read += len(chunk)
                
                # Report progress if callback provided
                if progress_callback and file_size > 0:
                    progress = (bytes_read / file_size) * 100
                    progress_callback(progress)
        
        checksum = hash_obj.hexdigest()
        
        # Verify integrity by re-reading and comparing
        if verify_integrity and file_size > 0:
            # For large files, skip integrity verification or implement partial verification
            if file_size > 100 * 1024 * 1024:  # 100MB
                logger.info(f"Skipping integrity verification for large file: {file_path}")
            else:
                # Re-calculate to verify
                verify_hash = hashlib.new(algorithm)
                with open(file_path, 'rb') as f:
                    verify_hash.update(f.read())
                if verify_hash.hexdigest() != checksum:
                    raise ValueError("File integrity check failed")
        
        return checksum
        
    except Exception as e:
        logger.error(f"Checksum calculation failed for {file_path}: {str(e)}")
        raise


def generate_rsa_keypair(
    key_size: int = 2048,
    key_format: str = "pem",
    passphrase: Optional[str] = None,
    validate_key: bool = True
) -> Tuple[bytes, bytes]:
    """
    Generate RSA public/private key pair.
    
    Args:
        key_size: RSA key size in bits
        key_format: Key format ('pem', 'der')
        passphrase: Optional passphrase to encrypt private key
        validate_key: Whether to validate generated keys
        
    Returns:
        Tuple of (private_key_bytes, public_key_bytes)
    """
    # Validate key size
    if key_size < 2048:
        raise ValueError("Key size must be at least 2048 bits for security")
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )
    
    # Encrypt private key with passphrase if provided
    encryption_algorithm = serialization.NoEncryption()
    if passphrase:
        encryption_algorithm = serialization.BestAvailableEncryption(passphrase.encode('utf-8'))
    
    # Select encoding format
    encoding = serialization.Encoding.PEM if key_format == "pem" else serialization.Encoding.DER
    
    private_bytes = private_key.private_bytes(
        encoding=encoding,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption_algorithm
    )
    
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=encoding,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Validate keys if requested
    if validate_key:
        try:
            # Test the keys by encrypting and decrypting a small message
            test_message = b"test_key_validation"
            encrypted = rsa_encrypt(test_message, public_bytes)
            decrypted = rsa_decrypt(encrypted, private_bytes, passphrase)
            if decrypted != test_message:
                raise ValueError("Key validation failed")
        except Exception as e:
            logger.error(f"Key validation failed: {str(e)}")
            raise
    
    return private_bytes, public_bytes


def rsa_encrypt(
    data: bytes, 
    public_key_pem: bytes,
    padding_type: str = "oaep",
    validate_key: bool = True
) -> bytes:
    """
    Encrypt data using RSA public key with hybrid encryption support.
    
    Args:
        data: Data to encrypt
        public_key_pem: PEM-encoded public key
        padding_type: Padding type ('oaep', 'pkcs1')
        validate_key: Whether to validate the key
        
    Returns:
        Encrypted data bytes
    """
    from cryptography.hazmat.primitives.asymmetric import rsa
    
    # Validate and load public key
    try:
        public_key = serialization.load_pem_public_key(public_key_pem)
    except Exception as e:
        logger.error(f"Failed to load public key: {str(e)}")
        raise
    
    # Ensure we have an RSA key
    if not isinstance(public_key, rsa.RSAPublicKey):
        raise ValueError("Only RSA keys are supported for encryption")
    
    # Validate key if requested
    if validate_key:
        key_size = public_key.key_size
        if key_size < 2048:
            logger.warning(f"Public key size ({key_size}) is below recommended minimum (2048)")
    
    # For large data, implement hybrid encryption
    max_data_size = (public_key.key_size // 8) - 66  # Account for OAEP padding
    if len(data) > max_data_size:
        # Use symmetric encryption for data and RSA for the symmetric key
        symmetric_key = generate_encryption_key()
        encrypted_data = encrypt_data(data, symmetric_key)
        
        # Encrypt the symmetric key with RSA
        encrypted_key = public_key.encrypt(
            symmetric_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Combine encrypted key and data
        return encrypted_key + b"|||HYBRID|||" + encrypted_data
    
    # Select padding
    if padding_type == "oaep":
        pad = padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    elif padding_type == "pkcs1":
        pad = padding.PKCS1v15()
    else:
        raise ValueError(f"Unsupported padding type: {padding_type}")
    
    encrypted = public_key.encrypt(data, pad)
    return encrypted


def rsa_decrypt(
    encrypted_data: bytes, 
    private_key_pem: bytes,
    passphrase: Optional[str] = None,
    padding_type: str = "oaep",
    validate_key: bool = True
) -> bytes:
    """
    Decrypt data using RSA private key with hybrid decryption support.
    
    Args:
        encrypted_data: Data to decrypt
        private_key_pem: PEM-encoded private key
        passphrase: Passphrase for encrypted private key
        padding_type: Padding type ('oaep', 'pkcs1')
        validate_key: Whether to validate the key
        
    Returns:
        Decrypted data bytes
    """
    from cryptography.hazmat.primitives.asymmetric import rsa
    
    # Load private key with optional passphrase
    try:
        password = passphrase.encode('utf-8') if passphrase else None
        private_key = serialization.load_pem_private_key(private_key_pem, password=password)
    except Exception as e:
        logger.error(f"Failed to load private key: {str(e)}")
        raise
    
    # Ensure we have an RSA key
    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise ValueError("Only RSA keys are supported for decryption")
    
    # Validate key if requested
    if validate_key:
        key_size = private_key.key_size
        if key_size < 2048:
            logger.warning(f"Private key size ({key_size}) is below recommended minimum (2048)")
    
    # Check for hybrid encryption
    hybrid_delimiter = b"|||HYBRID|||"
    if hybrid_delimiter in encrypted_data:
        # Split encrypted key and data
        parts = encrypted_data.split(hybrid_delimiter, 1)
        if len(parts) != 2:
            raise ValueError("Invalid hybrid encrypted data format")
        
        encrypted_key, encrypted_data_part = parts
        
        # Decrypt the symmetric key
        symmetric_key = private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Decrypt the data with symmetric key
        return decrypt_data(encrypted_data_part, symmetric_key)
    
    # Select padding
    if padding_type == "oaep":
        pad = padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    elif padding_type == "pkcs1":
        pad = padding.PKCS1v15()
    else:
        raise ValueError(f"Unsupported padding type: {padding_type}")
    
    decrypted = private_key.decrypt(encrypted_data, pad)
    return decrypted


def sign_data(
    data: bytes, 
    private_key_pem: bytes,
    algorithm: str = "sha256",
    passphrase: Optional[str] = None
) -> bytes:
    """
    Sign data using RSA private key.
    
    Args:
        data: Data to sign
        private_key_pem: PEM-encoded private key
        algorithm: Hash algorithm for signature
        passphrase: Passphrase for encrypted private key
        
    Returns:
        Digital signature bytes
    """
    from cryptography.hazmat.primitives.asymmetric import rsa
    
    # Load private key
    try:
        password = passphrase.encode('utf-8') if passphrase else None
        private_key = serialization.load_pem_private_key(private_key_pem, password=password)
    except Exception as e:
        logger.error(f"Failed to load private key for signing: {str(e)}")
        raise
    
    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise ValueError("Only RSA keys are supported for signing")
    
    # Select hash algorithm
    hash_algorithm = {
        "sha256": hashes.SHA256(),
        "sha384": hashes.SHA384(),
        "sha512": hashes.SHA512(),
        "sha1": hashes.SHA1()
    }.get(algorithm)
    
    if not hash_algorithm:
        raise ValueError(f"Unsupported signature algorithm: {algorithm}")
    
    # Create signature with metadata
    timestamp = int(datetime.now().timestamp())
    metadata = f"alg:{algorithm}|ts:{timestamp}|".encode('utf-8')
    
    signature = private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hash_algorithm),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hash_algorithm
    )
    
    # Combine metadata and signature
    return metadata + signature


def verify_signature(
    data: bytes, 
    signature: bytes, 
    public_key_pem: bytes,
    passphrase: Optional[str] = None
) -> bool:
    """
    Verify signature using RSA public key.
    
    Args:
        data: Original data that was signed
        signature: Signature to verify
        public_key_pem: PEM-encoded public key
        passphrase: Passphrase (not used for public keys, kept for compatibility)
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        from cryptography.hazmat.primitives.asymmetric import rsa
        
        # Load public key
        public_key = serialization.load_pem_public_key(public_key_pem)
        
        if not isinstance(public_key, rsa.RSAPublicKey):
            raise ValueError("Only RSA keys are supported for verification")
        
        # Extract metadata and signature
        if b"|" not in signature:
            logger.warning("Signature missing metadata, assuming legacy format")
            return False
        
        # Parse metadata
        try:
            metadata_end = signature.rindex(b"|")
            metadata = signature[:metadata_end + 1].decode('utf-8')
            actual_signature = signature[metadata_end + 1:]
            
            # Extract algorithm from metadata
            alg_part = [part for part in metadata.split("|") if part.startswith("alg:")]
            if not alg_part:
                raise ValueError("Algorithm not found in signature metadata")
            
            algorithm = alg_part[0].split(":", 1)[1]
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse signature metadata: {str(e)}")
            return False
        
        # Select hash algorithm
        hash_algorithm = {
            "sha256": hashes.SHA256(),
            "sha384": hashes.SHA384(),
            "sha512": hashes.SHA512(),
            "sha1": hashes.SHA1()
        }.get(algorithm)
        
        if not hash_algorithm:
            logger.warning(f"Unsupported signature algorithm: {algorithm}")
            return False
        
        # Verify signature
        public_key.verify(
            actual_signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hash_algorithm),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hash_algorithm
        )
        
        return True
        
    except Exception as e:
        logger.warning(f"Signature verification failed: {str(e)}")
        return False


def create_hmac(
    data: bytes, 
    key: bytes, 
    algorithm: str = 'sha256',
    derive_key: bool = False
) -> str:
    """
    Create HMAC for data integrity with timing attack protection.
    
    Args:
        data: Data to create HMAC for
        key: HMAC key
        algorithm: Hash algorithm to use
        derive_key: Whether to derive key using PBKDF2
        
    Returns:
        Hexadecimal HMAC string
    """
    # Validate algorithm
    if algorithm not in ['sha256', 'sha512', 'sha1']:
        raise ValueError(f"Unsupported HMAC algorithm: {algorithm}")
    
    # Derive key if requested (for additional security)
    if derive_key:
        salt = generate_random_bytes(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=10000,
        )
        derived_key = kdf.derive(key)
        # Prepend salt to result for verification
        mac = hmac.new(derived_key, data, algorithm)
        return base64.b64encode(salt).decode('utf-8') + ":" + mac.hexdigest()
    
    mac = hmac.new(key, data, algorithm)
    return mac.hexdigest()


def verify_hmac(
    data: bytes, 
    key: bytes, 
    expected_hmac: str, 
    algorithm: str = 'sha256',
    derive_key: bool = False
) -> bool:
    """
    Verify HMAC for data integrity with constant-time comparison.
    
    Args:
        data: Original data
        key: HMAC key
        expected_hmac: Expected HMAC value
        algorithm: Hash algorithm used
        derive_key: Whether key was derived
        
    Returns:
        True if HMAC is valid, False otherwise
    """
    try:
        # Handle derived key case
        if derive_key and ":" in expected_hmac:
            salt_b64, expected_mac = expected_hmac.split(":", 1)
            salt = base64.b64decode(salt_b64)
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=10000,
            )
            derived_key = kdf.derive(key)
            calculated_hmac = hmac.new(derived_key, data, algorithm).hexdigest()
        else:
            calculated_hmac = create_hmac(data, key, algorithm, derive_key=False)
            expected_mac = expected_hmac
        
        # Use constant-time comparison to prevent timing attacks
        return secrets.compare_digest(calculated_hmac, expected_mac)
        
    except Exception as e:
        logger.warning(f"HMAC verification failed: {str(e)}")
        return False


class SecureStorage:
    """
    Secure storage wrapper with encryption, compression, and key rotation.
    """
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        self.key = encryption_key or generate_encryption_key()
        self.key_history = []  # For key rotation
        self.compression_enabled = True
        self.integrity_checking = True
    
    def store(self, data: bytes, metadata: Optional[Dict] = None) -> bytes:
        """
        Store data with encryption, compression, and integrity checking.
        
        Args:
            data: Data to store
            metadata: Optional metadata to encrypt with data
            
        Returns:
            Encrypted data with metadata
        """
        # Add metadata if provided
        if metadata:
            metadata_json = base64.b64encode(str(metadata).encode('utf-8'))
            data = metadata_json + b"|||META|||" + data
        
        # Add integrity check
        if self.integrity_checking:
            checksum = calculate_hash(data)
            data = checksum.encode('utf-8') + b"|||CHECKSUM|||" + data
        
        return encrypt_data(data, self.key, compress=self.compression_enabled)
    
    def retrieve(self, encrypted_data: bytes) -> Tuple[bytes, Optional[Dict]]:
        """
        Retrieve and decrypt data with integrity verification.
        
        Args:
            encrypted_data: Encrypted data to retrieve
            
        Returns:
            Tuple of (decrypted_data, metadata)
        """
        data = decrypt_data(encrypted_data, self.key, decompress=self.compression_enabled)
        metadata = None
        
        # Check integrity
        if self.integrity_checking and b"|||CHECKSUM|||" in data:
            checksum_part, data = data.split(b"|||CHECKSUM|||", 1)
            expected_checksum = checksum_part.decode('utf-8')
            actual_checksum = calculate_hash(data)
            
            if not secrets.compare_digest(expected_checksum, actual_checksum):
                raise ValueError("Data integrity check failed")
        
        # Extract metadata
        if b"|||META|||" in data:
            metadata_part, data = data.split(b"|||META|||", 1)
            try:
                metadata_str = base64.b64decode(metadata_part).decode('utf-8')
                metadata = eval(metadata_str)  # Safe for internal use
            except Exception as e:
                logger.warning(f"Failed to parse metadata: {str(e)}")
        
        return data, metadata
    
    def rotate_key(self, new_key: Optional[bytes] = None) -> bytes:
        """
        Rotate encryption key and return old key.
        
        Args:
            new_key: New encryption key (generated if not provided)
            
        Returns:
            Previous encryption key
        """
        old_key = self.key
        self.key_history.append({
            'key': old_key,
            'rotated_at': datetime.now(),
            'key_id': generate_random_string(16)
        })
        
        self.key = new_key or generate_encryption_key()
        logger.info(f"Encryption key rotated. History length: {len(self.key_history)}")
        
        return old_key
    
    def migrate_data(self, encrypted_data: bytes, old_key: bytes) -> bytes:
        """
        Migrate data from old key to current key.
        
        Args:
            encrypted_data: Data encrypted with old key
            old_key: Previous encryption key
            
        Returns:
            Data re-encrypted with current key
        """
        # Decrypt with old key
        data = decrypt_data(encrypted_data, old_key, decompress=self.compression_enabled)
        
        # Re-encrypt with current key
        return encrypt_data(data, self.key, compress=self.compression_enabled)


class TokenGenerator:
    """
    Secure token generator with expiration, validation, and blacklisting.
    """
    
    def __init__(self):
        self.blacklisted_tokens = set()
        self.token_metadata = {}
    
    def generate_api_key(self, length: int = 32, user_id: Optional[str] = None) -> str:
        """
        Generate API key with optional user association.
        
        Args:
            length: Token length
            user_id: Optional user ID to associate with token
            
        Returns:
            API key string
        """
        token = f"ak_{generate_random_string(length)}"
        
        if user_id:
            self.token_metadata[token] = {
                'type': 'api_key',
                'user_id': user_id,
                'created_at': datetime.now(),
                'expires_at': None  # API keys don't expire by default
            }
        
        return token
    
    def generate_session_token(
        self, 
        length: int = 64, 
        expires_in_hours: int = 24,
        user_id: Optional[str] = None
    ) -> str:
        """
        Generate session token with expiration.
        
        Args:
            length: Token length
            expires_in_hours: Hours until token expires
            user_id: Optional user ID to associate with token
            
        Returns:
            Session token string
        """
        token = f"st_{generate_random_string(length)}"
        
        self.token_metadata[token] = {
            'type': 'session',
            'user_id': user_id,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=expires_in_hours)
        }
        
        return token
    
    def generate_reset_token(
        self, 
        length: int = 32, 
        expires_in_hours: int = 1,
        user_id: Optional[str] = None
    ) -> str:
        """
        Generate password reset token with expiration.
        
        Args:
            length: Token length
            expires_in_hours: Hours until token expires
            user_id: User ID to associate with token
            
        Returns:
            Reset token string
        """
        token = f"rt_{generate_random_string(length)}"
        
        self.token_metadata[token] = {
            'type': 'reset',
            'user_id': user_id,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=expires_in_hours)
        }
        
        return token
    
    def generate_verification_token(
        self, 
        length: int = 32, 
        expires_in_hours: int = 24,
        user_id: Optional[str] = None,
        verification_type: str = 'email'
    ) -> str:
        """
        Generate verification token with expiration.
        
        Args:
            length: Token length
            expires_in_hours: Hours until token expires
            user_id: User ID to associate with token
            verification_type: Type of verification (email, phone, etc.)
            
        Returns:
            Verification token string
        """
        token = f"vt_{generate_random_string(length)}"
        
        self.token_metadata[token] = {
            'type': 'verification',
            'verification_type': verification_type,
            'user_id': user_id,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=expires_in_hours)
        }
        
        return token
    
    def validate_token(self, token: str) -> Dict:
        """
        Validate token and return metadata.
        
        Args:
            token: Token to validate
            
        Returns:
            Token validation result
        """
        # Check if token is blacklisted
        if token in self.blacklisted_tokens:
            return {'valid': False, 'reason': 'blacklisted'}
        
        # Check if token has metadata
        if token not in self.token_metadata:
            return {'valid': False, 'reason': 'not_found'}
        
        metadata = self.token_metadata[token]
        
        # Check expiration
        if metadata.get('expires_at') and datetime.now() > metadata['expires_at']:
            return {'valid': False, 'reason': 'expired', 'metadata': metadata}
        
        return {'valid': True, 'metadata': metadata}
    
    def blacklist_token(self, token: str) -> bool:
        """
        Add token to blacklist.
        
        Args:
            token: Token to blacklist
            
        Returns:
            True if token was blacklisted, False if already blacklisted
        """
        if token in self.blacklisted_tokens:
            return False
        
        self.blacklisted_tokens.add(token)
        logger.info(f"Token blacklisted: {token[:10]}...")
        return True
    
    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens from metadata.
        
        Returns:
            Number of tokens cleaned up
        """
        now = datetime.now()
        expired_tokens = []
        
        for token, metadata in self.token_metadata.items():
            if metadata.get('expires_at') and now > metadata['expires_at']:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self.token_metadata[token]
            self.blacklisted_tokens.discard(token)
        
        logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
        return len(expired_tokens)
