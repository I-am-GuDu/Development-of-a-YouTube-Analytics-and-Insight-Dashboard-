"""Regression coverage for stable login-page element positions across reruns."""
import hashlib
import re
from html import escape
from unittest.mock import Mock, patch

import pytest
from streamlit.testing.v1 import AppTest
from streamlit.testing.v1.element_tree import Block


_APP_SOURCE = """\
from login_page import render_login_page

render_login_page()
"""


def _child_types(block):
    return tuple(child.type for child in block.children.values())


def _right_column_types(at):
    assert len(at.columns) == 2
    return _child_types(at.columns[1])


def _error_banners(at):
    return [
        markdown.value
        for markdown in at.markdown
        if markdown.value.startswith('<div class="login-note login-err">')
    ]


def _fixed_height_slots(at):
    slots = []
    for child in at.columns[1].children.values():
        if isinstance(child, Block) and child.proto.height_config.pixel_height:
            slots.append((
                child.proto.height_config.pixel_height,
                child.proto.allow_empty,
                child.proto.flex_container.border,
            ))
    return slots


@pytest.fixture(autouse=True)
def _ui_v2_off_by_default(monkeypatch):
    """LOGIN_UI_V2 is read once per process; start every test with it unset."""
    import login_page

    monkeypatch.delenv("LOGIN_UI_V2", raising=False)
    login_page._ui_v2_enabled.cache_clear()
    yield
    login_page._ui_v2_enabled.cache_clear()


@pytest.fixture
def app_test(monkeypatch):
    monkeypatch.setenv("AUTH_GOOGLE_ENABLED", "false")

    import auth

    no_network = Mock(side_effect=AssertionError("layout tests must not use the network"))
    monkeypatch.setattr(auth.requests, "get", no_network)
    monkeypatch.setattr(auth.requests, "post", no_network)
    return AppTest.from_string(_APP_SOURCE)


def test_main_block_structure_is_stable_across_reruns(app_test):
    at = app_test.run()
    first_run = _child_types(at.main)

    at.run()

    assert _child_types(at.main) == first_run
    assert not at.exception


@pytest.mark.parametrize(
    ("state_key", "state_value"),
    [
        ("login_error", "A temporary problem."),
        ("login_success", "Account created."),
        ("_google_redirect", "https://accounts.google.com/o/oauth2/auth?state=test"),
    ],
)
def test_conditional_content_keeps_right_column_structure(app_test, state_key, state_value):
    at = app_test.run()
    clean_run = _right_column_types(at)

    at.session_state[state_key] = state_value
    at.run()

    assert _right_column_types(at) == clean_run
    assert not at.exception


def test_error_banner_is_escaped_and_cleared_after_display(app_test):
    message = '<b>Try "again" & later.</b>'
    at = app_test.run()
    at.session_state["login_error"] = message

    at.run()

    assert _error_banners(at) == [
        f'<div class="login-note login-err">{escape(message)}</div>'
    ]
    assert at.session_state["login_error"] == ""
    assert not at.exception

    at.run()

    assert _error_banners(at) == []
    assert not at.exception


@pytest.mark.parametrize(
    ("state_key", "state_value"),
    [
        (None, None),
        ("login_error", "A temporary problem."),
        ("_google_redirect", "https://accounts.google.com/o/oauth2/auth?state=test"),
        ("login_mode", "signup"),
    ],
)
def test_message_slots_have_no_fixed_height_in_any_state(app_test, state_key, state_value):
    at = app_test.run()
    if state_key:
        at.session_state[state_key] = state_value
    at.run()

    # Slots have no fixed pixel height
    assert _fixed_height_slots(at) == []
    assert not at.exception


def test_empty_containers_and_scrollbars_css_rules(app_test):
    at = app_test.run()
    styles = "".join(m.value for m in at.markdown if "<style>" in m.value)

    # Empty containers and wrappers are display:none (zero height & zero flex gap)
    assert '[data-testid="stLayoutWrapper"]:has(> .st-key-sr_msg_slot:empty)' in styles
    assert '[data-testid="stLayoutWrapper"]:has(> .st-key-sr_hint_slot:empty)' in styles
    assert ".st-key-sr_msg_slot:empty" in styles
    assert ".st-key-sr_hint_slot:empty" in styles

    # Scrollbars are hidden on the form panel
    assert "scrollbar-width: none" in styles
    assert "::-webkit-scrollbar" in styles

    # Fixed slot height CSS overrides removed
    assert "flex: 0 0 56px" not in styles
    assert "flex: 0 0 20px" not in styles
    assert "flex: 0 0 76px" not in styles
    assert "flex: 0 0 38px" not in styles
    assert not at.exception


def test_hint_and_error_display_unclipped_natural_content(app_test):
    long_msg = "A" * 150
    at = app_test.run()
    at.session_state["login_error"] = long_msg
    at.session_state["_google_redirect"] = "https://accounts.google.com/test?param=1"
    at.run()

    # Both banner and hint rendered with full content
    banners = _error_banners(at)
    assert len(banners) == 1
    assert long_msg in banners[0]

    hints = [m.value for m in at.markdown if '<p class="sr-hint">' in m.value]
    assert len(hints) >= 1
    assert "continue to Google" in hints[0]
    assert "https://accounts.google.com/test?param=1" in hints[0]
    assert not at.exception


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN_UI_V2 switch
# ─────────────────────────────────────────────────────────────────────────────

# SHA-256 of what HEAD 1295020 emitted with the switch off. If you change the
# off-state look on purpose, regenerate these; any other change is a regression.
_HEAD_SCENE_SHA = "933c1584e078a18d01a5088e2b5624c3956801a823b1a440979c6eccf301f811"
_HEAD_STYLE_SHA = {
    "dark": "42293708ed78f6d62c2bab40dcf9e2c6c5911d928a6bd883691c40b0fe77d3ec",
    "light": "d9936437d93b508d3ee5b5c4231b6873519dff90944f1bcc232f9dd418fbcec0",
}
_V2_SCOPE = ".stApp:has(.sr-scene.sr-v2)"


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _style_string(mode):
    import login_page

    emitted = []
    with patch.object(login_page.st, "markdown", side_effect=lambda body, **kw: emitted.append(body)):
        login_page._inject_login_styles(mode)
    return "".join(emitted)


def _enable_v2(monkeypatch):
    import login_page

    monkeypatch.setenv("LOGIN_UI_V2", "on")
    login_page._ui_v2_enabled.cache_clear()


def _disable_v2(monkeypatch):
    import login_page

    monkeypatch.delenv("LOGIN_UI_V2", raising=False)
    login_page._ui_v2_enabled.cache_clear()


def test_switch_off_output_equals_head():
    import login_page

    assert _sha(login_page._scene_html()) == _HEAD_SCENE_SHA
    assert _sha(_style_string("dark")) == _HEAD_STYLE_SHA["dark"]
    assert _sha(_style_string("light")) == _HEAD_STYLE_SHA["light"]


@pytest.mark.parametrize("value", ["1", "true", "YES", " on "])
def test_switch_accepts_truthy_values(monkeypatch, value):
    import login_page

    monkeypatch.setenv("LOGIN_UI_V2", value)
    login_page._ui_v2_enabled.cache_clear()
    assert login_page._ui_v2_enabled() is True


@pytest.mark.parametrize("value", ["", "0", "false", "off", "no", "v2"])
def test_switch_rejects_other_values(monkeypatch, value):
    import login_page

    monkeypatch.setenv("LOGIN_UI_V2", value)
    login_page._ui_v2_enabled.cache_clear()
    assert login_page._ui_v2_enabled() is False


def test_switch_on_adds_class_and_v2_css_in_both_themes(monkeypatch):
    import login_page

    _enable_v2(monkeypatch)
    scene = login_page._scene_html()
    assert scene.startswith('<div class="sr-scene sr-v2">')
    # Constant per process: no session or theme input.
    assert login_page._scene_html() == scene

    _disable_v2(monkeypatch)
    off_scene = login_page._scene_html()
    _enable_v2(monkeypatch)

    # Every existing id (and the JS hooks) survives unchanged; new markup adds no ids.
    assert re.findall(r'\bid="([^"]+)"', scene) == re.findall(r'\bid="([^"]+)"', off_scene)
    for hook in ('class="sr-chartwrap"', 'class="sr-chart"', 'class="sr-num"', 'class="sr-captions"'):
        assert scene.count(hook) == off_scene.count(hook)
    # The chart card replaces .sr-chartwrap in the same child position (4th), and
    # its extra pieces are `hidden` so they take no space without the v2 CSS.
    assert 'dashboard.</p><div class="sr2-card"><div class="sr2-cardhead" hidden>' in scene
    assert '</div></div></div><div class="sr-kpis">' in scene
    assert scene.count(' hidden') == 3
    assert "Last 30 days" in scene and "Audience retention" in scene
    # Same tip wording; only a <b> wrapper is added.
    assert re.sub(r"<b[^>]*>|</b>", "", scene.split('<div class="sr-captions">')[1]) \
        == off_scene.split('<div class="sr-captions">')[1]

    # Both themes get the v2 block: the same rules, only the values differ. The
    # scene class does not depend on the theme, so the hero never remounts.
    dark, light = _style_string("dark"), _style_string("light")
    for css, mode in ((dark, "dark"), (light, "light")):
        assert _V2_SCOPE in css
        assert "@S" not in css
        assert f"LOGIN_UI_V2 · {mode} theme values" in css
        assert login_page._V2_RULES in css
    assert dark != light


def test_v2_theme_values_cover_every_variable():
    import login_page

    dark, light = login_page._V2_THEME["dark"], login_page._V2_THEME["light"]
    assert dark.keys() == light.keys()
    used = set(re.findall(r"var\(--sr2-([\w-]+)\)", login_page._V2_RULES))
    set_in_rules = set(re.findall(r"--sr2-([\w-]+)\s*:", login_page._V2_RULES))
    assert used <= set(dark) | set_in_rules, used - set(dark) - set_in_rules


@pytest.mark.parametrize("mode", ["dark", "light"])
def test_v2_css_rules_are_all_scoped(mode):
    import login_page

    css = re.sub(r"/\*.*?\*/", "", login_page._v2_css(mode), flags=re.S)
    # Keyframe steps (from/to/50%) are not selectors; names must be sr2- prefixed.
    keyframes = re.findall(r"@keyframes\s+([\w-]+)\s*\{(?:[^{}]*\{[^{}]*\})*\s*\}", css)
    assert all(name.startswith("sr2-") for name in keyframes)
    css = re.sub(r"@keyframes\s+[\w-]+\s*\{(?:[^{}]*\{[^{}]*\})*\s*\}", "", css)
    assert "@keyframes" not in css
    selectors = [m.group(1) for m in re.finditer(r"([^{}]+)\{[^{}]*\}", css)]
    assert selectors
    for group in selectors:
        for selector in group.split(","):
            assert selector.strip().startswith(_V2_SCOPE), selector.strip()
    # Nothing external: no remote URLs other than the SVG namespace in data URIs.
    assert "@import" not in css
    assert not re.search(r"url\(\s*(?!['\"]?data:)", css)
    assert "<script" not in css.lower()


def test_switch_on_keeps_element_structure_stable(monkeypatch, app_test):
    _enable_v2(monkeypatch)
    at = app_test.run()
    first_run = _child_types(at.main)
    right_clean = _right_column_types(at)

    at.run()
    assert _child_types(at.main) == first_run

    at.session_state["login_error"] = "A temporary problem."
    at.run()
    assert _right_column_types(at) == right_clean
    assert not at.exception
