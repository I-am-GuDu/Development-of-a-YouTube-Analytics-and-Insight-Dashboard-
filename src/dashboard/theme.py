"""
Theme tokens — single source of truth for all colors.

Premium violet "creator console" palette. Light mode is the premium base;
dark mode is an equal-quality violet-black counterpart.

Replaces the three duplicated color maps that used to live in
main.py, charts.py and effects_3d.py.
"""
import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# Shared viz ramp (works on both light and dark cards)
# ─────────────────────────────────────────────────────────────────────────────
VIZ_RAMP = ['#7C3AED', '#5B6CFF', '#2D9CDB', '#22B8A6', '#E8639B', '#F59E0B']

DONUT_PALETTE_DARK = ['#A78BFA', '#818CF8', '#38BDF8', '#2DD4BF', '#F472B6', '#FBBF24', '#C084FC', '#60A5FA']
DONUT_PALETTE_LIGHT = ['#7C3AED', '#5B6CFF', '#2D9CDB', '#14B8A6', '#DB2777', '#D97706', '#9333EA', '#2563EB']


# ─────────────────────────────────────────────────────────────────────────────
# Token maps
# ─────────────────────────────────────────────────────────────────────────────

_LIGHT = {
    'mode': 'light',
    # surfaces
    'bg_page': '#F6F4FB',
    'bg_card': '#FFFFFF',
    'bg_card_hover': '#FBFAFE',
    'bg_sidebar': '#F1ECF9',
    'bg_subtle': '#EFEAF8',
    # lines
    'border': '#E6E0F2',
    'border_strong': '#D6CCEC',
    'divider': '#ECE6F6',
    'grid': 'rgba(26,20,38,0.06)',
    # text
    'text_primary': '#1A1426',
    'text_secondary': '#6B6480',
    'text_body': '#2A2435',
    'text_faint': '#9A93AC',
    # brand
    'brand': '#7C3AED',
    'brand_hover': '#6D28D9',
    'brand_soft': '#EDE7FF',
    'brand_on': '#FFFFFF',
    'focus_ring': 'rgba(124,58,237,0.25)',
    # state
    'pos': '#16A34A',
    'neg': '#DC2626',
    # inputs
    'input_bg': '#FFFFFF',
    'input_border': '#DDD5EE',
    # scrollbar
    'scrollbar_track': '#F1ECF9',
    'scrollbar_thumb': '#CDBFEA',
    # viz
    'viz': VIZ_RAMP,
    'donut': DONUT_PALETTE_LIGHT,
    'chart_line': '#7C3AED',
    'chart_fill': 'rgba(124,58,237,0.14)',
    'chart_bar': 'rgba(124,58,237,0.55)',
    'plot_bg': 'rgba(0,0,0,0)',
    'template': 'plotly_white',
    'heat_low': '#EDE7FF',
}

_DARK = {
    'mode': 'dark',
    # surfaces
    'bg_page': '#0E0A16',
    'bg_card': '#1A1426',
    'bg_card_hover': '#221A33',
    'bg_sidebar': '#140F1F',
    'bg_subtle': '#241B36',
    # lines
    'border': 'rgba(167,139,250,0.16)',
    'border_strong': 'rgba(167,139,250,0.28)',
    'divider': 'rgba(167,139,250,0.12)',
    'grid': 'rgba(245,242,250,0.06)',
    # text
    'text_primary': '#F5F2FA',
    'text_secondary': '#A39CB5',
    'text_body': '#E4DFEE',
    'text_faint': '#736B85',
    # brand
    'brand': '#A78BFA',
    'brand_hover': '#B9A3FC',
    'brand_soft': 'rgba(167,139,250,0.14)',
    'brand_on': '#140F1F',
    'focus_ring': 'rgba(167,139,250,0.30)',
    # state
    'pos': '#34D399',
    'neg': '#F87171',
    # inputs
    'input_bg': '#221A33',
    'input_border': 'rgba(167,139,250,0.22)',
    # scrollbar
    'scrollbar_track': '#140F1F',
    'scrollbar_thumb': '#3A2F52',
    # viz
    'viz': VIZ_RAMP,
    'donut': DONUT_PALETTE_DARK,
    'chart_line': '#A78BFA',
    'chart_fill': 'rgba(167,139,250,0.20)',
    'chart_bar': 'rgba(167,139,250,0.55)',
    'plot_bg': 'rgba(0,0,0,0)',
    'template': 'plotly_dark',
    'heat_low': '#1E1730',
}


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def get_tokens(mode: str = None):
    """Return the token dict for a mode ('light' | 'dark').

    If mode is None, resolves the active mode from session/system.
    """
    if mode is None:
        mode = resolve_mode()
    return _DARK if mode == 'dark' else _LIGHT


def system_mode() -> str | None:
    """Read the OS/browser preferred theme via st.context.theme.

    Returns 'dark', 'light', or None when not yet known.
    """
    try:
        t = st.context.theme.type  # 'dark' | 'light' | None
        if t in ('dark', 'light'):
            return t
    except Exception:
        pass
    return None


def resolve_mode() -> str:
    """Resolve the active theme mode.

    Priority: manual override from the corner toggle (session) →
    OS/browser theme → 'light'. Default is auto-follow; the toggle only
    sets a per-session override.
    """
    override = st.session_state.get('theme_override')
    if override in ('dark', 'light'):
        return override
    return system_mode() or 'light'


# ─────────────────────────────────────────────────────────────────────────────
# Global theme toggle (fixed top-right, every page)
# ─────────────────────────────────────────────────────────────────────────────

def _toggle_theme():
    """Callback: flip the per-session manual theme override."""
    st.session_state['theme_override'] = (
        'light' if resolve_mode() == 'dark' else 'dark')


def inject_theme_toggle():
    """Render the fixed top-right animated sun/moon theme toggle.

    Single global utility — call once per page, right after that page's
    style injector. It uses a real Streamlit button so the click stays in
    the same session (auth lives in session_state, so a page reload would
    log the user out) and triggers a normal rerun. That rerun re-resolves
    the mode, so both the injected CSS tokens *and* the server-rendered
    Plotly charts (via get_tokens / charts.get_theme_colors) re-theme.

    Note vs. the React reference: Streamlit sanitizes injected <script>,
    so localStorage / body-class / CustomEvent can't run from st.markdown.
    The session + rerun model is the working equivalent and re-themes
    everything, including charts, which a client-only toggle cannot.
    """
    mode = resolve_mode()
    t = get_tokens(mode)
    is_dark = mode == 'dark'
    icon = '🌙' if is_dark else '☀️'
    next_mode = 'light' if is_dark else 'dark'

    st.markdown(f"""
    <style>
      :root {{
        --toggle-size: 44px;
        --toggle-bg: {t['bg_card']};
        --toggle-border: {t['border_strong']};
        --toggle-fg: {t['brand']};
        --toggle-ring: {t['focus_ring']};
      }}
      /* Pin the toggle's element container to the corner, above all
         Streamlit chrome (header/sidebar/toolbar sit at ~999990). */
      .st-key-theme_toggle_btn {{
        position: fixed !important;
        top: 16px; right: 16px;
        z-index: 1000000;
        width: var(--toggle-size); height: var(--toggle-size);
        margin: 0 !important;
      }}
      .st-key-theme_toggle_btn .stButton {{ margin: 0 !important; width: auto !important; }}
      .st-key-theme_toggle_btn button {{
        width: var(--toggle-size) !important;
        height: var(--toggle-size) !important;
        min-height: var(--toggle-size) !important;
        padding: 0 !important;
        border-radius: 50% !important;
        background: var(--toggle-bg) !important;
        border: 1px solid var(--toggle-border) !important;
        color: var(--toggle-fg) !important;
        font-size: 1.15rem !important; line-height: 1 !important;
        display: flex !important; align-items: center; justify-content: center;
        box-shadow: 0 6px 18px var(--toggle-ring) !important;
        transition: transform .3s ease, background-color .3s ease, border-color .3s ease;
      }}
      .st-key-theme_toggle_btn button:hover {{
        transform: rotate(35deg) scale(1.08);
        border-color: var(--toggle-fg) !important;
      }}
      .st-key-theme_toggle_btn button:active {{ transform: scale(0.94); }}
      .st-key-theme_toggle_btn button:focus-visible {{
        outline: none !important;
        box-shadow: 0 0 0 3px var(--toggle-ring) !important;
      }}
      /* rotate+scale swap when the icon re-renders after a toggle */
      .st-key-theme_toggle_btn button p {{ animation: toggleSwap .3s ease; }}
      @keyframes toggleSwap {{
        from {{ transform: rotate(-90deg) scale(0.5); opacity: 0; }}
        to   {{ transform: rotate(0) scale(1); opacity: 1; }}
      }}
      @media (prefers-reduced-motion: reduce) {{
        .st-key-theme_toggle_btn button,
        .st-key-theme_toggle_btn button:hover,
        .st-key-theme_toggle_btn button p {{
          transition: none !important; animation: none !important; transform: none !important;
        }}
      }}
    </style>
    """, unsafe_allow_html=True)

    st.button(
        icon,
        key='theme_toggle_btn',
        on_click=_toggle_theme,
        help=f'Switch to {next_mode} mode',
    )
