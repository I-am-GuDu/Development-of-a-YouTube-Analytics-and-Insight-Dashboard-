"""
Authentication Module
Handles user registration, login, session management.
Uses PostgreSQL database for persistent user storage.

Security features:
- bcrypt password hashing (cost factor 12)
- Login rate limiting with account lockout
- Strong password policy (10+ chars, common password blocklist)
- Uniform registration responses (prevents user enumeration)
"""
import hashlib
import logging
import secrets
import streamlit as st
import bcrypt
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# SECURITY CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Rate limiting configuration
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

# Password policy
MIN_PASSWORD_LENGTH = 10
COMMON_PASSWORDS = frozenset({
    'password', 'password1', 'password123', '123456', '12345678', '123456789',
    '1234567890', 'qwerty', 'abc123', 'letmein', 'welcome', 'monkey',
    'dragon', 'master', 'login', 'admin', 'princess', 'football', 'shadow',
    'sunshine', 'trustno1', 'iloveyou', 'batman', 'superman', 'starwars',
    'freedom', 'whatever', 'qazwsx', '654321', '111111', '000000', '121212',
    'passw0rd', 'p@ssword', 'p@ssw0rd', 'changeme', 'secret', 'default',
})

# In-memory rate limiting store (per-process; for multi-worker deployments,
# consider Redis or database-backed storage)
_login_attempts: dict[str, dict] = {}


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE CONNECTION (lazy singleton)
# ═══════════════════════════════════════════════════════════════════════════════

def _get_db_manager():
    """Get the process-wide DatabaseManager.

    Was cached in ``st.session_state``, which meant one engine -- and one
    connection pool -- per *logged-in user*. The shared provider is cached with
    ``st.cache_resource``, so a single pool now serves every session.
    """
    from data_storage.database import get_shared_manager
    return get_shared_manager()


# ═══════════════════════════════════════════════════════════════════════════════
# PASSWORD HASHING (bcrypt with legacy SHA-256 migration support)
# ═══════════════════════════════════════════════════════════════════════════════

BCRYPT_ROUNDS = 12


def _generate_salt() -> str:
    """Generate a cryptographically secure random salt (legacy support)."""
    return secrets.token_hex(32)


def _legacy_hash_password(password: str, salt: str) -> tuple[str, str]:
    """Legacy SHA-256 hashing — kept ONLY for verifying old hashes during migration."""
    salted = f"{salt}{password}".encode('utf-8')
    hashed = hashlib.sha256(salted).hexdigest()
    return hashed, salt


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Hash a password using bcrypt (cost factor 12).

    Returns:
        Tuple of (hashed_password, salt) — salt is empty string for bcrypt
        since bcrypt embeds the salt in the hash itself.
    """
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=BCRYPT_ROUNDS))
    return hashed.decode('utf-8'), ''


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify a password against a stored hash.

    Supports both bcrypt (new) and legacy SHA-256 hashes for migration.
    """
    if salt:
        # Legacy SHA-256 hash (has separate salt)
        computed_hash, _ = _legacy_hash_password(password, salt)
        return secrets.compare_digest(computed_hash, stored_hash)
    else:
        # bcrypt hash (salt embedded)
        try:
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        except (ValueError, TypeError):
            return False


def _is_bcrypt_hash(stored_hash: str, salt: str) -> bool:
    """Check if a stored hash is bcrypt format (for migration detection)."""
    return not salt and stored_hash.startswith('$2')


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


def _upgrade_password_hash(email: str, password: str) -> None:
    """Transparently upgrade a legacy SHA-256 hash to bcrypt on successful login."""
    new_hash, new_salt = hash_password(password)
    db = _get_db_manager()
    try:
        with db.engine.connect() as conn:
            conn.execute(
                text("UPDATE users SET password_hash = :hash, salt = :salt WHERE email = :email"),
                {"hash": new_hash, "salt": new_salt, "email": email}
            )
            conn.commit()
        logger.info("Password hash upgraded to bcrypt for user: %s", email)
    except SQLAlchemyError as e:
        logger.error("Error upgrading password hash: %s", e)


# ═══════════════════════════════════════════════════════════════════════════════
# RATE LIMITING (login attempt tracking with lockout)
# ═══════════════════════════════════════════════════════════════════════════════

def _check_rate_limit(email: str) -> tuple[bool, str]:
    """Check if an email is currently locked out due to failed attempts.

    Returns:
        Tuple of (allowed: bool, message: str)
    """
    if email not in _login_attempts:
        return True, ""

    info = _login_attempts[email]
    locked_until = info.get('locked_until')

    if locked_until and datetime.now() < locked_until:
        remaining = int((locked_until - datetime.now()).total_seconds() / 60) + 1
        return False, f"Too many failed attempts. Please try again in {remaining} minute(s)."

    # Lockout expired — reset counter
    if locked_until and datetime.now() >= locked_until:
        del _login_attempts[email]

    return True, ""


def _record_failed_attempt(email: str) -> None:
    """Record a failed login attempt; lock account after MAX_LOGIN_ATTEMPTS."""
    if email not in _login_attempts:
        _login_attempts[email] = {'count': 0, 'locked_until': None}

    _login_attempts[email]['count'] += 1

    if _login_attempts[email]['count'] >= MAX_LOGIN_ATTEMPTS:
        _login_attempts[email]['locked_until'] = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
        logger.warning("Account locked due to %d failed attempts: %s",
                       MAX_LOGIN_ATTEMPTS, email)


def _clear_failed_attempts(email: str) -> None:
    """Clear failed attempt counter on successful login."""
    _login_attempts.pop(email, None)


def _validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets security policy.

    Returns:
        Tuple of (valid: bool, error_message: str)
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if password.lower() in COMMON_PASSWORDS:
        return False, "This password is too common. Please choose a stronger one."
    return True, ""


def register_user(email: str, password: str, display_name: str = '') -> tuple[bool, str]:
    """Register a new user in the PostgreSQL database.

    Security: Returns uniform response to prevent user enumeration.

    Returns:
        Tuple of (success: bool, message: str)
    """
    email = email.strip().lower()

    # Validation
    if not email or '@' not in email:
        return False, "Please enter a valid email address."

    # Strong password policy
    valid, pwd_error = _validate_password_strength(password)
    if not valid:
        return False, pwd_error

    if not display_name.strip():
        display_name = email.split('@')[0]

    # Check if user already exists — return uniform response to prevent enumeration
    if _get_user_by_email(email):
        # Don't reveal that the email is already registered
        return True, "If this email is available, you will be able to log in. Try signing in."

    # Hash password with bcrypt and insert
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

    Security features:
    - Rate limiting with account lockout after failed attempts
    - Transparent bcrypt hash migration for legacy users

    Returns:
        Tuple of (success: bool, message: str, user_data: dict | None)
    """
    email = email.strip().lower()

    # Check rate limit before any database access
    allowed, limit_msg = _check_rate_limit(email)
    if not allowed:
        return False, limit_msg, None

    user = _get_user_by_email(email)

    if not user:
        # Record failed attempt even for non-existent users (prevents timing attacks)
        _record_failed_attempt(email)
        return False, "Invalid email or password.", None

    if not user.get("is_active", True):
        return False, "This account has been deactivated.", None

    if not verify_password(password, user['password_hash'], user['salt']):
        _record_failed_attempt(email)
        return False, "Invalid email or password.", None

    # Successful login — clear failed attempts
    _clear_failed_attempts(email)

    # Transparent hash migration: upgrade legacy SHA-256 to bcrypt
    if user['salt'] and not _is_bcrypt_hash(user['password_hash'], user['salt']):
        _upgrade_password_hash(email, password)

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
    """Log out the current user and clear ALL session data."""
    keys_to_clear = [
        # Auth state
        'authenticated', 'user_email', 'user_display_name',
        # Analytics data
        'channel_data', 'video_df', 'engagement_metrics',
        'comments_df', 'ai_insights_result',
        # Additional cached data
        'selected_channel_id', 'video_analytics', 'trend_data',
        'comparison_data', 'sentiment_results',
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
