"""
Security Module: API Key Encryption & Rate Limiting
"""

import os
import base64
import hashlib
import hmac
import time
import threading
from typing import Dict, Any, Optional, Callable
from functools import wraps
from loguru import logger
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


class SecureKeyManager:
    """Encrypt and decrypt API keys."""
    
    def __init__(self, master_password: str = None):
        self.master_password = master_password or os.getenv('ENCRYPTION_KEY', 'default_key_change_me')
        self.key = self._derive_key(self.master_password)
        self.cipher = Fernet(self.key)
    
    def _derive_key(self, password: str) -> bytes:
        salt = b'financial_orchestrator_salt'
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, value: str) -> str:
        """Encrypt a sensitive value."""
        try:
            encrypted = self.cipher.encrypt(value.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return value
    
    def decrypt(self, encrypted_value: str) -> str:
        """Decrypt a sensitive value."""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return encrypted_value
    
    @staticmethod
    def hash_api_secret(secret: str) -> str:
        """Create a hash of API secret for verification."""
        return hashlib.sha256(secret.encode()).hexdigest()[:16]
    
    @staticmethod
    def verify_signature(secret: str, message: str, signature: str) -> bool:
        """Verify HMAC signature."""
        expected = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


class RateLimiter:
    """Rate limiting for API calls."""
    
    def __init__(self, calls_per_second: int = 10, burst: int = 20):
        self.calls_per_second = calls_per_second
        self.burst = burst
        
        self.tokens = burst
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens, return True if allowed."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            self.tokens = min(
                self.burst,
                self.tokens + elapsed * self.calls_per_second
            )
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait_and_acquire(self, tokens: int = 1, timeout: float = 5.0) -> bool:
        """Wait for tokens to become available."""
        start = time.time()
        
        while time.time() - start < timeout:
            if self.acquire(tokens):
                return True
            time.sleep(0.1)
        
        return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Get estimated wait time for tokens."""
        with self.lock:
            if self.tokens >= tokens:
                return 0.0
            needed = tokens - self.tokens
            return needed / self.calls_per_second


class RateLimitDecorator:
    """Decorator for rate-limited function calls."""
    
    def __init__(self, calls_per_second: int = 10, burst: int = 20):
        self.limiter = RateLimiter(calls_per_second, burst)
    
    def __call__(self, func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.limiter.wait_and_acquire():
                logger.warning(f"Rate limit exceeded for {func.__name__}")
                raise Exception(f"Rate limit exceeded for {func.__name__}")
            return func(*args, **kwargs)
        return wrapper


class BinanceRateLimiter:
    """Rate limiter specific to Binance API endpoints."""
    
    def __init__(self):
        self.weight_endpoints = {
            'GET /api/v3/order': 1,
            'GET /api/v3/openOrders': 1,
            'GET /api/v3/allOrders': 5,
            'GET /api/v3/account': 5,
            'GET /api/v3/myTrades': 5,
            'POST /api/v3/order': 1,
            'DELETE /api/v3/order': 1,
        }
        
        self.limits = {
            'order': RateLimiter(calls_per_second=10, burst=10),
            'account': RateLimiter(calls_per_second=5, burst=10),
            'trades': RateLimiter(calls_per_second=5, burst=10),
        }
    
    def acquire(self, endpoint: str, weight: int = 1) -> bool:
        """Acquire rate limit for endpoint."""
        category = 'account'
        
        for key in self.limits:
            if key in endpoint.lower():
                category = key
                break
        
        return self.limits[category].acquire(weight)
    
    def wait_and_acquire(self, endpoint: str, weight: int = 1) -> bool:
        """Wait and acquire rate limit."""
        category = 'account'
        
        for key in self.limits:
            if key in endpoint.lower():
                category = key
                break
        
        return self.limits[category].wait_and_acquire(weight, timeout=10.0)


class APIKeyValidator:
    """Validate API keys before use."""
    
    @staticmethod
    def validate_binance_key(api_key: str) -> bool:
        """Validate Binance API key format."""
        if not api_key:
            return False
        
        if len(api_key) < 16:
            return False
        
        return True
    
    @staticmethod
    def validate_binance_secret(secret: str) -> bool:
        """Validate Binance secret format."""
        if not secret:
            return False
        
        if len(secret) < 16:
            return False
        
        return True
    
    @staticmethod
    def validate_telegram_token(token: str) -> bool:
        """Validate Telegram bot token format."""
        if not token:
            return False
        
        parts = token.split(':')
        if len(parts) != 2:
            return False
        
        if not parts[0].isdigit():
            return False
        
        return True


class SecurityMonitor:
    """Monitor for suspicious activity."""
    
    def __init__(self):
        self.failed_attempts: Dict[str, int] = {}
        self.lock = threading.Lock()
        
        self.max_attempts = 5
        self.lockout_duration = 300
    
    def record_failure(self, identifier: str):
        """Record a failed attempt."""
        with self.lock:
            self.failed_attempts[identifier] = self.failed_attempts.get(identifier, 0) + 1
    
    def record_success(self, identifier: str):
        """Record a successful attempt."""
        with self.lock:
            self.failed_attempts[identifier] = 0
    
    def is_locked_out(self, identifier: str) -> bool:
        """Check if identifier is locked out."""
        with self.lock:
            return self.failed_attempts.get(identifier, 0) >= self.max_attempts
    
    def get_remaining_attempts(self, identifier: str) -> int:
        """Get remaining attempts before lockout."""
        with self.lock:
            return max(0, self.max_attempts - self.failed_attempts.get(identifier, 0))


security_monitor = SecurityMonitor()
binance_rate_limiter = BinanceRateLimiter()
