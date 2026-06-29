"""
Login / signup page — clean premium violet.

No WebGL, no particle JS, no spinning crystal. A quiet, centered glass-light
card on a soft violet wash. Follows the system theme like the rest of the app.
"""
import streamlit as st
from auth import login, register_user
from dashboard import theme as theme_tokens


# ─────────────────────────────────────────────────────────────────────────────
# Styles
# ─────────────────────────────────────────────────────────────────────────────

def _inject_login_styles(mode='light'):
    t = theme_tokens.get_tokens(mode)
    is_dark = mode == 'dark'
    glow_1 = 'rgba(124,58,237,0.18)' if is_dark else 'rgba(124,58,237,0.12)'
    glow_2 = 'rgba(91,108,255,0.14)' if is_dark else 'rgba(232,99,155,0.10)'
    card_bg = t['bg_card']
    card_border = t['border_strong']
    # Hexagon texture — violet honeycomb, theme-tuned. Base bg color stays the same.
    hex_fill = 'A78BFA' if is_dark else '7C3AED'
    hex_op = '0.40' if is_dark else '0.28'
    # Frosted-glass card behind the form — legibility over the busy hex pattern
    panel_bg = 'rgba(26,20,38,0.72)' if is_dark else 'rgba(255,255,255,0.78)'
    panel_shadow = ('0 24px 60px rgba(0,0,0,0.55)' if is_dark
                    else '0 24px 60px rgba(79,70,229,0.14)')

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

        [data-testid="stSidebar"], [data-testid="collapsedControl"] {{ display: none !important; }}
        #MainMenu, footer, header {{ visibility: hidden; }}

        .stApp {{
            isolation: isolate;   /* stacking context for the ::before texture, no layout change */
            background:
                radial-gradient(42% 38% at 18% 22%, {glow_1}, transparent 70%),
                radial-gradient(40% 36% at 82% 78%, {glow_2}, transparent 70%),
                {t['bg_page']} !important;
            font-family: 'Inter', sans-serif;
        }}
        /* Hexagon Pattern texture — honeycomb tile, radial-masked + skewed.
           Sits above the glow wash, below the card. Base bg color unchanged. */
        .stApp::before {{
            content: '';
            position: fixed;
            top: -25%; left: -15%;
            width: 130%; height: 150%;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='28' height='49' viewBox='0 0 28 49'%3E%3Cpath fill='%23{hex_fill}' fill-opacity='{hex_op}' fill-rule='evenodd' d='M13.99 9.25l13 7.5v15l-13 7.5L1 31.75v-15l12.99-7.5zM3 17.9v12.7l10.99 6.34 11-6.35V17.9l-11-6.34L3 17.9zM0 15l12.98-7.5V0h-2v6.35L0 12.69v2.3zm0 18.5L12.98 41v8h-2v-6.85L0 35.81v-2.3zM15 0v7.5L27.99 15H28v-2.31h-.01L17 6.35V0h-2zm0 49v-8l12.99-7.5H28v2.31h-.01L17 42.15V49h-2z'/%3E%3C/svg%3E");
            background-size: 40px 70px;
            background-repeat: repeat;
            transform: skewY(-6deg);
            transform-origin: center;
            -webkit-mask: radial-gradient(58% 55% at 50% 40%, #000 0%, rgba(0,0,0,0.85) 38%, transparent 76%);
                    mask: radial-gradient(58% 55% at 50% 40%, #000 0%, rgba(0,0,0,0.85) 38%, transparent 76%);
            pointer-events: none;
            z-index: -1;
        }}
        .block-container {{
            position: relative; z-index: 1;
            max-width: 460px !important;
            margin: 6vh auto 4vh !important;
            padding: 34px 34px 30px !important;
        }}
        /* Frost lives on a pseudo, NOT on .block-container itself —
           backdrop-filter on the container would make it the containing
           block for the fixed theme toggle and trap it inside the card. */
        .block-container::before {{
            content: ''; position: absolute; inset: 0; z-index: -1;
            background: {panel_bg};
            -webkit-backdrop-filter: blur(16px) saturate(115%);
            backdrop-filter: blur(16px) saturate(115%);
            border: 1px solid {card_border};
            border-radius: 22px;
            box-shadow: {panel_shadow};
        }}

        .login-brand {{ text-align: center; margin-bottom: 6px; }}
        .login-mark {{
            width: 54px; height: 54px; margin: 0 auto 16px;
            border-radius: 15px;
            background: linear-gradient(135deg, {t['brand']}, {t['brand_hover']});
            display: flex; align-items: center; justify-content: center;
            font-size: 1.7rem;
            box-shadow: 0 10px 26px {t['focus_ring']};
        }}
        .login-title {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.55rem; font-weight: 700; letter-spacing: -0.02em;
            color: {t['text_primary']}; text-align: center; margin: 0;
        }}
        .login-sub {{
            font-family: 'Inter', sans-serif; font-size: 0.88rem;
            color: {t['text_secondary']}; text-align: center; margin: 8px 0 24px;
        }}
        .login-eyebrow {{
            display: block; text-align: center;
            font-size: 0.68rem; font-weight: 600; letter-spacing: 0.16em;
            text-transform: uppercase; color: {t['brand']}; margin-bottom: 10px;
        }}

        /* Card = the form container */
        .stApp .block-container [data-testid="stVerticalBlock"] {{ gap: 0.55rem; }}

        .stApp .block-container .stTextInput > div > div > input {{
            background: {t['input_bg']} !important;
            border: 1px solid {t['input_border']} !important;
            border-radius: 11px !important;
            color: {t['text_body']} !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.94rem !important;
            padding: 13px 16px !important;
            height: auto !important;
        }}
        .stApp .block-container .stTextInput > div > div > input:focus {{
            border-color: {t['brand']} !important;
            box-shadow: 0 0 0 3px {t['focus_ring']} !important;
        }}
        .stApp .block-container .stTextInput > label {{
            color: {t['text_secondary']} !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.8rem !important; font-weight: 500 !important;
        }}

        .stApp .block-container .stButton > button {{
            width: 100% !important;
            background: {t['brand']} !important;
            border: 1px solid {t['brand']} !important;
            border-radius: 11px !important;
            color: {t['brand_on']} !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.96rem !important; font-weight: 600 !important;
            padding: 12px 22px !important;
            box-shadow: 0 6px 18px {t['focus_ring']} !important;
            transition: all 0.18s ease !important;
        }}
        .stApp .block-container .stButton > button:hover {{
            background: {t['brand_hover']} !important;
            border-color: {t['brand_hover']} !important;
            transform: translateY(-1px) !important;
        }}
        /* secondary (switch mode) button */
        .stApp .block-container .stButton > button[kind="secondary"] {{
            background: transparent !important;
            color: {t['brand']} !important;
            border: 1px solid {t['input_border']} !important;
            box-shadow: none !important;
        }}
        .stApp .block-container .stButton > button[kind="secondary"]:hover {{
            background: {t['brand_soft']} !important;
            border-color: {t['brand']} !important;
        }}

        .login-chip {{
            background: {t['brand_soft']};
            border: 1px solid {card_border};
            border-radius: 11px; padding: 11px 14px;
            font-family: 'Inter', sans-serif; font-size: 0.78rem;
            color: {t['text_secondary']}; text-align: center; margin-bottom: 18px;
        }}
        .login-chip strong {{ color: {t['brand']}; }}

        .login-note {{
            border-radius: 11px; padding: 11px 14px; margin-bottom: 14px;
            font-family: 'Inter', sans-serif; font-size: 0.84rem;
        }}
        .login-err {{ background: rgba(220,38,38,0.10); border: 1px solid rgba(220,38,38,0.30); color: {t['neg']}; }}
        .login-ok  {{ background: rgba(22,163,74,0.10); border: 1px solid rgba(22,163,74,0.30); color: {t['pos']}; }}

        .login-divider {{
            display: flex; align-items: center; gap: 14px; margin: 20px 0 14px;
        }}
        .login-divider::before, .login-divider::after {{
            content: ''; flex: 1; height: 1px; background: {t['divider']};
        }}
        .login-divider span {{
            font-size: 0.72rem; color: {t['text_faint']};
            text-transform: uppercase; letter-spacing: 0.1em;
        }}

        @media (prefers-reduced-motion: reduce) {{
            * {{ transition-duration: 0.01ms !important; }}
        }}
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Render
# ─────────────────────────────────────────────────────────────────────────────

def _show_messages():
    if st.session_state.get('login_error'):
        st.markdown(f'<div class="login-note login-err">{st.session_state["login_error"]}</div>',
                    unsafe_allow_html=True)
        st.session_state['login_error'] = ''
    if st.session_state.get('login_success'):
        st.markdown(f'<div class="login-note login-ok">{st.session_state["login_success"]}</div>',
                    unsafe_allow_html=True)
        st.session_state['login_success'] = ''


def render_login_page():
    """Render the clean login / signup page."""
    _inject_login_styles(theme_tokens.resolve_mode())

    # Theme toggle — injected globally
    theme_tokens.inject_theme_toggle()

    if 'login_mode' not in st.session_state:
        st.session_state['login_mode'] = 'login'

    if st.session_state['login_mode'] == 'login':
        st.markdown("""
        <div class="login-brand">
            <div class="login-mark">📊</div>
        </div>
        <span class="login-eyebrow">YouTube Analytics</span>
        <h1 class="login-title">Welcome back</h1>
        <p class="login-sub">Sign in to your analytics dashboard</p>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="login-chip">
            Demo &nbsp;·&nbsp; <strong>demo@youtube.com</strong> &nbsp;/&nbsp; <strong>demo123</strong>
        </div>
        """, unsafe_allow_html=True)

        _show_messages()

        email = st.text_input("Email", placeholder="you@example.com", key="login_email")
        password = st.text_input("Password", placeholder="Your password",
                                 type="password", key="login_password")

        if st.button("Sign in", key="login_btn", type="primary"):
            if email and password:
                success, message = login(email, password)
                if success:
                    st.rerun()
                else:
                    st.session_state['login_error'] = message
                    st.rerun()
            else:
                st.session_state['login_error'] = "Enter your email and password."
                st.rerun()

        st.markdown('<div class="login-divider"><span>new here</span></div>', unsafe_allow_html=True)

        if st.button("Create an account", key="switch_to_signup", type="secondary"):
            st.session_state['login_mode'] = 'signup'
            st.session_state['login_error'] = ''
            st.session_state['login_success'] = ''
            st.rerun()

    else:
        st.markdown("""
        <div class="login-brand">
            <div class="login-mark">🚀</div>
        </div>
        <span class="login-eyebrow">Get started</span>
        <h1 class="login-title">Create account</h1>
        <p class="login-sub">Free — no credit card needed</p>
        """, unsafe_allow_html=True)

        _show_messages()

        display_name = st.text_input("Display name", placeholder="Your name", key="signup_name")
        email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
        password = st.text_input("Password", placeholder="Min 5 characters",
                                 type="password", key="signup_password")
        confirm = st.text_input("Confirm password", placeholder="Re-enter password",
                                type="password", key="signup_confirm")

        if st.button("Create account", key="signup_btn", type="primary"):
            if not all([email, password, confirm]):
                st.session_state['login_error'] = "Fill in all fields."
                st.rerun()
            elif password != confirm:
                st.session_state['login_error'] = "Passwords do not match."
                st.rerun()
            else:
                success, message = register_user(email, password, display_name)
                if success:
                    st.session_state['login_success'] = message
                    st.session_state['login_mode'] = 'login'
                    st.rerun()
                else:
                    st.session_state['login_error'] = message
                    st.rerun()

        st.markdown('<div class="login-divider"><span>or</span></div>', unsafe_allow_html=True)

        if st.button("Back to sign in", key="switch_to_login", type="secondary"):
            st.session_state['login_mode'] = 'login'
            st.session_state['login_error'] = ''
            st.session_state['login_success'] = ''
            st.rerun()
