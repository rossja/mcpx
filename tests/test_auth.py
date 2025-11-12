"""Tests for authentication functionality."""

import pytest
import tempfile
import os
from datetime import datetime, timedelta

from src.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_auth_code,
    verify_code_challenge,
)
from src.auth.database import (
    init_database,
    create_default_user,
    get_user_by_username,
    get_user_by_id,
    save_auth_code,
    get_auth_code,
    mark_auth_code_used,
    save_tokens,
    get_token_info,
    get_refresh_token_info,
    revoke_token,
    revoke_refresh_token,
)
from src.config import config


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Save original db path
    original_path = config.AUTH_DB_PATH
    
    # Set config to use temp db
    config.AUTH_DB_PATH = path
    
    # Initialize database
    init_database()
    
    yield path
    
    # Cleanup
    os.unlink(path)
    config.AUTH_DB_PATH = original_path


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        password_hash = hash_password(password)
        
        assert password_hash is not None
        assert password_hash != password
        assert password_hash.startswith("$2b$")
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        password_hash = hash_password(password)
        
        assert verify_password(password, password_hash) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        password_hash = hash_password(password)
        
        assert verify_password(wrong_password, password_hash) is False


class TestJWTTokens:
    """Test JWT token creation and verification."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        user_id = 1
        username = "testuser"
        
        token = create_access_token(user_id, username)
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        user_id = 1
        username = "testuser"
        
        token = create_refresh_token(user_id, username)
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_verify_valid_token(self):
        """Test verification of valid token."""
        user_id = 1
        username = "testuser"
        
        token = create_access_token(user_id, username)
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["username"] == username
        assert payload["type"] == "access"
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = verify_token(invalid_token)
        
        assert payload is None


class TestCodeChallenge:
    """Test PKCE code challenge verification."""
    
    def test_verify_code_challenge_s256(self):
        """Test S256 code challenge verification."""
        import hashlib
        import base64
        
        code_verifier = "test_verifier_12345678901234567890"
        
        # Generate challenge
        verifier_hash = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(verifier_hash).decode('utf-8').rstrip('=')
        
        # Verify
        assert verify_code_challenge(code_verifier, code_challenge, "S256") is True
    
    def test_verify_code_challenge_plain(self):
        """Test plain code challenge verification."""
        code_verifier = "test_verifier"
        code_challenge = "test_verifier"
        
        assert verify_code_challenge(code_verifier, code_challenge, "plain") is True
    
    def test_verify_code_challenge_invalid(self):
        """Test invalid code challenge verification."""
        code_verifier = "test_verifier"
        code_challenge = "wrong_challenge"
        
        assert verify_code_challenge(code_verifier, code_challenge, "plain") is False


class TestDatabase:
    """Test database operations."""
    
    def test_init_database(self, temp_db):
        """Test database initialization."""
        # Database is already initialized in fixture
        assert os.path.exists(temp_db)
    
    def test_create_default_user(self, temp_db):
        """Test default user creation."""
        create_default_user()
        
        user = get_user_by_username("mcpuser")
        
        assert user is not None
        assert user["username"] == "mcpuser"
        assert user["password_hash"] is not None
    
    def test_get_user_by_username(self, temp_db):
        """Test getting user by username."""
        create_default_user()
        
        user = get_user_by_username("mcpuser")
        
        assert user is not None
        assert user["username"] == "mcpuser"
    
    def test_get_user_by_username_not_found(self, temp_db):
        """Test getting non-existent user."""
        user = get_user_by_username("nonexistent")
        
        assert user is None
    
    def test_get_user_by_id(self, temp_db):
        """Test getting user by ID."""
        create_default_user()
        
        # Get user by username first to get ID
        user1 = get_user_by_username("mcpuser")
        user_id = user1["id"]
        
        # Get by ID
        user2 = get_user_by_id(user_id)
        
        assert user2 is not None
        assert user2["id"] == user_id
        assert user2["username"] == "mcpuser"
    
    def test_save_and_get_auth_code(self, temp_db):
        """Test saving and retrieving authorization code."""
        create_default_user()
        user = get_user_by_username("mcpuser")
        
        code = generate_auth_code()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        save_auth_code(
            code=code,
            user_id=user["id"],
            client_id="test-client",
            redirect_uri="http://localhost/callback",
            code_challenge="test_challenge",
            code_challenge_method="S256",
            expires_at=expires_at
        )
        
        auth_code = get_auth_code(code)
        
        assert auth_code is not None
        assert auth_code["code"] == code
        assert auth_code["user_id"] == user["id"]
        assert auth_code["used"] == 0
    
    def test_mark_auth_code_used(self, temp_db):
        """Test marking authorization code as used."""
        create_default_user()
        user = get_user_by_username("mcpuser")
        
        code = generate_auth_code()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        save_auth_code(
            code=code,
            user_id=user["id"],
            client_id="test-client",
            redirect_uri="http://localhost/callback",
            code_challenge="test_challenge",
            code_challenge_method="S256",
            expires_at=expires_at
        )
        
        mark_auth_code_used(code)
        
        auth_code = get_auth_code(code)
        assert auth_code["used"] == 1
    
    def test_save_and_get_tokens(self, temp_db):
        """Test saving and retrieving tokens."""
        create_default_user()
        user = get_user_by_username("mcpuser")
        
        access_token = create_access_token(user["id"], user["username"])
        refresh_token = create_refresh_token(user["id"], user["username"])
        
        access_expires_at = datetime.utcnow() + timedelta(hours=1)
        refresh_expires_at = datetime.utcnow() + timedelta(days=30)
        
        save_tokens(
            user_id=user["id"],
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_at=access_expires_at,
            refresh_token_expires_at=refresh_expires_at
        )
        
        token_info = get_token_info(access_token)
        
        assert token_info is not None
        assert token_info["access_token"] == access_token
        assert token_info["user_id"] == user["id"]
        assert token_info["revoked"] == 0
    
    def test_revoke_token(self, temp_db):
        """Test token revocation."""
        create_default_user()
        user = get_user_by_username("mcpuser")
        
        access_token = create_access_token(user["id"], user["username"])
        refresh_token = create_refresh_token(user["id"], user["username"])
        
        access_expires_at = datetime.utcnow() + timedelta(hours=1)
        refresh_expires_at = datetime.utcnow() + timedelta(days=30)
        
        save_tokens(
            user_id=user["id"],
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_at=access_expires_at,
            refresh_token_expires_at=refresh_expires_at
        )
        
        revoke_token(access_token)
        
        token_info = get_token_info(access_token)
        assert token_info is None  # Should not return revoked tokens
    
    def test_get_refresh_token_info(self, temp_db):
        """Test getting refresh token info."""
        create_default_user()
        user = get_user_by_username("mcpuser")
        
        access_token = create_access_token(user["id"], user["username"])
        refresh_token = create_refresh_token(user["id"], user["username"])
        
        access_expires_at = datetime.utcnow() + timedelta(hours=1)
        refresh_expires_at = datetime.utcnow() + timedelta(days=30)
        
        save_tokens(
            user_id=user["id"],
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_at=access_expires_at,
            refresh_token_expires_at=refresh_expires_at
        )
        
        refresh_info = get_refresh_token_info(refresh_token)
        
        assert refresh_info is not None
        assert refresh_info["refresh_token"] == refresh_token
        assert refresh_info["user_id"] == user["id"]


class TestAuthenticationFlow:
    """Test complete authentication flow."""
    
    def test_user_creation_and_login(self, temp_db):
        """Test user creation and password verification."""
        create_default_user()
        
        user = get_user_by_username("mcpuser")
        
        assert user is not None
        assert verify_password("OMG!letmein", user["password_hash"]) is True
    
    def test_token_generation_and_verification(self, temp_db):
        """Test token generation and verification."""
        create_default_user()
        user = get_user_by_username("mcpuser")
        
        # Generate tokens
        access_token = create_access_token(user["id"], user["username"])
        refresh_token = create_refresh_token(user["id"], user["username"])
        
        # Verify access token
        access_payload = verify_token(access_token)
        assert access_payload is not None
        assert access_payload["type"] == "access"
        assert access_payload["sub"] == str(user["id"])
        
        # Verify refresh token
        refresh_payload = verify_token(refresh_token)
        assert refresh_payload is not None
        assert refresh_payload["type"] == "refresh"
        assert refresh_payload["sub"] == str(user["id"])

