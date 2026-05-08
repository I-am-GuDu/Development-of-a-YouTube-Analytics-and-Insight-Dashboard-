"""
Authentication Module
Handles user registration, login, session management.
Uses file-based storage (users.json) — upgradeable to PostgreSQL later.
"""
import hashlib
import json
import os
import secrets
import streamlit as st
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')


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
# USER STORE (JSON file)
# ═══════════════════════════════════════════════════════════════════════════════

def load_users() -> dict:
    """Load users from the JSON file."""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_users(users: dict) -> None:
    """Save users to the JSON file."""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def register_user(email: str, password: str, display_name: str = '') -> tuple[bool, str]:
    """Register a new user.

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

    users = load_users()

    if email in users:
        return False, "An account with this email already exists."

    hashed, salt = hash_password(password)
    users[email] = {
        'display_name': display_name.strip(),
        'password_hash': hashed,
        'salt': salt,
        'created_at': datetime.now().isoformat(),
    }

    save_users(users)
    return True, "Account created successfully! You can now log in."


def authenticate_user(email: str, password: str) -> tuple[bool, str, dict | None]:
    """Authenticate a user with email and password.

    Returns:
        Tuple of (success: bool, message: str, user_data: dict | None)
    """
    email = email.strip().lower()
    users = load_users()

    if email not in users:
        return False, "Invalid email or password.", None

    user = users[email]
    if not verify_password(password, user['password_hash'], user['salt']):
        return False, "Invalid email or password.", None

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
