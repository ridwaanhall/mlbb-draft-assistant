#!/usr/bin/env python3
"""
URL Encryption Utility for MLBB Draft Assistant

This script encrypts the API URL using the key from .env file.
Run this script to generate the encrypted URL for use in the main application.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv


def derive_key_from_password(password: str) -> bytes:
    """
    Derive a Fernet-compatible key from a password.
    
    Args:
        password (str): Password to derive key from
        
    Returns:
        bytes: Fernet-compatible encryption key
    """
    password_bytes = password.encode()
    salt = b'mlbb_draft_assistant_salt'  # Fixed salt for consistency
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
    return key


def encrypt_url(url: str, key: bytes) -> str:
    """
    Encrypt a URL using Fernet encryption.
    
    Args:
        url (str): URL to encrypt
        key (bytes): Encryption key
        
    Returns:
        str: Base64 encoded encrypted URL
    """
    fernet = Fernet(key)
    encrypted_url = fernet.encrypt(url.encode())
    return base64.urlsafe_b64encode(encrypted_url).decode()


def decrypt_url(encrypted_url_b64: str, key: bytes) -> str:
    """
    Decrypt a URL using Fernet encryption.
    
    Args:
        encrypted_url_b64 (str): Base64 encoded encrypted URL
        key (bytes): Encryption key
        
    Returns:
        str: Decrypted URL
    """
    fernet = Fernet(key)
    encrypted_url = base64.urlsafe_b64decode(encrypted_url_b64.encode())
    decrypted_url = fernet.decrypt(encrypted_url).decode()
    return decrypted_url


def main():
    """Main function to encrypt the MLBB API URL."""
    # Load environment variables
    load_dotenv()
    
    # Get the key from environment
    key_string = os.getenv('KEY')
    if not key_string:
        print("❌ Error: KEY environment variable not set.")
        print("Please create a .env file with: KEY=ridwaanhall")
        return
    
    # Original URL to encrypt
    original_url = "haha"
    
    # Derive encryption key
    encryption_key = derive_key_from_password(key_string)
    
    # Encrypt the URL
    encrypted_url = encrypt_url(original_url, encryption_key)
    
    print("🔐 URL Encryption Utility")
    print("=" * 50)
    print(f"🔑 Key: {key_string}")
    print(f"📝 Original URL: {original_url}")
    print(f"🔒 Encrypted URL: {encrypted_url}")
    
    # Verify decryption works
    try:
        decrypted_url = decrypt_url(encrypted_url, encryption_key)
        print(f"✅ Decryption Test: {decrypted_url}")
        
        if decrypted_url == original_url:
            print("✅ Encryption/Decryption successful!")
            print("\n📋 Copy this encrypted URL to your code:")
            print(f'ENCRYPTED_BASE_URL: str = "{encrypted_url}"')
        else:
            print("❌ Decryption failed - URLs don't match!")
            
    except Exception as e:
        print(f"❌ Error during decryption test: {str(e)}")


if __name__ == "__main__":
    main()
