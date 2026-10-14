"""Regression coverage for stable login-page element positions across reruns."""
from html import escape
from unittest.mock import Mock

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
