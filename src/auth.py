"""Streamlit-native authentication (no separate Node.js gateway).

Two ways to sign in, both ending in the same app session:

* Email + password  -> the app's own ``users`` table (bcrypt, rate limited).
* Continue with Google -> Neon Auth's managed Google provider. Python starts the
  flow server-side, the browser visits Google, and on return Python exchanges
  Neon's one-time verifier for the identity (the same handshake the Neon SDK
  performs). The Neon session is revoked right away; only the app session below
  is kept.

App sessions: a random token lives in the ``yt_session`` browser cookie, and only
its SHA-256 hash is stored in ``user_sessions``. Sessions expire after
``SESSION_DAYS``, are revoked on logout, and are re-checked against the database
at least every ``REVALIDATE_SECONDS`` so a logout in one tab ends the others.

Streamlit's ``st.context.cookies`` is a snapshot from the WebSocket handshake and
Python cannot set cookies, so cookie writes are queued and performed by a tiny
same-origin script (``render_auth_bridge``). That cookie cannot be HttpOnly;
server-side hashing, expiry and revocation limit what a stolen value is worth.
"""
import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, urlsplit

import bcrypt
import requests
import streamlit as st
import streamlit.components.v1 as components
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

SESSION_COOKIE = "yt_session"
OAUTH_NONCE_COOKIE = "yt_oauth_nonce"
SESSION_DAYS = 7
REVALIDATE_SECONDS = 60
OAUTH_FLOW_SECONDS = 600
MAX_PENDING_OAUTH_FLOWS = 500

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 72          # bcrypt only uses the first 72 bytes
BCRYPT_ROUNDS = 12
COMMON_PASSWORDS = frozenset({
    'password', 'password1', 'password123', '123456', '12345678', '123456789',
    '1234567890', 'qwerty', 'abc123', 'letmein', 'welcome', 'monkey',
    'dragon', 'master', 'login', 'admin', 'princess', 'football', 'shadow',
    'sunshine', 'trustno1', 'iloveyou', 'batman', 'superman', 'starwars',
    'freedom', 'whatever', 'qazwsx', '654321', '111111', '000000', '121212',
    'passw0rd', 'p@ssword', 'p@ssw0rd', 'changeme', 'secret', 'default',
})
_NO_PROXY = {"http": "", "https": "", "all": ""}
_KEEP_ON_CLEAR = {"theme_mode", "theme_override", "_login_entered", "_cookie_actions"}

# Per-process stores (single Streamlit process on EC2). A restart only forces
# in-progress Google sign-ins to start again; app sessions live in the DB.
_login_attempts: dict[str, dict] = {}
_attempts_lock = threading.Lock()
_oauth_flows: dict[str, dict] = {}
_oauth_lock = threading.Lock()
_tables_ready = False
_tables_lock = threading.Lock()


def _setting(name, default=""):
    value = os.getenv(name)
    if value is not None:
        return value
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def _hash_token(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now():
    return datetime.now(timezone.utc)


def _valid_origin(value) -> str | None:
    """Accept https origins, or http only for localhost development."""
    try:
        parts = urlsplit(value or "")
        local = parts.hostname in ("localhost", "127.0.0.1")
        if (parts.scheme not in ("https", "http") or (parts.scheme == "http" and not local)
                or not parts.hostname or parts.username or parts.password
                or parts.path not in ("", "/") or parts.query or parts.fragment):
            return None
        return f"{parts.scheme}://{parts.netloc}"
    except (ValueError, TypeError):
        return None


def _app_origin() -> str | None:
    """APP_ORIGIN if configured, otherwise the origin shown in the browser."""
    configured = _setting("APP_ORIGIN")
    if configured:
        return _valid_origin(configured)
    try:
        return _valid_origin(urlsplit(st.context.url)._replace(path="", query="", fragment="").geturl())
    except Exception:
        return None


def _neon_auth_url() -> str | None:
    try:
        url = _setting("NEON_AUTH_URL").strip().rstrip("/")
        parts = urlsplit(url)
        if (parts.scheme != "https" or not parts.hostname or not parts.hostname.endswith(".neon.tech")
                or ".neonauth." not in parts.hostname or parts.username or parts.password
                or parts.port or parts.query or parts.fragment or not parts.path.endswith("/auth")):
            return None
        return url
    except (ValueError, TypeError):
        return None


def google_available() -> bool:
    """Google is on when Neon Auth is configured, unless switched off explicitly."""
    return _setting("AUTH_GOOGLE_ENABLED", "true").lower() != "false" and _neon_auth_url() is not None


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

def _engine():
    from data_storage.database import get_shared_manager
    return get_shared_manager().engine


def _ensure_tables():
    """Create the two auth tables this module needs (idempotent, once per process)."""
    global _tables_ready
    if _tables_ready:
        return
    with _tables_lock:
        if _tables_ready:
            return
        with _engine().begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS oauth_users (
                    id SERIAL PRIMARY KEY,
                    provider VARCHAR(50) NOT NULL,
                    provider_user_id VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    display_name VARCHAR(255) NOT NULL DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (provider, provider_user_id)
                )"""))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    token_hash CHAR(64) PRIMARY KEY,
                    user_key VARCHAR(80) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    display_name VARCHAR(255) NOT NULL DEFAULT '',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMPTZ NOT NULL,
                    revoked_at TIMESTAMPTZ
                )"""))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_key)"))
        _tables_ready = True


def _db_find_user(email):
    with _engine().connect() as conn:
        row = conn.execute(text(
            "SELECT id, email, display_name, password_hash, is_active FROM users WHERE email = :email"),
            {"email": email}).fetchone()
    if not row:
        return None
    return {"id": row[0], "email": row[1], "display_name": row[2],
            "password_hash": row[3], "is_active": row[4]}


def _db_insert_user(email, display_name, password_hash):
    """Insert a user; returns False if the email already exists."""
    with _engine().begin() as conn:
        result = conn.execute(text("""
            INSERT INTO users (email, display_name, password_hash, salt, created_at)
            VALUES (:email, :display_name, :password_hash, '', NOW())
            ON CONFLICT (email) DO NOTHING"""),
            {"email": email, "display_name": display_name, "password_hash": password_hash})
        return result.rowcount == 1


def _db_touch_user(user_id):
    with _engine().begin() as conn:
        conn.execute(text("UPDATE users SET last_login = NOW() WHERE id = :id"), {"id": user_id})


def _db_upsert_oauth_user(provider, subject, email, display_name):
    _ensure_tables()
    with _engine().begin() as conn:
        return conn.execute(text("""
            INSERT INTO oauth_users (provider, provider_user_id, email, display_name, last_login)
            VALUES (:provider, :subject, :email, :name, NOW())
            ON CONFLICT (provider, provider_user_id) DO UPDATE
                SET email = EXCLUDED.email, display_name = EXCLUDED.display_name, last_login = NOW()
            RETURNING id"""),
            {"provider": provider, "subject": subject, "email": email, "name": display_name}).scalar_one()


def _db_create_session(token_hash, identity, expires_at):
    _ensure_tables()
    with _engine().begin() as conn:
        conn.execute(text("""
            INSERT INTO user_sessions (token_hash, user_key, email, display_name, expires_at)
            VALUES (:h, :key, :email, :name, :expires)"""),
            {"h": token_hash, "key": identity["id"], "email": identity["email"],
             "name": identity["display_name"], "expires": expires_at})
        conn.execute(text("DELETE FROM user_sessions WHERE expires_at < NOW() - INTERVAL '1 day'"))


def _db_lookup_session(token_hash):
    _ensure_tables()
    with _engine().connect() as conn:
        row = conn.execute(text("""
            SELECT s.user_key, s.email, s.display_name
            FROM user_sessions s
            LEFT JOIN users u ON s.user_key = 'local:' || u.id::text
            WHERE s.token_hash = :h AND s.revoked_at IS NULL AND s.expires_at > NOW()
              AND (s.user_key NOT LIKE 'local:%' OR COALESCE(u.is_active, FALSE))"""),
            {"h": token_hash}).fetchone()
    return {"id": row[0], "email": row[1], "display_name": row[2]} if row else None


def _db_revoke_session(token_hash):
    _ensure_tables()
    with _engine().begin() as conn:
        conn.execute(text(
            "UPDATE user_sessions SET revoked_at = NOW() WHERE token_hash = :h AND revoked_at IS NULL"),
            {"h": token_hash})


# ═══════════════════════════════════════════════════════════════════════════════
# PASSWORDS + RATE LIMITING
# ═══════════════════════════════════════════════════════════════════════════════

_DUMMY_HASH = None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _burn_password_check(password):
    """Spend bcrypt time for unknown emails so response timing doesn't reveal accounts."""
    global _DUMMY_HASH
    if _DUMMY_HASH is None:
        _DUMMY_HASH = hash_password(secrets.token_urlsafe(16))
    verify_password(password, _DUMMY_HASH)


def _check_rate_limit(email):
    with _attempts_lock:
        info = _login_attempts.get(email)
        if not info:
            return True, ""
        locked_until = info.get("locked_until")
        if locked_until and _now() < locked_until:
            minutes = int((locked_until - _now()).total_seconds() // 60) + 1
            return False, f"Too many failed attempts. Please try again in {minutes} minute(s)."
        if locked_until:
            del _login_attempts[email]
        return True, ""


def _record_failed_attempt(email):
    with _attempts_lock:
        if len(_login_attempts) > 10000:      # bound memory under scripted abuse
            _login_attempts.clear()
        info = _login_attempts.setdefault(email, {"count": 0, "locked_until": None})
        info["count"] += 1
        if info["count"] >= MAX_LOGIN_ATTEMPTS:
            info["locked_until"] = _now() + timedelta(minutes=LOCKOUT_MINUTES)
            logger.warning("Sign-in temporarily locked after repeated failures")


def _clear_failed_attempts(email):
    with _attempts_lock:
        _login_attempts.pop(email, None)


def _validate_password_strength(password):
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if len(password.encode("utf-8")) > MAX_PASSWORD_LENGTH:
        return False, f"Password must be at most {MAX_PASSWORD_LENGTH} characters."
    if password.lower() in COMMON_PASSWORDS:
        return False, "This password is too common. Please choose a stronger one."
    return True, ""


def _normalise_email(email: str | None) -> str | None:
    email = (email or "").strip().lower()
    if not email or len(email) > 255 or "@" not in email or any(c.isspace() for c in email):
        return None
    return email


# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL + PASSWORD
# ═══════════════════════════════════════════════════════════════════════════════

def register_user(email: str, password: str, display_name: str = "") -> tuple[bool, str]:
    """Create a local account. Existing emails get the same reply (no enumeration)."""
    normalised_email = _normalise_email(email)
    if normalised_email is None:
        return False, "Please enter a valid email address."
    email = normalised_email

    try:
        _ensure_tables()
        with _engine().connect() as conn:
            if conn.execute(text("SELECT 1 FROM oauth_users WHERE email = :email"), {"email": email}).scalar():
                return False, "This email is registered with Google sign-in. Please use Continue with Google."
    except SQLAlchemyError:
        return False, "Account creation is temporarily unavailable. Please try again."

    valid, problem = _validate_password_strength(password or "")
    if not valid:
        return False, problem
    display_name = (display_name or "").strip()[:100] or email.split("@")[0]
    try:
        _db_insert_user(email, display_name, hash_password(password))
    except SQLAlchemyError:
        logger.error("Account creation failed")
        return False, "Account creation is temporarily unavailable. Please try again."
    return True, "If this email can be registered, your account is ready. Sign in to continue."


def authenticate_user(email: str, password: str) -> tuple[bool, str, dict | None]:
    normalised_email = _normalise_email(email)
    if normalised_email is None or not password:
        return False, "Invalid email or password.", None
    email = normalised_email
    allowed, message = _check_rate_limit(email)
    if not allowed:
        return False, message, None
    try:
        user = _db_find_user(email)
    except SQLAlchemyError:
        logger.error("User lookup failed")
        return False, "Sign-in is temporarily unavailable. Please try again.", None
    if not user or not user.get("is_active", True):
        _burn_password_check(password)
        _record_failed_attempt(email)
        return False, "Invalid email or password.", None
    if not verify_password(password, user["password_hash"]):
        _record_failed_attempt(email)
        return False, "Invalid email or password.", None
    _clear_failed_attempts(email)
    try:
        _db_touch_user(user["id"])
    except SQLAlchemyError:
        logger.warning("Could not update last sign-in time")
    return True, "Signed in.", {"id": f"local:{user['id']}", "email": user["email"],
                                "display_name": user["display_name"] or email.split("@")[0]}


def login(email: str, password: str) -> tuple[bool, str]:
    success, message, identity = authenticate_user(email, password)
    if success and identity:
        if not _start_session(identity):
            return False, "Sign-in is temporarily unavailable. Please try again."
    return success, message


# ═══════════════════════════════════════════════════════════════════════════════
# APP SESSIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _queue_cookie_action(action):
    st.session_state.setdefault("_cookie_actions", []).append(action)


def _clear_user_state():
    for key in list(st.session_state):
        if key not in _KEEP_ON_CLEAR:
            del st.session_state[key]


def _bind_identity(identity, token):
    previous = st.session_state.get("auth_user", {}).get("id")
    if previous != identity["id"]:
        _clear_user_state()              # never show one account's data to another
    st.session_state["auth_user"] = dict(identity)
    st.session_state["_auth_token"] = token
    st.session_state["_auth_checked_at"] = time.monotonic()


def _start_session(identity) -> bool:
    token = secrets.token_urlsafe(32)
    try:
        _db_create_session(_hash_token(token), identity, _now() + timedelta(days=SESSION_DAYS))
    except SQLAlchemyError:
        logger.error("Could not create session")
        return False
    _bind_identity(identity, token)
    _queue_cookie_action({"type": "set", "token": token})
    return True


def _lookup(token):
    """Return (identity | None, service_ok)."""
    if not token or len(token) > 128:
        return None, True
    try:
        return _db_lookup_session(_hash_token(token)), True
    except SQLAlchemyError:
        logger.warning("Session validation unavailable")
        return None, False


def _browser_cookie(name=SESSION_COOKIE):
    try:
        value = st.context.cookies.get(name, "")
    except Exception:
        return None
    if not value or len(value) > 128 or any(c.isspace() or c in ";,\0" for c in value):
        return None
    return value


def is_logged_in() -> bool:
    _complete_google_sign_in()
    token = st.session_state.get("_auth_token")
    if token:
        fresh = time.monotonic() - st.session_state.get("_auth_checked_at", 0) < REVALIDATE_SECONDS
        if fresh and st.session_state.get("auth_user"):
            return True
        identity, ok = _lookup(token)
        if identity:
            _bind_identity(identity, token)
            return True
        if not ok:
            st.session_state["login_error"] = "Sign-in is temporarily unavailable. Please try again."
            return False
        _clear_user_state()
        _queue_cookie_action({"type": "clear"})
        return False

    cookie = _browser_cookie()
    if cookie and _hash_token(cookie) != st.session_state.get("_ignored_cookie"):
        identity, ok = _lookup(cookie)
        if identity:
            _bind_identity(identity, cookie)
            return True
        if ok:
            st.session_state["_ignored_cookie"] = _hash_token(cookie)
            _queue_cookie_action({"type": "clear"})
    return False


def get_current_user():
    return st.session_state["auth_user"].copy() if is_logged_in() else None


def require_authenticated():
    user = get_current_user()
    if user is None:
        st.error("Your session ended. Refresh the page to sign in again.")
        st.stop()
    return user


def logout() -> None:
    """Revoke this browser's session everywhere and clear all user data."""
    tokens = {st.session_state.get("_auth_token"), _browser_cookie()} - {None}
    for token in tokens:
        try:
            _db_revoke_session(_hash_token(token))
        except SQLAlchemyError:
            logger.warning("Session revocation unavailable")
    _clear_user_state()
    cookie = _browser_cookie()
    if cookie:
        st.session_state["_ignored_cookie"] = _hash_token(cookie)
    _queue_cookie_action({"type": "clear"})


# ═══════════════════════════════════════════════════════════════════════════════
# GOOGLE (via Neon Auth)
# ═══════════════════════════════════════════════════════════════════════════════

def _neon_headers(origin):
    return {"Origin": origin, "x-neon-auth-middleware": "true", "Accept": "application/json"}


def _neon_cookies(response):
    try:
        return {name: value for name, value in response.cookies.items()
                if name.startswith("__Secure-neon-auth.") and value and len(value) <= 4096}
    except Exception:
        return {}


def _purge_flows():
    cutoff = time.monotonic() - OAUTH_FLOW_SECONDS
    for flow_id in [k for k, v in _oauth_flows.items() if v["created"] < cutoff]:
        del _oauth_flows[flow_id]


def start_google_sign_in() -> bool:
    """Begin Neon's Google flow; the auth bridge then redirects the browser."""
    base, origin = _neon_auth_url(), _app_origin()
    if not google_available() or not base or not origin:
        st.session_state["login_error"] = "Google sign-in is not available right now."
        return False
    flow_id, nonce = secrets.token_urlsafe(24), secrets.token_urlsafe(32)
    callback = origin + "/?" + urlencode({"auth_flow": flow_id})
    response: requests.Response | None = None
    try:
        response = requests.post(base + "/sign-in/social",
                                 json={"provider": "google", "callbackURL": callback, "newUserCallbackURL": callback, "errorCallbackURL": callback},
                                 headers=_neon_headers(origin), timeout=(3, 10),
                                 allow_redirects=False, proxies=_NO_PROXY)
        target = response.json().get("url") if response.status_code == 200 else None
    except (ValueError, AttributeError):
        target = None
    except requests.RequestException as error:
        logger.warning("Google sign-in request failed (%s)", type(error).__name__)
        st.session_state["login_error"] = "Google sign-in is temporarily unreachable. Please try again later."
        return False
    cookies = _neon_cookies(response) if target and response is not None else {}
    parts = urlsplit(target) if isinstance(target, str) else None
    neon = urlsplit(base)
    expected = parts and parts.scheme == "https" and not parts.username and not parts.port and (
        parts.hostname == "accounts.google.com"
        or (parts.hostname == neon.hostname and parts.path == neon.path + "/sign-in/social/init"))
    if not expected or not cookies:
        logger.warning("Google sign-in could not start")
        st.session_state["login_error"] = ("Google sign-in could not start. If this keeps happening, "
                                           "add this site to Neon Auth's trusted domains.")
        return False
    with _oauth_lock:
        _purge_flows()
        if len(_oauth_flows) >= MAX_PENDING_OAUTH_FLOWS:
            st.session_state["login_error"] = "Too many sign-ins in progress. Please try again shortly."
            return False
        _oauth_flows[flow_id] = {"cookies": cookies, "nonce": _hash_token(nonce),
                                 "origin": origin, "created": time.monotonic()}
    st.session_state["_google_redirect"] = target
    _queue_cookie_action({"type": "google", "nonce": nonce, "url": target})
    return True


def pending_google_redirect():
    return st.session_state.get("_google_redirect")


def _complete_google_sign_in():
    """Finish the Google flow when the browser returns with Neon's verifier."""
    try:
        params = st.query_params
    except Exception:
        return

    if st.session_state.get("_auth_token"):
        for key in ("auth_flow", "neon_auth_session_verifier", "error", "error_description"):
            if key in params:
                del params[key]
        return

    flow_id = params.get("auth_flow")
    verifier = params.get("neon_auth_session_verifier")
    provider_error = params.get("error")
    nonce = _browser_cookie(OAUTH_NONCE_COOKIE)

    if not flow_id and not verifier and not provider_error:
        return

    if not flow_id and nonce:
        hashed_nonce = _hash_token(nonce)
        with _oauth_lock:
            for fid, f in _oauth_flows.items():
                if f["nonce"] == hashed_nonce:
                    flow_id = fid
                    break

    if not flow_id:
        for key in ("auth_flow", "neon_auth_session_verifier", "error", "error_description"):
            if key in params:
                del params[key]
        st.session_state["login_error"] = "Google sign-in was cancelled or expired. Please try again."
        return

    for key in ("auth_flow", "neon_auth_session_verifier", "error", "error_description"):
        if key in params:
            del params[key]
    st.session_state.pop("_google_redirect", None)
    _queue_cookie_action({"type": "clear_nonce"})

    with _oauth_lock:
        _purge_flows()
        flow = _oauth_flows.pop(flow_id, None)      # single use

    failure = "Google sign-in was cancelled or expired. Please try again."
    if provider_error or not flow or not verifier or len(verifier) > 2048:
        st.session_state["login_error"] = failure
        return
    if not nonce or not hmac.compare_digest(_hash_token(nonce), flow["nonce"]):
        # The flow was started in a different browser: refuse (login-CSRF guard).
        st.session_state["login_error"] = failure
        return

    base, origin = _neon_auth_url(), flow["origin"]
    if base is None:
        st.session_state["login_error"] = failure
        return
    cookie_header = "; ".join(f"{k}={v}" for k, v in flow["cookies"].items())
    try:
        response = requests.get(base + "/get-session",
                                params={"neon_auth_session_verifier": verifier},
                                headers={**_neon_headers(origin), "Cookie": cookie_header},
                                timeout=(3, 10), allow_redirects=False, proxies=_NO_PROXY)
        data = response.json() if response.status_code == 200 else None
        user = (data or {}).get("user") or {}
        if response.status_code == 200 and not user and _neon_cookies(response):
            session_cookie = "; ".join(f"{k}={v}" for k, v in _neon_cookies(response).items())
            second = requests.get(base + "/get-session", params={"disableCookieCache": "true"},
                                  headers={**_neon_headers(origin), "Cookie": session_cookie},
                                  timeout=(3, 10), allow_redirects=False, proxies=_NO_PROXY)
            user = ((second.json() if second.status_code == 200 else None) or {}).get("user") or {}
    except (requests.RequestException, ValueError, AttributeError):
        user, response = {}, None
    if not isinstance(user, dict):
        user = {}
    subject, email = user.get("id"), _normalise_email(user.get("email"))
    if (not isinstance(subject, str) or not subject or len(subject) > 255 or not email
            or user.get("emailVerified") is not True):
        logger.warning("Google sign-in verification failed")
        st.session_state["login_error"] = "Google sign-in could not be verified. Please try again."
        return

    # Only the app session is kept: end Neon's session straight away (best effort).
    session_cookies = _neon_cookies(response)
    if session_cookies:
        try:
            requests.post(base + "/sign-out", json={},
                          headers={**_neon_headers(origin),
                                   "Cookie": "; ".join(f"{k}={v}" for k, v in session_cookies.items())},
                          timeout=(3, 5), allow_redirects=False, proxies=_NO_PROXY)
        except requests.RequestException:
            pass

    try:
        _ensure_tables()
        with _engine().connect() as conn:
            has_oauth = conn.execute(text("SELECT 1 FROM oauth_users WHERE provider = 'google' AND provider_user_id = :subject"), {"subject": subject}).scalar()
            if not has_oauth:
                if conn.execute(text("SELECT 1 FROM users WHERE email = :email"), {"email": email}).scalar():
                    st.session_state["login_error"] = "This email already has a password account. Please sign in with your email and password."
                    return
    except SQLAlchemyError:
        st.session_state["login_error"] = "Sign-in is temporarily unavailable. Please try again."
        return

    name = str(user.get("name") or "").strip()[:100] or email.split("@")[0]
    try:
        row_id = _db_upsert_oauth_user("google", subject, email, name)
    except SQLAlchemyError:
        logger.error("Could not save Google account")
        st.session_state["login_error"] = "Sign-in is temporarily unavailable. Please try again."
        return
    if not _start_session({"id": f"google:{row_id}", "email": email, "display_name": name}):
        st.session_state["login_error"] = "Sign-in is temporarily unavailable. Please try again."


# ═══════════════════════════════════════════════════════════════════════════════
# BROWSER BRIDGE (cookie writes + Google redirect)
# ═══════════════════════════════════════════════════════════════════════════════

def render_auth_bridge():
    """Run queued cookie writes / redirects in the browser. Call once per page."""
    actions = st.session_state.pop("_cookie_actions", [])
    if not actions:
        return
    js = json.dumps({"actions": actions, "session": SESSION_COOKIE, "nonce": OAUTH_NONCE_COOKIE,
                     "maxAge": SESSION_DAYS * 86400, "flowAge": OAUTH_FLOW_SECONDS,
                     "id": secrets.token_hex(4)}).replace("</", "<\\/")
    st.markdown("""<style>
      div[data-testid="stElementContainer"]:has(iframe[height="0"]) { display: none !important; }
    </style>""", unsafe_allow_html=True)
    components.html("""<script>
(function () {
  const cfg = %s;
  const P = window.parent, doc = P.document;
  const secure = P.location.protocol === 'https:' ? '; Secure' : '';
  const put = (name, value, age) =>
    { doc.cookie = name + '=' + value + '; Path=/; Max-Age=' + age + '; SameSite=Lax' + secure; };
  cfg.actions.forEach(function (a) {
    if (a.type === 'set') put(cfg.session, a.token, cfg.maxAge);
    else if (a.type === 'clear') put(cfg.session, '', 0);
    else if (a.type === 'clear_nonce') put(cfg.nonce, '', 0);
    else if (a.type === 'google') {
      put(cfg.nonce, a.nonce, cfg.flowAge);
      const link = doc.createElement('a');
      link.href = a.url; link.target = '_self'; link.rel = 'noopener';
      doc.body.appendChild(link); link.click();
    }
  });
})();
</script>""" % js, height=0)
