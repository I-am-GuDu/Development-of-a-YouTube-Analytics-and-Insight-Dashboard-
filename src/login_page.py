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
  * Session keys preserved: login_mode, login_error, login_success.
  * No third-party component libs — pure Streamlit widgets + CSS/HTML/JS.
"""
import streamlit as st
import streamlit.components.v1 as components

from auth import login, register_user
from dashboard import theme as theme_tokens


DEMO_EMAIL = 'demo@youtube.com'
DEMO_PASSWORD = 'demo123'


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
    </style>
    """, unsafe_allow_html=True)


def _inject_entrance_styles():
    """Play-once entrance choreography — emitted only on the first render of the
    session. On later reruns it is not injected, so everything renders settled
    (no replay on failed login / theme toggle / mode switch)."""
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
    return (
        '<div class="sr-scene">'
        '<div class="sr-top">'
        '<span class="sr-eyebrow">YouTube Analytics</span>'
        '<span class="sr-live"><span class="sr-live-dot"></span>LIVE · CHANNEL PULSE</span>'
        '</div>'
        '<h1 class="sr-h1">Know what your <span class="sr-grad">audience</span> actually watches.</h1>'
        '<p class="sr-sub">Retention, engagement and revenue for every video'
        ' — decoded into decisions, in one dashboard.</p>'
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
        '</div>'
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
        '<span>Best upload window for this channel: Friday, 6 PM.</span>'
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


def _show_messages():
    if st.session_state.get('login_error'):
        st.markdown(f'<div class="login-note login-err">{st.session_state["login_error"]}</div>',
                    unsafe_allow_html=True)
        st.session_state['login_error'] = ''
    if st.session_state.get('login_success'):
        st.markdown(f'<div class="login-note login-ok">{st.session_state["login_success"]}</div>',
                    unsafe_allow_html=True)
        st.session_state['login_success'] = ''


# ─────────────────────────────────────────────────────────────────────────────
# Form sides
# ─────────────────────────────────────────────────────────────────────────────

def _render_login_side():
    st.markdown(_form_header_html("Welcome", "Sign in to your analytics dashboard"),
                unsafe_allow_html=True)
    _show_messages()

    with st.form("login_form", border=False):
        email = st.text_input("Email", placeholder="you@example.com", key="login_email")
        password = st.text_input("Password", placeholder="Your password",
                                 type="password", key="login_password")
        submitted = st.form_submit_button("Sign in", type="primary")

    if submitted:
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

    # Demo — outside the form so its own click drives the login.
    if st.button("▶ Try the live demo — no account needed", key="demo_btn"):
        success, message = login(DEMO_EMAIL, DEMO_PASSWORD)
        if success:
            # Clear login page state to prevent duplication on rerun
            for key in ['login_mode', '_login_entered', 'login_error', 'login_success']:
                st.session_state.pop(key, None)
            st.rerun()
        else:
            st.session_state['login_error'] = message
            st.rerun()

    st.markdown('<div class="login-divider"><span>new here</span></div>', unsafe_allow_html=True)

    # Real, visible button (styled as a centered link) — switches to sign-up.
    if st.button("Create a free account — Sign up", key="switch_to_signup"):
        st.session_state['login_mode'] = 'signup'
        st.session_state['login_error'] = ''
        st.session_state['login_success'] = ''
        st.rerun()


def _render_signup_side():
    st.markdown(_form_header_html("Create your account", "Free — no credit card needed"),
                unsafe_allow_html=True)
    _show_messages()

    with st.form("signup_form", border=False):
        display_name = st.text_input("Display name", placeholder="Your name", key="signup_name")
        email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
        password = st.text_input("Password", placeholder="Min 5 characters",
                                 type="password", key="signup_password")
        confirm = st.text_input("Confirm password", placeholder="Re-enter password",
                                type="password", key="signup_confirm")
        submitted = st.form_submit_button("Create account", type="primary")

    if submitted:
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

    if st.button("Already have an account? Sign in", key="switch_to_login"):
        st.session_state['login_mode'] = 'login'
        st.session_state['login_error'] = ''
        st.session_state['login_success'] = ''
        st.rerun()


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
    # Collapse the iframe's element-container slot so it takes no vertical space.
    st.markdown("""
    <style>
      div[data-testid="stElementContainer"]:has(iframe[height="0"]) { display: none !important; }
      iframe[height="0"] { height: 0 !important; display: block; }
    </style>
    """, unsafe_allow_html=True)
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
    if first_render:
        _inject_entrance_styles()
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
