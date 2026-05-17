"""
Authentication Module
Handles user registration, login, session management.
Uses PostgreSQL database for persistent user storage.
"""
import hashlib
import logging
import secrets
import streamlit as st
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE CONNECTION (lazy singleton)
# ═══════════════════════════════════════════════════════════════════════════════

def _get_db_manager():
    """Get or create a cached DatabaseManager instance."""
    if 'db_manager' not in st.session_state:
        from data_storage.database import DatabaseManager
        st.session_state['db_manager'] = DatabaseManager()
    return st.session_state['db_manager']


# ═══════════════════════════════════════════════════════════════════════════════
# PASSWORD HASHING (using hashlib — no extra dependencies)
# ═══════════════════════════════════════════════════════════════════════════════

def _generate_salt() -> str:
    """Generate a cryptographically secure random salt."""
    return secrets.token_hex(32)


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hash a password with a salt using SHA-256.

    Returns:
        Tuple of (hashed_password, salt)
    """
    if salt is None:
        salt = _generate_salt()
    salted = f"{salt}{password}".encode('utf-8')
    hashed = hashlib.sha256(salted).hexdigest()
    return hashed, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify a password against a stored hash."""
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, stored_hash)


# ═══════════════════════════════════════════════════════════════════════════════
# USER STORE (PostgreSQL)
# ═══════════════════════════════════════════════════════════════════════════════

def _get_user_by_email(email: str) -> dict | None:
    """Fetch a user record from the database by email.

    Returns:
        User dict or None if not found.
    """
    db = _get_db_manager()
    try:
        with db.engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, email, display_name, password_hash, salt, is_active, created_at, last_login "
                     "FROM users WHERE email = :email"),
                {"email": email}
            )
            row = result.fetchone()
            if row:
                return {
                    "id": row[0],
                    "email": row[1],
                    "display_name": row[2],
                    "password_hash": row[3],
                    "salt": row[4],
                    "is_active": row[5],
                    "created_at": row[6],
                    "last_login": row[7],
                }
    except SQLAlchemyError as e:
        logger.error("Error fetching user by email: %s", e)
    return None


def _update_last_login(email: str) -> None:
    """Update the last_login timestamp for a user."""
    db = _get_db_manager()
    try:
        with db.engine.connect() as conn:
            conn.execute(
                text("UPDATE users SET last_login = :now WHERE email = :email"),
                {"now": datetime.now(), "email": email}
            )
            conn.commit()
    except SQLAlchemyError as e:
        logger.error("Error updating last_login: %s", e)


def register_user(email: str, password: str, display_name: str = '') -> tuple[bool, str]:
    """Register a new user in the PostgreSQL database.

    Returns:
        Tuple of (success: bool, message: str)
    """
    email = email.strip().lower()

    # Validation
    if not email or '@' not in email:
        return False, "Please enter a valid email address."
    if len(password) < 5:
        return False, "Password must be at least 5 characters."
    if not display_name.strip():
        display_name = email.split('@')[0]

    # Check if user already exists
    if _get_user_by_email(email):
        return False, "An account with this email already exists."

    # Hash password and insert
    hashed, salt = hash_password(password)
    db = _get_db_manager()
    try:
        with db.engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO users (email, display_name, password_hash, salt, created_at)
                    VALUES (:email, :display_name, :password_hash, :salt, :created_at)
                """),
                {
                    "email": email,
                    "display_name": display_name.strip(),
                    "password_hash": hashed,
                    "salt": salt,
                    "created_at": datetime.now(),
                }
            )
            conn.commit()
        logger.info("New user registered: %s", email)
        return True, "Account created successfully! You can now log in."
    except SQLAlchemyError as e:
        logger.error("Error registering user: %s", e)
        return False, "Registration failed. Please try again later."


def authenticate_user(email: str, password: str) -> tuple[bool, str, dict | None]:
    """Authenticate a user with email and password.

    Returns:
        Tuple of (success: bool, message: str, user_data: dict | None)
    """
    email = email.strip().lower()
    user = _get_user_by_email(email)

    if not user:
        return False, "Invalid email or password.", None

    if not user.get("is_active", True):
        return False, "This account has been deactivated.", None

    if not verify_password(password, user['password_hash'], user['salt']):
        return False, "Invalid email or password.", None

    # Update last login timestamp
    _update_last_login(email)

    return True, "Login successful!", {
        'email': email,
        'display_name': user['display_name'],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def is_logged_in() -> bool:
    """Check if the current user is logged in."""
    return st.session_state.get('authenticated', False)


def get_current_user() -> dict | None:
    """Get the current logged-in user's data."""
    if not is_logged_in():
        return None
    return {
        'email': st.session_state.get('user_email', ''),
        'display_name': st.session_state.get('user_display_name', ''),
    }


def login(email: str, password: str) -> tuple[bool, str]:
    """Attempt to log in a user and create a session.

    Returns:
        Tuple of (success: bool, message: str)
    """
    success, message, user_data = authenticate_user(email, password)

    if success and user_data:
        st.session_state['authenticated'] = True
        st.session_state['user_email'] = user_data['email']
        st.session_state['user_display_name'] = user_data['display_name']

    return success, message


def logout() -> None:
    """Log out the current user and clear the session."""
    keys_to_clear = [
        'authenticated', 'user_email', 'user_display_name',
        'channel_data', 'video_df', 'engagement_metrics',
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
