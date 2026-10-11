"""Streamlit-native auth behaviour with an in-memory fake database (no live services)."""
import time
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests

import auth

NEON = "https://ep-unit-test.neonauth.c-2.ap-southeast-1.aws.neon.tech/neondb/auth"


class FakeDB:
    def __init__(self):
        self.users, self.oauth, self.sessions = {}, {}, {}

    def find_user(self, email):
        return self.users.get(email)

    def insert_user(self, email, name, password_hash):
        if email in self.users:
            return False
        self.users[email] = {"id": len(self.users) + 1, "email": email, "display_name": name,
                             "password_hash": password_hash, "is_active": True}
        return True

    def upsert_oauth(self, provider, subject, email, name):
        return self.oauth.setdefault((provider, subject), len(self.oauth) + 1)

    def create_session(self, token_hash, identity, expires_at):
        self.sessions[token_hash] = {"identity": dict(identity), "revoked": False}

    def lookup_session(self, token_hash):
        row = self.sessions.get(token_hash)
        return dict(row["identity"]) if row and not row["revoked"] else None

    def revoke_session(self, token_hash):
        if token_hash in self.sessions:
            self.sessions[token_hash]["revoked"] = True


@pytest.fixture(autouse=True)
def env(monkeypatch):
    db = FakeDB()
    state, cookies, params = {}, {}, {}
    fake_st = SimpleNamespace(session_state=state, query_params=params, secrets={},
                              context=SimpleNamespace(cookies=cookies, url="http://localhost:8509/"),
                              error=Mock(), stop=Mock(side_effect=RuntimeError("stopped")))
    monkeypatch.setattr(auth, "st", fake_st)
    monkeypatch.setattr(auth, "BCRYPT_ROUNDS", 4)
    monkeypatch.setattr(auth, "_db_find_user", db.find_user)
    monkeypatch.setattr(auth, "_db_insert_user", db.insert_user)
    monkeypatch.setattr(auth, "_db_touch_user", lambda user_id: None)
    monkeypatch.setattr(auth, "_db_upsert_oauth_user", db.upsert_oauth)
    monkeypatch.setattr(auth, "_db_create_session", db.create_session)
    monkeypatch.setattr(auth, "_db_lookup_session", db.lookup_session)
    monkeypatch.setattr(auth, "_db_revoke_session", db.revoke_session)
    monkeypatch.setattr(auth.requests, "post", Mock(side_effect=AssertionError("no network")))
    monkeypatch.setattr(auth.requests, "get", Mock(side_effect=AssertionError("no network")))
    monkeypatch.delenv("APP_ORIGIN", raising=False)
    monkeypatch.setenv("NEON_AUTH_URL", NEON)
    monkeypatch.delenv("AUTH_GOOGLE_ENABLED", raising=False)
    auth._login_attempts.clear()
    auth._oauth_flows.clear()
    return SimpleNamespace(db=db, state=state, cookies=cookies, params=params)


def cookie_token(env):
    sets = [a for a in env.state.get("_cookie_actions", []) if a["type"] == "set"]
    return sets[-1]["token"] if sets else None


def new_browser(env, token=None):
    """Simulate a page refresh: fresh session_state, cookie snapshot from the browser."""
    env.state.clear()
    env.cookies.clear()
    if token:
        env.cookies[auth.SESSION_COOKIE] = token


def test_signup_then_login_creates_hashed_session(env):
    ok, _ = auth.register_user("A@Example.com ", "correct horse battery", "Alice")
    assert ok and env.db.users["a@example.com"]["password_hash"].startswith("$2")
    assert auth.login("a@example.com", "correct horse battery") == (True, "Signed in.")
    token = cookie_token(env)
    assert token and auth._hash_token(token) in env.db.sessions
    assert token not in str(env.db.sessions)          # raw token never stored
    assert auth.is_logged_in()
    assert auth.get_current_user()["id"] == "local:1"


def test_duplicate_signup_reply_matches_new_signup(env):
    first = auth.register_user("a@example.com", "correct horse battery")
    second = auth.register_user("a@example.com", "another long password")
    assert first == second


@pytest.mark.parametrize("password", ["short", "password123", "x" * 73])
def test_weak_passwords_rejected(env, password):
    assert auth.register_user("a@example.com", password)[0] is False


def test_wrong_password_and_unknown_user_look_the_same(env):
    auth.register_user("a@example.com", "correct horse battery")
    assert auth.login("a@example.com", "wrong password!!") == auth.login("nobody@example.com", "x" * 12)
    assert not auth.is_logged_in()


def test_lockout_after_repeated_failures(env):
    auth.register_user("a@example.com", "correct horse battery")
    for _ in range(auth.MAX_LOGIN_ATTEMPTS):
        auth.login("a@example.com", "wrong password!!")
    ok, message = auth.login("a@example.com", "correct horse battery")
    assert not ok and "Too many" in message


def test_session_survives_refresh_via_cookie(env):
    auth.register_user("a@example.com", "correct horse battery")
    auth.login("a@example.com", "correct horse battery")
    token = cookie_token(env)
    new_browser(env, token)
    assert auth.is_logged_in()
    assert auth.get_current_user()["email"] == "a@example.com"


def test_forged_flag_or_unknown_cookie_never_grants_access(env):
    env.state.update(authenticated=True, auth_user={"id": "local:1", "email": "x@example.com"})
    assert not auth.is_logged_in()
    new_browser(env, "made-up-token")
    assert not auth.is_logged_in()
    assert {"type": "clear"} in env.state["_cookie_actions"]


def test_logout_revokes_and_other_tabs_lose_access(env):
    auth.register_user("a@example.com", "correct horse battery")
    auth.login("a@example.com", "correct horse battery")
    token = cookie_token(env)
    env.cookies[auth.SESSION_COOKIE] = token
    auth.logout()
    assert env.db.sessions[auth._hash_token(token)]["revoked"]
    assert not auth.is_logged_in()                     # stale cookie snapshot is ignored
    new_browser(env, token)                            # another tab / refresh
    assert not auth.is_logged_in()


def test_revocation_detected_after_revalidation_window(env, monkeypatch):
    auth.register_user("a@example.com", "correct horse battery")
    auth.login("a@example.com", "correct horse battery")
    env.state["channel_data"] = {"private": True}
    env.db.revoke_session(auth._hash_token(cookie_token(env)))
    env.state["_auth_checked_at"] = time.monotonic() - auth.REVALIDATE_SECONDS - 1
    assert not auth.is_logged_in()
    assert "channel_data" not in env.state


def test_database_outage_fails_closed(env, monkeypatch):
    auth.register_user("a@example.com", "correct horse battery")
    auth.login("a@example.com", "correct horse battery")
    monkeypatch.setattr(auth, "_db_lookup_session",
                        Mock(side_effect=auth.SQLAlchemyError("DO-NOT-LOG")))
    env.state["_auth_checked_at"] = 0
    assert not auth.is_logged_in()


def test_require_authenticated_stops_without_session(env):
    with pytest.raises(RuntimeError, match="stopped"):
        auth.require_authenticated()


# ── Google via Neon Auth ────────────────────────────────────────────────────

def neon_response(status=200, json=None, cookies=None):
    response = Mock(status_code=status)
    response.json.return_value = json or {}
    response.cookies = cookies or {}
    return response


def start_flow(env, monkeypatch, url=NEON + "/sign-in/social/init?x=1"):
    post = Mock(return_value=neon_response(json={"url": url, "redirect": True},
                                           cookies={"__Secure-neon-auth.session_challenge": "chal"}))
    monkeypatch.setattr(auth.requests, "post", post)
    started = auth.start_google_sign_in()
    return started, post


def return_from_google(env, flow_id, nonce, verifier="verifier-1"):
    env.state.clear()
    env.cookies.clear()
    env.cookies[auth.OAUTH_NONCE_COOKIE] = nonce
    env.params.update(auth_flow=flow_id, neon_auth_session_verifier=verifier)


def test_google_flow_signs_in_and_cleans_up(env, monkeypatch):
    started, post = start_flow(env, monkeypatch)
    assert started
    callback = post.call_args.kwargs["json"]["callbackURL"]
    assert callback.startswith("http://localhost:8509/?auth_flow=")
    action = env.state["_cookie_actions"][-1]
    flow_id = callback.split("auth_flow=")[1]

    return_from_google(env, flow_id, action["nonce"])
    user = {"id": "neon-user-1", "email": "g@example.com", "name": "Gina", "emailVerified": True}
    get = Mock(return_value=neon_response(json={"user": user},
                                          cookies={"__Secure-neon-auth.session_token": "neon-tok"}))
    monkeypatch.setattr(auth.requests, "get", get)
    monkeypatch.setattr(auth.requests, "post", Mock(return_value=neon_response()))
    assert auth.is_logged_in()
    assert auth.get_current_user() == {"id": "google:1", "email": "g@example.com", "display_name": "Gina"}
    assert "chal" in get.call_args.kwargs["headers"]["Cookie"]
    assert auth.requests.post.call_args.args[0].endswith("/sign-out")   # Neon session ended
    assert not env.params and flow_id not in auth._oauth_flows


def test_google_return_from_another_browser_is_rejected(env, monkeypatch):
    _, post = start_flow(env, monkeypatch)
    flow_id = post.call_args.kwargs["json"]["callbackURL"].split("auth_flow=")[1]
    return_from_google(env, flow_id, "attacker-nonce")
    assert not auth.is_logged_in()
    auth.requests.get.assert_not_called()


def test_google_flow_is_single_use(env, monkeypatch):
    _, post = start_flow(env, monkeypatch)
    flow_id = post.call_args.kwargs["json"]["callbackURL"].split("auth_flow=")[1]
    nonce = env.state["_cookie_actions"][-1]["nonce"]
    auth._oauth_flows.pop(flow_id)
    return_from_google(env, flow_id, nonce)
    assert not auth.is_logged_in()


def test_unverified_google_email_rejected(env, monkeypatch):
    _, post = start_flow(env, monkeypatch)
    flow_id = post.call_args.kwargs["json"]["callbackURL"].split("auth_flow=")[1]
    return_from_google(env, flow_id, env.state["_cookie_actions"][-1]["nonce"])
    user = {"id": "u", "email": "g@example.com", "emailVerified": False}
    monkeypatch.setattr(auth.requests, "get", Mock(return_value=neon_response(json={"user": user})))
    assert not auth.is_logged_in()


@pytest.mark.parametrize("url", ["https://evil.example/sign-in/social/init",
                                 "http://accounts.google.com/o/oauth2", None])
def test_unexpected_redirect_target_refused(env, monkeypatch, url):
    started, _ = start_flow(env, monkeypatch, url=url)
    assert not started and not auth._oauth_flows


def test_google_hidden_without_valid_neon_url(env, monkeypatch):
    monkeypatch.setenv("NEON_AUTH_URL", "https://attacker.example/auth")
    assert not auth.google_available()
    monkeypatch.setenv("NEON_AUTH_URL", NEON)
    monkeypatch.setenv("AUTH_GOOGLE_ENABLED", "false")
    assert not auth.google_available()


@pytest.mark.parametrize("error_type", [requests.ConnectionError, requests.Timeout])
def test_network_error_does_not_leak(env, monkeypatch, caplog, error_type):
    monkeypatch.setattr(auth.requests, "post",
                        Mock(side_effect=error_type("DO-NOT-LOG-THIS")))
    assert not auth.start_google_sign_in()
    assert env.state["login_error"] == "Google sign-in is temporarily unreachable. Please try again later."
    assert not auth._oauth_flows
    assert not env.state.get("_cookie_actions")
    assert "DO-NOT-LOG-THIS" not in caplog.text
    assert "DO-NOT-LOG-THIS" not in env.state["login_error"]


def test_storage_rechecks_authorization_after_service_creation(mock_db_manager, processed_channel):
    from data_storage.storage_service import DataStorageService
    guard = Mock(side_effect=RuntimeError("revoked"))
    service = DataStorageService(db_manager=mock_db_manager, authorization=guard)
    with pytest.raises(RuntimeError, match="revoked"):
        service.save_channel_data(processed_channel)
    mock_db_manager.get_session.return_value.execute.assert_not_called()
