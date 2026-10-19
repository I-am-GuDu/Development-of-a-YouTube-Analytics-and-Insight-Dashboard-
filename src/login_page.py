"""
Login / signup page — "Signal Room" split-showcase.

A two-column glass panel: the LEFT column is an always-dark "product
screenshot" — a live YouTube-analytics scene with a self-drawing retention
curve, a scrubbable playhead, count-up KPIs and rotating insight captions.
The RIGHT column is the theme-aware sign-in / sign-up form.

Design constraints honoured from the codebase:
  * One big injected <style> f-string (literal CSS braces are doubled `{{ }}`).
  * backdrop-filter lives on `.block-container::before`, never on
    `.block-container` itself — otherwise it becomes the containing block for
    the fixed theme toggle and traps it.
  * Public entry point stays `render_login_page()`; theme toggle still called.
  * Sign-in / sign-up run in Streamlit itself (see auth.py): email + password
    against the app's users table, or "Continue with Google" via Neon Auth.
"""
import os
from functools import lru_cache
from html import escape
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

from auth import (
    google_available,
    login,
    pending_google_redirect,
    register_user,
    start_google_sign_in,
)
from dashboard import theme as theme_tokens

# ─────────────────────────────────────────────────────────────────────────────
# LOGIN_UI_V2 switch (default off)
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _ui_v2_enabled():
    """True when LOGIN_UI_V2 is 1/true/yes/on. Read once per process (the first
    render, after main.py has loaded .env), so every rerun and every session
    sees the same value and the element tree never changes between runs."""
    return os.getenv('LOGIN_UI_V2', '').strip().lower() in ('1', 'true', 'yes', 'on')


# v2 look, dark theme only (phases A + B). Plain string (real CSS braces); every
# rule starts with @S, which becomes `.stApp:has(.sr-scene.sr-v2)`, so nothing
# can reach the dashboard or the off state. No external URLs: icons are inline
# SVG data URIs. The only motion (phase C cube float) is under
# prefers-reduced-motion: no-preference.
_V2_DARK_CSS = """

        /* ═══════════════ LOGIN_UI_V2 · dark only · phases A + B ═══════════════ */

        /* A · page: purple glow + dot texture behind the card; shared v2 sizes */
        @S {
            --sr2-h: clamp(38px, 6.2vh, 56px);
            --sr2-gap: clamp(6px, 1.85vh, 16px);
            --sr2-tp: clamp(0px, calc(3vh - 12px), 16px);
            --sr2-ring: #DDD6FE;
            background:
                radial-gradient(54% 48% at 14% 14%, rgba(124,58,237,0.34), transparent 72%),
                radial-gradient(50% 46% at 90% 88%, rgba(91,108,255,0.24), transparent 72%),
                radial-gradient(70% 60% at 50% 50%, rgba(76,29,149,0.20), transparent 78%),
                #0E0A16 !important;
        }
        @S::before {
            background-image: radial-gradient(circle, rgba(196,181,253,0.30) 1px, transparent 1.4px);
            background-size: 22px 22px;
            -webkit-mask: radial-gradient(95% 95% at 50% 50%, #000 35%, rgba(0,0,0,0.45) 100%);
                    mask: radial-gradient(95% 95% at 50% 50%, #000 35%, rgba(0,0,0,0.45) 100%);
        }
        /* A · card: lighter glass, gradient border, inset violet glow (an outer
           glow would be clipped by the 8px viewport margin) */
        @S .block-container::before {
            border: 1px solid transparent;
            background:
                linear-gradient(180deg, #221A38 0%, #1C1531 100%) padding-box,
                linear-gradient(135deg, rgba(196,181,253,0.85) 0%, rgba(124,58,237,0.55) 38%,
                                        rgba(91,108,255,0.45) 68%, rgba(167,139,250,0.80) 100%) border-box;
            background-origin: border-box;
            box-shadow:
                inset 0 0 46px rgba(124,58,237,0.26),
                inset 0 0 0 1px rgba(196,181,253,0.10),
                0 0 12px rgba(124,58,237,0.38),
                0 40px 110px rgba(0,0,0,0.6);
        }

        /* B · signup uses a slightly smaller control height */
        @S [data-testid="stColumn"]:has(.st-key-switch_to_login) {
            --sr2-h: clamp(38px, calc(6.2vh - 8px), 52px);
        }
        /* B · vh-based rhythm of the form column and the heading */
        @S [data-testid="stColumn"]:nth-of-type(2) > [data-testid="stVerticalBlock"] { gap: var(--sr2-gap) !important; }
        @S .sr-formtitle { padding-top: var(--sr2-tp) !important; padding-bottom: var(--sr2-tp) !important; }

        /* B · inputs: the chrome moves to the field root so the reveal button sits inside it */
        @S [data-testid="stTextInputRootElement"] {
            height: var(--sr2-h) !important; min-height: var(--sr2-h) !important;
            box-sizing: border-box !important;
            background: rgba(11,8,20,0.55) !important;
            border: 1px solid rgba(167,139,250,0.34) !important;
            border-radius: 14px !important;
            overflow: hidden;
        }
        @S [data-testid="stTextInputRootElement"]:focus-within {
            border-color: var(--sr2-ring) !important;
            outline: 2px solid var(--sr2-ring); outline-offset: 2px;
        }
        @S [data-baseweb="base-input"] {
            position: relative; height: 100% !important; min-height: 0 !important;
            background: transparent !important;
        }
        @S [data-baseweb="base-input"] input,
        @S [data-baseweb="base-input"] input:focus {
            height: 100% !important; box-sizing: border-box !important;
            padding-top: 0 !important; padding-bottom: 0 !important;
            background: transparent !important; border: none !important;
            border-radius: 0 !important; box-shadow: none !important; outline: none !important;
        }
        @S [data-baseweb="base-input"] input::placeholder { color: #9D95B2 !important; opacity: 1; }
        @S [data-testid="stWidgetLabel"] p, @S [data-testid="stWidgetLabel"] label { color: #B4ADC6 !important; }
        @S [data-testid="stTextInputRootElement"] button { background: transparent !important; color: #B7AFCB !important; border: none !important; }
        @S [data-testid="stTextInputRootElement"] button:focus-visible { outline: 2px solid var(--sr2-ring) !important; outline-offset: -3px !important; }

        /* B · envelope (email) and lock (password, survives the reveal toggle:
           matched on autocomplete, not on type) */
        @S [data-baseweb="base-input"]:has(input[autocomplete="email"])::before,
        @S [data-baseweb="base-input"]:has(input[autocomplete$="password"])::before {
            content: ""; position: absolute; left: 16px; top: 50%;
            width: 18px; height: 18px; transform: translateY(-50%);
            background: #B7AFCB; pointer-events: none; z-index: 2;
        }
        @S [data-baseweb="base-input"]:has(input[autocomplete="email"])::before {
            -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='5' width='18' height='14' rx='2'/%3E%3Cpath d='M3 7l9 6 9-6'/%3E%3C/svg%3E") center / contain no-repeat;
                    mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='5' width='18' height='14' rx='2'/%3E%3Cpath d='M3 7l9 6 9-6'/%3E%3C/svg%3E") center / contain no-repeat;
        }
        @S [data-baseweb="base-input"]:has(input[autocomplete$="password"])::before {
            -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='4' y='11' width='16' height='10' rx='2'/%3E%3Cpath d='M8 11V7a4 4 0 0 1 8 0v4'/%3E%3C/svg%3E") center / contain no-repeat;
                    mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='4' y='11' width='16' height='10' rx='2'/%3E%3Cpath d='M8 11V7a4 4 0 0 1 8 0v4'/%3E%3C/svg%3E") center / contain no-repeat;
        }
        @S [data-baseweb="base-input"]:has(input[autocomplete="email"]) input,
        @S [data-baseweb="base-input"]:has(input[autocomplete$="password"]) input { padding-left: 46px !important; }

        /* B · buttons share the control height */
        @S .st-key-google_btn button,
        @S [data-testid="stFormSubmitButton"] button {
            height: var(--sr2-h) !important; min-height: var(--sr2-h) !important;
            padding-top: 0 !important; padding-bottom: 0 !important;
            border-radius: 14px !important;
        }
        /* Google: taller, larger G */
        @S .st-key-google_btn button {
            background: rgba(255,255,255,0.045) !important;
            border: 1px solid rgba(167,139,250,0.34) !important;
            gap: 12px !important;
        }
        @S .st-key-google_btn button::before { width: 22px; height: 22px; }

        /* Sign in: full width (its element container shrink-wraps by default),
           gradient, arrow on the label's <p> (the button's ::before is the beam) */
        @S [data-testid="stForm"] [data-testid="stElementContainer"]:has([data-testid="stFormSubmitButton"]),
        @S [data-testid="stForm"] [data-testid="stElementContainer"]:has([data-testid="stFormSubmitButton"]) > div { width: 100% !important; }
        @S [data-testid="stFormSubmitButton"] button {
            background: linear-gradient(100deg, #7C3AED 0%, #6D28D9 55%, #5B3FD6 100%) !important;
        }
        @S [data-testid="stFormSubmitButton"] button p::after,
        @S .st-key-switch_to_signup button p::after,
        @S .st-key-switch_to_login button p::after {
            content: ""; display: inline-block; width: 16px; height: 16px;
            margin-left: 8px; vertical-align: -3px; background: currentColor;
            -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12h14M13 6l6 6-6 6'/%3E%3C/svg%3E") center / contain no-repeat;
                    mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12h14M13 6l6 6-6 6'/%3E%3C/svg%3E") center / contain no-repeat;
        }

        /* Sign up / Sign in link: violet, centred, with an arrow */
        @S .st-key-switch_to_signup, @S .st-key-switch_to_login { width: 100% !important; }
        @S .st-key-switch_to_signup button, @S .st-key-switch_to_login button {
            color: #B9A6FC !important; font-weight: 600 !important;
        }
        @S .st-key-switch_to_signup button:hover, @S .st-key-switch_to_login button:hover { color: #DDD6FE !important; }

        /* Divider text ("OR", "NEW HERE"): letter-spaced and readable */
        @S .login-divider span { letter-spacing: 0.22em !important; color: #A39CB5 !important; }
        @S .sr-legal { color: #B4ADC6 !important; }
        @S .sr-legal a { color: #C4B5FD !important; }
        @S .sr-hint { color: #A39CB5 !important; }

        /* Focus ring >= 3:1 on every button (2px outline, offset onto the panel) */
        @S [data-testid="stFormSubmitButton"] button:focus-visible,
        @S .st-key-google_btn button:focus-visible,
        @S .st-key-switch_to_signup button:focus-visible,
        @S .st-key-switch_to_login button:focus-visible,
        @S .st-key-theme_toggle_btn button:focus-visible {
            outline: 2px solid var(--sr2-ring) !important; outline-offset: 3px !important;
        }
""".replace('@S', '.stApp:has(.sr-scene.sr-v2)')


# ── Phase C (hero) ──────────────────────────────────────────────────────────
# Static markup, emitted only when the switch is on (see _scene_html). The new
# pieces carry `hidden`, so with the switch on but no v2 CSS (light theme) they
# take no space; the bare .sr2-card wrapper is then a plain block of the same
# height as the chart it wraps. No ids: nothing here can collide with sr-* ids.
_V2_CHART_CARD_OPEN = (
    '<div class="sr2-card">'
    '<div class="sr2-cardhead" hidden>'
    '<span class="sr2-cardtitle">Audience retention</span>'
    '<svg class="sr2-info" viewBox="0 0 24 24" width="14" height="14" aria-hidden="true" focusable="false">'
    '<circle cx="12" cy="12" r="9.5" fill="none" stroke="currentColor" stroke-width="1.8"/>'
    '<path d="M12 11v5.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>'
    '<circle cx="12" cy="7.6" r="1.2" fill="currentColor"/>'
    '</svg>'
    '<span class="sr2-chip">Last 30 days</span>'
    '</div>'
    '<div class="sr2-y" hidden aria-hidden="true"><span>100%</span><span>50%</span><span>0%</span></div>'
    '<div class="sr2-grid" hidden aria-hidden="true"><i></i><i></i><i></i></div>'
)
# Inline style keeps the light theme (no v2 CSS) looking like the off state:
# normal weight, and the flex gap of the caption is cancelled down to a space.
_V2_BEST_WINDOW = '<b style="font-weight:inherit;margin-left:calc(0.25em - 8px)">Friday, 6 PM.</b>'


def _svg_url(svg):
    """CSS url() for an inline SVG (data URI, fully percent-encoded)."""
    return 'url("data:image/svg+xml,' + quote(svg, safe='') + '")'


def _spark_svg(points):
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 16'>"
        "<defs><linearGradient id='sr2-sf' x1='0' y1='0' x2='0' y2='1'>"
        "<stop offset='0' stop-color='#8B5CF6' stop-opacity='.38'/>"
        "<stop offset='1' stop-color='#8B5CF6' stop-opacity='0'/></linearGradient></defs>"
        f"<path d='M{points} L39 16 L1 16 Z' fill='url(#sr2-sf)'/>"
        f"<path d='M{points}' fill='none' stroke='#A78BFA' stroke-width='1.6'"
        " stroke-linecap='round' stroke-linejoin='round'/></svg>"
    )


def _icon_svg(body, width='2'):
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='#DDD6FE'"
        f" stroke-width='{width}' stroke-linecap='round' stroke-linejoin='round'>{body}</svg>"
    )


_V2_SVG = {
    '@WAVES': (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 300' preserveAspectRatio='none'>"
        "<defs>"
        "<linearGradient id='sr2-wa' x1='0' y1='0' x2='1' y2='0'>"
        "<stop offset='0' stop-color='#5B21B6' stop-opacity='.06'/>"
        "<stop offset='.6' stop-color='#7C3AED' stop-opacity='.30'/>"
        "<stop offset='1' stop-color='#6366F1' stop-opacity='.22'/></linearGradient>"
        "<linearGradient id='sr2-wb' x1='0' y1='0' x2='0' y2='1'>"
        "<stop offset='0' stop-color='#4C1D95' stop-opacity='.34'/>"
        "<stop offset='1' stop-color='#1E1036' stop-opacity='.08'/></linearGradient>"
        "</defs>"
        "<path d='M0 170 C150 120 260 210 420 180 C560 154 660 100 800 118 L800 300 L0 300 Z' fill='url(#sr2-wa)'/>"
        "<path d='M0 230 C170 196 300 262 470 232 C610 208 700 176 800 186 L800 300 L0 300 Z' fill='url(#sr2-wb)'/>"
        "<path d='M0 170 C150 120 260 210 420 180 C560 154 660 100 800 118' fill='none' stroke='#A78BFA'"
        " stroke-opacity='.32' stroke-width='1.2' vector-effect='non-scaling-stroke'/>"
        "<path d='M0 230 C170 196 300 262 470 232 C610 208 700 176 800 186' fill='none' stroke='#C4B5FD'"
        " stroke-opacity='.16' stroke-width='1' vector-effect='non-scaling-stroke'/>"
        "</svg>"
    ),
    '@CUBE': (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 240 230'>"
        "<defs>"
        "<filter id='sr2-cb' x='-60%' y='-60%' width='220%' height='220%'><feGaussianBlur stdDeviation='14'/></filter>"
        "<filter id='sr2-cs' x='-60%' y='-60%' width='220%' height='220%'><feGaussianBlur stdDeviation='7'/></filter>"
        "<filter id='sr2-cg' x='-60%' y='-60%' width='220%' height='220%'><feGaussianBlur stdDeviation='5'/></filter>"
        "<linearGradient id='sr2-cf' x1='0' y1='0' x2='1' y2='1'>"
        "<stop offset='0' stop-color='#C4B5FD' stop-opacity='.42'/>"
        "<stop offset='.5' stop-color='#7C3AED' stop-opacity='.20'/>"
        "<stop offset='1' stop-color='#4C1D95' stop-opacity='.40'/></linearGradient>"
        "<linearGradient id='sr2-ct' x1='0' y1='1' x2='1' y2='0'>"
        "<stop offset='0' stop-color='#EDE9FE' stop-opacity='.40'/>"
        "<stop offset='1' stop-color='#A78BFA' stop-opacity='.18'/></linearGradient>"
        "<linearGradient id='sr2-cr' x1='0' y1='0' x2='0' y2='1'>"
        "<stop offset='0' stop-color='#7C3AED' stop-opacity='.55'/>"
        "<stop offset='1' stop-color='#2E1065' stop-opacity='.65'/></linearGradient>"
        "<linearGradient id='sr2-cp' x1='0' y1='0' x2='1' y2='1'>"
        "<stop offset='0' stop-color='#F5F3FF'/><stop offset='.45' stop-color='#C4B5FD'/>"
        "<stop offset='1' stop-color='#7C3AED'/></linearGradient>"
        "<linearGradient id='sr2-ch' x1='0' y1='0' x2='0' y2='1'>"
        "<stop offset='0' stop-color='#FFFFFF' stop-opacity='.50'/>"
        "<stop offset='1' stop-color='#FFFFFF' stop-opacity='0'/></linearGradient>"
        "</defs>"
        "<circle cx='118' cy='120' r='58' fill='#7C3AED' opacity='.30' filter='url(#sr2-cb)'/>"
        "<ellipse cx='112' cy='202' rx='72' ry='7' fill='#8B5CF6' opacity='.55' filter='url(#sr2-cs)'/>"
        "<path d='M180 64 L206 42 L206 164 L180 190 Z' fill='url(#sr2-cr)' stroke='#C4B5FD'"
        " stroke-opacity='.35' stroke-width='1.2' stroke-linejoin='round'/>"
        "<path d='M40 63 L66 41 L204 41 L178 63 Z' fill='url(#sr2-ct)' stroke='#EDE9FE'"
        " stroke-opacity='.45' stroke-width='1.2' stroke-linejoin='round'/>"
        "<rect x='30' y='62' width='150' height='136' rx='24' fill='url(#sr2-cf)' stroke='#DDD6FE'"
        " stroke-opacity='.60' stroke-width='1.5'/>"
        "<path d='M54 70 H156 Q170 70 172 84 Q118 96 38 116 V86 Q38 70 54 70 Z' fill='url(#sr2-ch)' opacity='.40'/>"
        "<path d='M92 106 L92 156 L138 131 Z' fill='#A78BFA' opacity='.85' filter='url(#sr2-cg)'/>"
        "<path d='M92 106 L92 156 L138 131 Z' fill='url(#sr2-cp)' stroke='url(#sr2-cp)'"
        " stroke-width='8' stroke-linejoin='round'/>"
        "</svg>"
    ),
    '@ICONEYE': _icon_svg("<path d='M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z'/><circle cx='12' cy='12' r='3'/>"),
    '@ICONPEOPLE': _icon_svg("<path d='M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2'/><circle cx='9' cy='7' r='4'/>"
                             "<path d='M22 21v-2a4 4 0 0 0-3-3.87'/><path d='M16 3.13a4 4 0 0 1 0 7.75'/>"),
    '@ICONBARS': _icon_svg("<path d='M6 20v-7M12 20V5M18 20V10'/>", width='2.4'),
    '@KPILINE1': _spark_svg('1 12 L6 10 L10 11 L15 6 L19 8 L24 5 L28 7 L33 3 L39 4'),
    '@KPILINE2': _spark_svg('1 11 L5 12 L9 9 L14 10 L18 6 L23 8 L27 5 L32 7 L39 3'),
    '@KPILINE3': _spark_svg('1 13 L6 12 L10 13 L14 9 L19 10 L24 7 L28 8 L33 4 L39 2'),
    '@CLOCK': (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>"
        "<circle cx='12' cy='12' r='11' fill='#EAB308'/>"
        "<circle cx='12' cy='12' r='8.2' fill='none' stroke='#FDE68A' stroke-opacity='.55' stroke-width='1'/>"
        "<path d='M12 6.8V12l3.4 2.1' fill='none' stroke='#1C1404' stroke-width='2.2'"
        " stroke-linecap='round' stroke-linejoin='round'/></svg>"
    ),
}

_V2_HERO_CSS = """

        /* ═══════════════ LOGIN_UI_V2 · dark only · phase C (hero) ═══════════════ */
        @S {
            --sr2-cpt: clamp(3px, 0.5vh, 8px);     /* card padding top/bottom (.block-container) */
            --sr2-cpl: clamp(10px, 1.4vw, 18px);   /* card padding left/right */
        }

        /* C1 · background: glow top right, waves at the bottom, dot texture. The
           ::before sits behind every child (isolation + z-index:-1). */
        @S .sr-scene.sr-v2 {
            isolation: isolate;
            --sr2-chart-h: clamp(88px, 13vh, 128px);   /* same as the base .sr-chart height */
            background: linear-gradient(160deg, #1B1233 0%, #120C22 48%, #0B0816 100%);
        }
        @S .sr-scene.sr-v2::before {
            content: ""; position: absolute; inset: 0; z-index: -1; pointer-events: none;
            background:
                radial-gradient(48% 40% at 94% 4%, rgba(139,92,246,0.45), transparent 72%),
                radial-gradient(36% 30% at 72% 30%, rgba(124,58,237,0.16), transparent 75%),
                @WAVES bottom / 100% clamp(150px, 34%, 260px) no-repeat,
                radial-gradient(circle, rgba(196,181,253,0.11) 1px, transparent 1.5px) 0 0 / 18px 18px;
        }
        /* Edge to edge: the hero grows over the card padding (left, top, bottom, 1px
           short so the card border stays visible) and adds the same amount to its own
           padding, so its content box does not move or change size. */
        @media (min-width: 901px) {
            @S [data-testid="stHorizontalBlock"]:has(.sr-scene) > [data-testid="stColumn"]:nth-of-type(1) {
                overflow: visible !important;
            }
            @S .sr-scene.sr-v2 {
                margin: calc(1px - var(--sr2-cpt)) 0 0 calc(1px - var(--sr2-cpl));
                height: calc(100% + 2 * var(--sr2-cpt) - 2px);
                padding-top: calc(clamp(10px, 1.3vh, 20px) + var(--sr2-cpt) - 1px);
                padding-bottom: calc(clamp(10px, 1.3vh, 20px) + var(--sr2-cpt) - 1px);
                padding-left: calc(clamp(30px, 3.4vw, 48px) + var(--sr2-cpl) - 1px);
                border-radius: 25px 0 0 25px;
            }
        }

        /* C2 · glass play-button cube: a flex item with zero net height (margin-top =
           -height), moved by `order` between the subtitle and the chart card and
           right-aligned. Hidden when the hero is too narrow for it. */
        @S .sr-scene.sr-v2 > :nth-child(n+4) { order: 2; }
        @S .sr-scene.sr-v2::after {
            content: ""; order: 1; flex: none; align-self: flex-end;
            width: 124px; height: 112px; margin: -112px 0 0;
            background: @CUBE center / contain no-repeat;
            pointer-events: none;
        }
        @media (max-width: 1239px) {
            @S .sr-scene.sr-v2::after { display: none; }
        }
        @media (prefers-reduced-motion: no-preference) {
            @S .sr-scene.sr-v2::after { animation: sr2-float 6s ease-in-out infinite; }
        }
        @keyframes sr2-float {
            0%, 100% { transform: translateY(0); }
            50%      { transform: translateY(-6px); }
        }

        /* C3 · chart card around .sr-chartwrap. The wrap itself is not padded or
           moved inside, so the playhead maths (relative to the svg) is unchanged. */
        @S .sr2-card {
            position: relative;
            padding: 10px 14px 6px 44px;
            border: 1px solid rgba(167,139,250,0.24); border-radius: 16px;
            background: linear-gradient(180deg, rgba(34,24,58,0.78) 0%, rgba(20,14,36,0.78) 100%);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 10px 30px rgba(0,0,0,0.25);
        }
        @S .sr2-cardhead {
            display: flex !important; align-items: center; gap: 7px;
            height: 22px; margin: 0 0 6px -30px;
            color: #A39CB5;
        }
        @S .sr2-cardtitle { font-size: 13px; font-weight: 600; color: #EDE9FE; }
        @S .sr2-info { flex: none; }
        @S .sr2-chip {
            margin-left: auto; padding: 2px 10px; border-radius: 999px; white-space: nowrap;
            font-size: 11px; font-weight: 500; color: #C4B5FD;
            background: rgba(124,58,237,0.14); border: 1px solid rgba(167,139,250,0.30);
        }
        /* Labels and grid cover the svg box: top = card padding 10 + head 22 + 6. */
        @S .sr2-y, @S .sr2-grid {
            display: block !important; position: absolute; top: 38px;
            height: var(--sr2-chart-h); pointer-events: none;
        }
        @S .sr2-y {
            left: 8px; width: 30px;
            font-family: 'JetBrains Mono', monospace; font-size: 9.5px; color: #A39CB5;
        }
        @S .sr2-y span { position: absolute; right: 0; transform: translateY(-50%); line-height: 1; }
        /* JS: pct = (210 - y) / 190 -> 100% at y=20, 50% at y=115, 0% at y=210 (of 210) */
        @S .sr2-y span:nth-child(1), @S .sr2-grid i:nth-child(1) { top: 9.524%; }
        @S .sr2-y span:nth-child(2), @S .sr2-grid i:nth-child(2) { top: 54.762%; }
        @S .sr2-y span:nth-child(3) { top: 100%; }
        @S .sr2-grid {
            left: 44px; right: 14px;
            background: repeating-linear-gradient(to right, rgba(167,139,250,0.07) 0 1px, transparent 1px calc(100% / 6));
        }
        @S .sr2-grid i { position: absolute; left: 0; right: 0; height: 1px; background: rgba(167,139,250,0.16); }
        @S .sr2-grid i:nth-child(3) { top: calc(100% - 1px); }
        @S .sr-scene.sr-v2 .sr-chart { height: var(--sr2-chart-h); }
        @S .sr-scene.sr-v2 .sr-chart > g { display: none; }   /* old grid; the card grid replaces it */

        /* C4 · no red progress bar: hidden, still in the DOM for the JS */
        @S .sr-scene.sr-v2 .sr-track { display: none; }

        /* C5 · KPI cards: icon in a circle (::before) and a sparkline (::after). The
           grid keeps the two text rows, so the card height does not change. Plain
           cards below 1350px, where the three would not fit side by side. */
        @media (min-width: 1350px) {
            @S .sr-scene.sr-v2 .sr-kpi {
                display: grid; grid-template-columns: 28px minmax(0, 1fr) 34px;
                column-gap: 8px; align-items: center;
                padding-left: 12px; padding-right: 12px;
            }
            @S .sr-scene.sr-v2 .sr-kpi:nth-child(-n+2) { grid-template-areas: "icon val spark" "icon lab lab"; }
            @S .sr-scene.sr-v2 .sr-kpi:nth-child(3) { grid-template-areas: "icon val val" "icon lab spark"; }
            @S .sr-scene.sr-v2 .sr-kpi-val { grid-area: val; white-space: nowrap; }
            @S .sr-scene.sr-v2 .sr-kpi-label { grid-area: lab; white-space: nowrap; }
            @S .sr-scene.sr-v2 .sr-kpi::before {
                content: ""; grid-area: icon; width: 28px; height: 28px; border-radius: 50%;
                box-sizing: border-box; border: 1px solid rgba(167,139,250,0.35);
                background: rgba(124,58,237,0.22) center / 15px 15px no-repeat;
            }
            @S .sr-scene.sr-v2 .sr-kpi:nth-child(1)::before { background-image: @ICONEYE; }
            @S .sr-scene.sr-v2 .sr-kpi:nth-child(2)::before { background-image: @ICONPEOPLE; }
            @S .sr-scene.sr-v2 .sr-kpi:nth-child(3)::before { background-image: @ICONBARS; }
            @S .sr-scene.sr-v2 .sr-kpi::after {
                content: ""; grid-area: spark; justify-self: end; width: 34px; height: 14px;
                background: center / contain no-repeat;
            }
            @S .sr-scene.sr-v2 .sr-kpi:nth-child(1)::after { background-image: @KPILINE1; }
            @S .sr-scene.sr-v2 .sr-kpi:nth-child(2)::after { background-image: @KPILINE2; }
            @S .sr-scene.sr-v2 .sr-kpi:nth-child(3)::after { background-image: @KPILINE3; }
        }

        /* C6 · tip line: yellow clock instead of the bullet; bold best window */
        @S .sr-scene.sr-v2 .sr-captions span::before {
            content: ""; flex: none; width: 16px; height: 16px;
            background: @CLOCK center / contain no-repeat;
        }
        @S .sr-scene.sr-v2 .sr-captions b { font-weight: 700 !important; color: #F5F2FA; }

        /* C7 · no heading anchor-link icon on hover */
        @S .sr-scene.sr-v2 [data-testid="stHeaderActionElements"] { display: none !important; }
"""
for _token, _svg in _V2_SVG.items():
    _V2_HERO_CSS = _V2_HERO_CSS.replace(_token, _svg_url(_svg))
_V2_DARK_CSS += _V2_HERO_CSS.replace('@S', '.stApp:has(.sr-scene.sr-v2)')


# ─────────────────────────────────────────────────────────────────────────────
# Styles
# ─────────────────────────────────────────────────────────────────────────────

def _inject_login_styles(mode='light'):
    t = theme_tokens.get_tokens(mode)
    is_dark = mode == 'dark'

    # Page-background glows (halved in light mode) + faint chart-grid texture.
    glow_v = 'rgba(124,58,237,0.16)' if is_dark else 'rgba(124,58,237,0.08)'
    glow_b = 'rgba(91,108,255,0.12)' if is_dark else 'rgba(91,108,255,0.06)'
    grid_line = 'rgba(167,139,250,0.05)' if is_dark else 'rgba(124,58,237,0.06)'
    # Solid panel behind both columns (matches reference --panel: #1A1426).
    panel_bg = '#1A1426' if is_dark else 'rgba(255,255,255,0.80)'
    # Form-side padding: trimmed vertically, generous horizontally, so the panel
    # reads landscape (wide + short) like option_a_split_showcase.html.
    form_pad = ('clamp(14px, 1.8vh, 26px) clamp(38px, 3.6vw, 52px)' if is_dark
                else 'clamp(12px, 1.6vh, 22px) clamp(32px, 3.2vw, 46px)')
    # LOGIN_UI_V2: dark theme only; empty (nothing emitted) otherwise.
    v2_css = _V2_DARK_CSS if (is_dark and _ui_v2_enabled()) else ''

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;600;700&display=swap');

        [data-testid="stSidebar"], [data-testid="collapsedControl"] {{ display: none !important; }}
        #MainMenu, footer, header {{ visibility: hidden; }}

        /* ── Page background: theme color + two soft radial glows ── */
        .stApp {{
            isolation: isolate;
            background:
                radial-gradient(46% 42% at 16% 18%, {glow_v}, transparent 72%),
                radial-gradient(44% 40% at 84% 84%, {glow_b}, transparent 72%),
                {t['bg_page']} !important;
            font-family: 'Inter', sans-serif;
        }}
        /* Smooth cross-theme fade (Telegram-style) — scoped to the surfaces that
           actually recolor (page bg, panel, form text/inputs/buttons/toggle).
           The always-dark left scene doesn't change, so it's left out. */
        .stApp,
        .block-container::before,
        .stApp .block-container .stTextInput > div > div > input,
        .sr-formtitle, .sr-formsub,
        [data-testid="stFormSubmitButton"] > button,
        .st-key-demo_btn button,
        .st-key-theme_toggle_btn button,
        .login-divider span, .login-divider::before, .login-divider::after {{
            transition: background-color .35s ease, color .35s ease,
                        border-color .35s ease !important;
        }}
        /* Ultra-faint chart-grid texture, radial-masked to fade at the edges */
        .stApp::before {{
            content: '';
            position: fixed; inset: 0;
            background-image:
                linear-gradient(to right, {grid_line} 1px, transparent 1px),
                linear-gradient(to bottom, {grid_line} 1px, transparent 1px);
            background-size: 72px 72px;
            -webkit-mask: radial-gradient(70% 65% at 50% 40%, #000 0%, rgba(0,0,0,0.6) 46%, transparent 82%);
                    mask: radial-gradient(70% 65% at 50% 40%, #000 0%, rgba(0,0,0,0.6) 46%, transparent 82%);
            pointer-events: none;
            z-index: -1;
        }}

        /* ── Glass panel wrapper ── */
        /* Vertically center the panel and keep it within the viewport so large
           screens show it as a single, no-scroll page (see desktop lock below). */
        .block-container {{
            position: relative; z-index: 1;
            max-width: min(1400px, 97vw) !important;
            margin: 0 auto !important;
            /* Vertical padding kept tight so the panel border hugs the content
               top/bottom; horizontal padding unchanged. */
            padding: clamp(3px, 0.5vh, 8px) clamp(10px, 1.4vw, 18px) !important;
            transform-style: preserve-3d;
            will-change: transform;
        }}
        /* Frost on a pseudo-element — NOT on the container (fixed-toggle trap) */
        .block-container::before {{
            content: ''; position: absolute; inset: 0; z-index: -1;
            background: {panel_bg};
            border: 1px solid {t['border_strong']};
            border-radius: 26px;
            box-shadow: 0 40px 110px rgba(0,0,0,0.6), 0 0 0 1px rgba(0,0,0,0.25);
            overflow: hidden;
        }}
        /* Cursor-following light reflection (JS sets --mx/--my/--refl) */
        .block-container::after {{
            content: ''; position: absolute; inset: 0; z-index: 0;
            border-radius: 26px; pointer-events: none;
            background: radial-gradient(240px 240px at var(--mx, 50%) var(--my, 30%),
                        rgba(185,163,252,0.10), transparent 62%);
            opacity: var(--refl, 0);
            transition: opacity .4s ease;
        }}
        /* keep real content above the reflection sheen */
        .block-container [data-testid="stHorizontalBlock"] {{ position: relative; z-index: 1; }}

        /* ── Theme toggle: pin INSIDE the panel's top-right corner ──
           Overrides the global fixed-viewport-corner placement from
           theme.inject_theme_toggle(). Higher specificity + !important win
           regardless of injection order. */
        .stApp .block-container .st-key-theme_toggle_btn {{
            position: absolute !important;
            top: clamp(10px, 1.2vw, 16px) !important;
            right: clamp(10px, 1.2vw, 16px) !important;
            left: auto !important; bottom: auto !important;
            z-index: 30 !important;
        }}
        /* Toggle chrome tuned for sitting over the (always-dark) scene / form. */
        .stApp .st-key-theme_toggle_btn button {{
            width: 40px !important; height: 40px !important;
            min-height: 40px !important;
            font-size: 1.05rem !important;
        }}

        /* ═══════════════ LEFT SCENE (always dark) ═══════════════ */
        .sr-scene {{
            position: relative;
            background: linear-gradient(158deg, #151021 0%, #0C0814 100%);
            border-right: 1px solid rgba(167,139,250,0.18);
            border-radius: 0;
            padding: clamp(10px, 1.3vh, 20px) clamp(30px, 3.4vw, 48px);
            overflow: hidden;
            color: #F5F2FA;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 0;
        }}
        /* Anchor scene content to the top on shorter viewports so the eyebrow /
           LIVE row is never clipped by overflow:hidden. */
        @media (max-height: 820px) {{
            .sr-scene {{ justify-content: flex-start; }}
        }}
        .sr-top {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: clamp(14px, 2.4vh, 26px); }}
        .sr-eyebrow {{
            font-size: 11px; font-weight: 600; letter-spacing: 0.2em;
            text-transform: uppercase; color: #A78BFA;
        }}
        .sr-live {{
            display: inline-flex; align-items: center; gap: 7px;
            font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 600;
            letter-spacing: 0.08em; color: #FFD3D3;
            background: rgba(255,75,75,0.10); border: 1px solid rgba(255,75,75,0.32);
            border-radius: 999px; padding: 4px 10px; white-space: nowrap;
        }}
        .sr-live-dot {{
            width: 7px; height: 7px; border-radius: 50%; background: #FF4B4B;
            box-shadow: 0 0 0 0 rgba(255,75,75,0.6);
            animation: sr-pulse 1.8s ease-out infinite;
        }}
        @keyframes sr-pulse {{
            0%   {{ box-shadow: 0 0 0 0 rgba(255,75,75,0.55); }}
            70%  {{ box-shadow: 0 0 0 8px rgba(255,75,75,0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(255,75,75,0); }}
        }}
        .sr-h1 {{
            font-family: 'Space Grotesk', sans-serif; font-weight: 700;
            font-size: clamp(26px, 2.6vw, 34px); line-height: 1.1; letter-spacing: -0.025em;
            margin: 0 0 clamp(5px, 0.9vh, 9px); color: #F5F2FA;
        }}
        .sr-grad {{
            background: linear-gradient(100deg, #A78BFA, #5B6CFF);
            -webkit-background-clip: text; background-clip: text;
            -webkit-text-fill-color: transparent; color: transparent;
        }}
        .sr-sub {{ font-size: 14px; line-height: 1.45; color: #A39CB5; margin: 0 0 clamp(10px, 1.5vh, 16px); max-width: 40ch; }}

        /* Retention curve */
        .sr-chartwrap {{ position: relative; width: 100%; margin-bottom: 4px; cursor: crosshair; }}
        /* SVG uses preserveAspectRatio="none", so it stretches to whatever height
           we give it. Cap the height (shorter) while width stays 100% (wider) —
           this is what makes the panel read landscape like the reference. */
        .sr-chart {{ display: block; width: 100%; height: clamp(88px, 13vh, 128px); overflow: visible; }}
        #sr-path {{ filter: drop-shadow(0 4px 12px rgba(124,58,237,0.55)); }}
        .sr-grid-line {{ stroke: rgba(167,139,250,0.10); stroke-width: 1; }}
        .sr-playhead {{
            position: absolute; top: 0; left: 40%; bottom: 26px;
            width: 1px; pointer-events: none;
            background: linear-gradient(rgba(245,242,250,0.0), rgba(245,242,250,0.5) 30%, rgba(245,242,250,0.5));
        }}
        .sr-ph-dot {{
            position: absolute; width: 11px; height: 11px; border-radius: 50%;
            transform: translate(-50%, -50%); pointer-events: none;
            background: #FEF08A; border: 2px solid #EAB308;
            box-shadow: 0 0 14px rgba(234,179,8,0.8);
        }}
        .sr-tip {{
            position: absolute; transform: translate(-50%, -130%);
            font-family: 'JetBrains Mono', monospace; font-size: 10.5px; font-weight: 600;
            color: #F5F2FA;
            background: rgba(14,10,22,0.92); border: 1px solid rgba(167,139,250,0.30);
            border-radius: 8px; padding: 5px 9px; white-space: nowrap; pointer-events: none;
        }}
        .sr-tip b {{ color: #FEF08A; font-weight: 700; }}

        /* YouTube-style timeline (inside chart) */
        .sr-timeline {{ margin-top: 4px; }}
        .sr-track {{
            position: relative; height: 5px; border-radius: 100px;
            background: rgba(245,242,250,0.12); overflow: hidden;
        }}
        .sr-progress {{
            position: absolute; left: 0; top: 0; height: 100%; width: 42%;
            border-radius: 100px; background: linear-gradient(90deg, #FF4B4B, #FF7B54);
        }}
        .sr-tick {{
            position: absolute; top: 0; bottom: 0; width: 2px;
            background: rgba(14,10,22,0.8);
        }}
        .sr-times {{
            display: flex; justify-content: space-between; margin-top: 7px;
            font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #736B85;
        }}

        /* KPI row */
        .sr-kpis {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: clamp(10px, 1.4vh, 16px); }}
        .sr-kpi {{
            border: 1px solid rgba(167,139,250,0.18); border-radius: 14px;
            padding: clamp(7px, 1vh, 10px) 15px clamp(6px, 0.9vh, 9px); background: rgba(167,139,250,0.05);
        }}
        .sr-kpi-val {{
            font-family: 'JetBrains Mono', monospace; font-weight: 700;
            font-size: 21px; color: #F5F2FA; letter-spacing: -0.02em;
        }}
        .sr-kpi-val .up {{ color: #34D399; font-size: 13px; }}
        .sr-kpi-label {{
            margin-top: 3px; font-size: 10.5px; font-weight: 500; letter-spacing: 0.08em;
            text-transform: uppercase; color: #736B85;
        }}

        /* Rotating captions */
        .sr-captions {{ position: relative; height: 20px; margin-top: clamp(10px, 1.5vh, 16px); }}
        .sr-captions span {{
            position: absolute; inset: 0; opacity: 0;
            font-size: 12.5px; color: #A39CB5;
            display: flex; align-items: center; gap: 8px;
            animation: sr-cap 12s linear infinite;
        }}
        .sr-captions span::before {{ content: '▸'; color: #EAB308; font-size: 11px; }}
        .sr-captions span:nth-child(2) {{ animation-delay: 4s; }}
        .sr-captions span:nth-child(3) {{ animation-delay: 8s; }}
        @keyframes sr-cap {{
            0%   {{ opacity: 0; transform: translateY(8px); }}
            4%   {{ opacity: 1; transform: translateY(0); }}
            30%  {{ opacity: 1; transform: translateY(0); }}
            34%  {{ opacity: 0; transform: translateY(-8px); }}
            100% {{ opacity: 0; }}
        }}

        /* ═══════════════ RIGHT FORM SIDE (theme-aware) ═══════════════ */
        /* Vertically center + add padding matching ref .form-side */
        .block-container [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-of-type(2) {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            height: 100%;
            padding: {form_pad} !important;
        }}
        .sr-formhead {{ margin-bottom: clamp(10px, 1.6vh, 18px); }}
        .sr-logo {{
            width: 46px; height: 46px; border-radius: 14px; margin-bottom: clamp(8px, 1.2vh, 14px);
            background: linear-gradient(135deg, #7C3AED, #A78BFA);
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 12px 30px rgba(124,58,237,0.4);
        }}
        .sr-logo svg {{ margin-left: 2px; }}
        .sr-formtitle {{
            font-family: 'Space Grotesk', sans-serif; font-weight: 700;
            font-size: 24px; letter-spacing: -0.02em;
            color: {t['text_primary']}; margin: 0;
        }}
        .sr-formsub {{ font-size: 13.5px; color: {t['text_secondary']}; margin: 7px 0 0; }}

        /* Strip Streamlit form chrome */
        [data-testid="stForm"] {{
            border: none !important; padding: 0 !important; background: transparent !important;
        }}

        .stApp .block-container .stTextInput > div > div > input {{
            background: {t['input_bg']} !important;
            border: 1px solid {t['input_border']} !important;
            border-radius: 12px !important;
            color: {t['text_body']} !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.94rem !important;
            padding: clamp(9px, 1.4vh, 13px) 16px !important; height: auto !important;
        }}
        /* Compress inter-widget vertical rhythm so the form fits one screen.
           Streamlit's default block gap is the main scroll driver here. */
        [data-testid="stForm"] [data-testid="stVerticalBlock"] {{ gap: clamp(0.35rem, 1vh, 0.7rem) !important; }}
        [data-testid="stForm"] .stTextInput {{ margin-bottom: 0 !important; }}
        [data-testid="stForm"] [data-testid="stWidgetLabel"] {{ margin-bottom: 2px !important; }}
        .stApp .block-container .stTextInput > div > div > input:focus {{
            border-color: {t['brand']} !important;
            box-shadow: 0 0 0 3px {t['focus_ring']} !important;
        }}
        .stApp .block-container .stTextInput > div > div > input::placeholder {{
            color: {t['text_faint']} !important; opacity: 1;
        }}
        .stApp .block-container .stTextInput > label {{
            color: {t['text_secondary']} !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.8rem !important; font-weight: 500 !important;
        }}

        /* Wrapper must also span full width, else button's 100% has no anchor */
        [data-testid="stFormSubmitButton"] {{ width: 100% !important; }}

        /* Primary submit button (inside form) — deep violet gradient + gold beam */
        [data-testid="stFormSubmitButton"] > button {{
            width: 100% !important;
            position: relative; isolation: isolate; overflow: hidden;
            background: linear-gradient(120deg, #7C3AED, #6D28D9) !important;
            border: none !important;
            border-radius: 12px !important;
            color: #fff !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 14.5px !important; font-weight: 600 !important;
            padding: clamp(10px, 1.5vh, 13px) 20px !important;
            box-shadow: 0 8px 24px rgba(124,58,237,0.4) !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease !important;
            margin-top: 6px !important;
        }}
        [data-testid="stFormSubmitButton"] > button:focus-visible {{
            outline: none !important; box-shadow: 0 0 0 3px {t['focus_ring']} !important;
        }}
        [data-testid="stFormSubmitButton"] > button::before {{
            content: ""; position: absolute; inset: 0; border-radius: 12px; padding: 2px;
            background: conic-gradient(from var(--beam-angle),
                transparent 0%, transparent 30%, #EAB308 45%, #FEF08A 50%, #EAB308 55%,
                transparent 70%, transparent 100%);
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
                    mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            -webkit-mask-composite: xor; mask-composite: exclude;
            animation: sr-beam 2800ms cubic-bezier(0.34, 1.56, 0.64, 1) infinite;
            pointer-events: none; z-index: 2;
        }}
        @property --beam-angle {{ syntax: "<angle>"; inherits: false; initial-value: 0deg; }}
        @keyframes sr-beam {{
            0%   {{ --beam-angle: 0deg;   }}
            60%  {{ --beam-angle: 230deg; }}
            75%  {{ --beam-angle: 215deg; }}
            88%  {{ --beam-angle: 365deg; }}
            100% {{ --beam-angle: 360deg; }}
        }}

        /* Wrapper must also span full width, else button's 100% has no anchor */
        .st-key-demo_btn {{ width: 100% !important; }}

        /* Demo button (gold-tinted) */
        .st-key-demo_btn button {{
            width: 100% !important;
            background: rgba(234,179,8,0.07) !important;
            border: 1px solid rgba(234,179,8,0.45) !important;
            border-radius: 12px !important;
            color: {'#FDE68A' if is_dark else '#A16207'} !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.92rem !important; font-weight: 600 !important;
            padding: clamp(9px, 1.4vh, 12px) 20px !important; box-shadow: none !important;
            transition: background 0.18s ease !important;
        }}
        .st-key-demo_btn button:hover {{
            background: rgba(234,179,8,0.14) !important;
        }}
        .st-key-demo_btn button:focus-visible {{
            outline: none !important; box-shadow: 0 0 0 3px rgba(234,179,8,0.35) !important;
        }}

        /* "Continue with Google" — same surface as the inputs, Google "G" mark */
        .st-key-google_btn {{ width: 100% !important; }}
        .st-key-google_btn button {{
            width: 100% !important;
            background: {t['input_bg']} !important;
            border: 1px solid {t['input_border']} !important;
            border-radius: 12px !important;
            color: {t['text_body']} !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 14px !important; font-weight: 600 !important;
            padding: clamp(9px, 1.4vh, 12px) 20px !important; box-shadow: none !important;
            display: flex !important; align-items: center; justify-content: center; gap: 10px;
            transition: border-color .18s ease, background-color .35s ease, color .35s ease !important;
        }}
        .st-key-google_btn button::before {{
            content: ''; width: 18px; height: 18px; flex: none;
            background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Cpath fill='%23FFC107' d='M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z'/%3E%3Cpath fill='%23FF3D00' d='M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z'/%3E%3Cpath fill='%234CAF50' d='M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-7.9l-6.5 5C9.5 39.6 16.2 44 24 44z'/%3E%3Cpath fill='%231976D2' d='M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5z'/%3E%3C/svg%3E") center / contain no-repeat;
        }}
        .st-key-google_btn button:hover {{ border-color: {t['brand']} !important; }}
        .st-key-google_btn button:focus-visible {{
            outline: none !important; box-shadow: 0 0 0 3px {t['focus_ring']} !important;
        }}
        .st-key-google_btn button:disabled {{ opacity: .55; cursor: not-allowed; }}
        .sr-hint {{ font-size: 12px; color: {t['text_faint']}; margin: 6px 0 0; text-align: center; }}
        .sr-hint a {{ color: {t['brand']}; }}

        /* Legal links under the form (public /privacy and /terms pages) */
        .stApp .sr-legal {{
            font-size: 12px; line-height: 1.5; text-align: center;
            color: {t['text_secondary']}; margin: clamp(8px, 1.4vh, 14px) 0 0;
        }}
        .stApp .sr-legal a {{
            color: {t['brand']}; text-decoration: underline; text-underline-offset: 2px;
        }}
        .stApp .sr-legal a:focus-visible {{
            outline: 2px solid {t['brand']}; outline-offset: 2px; border-radius: 3px;
        }}
        .sr-visually-hidden {{
            position: absolute !important; width: 1px; height: 1px; padding: 0; margin: -1px;
            overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0;
        }}

        /* Mode-switch buttons ("Sign up" / "Back to sign in") — real Streamlit
           buttons styled as a centered inline link (matches ref .switch). */
        .st-key-switch_to_signup, .st-key-switch_to_login {{
            display: flex; justify-content: center; margin-top: 2px;
        }}
        .st-key-switch_to_signup button, .st-key-switch_to_login button {{
            width: auto !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: {t['text_secondary']} !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 13px !important; font-weight: 500 !important;
            padding: 4px 8px !important;
            transition: color 0.15s ease !important;
        }}
        .st-key-switch_to_signup button:hover, .st-key-switch_to_login button:hover {{
            background: transparent !important;
            color: {t['brand']} !important;
        }}
        .st-key-switch_to_signup button span, .st-key-switch_to_login button span {{
            color: inherit !important;
        }}
        .st-key-switch_to_signup button:focus-visible, .st-key-switch_to_login button:focus-visible {{
            outline: none !important; box-shadow: 0 0 0 3px {t['focus_ring']} !important;
        }}

        /* Notes + divider */
        .login-note {{
            border-radius: 11px; padding: 11px 14px; margin: 4px 0 12px;
            font-family: 'Inter', sans-serif; font-size: 0.84rem;
        }}
        .login-err {{ background: rgba(220,38,38,0.10); border: 1px solid rgba(220,38,38,0.30); color: {t['neg']}; }}
        .login-ok  {{ background: rgba(22,163,74,0.10); border: 1px solid rgba(22,163,74,0.30); color: {t['pos']}; }}
        .login-divider {{ display: flex; align-items: center; gap: 14px; margin: clamp(10px, 1.8vh, 18px) 0 clamp(8px, 1.4vh, 12px); }}
        .login-divider::before, .login-divider::after {{ content: ''; flex: 1; height: 1px; background: {t['divider']}; }}
        .login-divider span {{
            font-size: 0.72rem; color: {t['text_faint']};
            text-transform: uppercase; letter-spacing: 0.1em;
        }}

        /* ═══════════════ DESKTOP: single no-scroll page ═══════════════ */
        /* On laptops/desktops the whole panel is centered and the app view is
           locked to the viewport height — no scrollbar, matching the reference
           option_a_split_showcase.html (body: overflow:hidden). Small screens
           below keep natural scrolling for the stacked layout. */
        @media (min-width: 901px) {{
            html, body {{ overflow: hidden !important; }}
            /* Centering lives on the SCROLL PARENT, so the panel itself hugs its
               content. Putting min-height:100vh on .block-container (which carries
               the ::before border) stretched the border to full screen height —
               that is what pushed the top/bottom borders away from the content. */
            [data-testid="stMain"], section.main {{
                overflow: hidden !important;
                min-height: 100vh;
                display: flex; flex-direction: column; justify-content: center;
            }}
            /* Panel = natural content height, vertically centered by the parent. */
            [data-testid="stMain"] > .block-container,
            [data-testid="stMainBlockContainer"].block-container {{
                min-height: 0 !important;
                height: auto !important;
                margin-top: auto !important;
                margin-bottom: auto !important;
            }}
            /* Equal-height columns so the left scene fills the panel */
            .block-container [data-testid="stHorizontalBlock"] {{ align-items: stretch; }}
        }}

        /* ═══════════════ RESPONSIVE ═══════════════ */
        @media (max-width: 900px) {{
            [data-testid="stColumn"] {{ width: 100% !important; flex: 1 1 100% !important; min-width: 100% !important; }}
            .sr-scene {{ border-right: none; border-bottom: 1px solid rgba(167,139,250,0.18); padding: 30px 28px 26px; }}
            .sr-h1 {{ font-size: 26px; }}
            .sr-captions {{ display: none; }}
            .block-container [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-of-type(2) {{
                padding: 32px 28px 30px !important;
            }}
        }}
        @media (max-width: 600px) {{
            .block-container {{ padding: 0 !important; }}
            .sr-scene {{ padding: 24px 20px; }}
            .sr-kpi-val {{ font-size: 16px; }}
            .sr-tip {{ font-size: 9.5px; }}
        }}

        /* Decorative motion off when the user asks for reduced motion.
           Beam + LIVE pulse + curve scrub intentionally stay active. */
        @media (prefers-reduced-motion: reduce) {{
            .sr-captions span {{ animation: none; }}
            .sr-captions span:nth-child(1) {{ opacity: 1; transform: none; }}
            .block-container {{ transform: none !important; }}
        }}

        /* ═══════════════ FIXED-HEIGHT CARD (login page only) ═══════════════
           Every rule is anchored on .sr-scene so nothing can leak to the
           dashboard. Card = viewport - 2×8px in every state; the form panel
           scrolls inside it; message slots are fixed (see _show_messages). */
        html:has(.sr-scene), body:has(.sr-scene) {{ overflow: hidden !important; }}
        .stApp:has(.sr-scene) [data-testid="stMain"] {{
            overflow: hidden !important;
            min-height: 0 !important;
            justify-content: flex-start !important;
        }}
        /* 100vh fallback first; no var() here or the fallback is lost. */
        .stApp:has(.sr-scene) [data-testid="stMainBlockContainer"] {{
            box-sizing: border-box !important;
            height: calc(100vh - 16px) !important;
            height: calc(100dvh - 16px) !important;
            min-height: 0 !important;
            max-height: none !important;
            flex: 0 0 auto !important;
            margin-top: 8px !important;
            margin-bottom: 8px !important;
            display: flex !important;
            flex-direction: column !important;
        }}
        .stApp:has(.sr-scene) [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {{
            flex: 1 1 0% !important; min-height: 0 !important; gap: 0 !important;
        }}
        .stApp:has(.sr-scene) [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:has(.sr-scene) {{
            flex: 1 1 0% !important; min-height: 0 !important;
            display: flex !important; flex-direction: column !important; align-items: stretch !important;
        }}
        .stApp:has(.sr-scene) [data-testid="stHorizontalBlock"]:has(.sr-scene) {{
            flex: 1 1 0% !important; min-height: 0 !important; align-items: stretch !important;
        }}
        .stApp:has(.sr-scene) [data-testid="stHorizontalBlock"]:has(.sr-scene) > [data-testid="stColumn"] {{
            min-height: 0 !important;
        }}
        .stApp:has(.sr-scene) [data-testid="stHorizontalBlock"]:has(.sr-scene) > [data-testid="stColumn"]:nth-of-type(1) {{
            overflow: hidden !important;
        }}
        /* Hero fills its (fixed) column: resolve .sr-scene's height:100%. */
        .stApp:has(.sr-scene) [data-testid="stColumn"]:has(.sr-scene) :is([data-testid="stVerticalBlock"], [data-testid="stElementContainer"], [data-testid="stMarkdown"], [data-testid="stMarkdown"] > div, [data-testid="stMarkdownContainer"]):has(.sr-scene) {{
            height: 100% !important; min-height: 0 !important; margin-bottom: 0 !important;
        }}
        /* Form panel scrolls inside the card; auto margins centre it when it fits
           (justify-content:center on a scroller would cut off the top).
           Scrollbar is hidden as a silent safety net. */
        .stApp:has(.sr-scene) [data-testid="stHorizontalBlock"]:has(.sr-scene) > [data-testid="stColumn"]:nth-of-type(2) {{
            overflow-y: auto !important; overflow-x: hidden !important;
            overscroll-behavior: contain;
            justify-content: flex-start !important;
            scrollbar-width: none !important;
            -ms-overflow-style: none !important;
        }}
        .stApp:has(.sr-scene) [data-testid="stHorizontalBlock"]:has(.sr-scene) > [data-testid="stColumn"]:nth-of-type(2)::-webkit-scrollbar {{
            display: none !important;
        }}
        .stApp:has(.sr-scene) [data-testid="stHorizontalBlock"]:has(.sr-scene) > [data-testid="stColumn"]:nth-of-type(2) > [data-testid="stVerticalBlock"] {{
            flex: 0 0 auto !important; margin-top: auto !important; margin-bottom: auto !important;
        }}
        /* Message & hint slots: take natural height when showing content.
           When empty, the slot and its wrapper element are display:none so they
           take zero space and zero flex gap. */
        .stApp:has(.sr-scene) [data-testid="stLayoutWrapper"]:has(> .st-key-sr_msg_slot:empty),
        .stApp:has(.sr-scene) .st-key-sr_msg_slot:empty,
        .stApp:has(.sr-scene) [data-testid="stLayoutWrapper"]:has(> .st-key-sr_hint_slot:empty),
        .stApp:has(.sr-scene) .st-key-sr_hint_slot:empty {{
            display: none !important;
        }}
        /* When showing content, restore the gap below the slot matching the clean-state
           gap below the subtitle (.sr-formhead margin-bottom: clamp(10px, 1.6vh, 18px)). */
        .stApp:has(.sr-scene) [data-testid="stLayoutWrapper"]:has(> .st-key-sr_msg_slot:not(:empty)),
        .stApp:has(.sr-scene) [data-testid="stLayoutWrapper"]:has(> .st-key-sr_hint_slot:not(:empty)) {{
            margin-bottom: clamp(10px, 1.6vh, 18px) !important;
        }}
        .stApp:has(.sr-scene) .st-key-sr_msg_slot .login-note {{ margin: 0 !important; padding: 8px 12px; line-height: 1.35; }}
        .stApp:has(.sr-scene) .st-key-sr_hint_slot .sr-hint {{ margin: 0 !important; line-height: 18px; }}
        /* Cookie/JS bridge iframes: out of flow, still in the DOM and running
           (never display:none). */
        .stApp:has(.sr-scene) [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(iframe) {{
            display: block !important; position: absolute !important; top: 0; left: 0;
            width: 100% !important; height: 0 !important; overflow: hidden !important; pointer-events: none;
        }}
        /* Stacked (phone/tablet): the hero becomes a fixed-height, top-anchored
           banner (its overflow:hidden crops the lower chart/KPIs); the form gets
           the rest of the card and scrolls inside it. */
        @media (max-width: 900px) {{
            .stApp:has(.sr-scene) [data-testid="stHorizontalBlock"]:has(.sr-scene) {{
                flex-direction: column !important; flex-wrap: nowrap !important; row-gap: 0 !important;
            }}
            .stApp:has(.sr-scene) [data-testid="stHorizontalBlock"]:has(.sr-scene) > [data-testid="stColumn"]:nth-of-type(1) {{
                flex: 0 0 auto !important;
                height: clamp(200px, 38vh, 340px) !important;
                height: clamp(200px, 38dvh, 340px) !important;
            }}
            .stApp:has(.sr-scene) [data-testid="stHorizontalBlock"]:has(.sr-scene) > [data-testid="stColumn"]:nth-of-type(2) {{
                flex: 1 1 0% !important; height: auto !important;
            }}
            .stApp:has(.sr-scene) .sr-scene {{ justify-content: flex-start; }}
        }}{v2_css}
    </style>
    """, unsafe_allow_html=True)


def _inject_entrance_styles(play=True):
    """Play-once entrance choreography — emitted only on the first render of the
    session. On later reruns it is not injected, so everything renders settled
    (no replay on failed login / theme toggle / mode switch).

    The markdown slot itself is emitted on EVERY run (an empty <style> after the
    first) so every element below keeps the same position between reruns.
    Streamlit matches elements by position: a slot that comes and goes makes it
    rebuild the page and show the previous copy below it until the run ends."""
    if not play:
        st.markdown("<style></style>", unsafe_allow_html=True)
        return
    st.markdown("""
    <style>
    @media (prefers-reduced-motion: no-preference) {
        .block-container { animation: sr-panel-in 0.85s cubic-bezier(0.22,1,0.36,1) both; }
        @keyframes sr-panel-in {
            from { opacity: 0; transform: translateY(22px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        .sr-scene > * { animation: sr-rise 0.6s cubic-bezier(0.22,1,0.36,1) both; }
        .sr-scene > *:nth-child(1) { animation-delay: 0.15s; }
        .sr-scene > *:nth-child(2) { animation-delay: 0.24s; }
        .sr-scene > *:nth-child(3) { animation-delay: 0.33s; }
        .sr-scene > *:nth-child(4) { animation-delay: 0.42s; }
        .sr-scene > *:nth-child(5) { animation-delay: 0.51s; }
        .sr-scene > *:nth-child(6) { animation-delay: 0.60s; }
        .sr-scene > *:nth-child(7) { animation-delay: 0.72s; }
        [data-testid="stForm"], .sr-formhead { animation: sr-rise 0.6s cubic-bezier(0.22,1,0.36,1) both; }
        .sr-formhead { animation-delay: 0.20s; }
        [data-testid="stForm"] { animation-delay: 0.34s; }
        @keyframes sr-rise {
            from { opacity: 0; transform: translateY(14px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        /* Curve self-draw, then area fade, then playhead fade */
        #sr-path { stroke-dasharray: 1600; stroke-dashoffset: 1600;
                   animation: sr-draw 1.5s 0.6s ease-out forwards; }
        @keyframes sr-draw { to { stroke-dashoffset: 0; } }
        #sr-area { opacity: 0; animation: sr-fade 0.8s 1.9s ease-out forwards; }
        .sr-playhead, .sr-tip { opacity: 0; animation: sr-fade 0.6s 2.1s ease-out forwards; }
        @keyframes sr-fade { to { opacity: 1; } }
    }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Static HTML blocks
# ─────────────────────────────────────────────────────────────────────────────

def _scene_html():
    """The always-dark left showcase — one single markdown block."""
    # Everything below is constant for the process (not theme- or session-dependent)
    # so the hero never remounts. With the switch off every v2 piece is '' and the
    # string is byte-identical to the pre-v2 page.
    v2 = _ui_v2_enabled()
    scene_open = '<div class="sr-scene sr-v2">' if v2 else '<div class="sr-scene">'
    card_open = _V2_CHART_CARD_OPEN if v2 else ''
    card_close = '</div>' if v2 else ''
    best_window = _V2_BEST_WINDOW if v2 else 'Friday, 6 PM.'
    return (
        scene_open +
        '<div class="sr-top">'
        '<span class="sr-eyebrow">YouTube Analytics</span>'
        '<span class="sr-live"><span class="sr-live-dot"></span>LIVE · CHANNEL PULSE</span>'
        '</div>'
        '<h1 class="sr-h1">Know what your <span class="sr-grad">audience</span> actually watches.</h1>'
        '<p class="sr-sub">Retention, engagement and revenue for every video'
        ' — decoded into decisions, in one dashboard.</p>' +
        card_open +
        '<div class="sr-chartwrap">'
        '<svg class="sr-chart" viewBox="0 0 560 210" preserveAspectRatio="none" aria-hidden="true">'
        '<defs>'
        '<linearGradient id="sr-stroke" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#A78BFA"/>'
        '<stop offset="0.6" stop-color="#7C3AED"/>'
        '<stop offset="1" stop-color="#5B6CFF"/>'
        '</linearGradient>'
        '<linearGradient id="sr-fill" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="rgba(124,58,237,0.35)"/>'
        '<stop offset="1" stop-color="rgba(124,58,237,0)"/>'
        '</linearGradient>'
        '</defs>'
        '<g stroke="rgba(167,139,250,0.10)" stroke-width="1">'
        '<line x1="0" y1="45" x2="560" y2="45"/>'
        '<line x1="0" y1="90" x2="560" y2="90"/>'
        '<line x1="0" y1="135" x2="560" y2="135"/>'
        '<line x1="0" y1="180" x2="560" y2="180"/>'
        '</g>'
        '<path id="sr-area" fill="url(#sr-fill)"'
        ' d="M0,55 C30,44 45,38 70,34 S110,28 130,32 S180,48 210,58 S260,72 300,64 S350,80 380,84 S440,76 470,90 S540,106 560,110 L560,210 L0,210 Z"/>'
        '<path id="sr-path" fill="none" stroke="url(#sr-stroke)" stroke-width="2.5"'
        ' stroke-linecap="round" stroke-linejoin="round"'
        ' d="M0,55 C30,44 45,38 70,34 S110,28 130,32 S180,48 210,58 S260,72 300,64 S350,80 380,84 S440,76 470,90 S540,106 560,110"/>'
        '</svg>'
        '<div class="sr-playhead" id="sr-playhead"></div>'
        '<div class="sr-ph-dot" id="sr-phdot"></div>'
        '<div class="sr-tip" id="sr-phtip"><b>0:42</b> · 84% watching</div>'
        '<div class="sr-timeline">'
        '<div class="sr-track">'
        '<div class="sr-progress" id="sr-prog"></div>'
        '<div class="sr-tick" style="left:22%"></div>'
        '<div class="sr-tick" style="left:47%"></div>'
        '<div class="sr-tick" style="left:74%"></div>'
        '</div>'
        '<div class="sr-times"><span class="sr-cur" id="sr-tnow">0:00</span><span>3:00</span></div>'
        '</div>'
        '</div>' +
        card_close +
        '<div class="sr-kpis">'
        '<div class="sr-kpi">'
        '<div class="sr-kpi-val"><span class="sr-num" data-target="2400000" data-kind="views" data-delay="0">0.0M</span></div>'
        '<div class="sr-kpi-label">Total views</div>'
        '</div>'
        '<div class="sr-kpi">'
        '<div class="sr-kpi-val"><span class="sr-num" data-target="98000" data-kind="subs" data-delay="150">0K</span></div>'
        '<div class="sr-kpi-label">Subscribers</div>'
        '</div>'
        '<div class="sr-kpi">'
        '<div class="sr-kpi-val"><span class="sr-num" data-target="12.4" data-kind="pct" data-delay="300">+0.0%</span> <span class="up">▲</span></div>'
        '<div class="sr-kpi-label">Engagement</div>'
        '</div>'
        '</div>'
        '<div class="sr-captions">'
        '<span>Retention peaks at the 0:42 hook — repeat it earlier.</span>'
        '<span>Shorts bring 3.1× more new subscribers than long-form.</span>'
        '<span>Best upload window for this channel: ' + best_window + '</span>'
        '</div>'
        '</div>'
    )


def _form_header_html(title, subtitle):
    play = ('<svg width="20" height="20" viewBox="0 0 24 24" fill="#fff" aria-hidden="true">'
            '<path d="M8 5v14l11-7z"/></svg>')
    return (
        f'<div class="sr-formhead">'
        f'<div class="sr-logo">{play}</div>'
        f'<h2 class="sr-formtitle">{title}</h2>'
        f'<p class="sr-formsub">{subtitle}</p>'
        f'</div>'
    )


def _legal_links_html():
    """Links to the public /privacy and /terms pages (served by nginx, not Streamlit)."""
    new_tab = '<span class="sr-visually-hidden"> (opens in a new tab)</span>'
    return (
        '<p class="sr-legal">By continuing, you agree to our '
        f'<a href="/terms" target="_blank" rel="noopener">Terms of Service{new_tab}</a>'
        ' and confirm you have read our '
        f'<a href="/privacy" target="_blank" rel="noopener">Privacy Policy{new_tab}</a>.</p>'
    )


def _show_messages():
    with st.container(border=False, key="sr_msg_slot"):
        if st.session_state.get('login_error'):
            st.markdown(f'<div class="login-note login-err">{escape(str(st.session_state["login_error"]))}</div>',
                        unsafe_allow_html=True)
            st.session_state['login_error'] = ''
        if st.session_state.get('login_success'):
            st.markdown(f'<div class="login-note login-ok">{escape(str(st.session_state["login_success"]))}</div>',
                        unsafe_allow_html=True)
            st.session_state['login_success'] = ''


# ─────────────────────────────────────────────────────────────────────────────
# Form sides
# ─────────────────────────────────────────────────────────────────────────────

def _switch_mode(mode):
    st.session_state['login_mode'] = mode
    st.session_state['login_error'] = ''
    st.session_state['login_success'] = ''
    st.rerun()


def _render_google_option():
    """"Continue with Google" (Neon Auth) + "or" divider, above the email form."""
    redirect = pending_google_redirect()
    with st.container(border=False, key="sr_hint_slot"):
        if redirect:
            st.markdown(
                '<p class="sr-hint">Opening Google… If nothing happens, '
                f'<a href="{escape(redirect, quote=True)}" target="_self">continue to Google</a>.</p>',
                unsafe_allow_html=True)
    enabled = google_available()
    if st.button("Continue with Google", key="google_btn", disabled=not enabled or bool(redirect)):
        start_google_sign_in()
        st.rerun()
    if not enabled:
        st.markdown('<p class="sr-hint">Google sign-in is coming soon.</p>', unsafe_allow_html=True)
    st.markdown('<div class="login-divider"><span>or</span></div>', unsafe_allow_html=True)


def _render_login_side():
    st.markdown(_form_header_html("Welcome", "Sign in to your analytics dashboard"),
                unsafe_allow_html=True)
    _show_messages()
    _render_google_option()

    with st.form("login_form", border=False):
        email = st.text_input("Email", placeholder="you@example.com", key="login_email",
                              max_chars=255, autocomplete="email")
        password = st.text_input("Password", placeholder="Your password", type="password",
                                 key="login_password", max_chars=128,
                                 autocomplete="current-password")
        submitted = st.form_submit_button("Sign in", type="primary")

    if submitted:
        if email and password:
            success, message = login(email, password)
            if not success:
                st.session_state['login_error'] = message
        else:
            st.session_state['login_error'] = "Enter your email and password."
        st.rerun()

    st.markdown('<div class="login-divider"><span>new here</span></div>', unsafe_allow_html=True)

    # Real, visible button (styled as a centered link) — switches to sign-up.
    if st.button("Create a free account — Sign up", key="switch_to_signup"):
        _switch_mode('signup')

    st.markdown(_legal_links_html(), unsafe_allow_html=True)


def _render_signup_side():
    st.markdown(_form_header_html("Create your account", "Free — no credit card needed"),
                unsafe_allow_html=True)
    _show_messages()

    with st.form("signup_form", border=False):
        display_name = st.text_input("Display name", placeholder="Your name", key="signup_name",
                                     max_chars=100, autocomplete="name")
        email = st.text_input("Email", placeholder="you@example.com", key="signup_email",
                              max_chars=255, autocomplete="email")
        password = st.text_input("Password", placeholder="Min 10 characters", type="password",
                                 key="signup_password", max_chars=72,
                                 autocomplete="new-password")
        confirm = st.text_input("Confirm password", placeholder="Re-enter password",
                                type="password", key="signup_confirm", max_chars=72,
                                autocomplete="new-password")
        submitted = st.form_submit_button("Create account", type="primary")

    if submitted:
        if not all([email, password, confirm]):
            st.session_state['login_error'] = "Fill in all fields."
        elif password != confirm:
            st.session_state['login_error'] = "Passwords do not match."
        else:
            success, message = register_user(email, password, display_name)
            if success:
                st.session_state['login_success'] = message
                st.session_state['login_mode'] = 'login'
            else:
                st.session_state['login_error'] = message
        st.rerun()

    st.markdown('<div class="login-divider"><span>or</span></div>', unsafe_allow_html=True)

    if st.button("Already have an account? Sign in", key="switch_to_login"):
        _switch_mode('login')

    st.markdown(_legal_links_html(), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# JS bridge — chart scrub, panel tilt, light reflection, KPI count-up.
# Rendered LAST, in a height:0 iframe whose slot is collapsed via CSS.
# ─────────────────────────────────────────────────────────────────────────────

_JS_BODY = r"""
<script>
(function () {
  const P = window.parent;
  const doc = P.document;
  const reduce = P.matchMedia && P.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const coarse = P.matchMedia && P.matchMedia('(pointer: coarse)').matches;

  function fmt(kind, v) {
    if (kind === 'views') return (v / 1e6).toFixed(1) + 'M';
    if (kind === 'subs')  return Math.round(v / 1e3) + 'K';
    return '+' + v.toFixed(1) + '%';
  }
  function mmss(sec) {
    sec = Math.max(0, Math.min(180, sec));
    const m = Math.floor(sec / 60), s = Math.floor(sec % 60);
    return m + ':' + (s < 10 ? '0' + s : s);
  }

  let tries = 0;
  function boot() {
    const scene = doc.querySelector('.sr-scene');
    const bc = doc.querySelector('.block-container');
    if (!scene || !bc) { if (tries++ < 20) setTimeout(boot, 120); return; }
    init(scene, bc);
  }

  function init(scene, bc) {
    // ---- rerun-safe teardown of any previous instance ----
    if (P.__srLoginFx) {
      try { cancelAnimationFrame(P.__srLoginFx.raf); } catch (e) {}
      (P.__srLoginFx.cleanup || []).forEach(function (fn) { try { fn(); } catch (e) {} });
    }
    const fx = P.__srLoginFx = { raf: 0, cleanup: [] };
    function on(el, ev, fn, opts) { el.addEventListener(ev, fn, opts); fx.cleanup.push(function () { el.removeEventListener(ev, fn, opts); }); }

    // ---- KPI count-up (once) ----
    scene.querySelectorAll('.sr-num').forEach(function (el) {
      const target = parseFloat(el.dataset.target);
      const kind = el.dataset.kind;
      const delay = parseFloat(el.dataset.delay || '0');
      if (!P.__srFirstRender || reduce) { el.textContent = fmt(kind, target); return; }
      const dur = 1500, start = performance.now();
      function tick(now) {
        let p = (now - start - delay) / dur;
        if (p < 0) { requestAnimationFrame(tick); return; }
        if (p > 1) p = 1;
        const e = 1 - Math.pow(1 - p, 3);
        el.textContent = fmt(kind, target * e);
        if (p < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    });

    // ---- Chart scrub ----
    const wrap = scene.querySelector('.sr-chartwrap');
    const svg  = scene.querySelector('.sr-chart');
    const path = scene.querySelector('#sr-path');
    const ph   = doc.querySelector('#sr-playhead');
    const dot  = doc.querySelector('#sr-phdot');
    const tip  = doc.querySelector('#sr-phtip');
    const prog = doc.querySelector('#sr-prog');
    const cur  = doc.querySelector('#sr-tnow');

    if (!wrap || !svg || !path || !ph || !dot || !tip || !prog || !cur) return;

    let pathLen = 0;
    try { pathLen = path.getTotalLength(); } catch (e) {}

    function pointAtX(xFrac) {
      if (!pathLen) return { x: xFrac * 560, y: 100 };
      var targetX = xFrac * 560;
      var lo = 0, hi = pathLen;
      for (var i = 0; i < 18; i++) {
        var mid = (lo + hi) / 2;
        if (path.getPointAtLength(mid).x < targetX) lo = mid; else hi = mid;
      }
      return path.getPointAtLength((lo + hi) / 2);
    }

    function place(frac) {
      frac = Math.max(0, Math.min(1, frac));
      var p = pointAtX(frac);
      var r = svg.getBoundingClientRect();
      var px = (p.x / 560) * r.width;
      var py = (p.y / 210) * r.height;
      ph.style.left = px + 'px';
      dot.style.left = px + 'px';
      dot.style.top = py + 'px';
      tip.style.left = px + 'px';
      tip.style.top = py + 'px';
      var secs = Math.round(frac * 180);
      var mm = Math.floor(secs / 60), ss = String(secs % 60).padStart(2, '0');
      var pct = Math.max(0, Math.min(100, Math.round(((210 - p.y) / 190) * 100)));
      tip.innerHTML = '<b>' + mm + ':' + ss + '</b> · ' + pct + '% watching';
      prog.style.width = (frac * 100) + '%';
      cur.textContent = mm + ':' + ss;
    }

    let manual = false, sweepStart = performance.now();
    if (reduce) {
      place(0.42);
    } else {
      place(0.42);
      on(wrap, 'mousemove', function (e) {
        manual = true;
        const rect = svg.getBoundingClientRect();
        place((e.clientX - rect.left) / rect.width);
      });
      on(wrap, 'touchmove', function (e) {
        if (!e.touches.length) return;
        manual = true;
        const rect = svg.getBoundingClientRect();
        place((e.touches[0].clientX - rect.left) / rect.width);
      }, { passive: true });
      on(wrap, 'mouseleave', function () { manual = false; sweepStart = performance.now(); });
    }

    // Panel tilt + cursor-follow light reflection removed (no hover wobble).

    // ---- single rAF loop: chart auto-sweep only ----
    function loop(now) {
      if (!reduce && !manual) {
        const frac = ((now - sweepStart) % 14000) / 14000;
        place(frac);
      }
      fx.raf = requestAnimationFrame(loop);
    }
    fx.raf = requestAnimationFrame(loop);
  }

  boot();
})();
</script>
"""


def _js_bridge(first_render):
    flag = 'window.parent.__srFirstRender = %s;' % ('true' if first_render else 'false')
    js = '<script>%s</script>' % flag + _JS_BODY
    # The iframe slot is taken out of flow (position:absolute; height:0) by the
    # FIXED-HEIGHT CARD rules, never display:none, so the script keeps running.
    # The empty markdown keeps this element slot so positions stay the same.
    st.markdown("<style></style>", unsafe_allow_html=True)
    components.html(js, height=0)


# ─────────────────────────────────────────────────────────────────────────────
# Render
# ─────────────────────────────────────────────────────────────────────────────

def render_login_page():
    """Render the "Signal Room" login / signup page."""
    # Theme-aware: the LEFT scene stays an always-dark product screenshot, while
    # the page background + RIGHT form side follow the active theme. The toggle
    # (below) is re-pinned to the panel's top-right corner in _inject_login_styles.
    mode = theme_tokens.resolve_mode()
    _inject_login_styles(mode)

    # Sun/moon theme toggle — same global button, repositioned inside the panel.
    theme_tokens.inject_theme_toggle()

    if 'login_mode' not in st.session_state:
        st.session_state['login_mode'] = 'login'

    # Play the entrance once per session; reruns render everything settled.
    first_render = not st.session_state.get('_login_entered')
    _inject_entrance_styles(play=first_render)   # same slot every run (see docstring)
    st.session_state['_login_entered'] = True

    left, right = st.columns([11, 9], gap="large")
    with left:
        st.markdown(_scene_html(), unsafe_allow_html=True)
    with right:
        if st.session_state['login_mode'] == 'login':
            _render_login_side()
        else:
            _render_signup_side()

    # JS bridge last, so its targets already exist in the DOM.
    _js_bridge(first_render)
