"""Database operations for authentication."""

import sqlite3
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from ..config import config
from .utils import hash_password

logger = logging.getLogger(__name__)


def get_db_connection():
    """Get a connection to the authentication database."""
    # Ensure the directory exists
    db_path = Path(config.AUTH_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(config.AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize the authentication database with required tables."""
    logger.info(f"Initializing authentication database at {config.AUTH_DB_PATH}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    # Create oauth_tokens table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS oauth_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            access_token TEXT UNIQUE NOT NULL,
            refresh_token TEXT UNIQUE NOT NULL,
            access_token_expires_at TIMESTAMP NOT NULL,
            refresh_token_expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            revoked INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create oauth_auth_codes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS oauth_auth_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            client_id TEXT NOT NULL,
            redirect_uri TEXT NOT NULL,
            code_challenge TEXT NOT NULL,
            code_challenge_method TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tokens_access ON oauth_tokens(access_token)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tokens_refresh ON oauth_tokens(refresh_token)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_codes_code ON oauth_auth_codes(code)")
    
    conn.commit()
    conn.close()
    
    logger.info("Database initialized successfully")


def create_default_user():
    """Create the default user if it doesn't exist."""
    username = "mcpuser"
    password = "OMG!letmein"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        logger.info(f"Default user '{username}' already exists")
        conn.close()
        return
    
    # Create the user
    password_hash = hash_password(password)
    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, password_hash)
    )
    conn.commit()
    conn.close()
    
    logger.info(f"Created default user '{username}'")


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get a user by username."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get a user by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def update_last_login(user_id: int):
    """Update the last login timestamp for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE users SET last_login = ? WHERE id = ?",
        (datetime.now().isoformat(), user_id)
    )
    conn.commit()
    conn.close()


def save_auth_code(
    code: str,
    user_id: int,
    client_id: str,
    redirect_uri: str,
    code_challenge: str,
    code_challenge_method: str,
    expires_at: datetime
):
    """Save an authorization code."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT INTO oauth_auth_codes 
        (code, user_id, client_id, redirect_uri, code_challenge, code_challenge_method, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (code, user_id, client_id, redirect_uri, code_challenge, code_challenge_method, expires_at.isoformat())
    )
    conn.commit()
    conn.close()


def get_auth_code(code: str) -> Optional[Dict[str, Any]]:
    """Get an authorization code."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM oauth_auth_codes WHERE code = ?", (code,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def mark_auth_code_used(code: str):
    """Mark an authorization code as used."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE oauth_auth_codes SET used = 1 WHERE code = ?", (code,))
    conn.commit()
    conn.close()


def save_tokens(
    user_id: int,
    access_token: str,
    refresh_token: str,
    access_token_expires_at: datetime,
    refresh_token_expires_at: datetime
):
    """Save access and refresh tokens."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT INTO oauth_tokens 
        (user_id, access_token, refresh_token, access_token_expires_at, refresh_token_expires_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, access_token, refresh_token, 
         access_token_expires_at.isoformat(), refresh_token_expires_at.isoformat())
    )
    conn.commit()
    conn.close()


def get_token_info(access_token: str) -> Optional[Dict[str, Any]]:
    """Get token information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM oauth_tokens WHERE access_token = ? AND revoked = 0", (access_token,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_refresh_token_info(refresh_token: str) -> Optional[Dict[str, Any]]:
    """Get refresh token information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM oauth_tokens WHERE refresh_token = ? AND revoked = 0", (refresh_token,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def revoke_token(access_token: str):
    """Revoke a token."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE oauth_tokens SET revoked = 1 WHERE access_token = ?", (access_token,))
    conn.commit()
    conn.close()


def revoke_refresh_token(refresh_token: str):
    """Revoke a refresh token."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE oauth_tokens SET revoked = 1 WHERE refresh_token = ?", (refresh_token,))
    conn.commit()
    conn.close()

