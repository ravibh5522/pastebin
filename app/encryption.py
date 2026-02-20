"""
Encryption utilities for private pastes.
Uses AES-256-GCM for symmetric encryption with PBKDF2 key derivation.
"""
import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Constants
SALT_SIZE = 16  # 128-bit salt
NONCE_SIZE = 12  # 96-bit nonce for GCM
KEY_SIZE = 32  # 256-bit key
ITERATIONS = 100000  # PBKDF2 iterations

def generate_salt() -> str:
    """Generate a random salt and return it as base64 string."""
    salt = os.urandom(SALT_SIZE)
    return base64.b64encode(salt).decode('utf-8')

def derive_key(pin: str, salt: str) -> bytes:
    """Derive a 256-bit key from PIN using PBKDF2."""
    salt_bytes = base64.b64decode(salt.encode('utf-8'))
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt_bytes,
        iterations=ITERATIONS,
    )
    return kdf.derive(pin.encode('utf-8'))

def hash_pin(pin: str) -> str:
    """Hash PIN for verification (separate from encryption key)."""
    # Use a different method for PIN verification vs encryption
    return hashlib.sha256(f"paste_pin_verify:{pin}".encode()).hexdigest()

def verify_pin(pin: str, pin_hash: str) -> bool:
    """Verify if the provided PIN matches the stored hash."""
    return hash_pin(pin) == pin_hash

def encrypt_content(content: str, pin: str, salt: str) -> str:
    """
    Encrypt content using AES-256-GCM.
    Returns base64-encoded ciphertext (nonce + ciphertext + tag).
    """
    key = derive_key(pin, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_SIZE)
    
    plaintext = content.encode('utf-8')
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    
    # Combine nonce + ciphertext for storage
    combined = nonce + ciphertext
    return base64.b64encode(combined).decode('utf-8')

def decrypt_content(encrypted_content: str, pin: str, salt: str) -> str:
    """
    Decrypt content using AES-256-GCM.
    Returns the original plaintext.
    Raises ValueError if decryption fails (wrong PIN).
    """
    try:
        key = derive_key(pin, salt)
        aesgcm = AESGCM(key)
        
        combined = base64.b64decode(encrypted_content.encode('utf-8'))
        nonce = combined[:NONCE_SIZE]
        ciphertext = combined[NONCE_SIZE:]
        
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')
    except Exception as e:
        raise ValueError("Invalid PIN or corrupted data") from e

def encrypt_file(file_content: bytes, pin: str, salt: str) -> bytes:
    """
    Encrypt file content using AES-256-GCM.
    Returns encrypted bytes (nonce + ciphertext + tag).
    """
    key = derive_key(pin, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_SIZE)
    
    ciphertext = aesgcm.encrypt(nonce, file_content, None)
    return nonce + ciphertext

def decrypt_file(encrypted_content: bytes, pin: str, salt: str) -> bytes:
    """
    Decrypt file content using AES-256-GCM.
    Returns the original file bytes.
    Raises ValueError if decryption fails.
    """
    try:
        key = derive_key(pin, salt)
        aesgcm = AESGCM(key)
        
        nonce = encrypted_content[:NONCE_SIZE]
        ciphertext = encrypted_content[NONCE_SIZE:]
        
        return aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as e:
        raise ValueError("Invalid PIN or corrupted data") from e
