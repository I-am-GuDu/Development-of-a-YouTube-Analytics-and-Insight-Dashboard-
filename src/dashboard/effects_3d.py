"""
3D Immersive Effects Engine
============================
Turns the dashboard into a true 3D experience:

- Real WebGL background (Three.js): particle constellation network,
  floating wireframe geometry (icosahedron, torus-knot, octahedron, ring),
  mouse-parallax camera and scroll-reactive rotation.
- 3D tilt cards with dynamic glare highlight that follows the cursor.
- Animated count-up metric values.
- Scroll-triggered staggered reveal animations.
- Cursor aura glow + sparkle trail.
- Aurora gradient mesh + film-grain background layers.
- Holographic conic-gradient card borders, neon glass, shimmer text.

NOTE: JavaScript is delivered through `streamlit.components.v1.html`
(an iframe) and injected into the parent document. Plain `st.markdown`
<script> tags are sanitized by Streamlit and never execute.
"""
import json
import streamlit as st
import streamlit.components.v1 as components


# ═══════════════════════════════════════════════════════════════════════════════
# CSS — 3D / GLASS / AURORA THEME LAYER
# ═══════════════════════════════════════════════════════════════════════════════

def inject_3d_effects(theme='dark'):
    """Inject the full 3D visual style layer (CSS only — JS lives in
    inject_3d_javascript)."""
    is_dark = theme == 'dark'

    # ── Theme tokens ──
    body_bg = '#030712' if is_dark else '#FAF5FF'
    body_glow_1 = 'rgba(124, 58, 237, 0.16)' if is_dark else 'rgba(167, 139, 250, 0.14)'
    body_glow_2 = 'rgba(14, 165, 233, 0.12)' if is_dark else 'rgba(96, 165, 250, 0.12)'
    body_glow_3 = 'rgba(34, 211, 238, 0.08)' if is_dark else 'rgba(103, 232, 249, 0.10)'

    orb_color_1 = 'rgba(123, 104, 238, 0.16)' if is_dark else 'rgba(123, 104, 238, 0.10)'
    orb_color_2 = 'rgba(62, 166, 255, 0.13)' if is_dark else 'rgba(62, 166, 255, 0.08)'
    orb_color_3 = 'rgba(34, 211, 238, 0.11)' if is_dark else 'rgba(34, 211, 238, 0.07)'
    orb_color_4 = 'rgba(244, 114, 182, 0.10)' if is_dark else 'rgba(244, 114, 182, 0.07)'

    glass_bg = 'rgba(18, 20, 34, 0.55)' if is_dark else 'rgba(255, 255, 255, 0.72)'
    glass_border = 'rgba(255, 255, 255, 0.09)' if is_dark else 'rgba(99, 102, 241, 0.12)'
    glass_shadow = 'rgba(0, 0, 0, 0.45)' if is_dark else 'rgba(79, 70, 229, 0.10)'

    glow_color = 'rgba(124, 104, 238, 0.45)' if is_dark else 'rgba(99, 102, 241, 0.25)'
    glow_hover = 'rgba(62, 166, 255, 0.35)' if is_dark else 'rgba(62, 166, 255, 0.18)'

    g1 = '#7B68EE' if is_dark else '#7c3aed'
    g2 = '#3EA6FF' if is_dark else '#2563eb'
    g3 = '#22d3ee' if is_dark else '#0891b2'
    g4 = '#f472b6' if is_dark else '#db2777'

    text_secondary = '#AAAAAA' if is_dark else '#606060'
    grain_opacity = '0.05' if is_dark else '0.03'

    st.markdown(f"""
    <style>
        /* ══════════════════════════════════════════════════════════════
           ROOT — let the WebGL canvas show through the app
           ══════════════════════════════════════════════════════════════ */
        @property --fx-angle {{
            syntax: '<angle>';
            initial-value: 0deg;
            inherits: false;
        }}

        html, body {{
            background: {body_bg} !important;
            min-height: 100vh;
        }}

        /* ── .stApp uses position:fixed so it shares the SAME stacking
             context as the WebGL canvas (also position:fixed). This is
             the ONLY way z-index comparisons work correctly between them.
             The semi-transparent bg lets the 3D effects subtly show. ── */
        .stApp {{
            background: {'rgba(3, 7, 18, 0.85)' if is_dark else 'rgba(250, 245, 255, 0.88)'} !important;
            position: fixed !important;
            inset: 0 !important;
            z-index: 1 !important;
            overflow: auto !important;
        }}

        #root {{
            position: relative;
        }}

        #fx3d-canvas {{
            position: fixed;
            inset: 0;
            width: 100vw;
            height: 100vh;
            z-index: 0;
            pointer-events: none;
        }}

        /* ══════════════════════════════════════════════════════════════
           AURORA MESH + FILM GRAIN LAYERS
           ══════════════════════════════════════════════════════════════ */
        .fx-aurora {{
            position: fixed;
            inset: -20%;
            z-index: 0;
            pointer-events: none;
            background:
                radial-gradient(40% 35% at 25% 30%, {orb_color_1}, transparent 70%),
                radial-gradient(35% 30% at 75% 20%, {orb_color_2}, transparent 70%),
                radial-gradient(45% 40% at 60% 80%, {orb_color_3}, transparent 70%),
                radial-gradient(30% 25% at 15% 75%, {orb_color_4}, transparent 70%);
            filter: blur(60px) saturate(140%);
            animation: auroraShift 26s ease-in-out infinite alternate;
            will-change: transform;
        }}

        @keyframes auroraShift {{
            0%   {{ transform: rotate(0deg) scale(1); }}
            50%  {{ transform: rotate(4deg) scale(1.08); }}
            100% {{ transform: rotate(-3deg) scale(1.04); }}
        }}

        .fx-grain {{
            position: fixed;
            inset: 0;
            z-index: 0;
            pointer-events: none;
            opacity: {grain_opacity};
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
            mix-blend-mode: overlay;
        }}

        /* ══════════════════════════════════════════════════════════════
           FLOATING ORBS (CSS layer on top of WebGL)
           ══════════════════════════════════════════════════════════════ */
        .orb-container {{
            position: fixed;
            top: 0; left: 0;
            width: 100vw; height: 100vh;
            pointer-events: none;
            z-index: 0;
            overflow: hidden;
        }}

        .floating-orb {{
            position: absolute;
            border-radius: 50%;
            filter: blur(80px);
            opacity: 0.7;
            will-change: transform;
        }}

        .orb-1 {{ width:420px;height:420px;background:radial-gradient(circle,{orb_color_1},transparent 70%);top:-5%;left:10%;animation:orbFloat1 18s ease-in-out infinite alternate; }}
        .orb-2 {{ width:360px;height:360px;background:radial-gradient(circle,{orb_color_2},transparent 70%);top:30%;right:-5%;animation:orbFloat2 22s ease-in-out infinite alternate; }}
        .orb-3 {{ width:300px;height:300px;background:radial-gradient(circle,{orb_color_3},transparent 70%);bottom:10%;left:20%;animation:orbFloat3 15s ease-in-out infinite alternate; }}
        .orb-4 {{ width:260px;height:260px;background:radial-gradient(circle,{orb_color_4},transparent 70%);top:60%;left:60%;animation:orbFloat4 20s ease-in-out infinite alternate; }}

        @keyframes orbFloat1 {{ 0%{{transform:translate(0,0) scale(1)}} 50%{{transform:translate(60px,40px) scale(1.1)}} 100%{{transform:translate(-30px,80px) scale(.95)}} }}
        @keyframes orbFloat2 {{ 0%{{transform:translate(0,0) scale(1)}} 50%{{transform:translate(-50px,60px) scale(1.08)}} 100%{{transform:translate(40px,-40px) scale(.92)}} }}
        @keyframes orbFloat3 {{ 0%{{transform:translate(0,0) scale(1)}} 50%{{transform:translate(70px,-50px) scale(1.12)}} 100%{{transform:translate(-40px,20px) scale(.97)}} }}
        @keyframes orbFloat4 {{ 0%{{transform:translate(0,0) scale(1)}} 50%{{transform:translate(-60px,-70px) scale(1.06)}} 100%{{transform:translate(30px,50px) scale(.94)}} }}

        /* ══════════════════════════════════════════════════════════════
           HOLOGRAPHIC GLASS CARDS + ROTATING GRADIENT BORDER
           ══════════════════════════════════════════════════════════════ */
        .yt-metric-card,
        .yt-chart-card,
        .yt-video-card,
        [data-testid="stMetric"] {{
            background: {glass_bg} !important;
            backdrop-filter: blur(20px) saturate(170%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(170%) !important;
            border: 1px solid {glass_border} !important;
            box-shadow: 0 8px 32px {glass_shadow},
                        inset 0 1px 0 rgba(255,255,255,0.06) !important;
            position: relative;
            overflow: hidden;
            transform-style: preserve-3d;
            transition: box-shadow 0.4s cubic-bezier(0.23,1,0.32,1),
                        border-color 0.4s cubic-bezier(0.23,1,0.32,1) !important;
        }}

        /* rotating conic gradient ring on hover */
        .yt-metric-card::after,
        .yt-chart-card::after {{
            content: '';
            position: absolute;
            inset: 0;
            border-radius: inherit;
            padding: 1px;
            background: conic-gradient(from var(--fx-angle),
                {g1}, {g2}, {g3}, {g4}, {g1});
            -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
            -webkit-mask-composite: xor;
            mask-composite: exclude;
            opacity: 0;
            transition: opacity 0.5s ease;
            animation: fxBorderSpin 4s linear infinite;
            pointer-events: none;
        }}

        .yt-metric-card:hover::after,
        .yt-chart-card:hover::after {{
            opacity: 0.9;
        }}

        @keyframes fxBorderSpin {{
            to {{ --fx-angle: 360deg; }}
        }}

        /* sweeping light beam */
        .yt-metric-card::before {{
            content: '';
            position: absolute;
            top: 0; left: -120%;
            width: 80%; height: 100%;
            background: linear-gradient(100deg, transparent,
                rgba(255,255,255,0.06), transparent);
            transform: skewX(-18deg);
            transition: left 0.7s ease;
            pointer-events: none;
        }}
        .yt-metric-card:hover::before {{ left: 140%; }}

        .yt-metric-card:hover,
        [data-testid="stMetric"]:hover {{
            box-shadow: 0 18px 50px {glass_shadow},
                        0 0 36px {glow_color},
                        inset 0 1px 0 rgba(255,255,255,0.1) !important;
        }}

        .yt-chart-card:hover,
        .yt-video-card:hover {{
            box-shadow: 0 12px 44px {glass_shadow},
                        0 0 26px {glow_hover} !important;
        }}

        /* glare layer added by JS tilt engine */
        .fx-glare {{
            position: absolute;
            inset: 0;
            border-radius: inherit;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s ease;
            z-index: 3;
        }}

        /* ══════════════════════════════════════════════════════════════
           GRADIENT TITLES + NEON CONTROLS
           ══════════════════════════════════════════════════════════════ */
        .yt-page-title {{
            background: linear-gradient(120deg, {g1}, {g2} 45%, {g3} 80%);
            background-size: 200% auto;
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: fxTitleShine 6s ease-in-out infinite alternate;
        }}

        @keyframes fxTitleShine {{
            0%   {{ background-position: 0% center; }}
            100% {{ background-position: 100% center; }}
        }}

        .stButton > button[kind="primary"],
        .stButton > button[data-testid="baseButton-primary"] {{
            background: linear-gradient(120deg, {g1}, {g2}) !important;
            background-size: 180% auto !important;
            color: #fff !important;
            border: none !important;
            box-shadow: 0 4px 20px {glow_color} !important;
            transition: all 0.35s cubic-bezier(0.23,1,0.32,1) !important;
        }}

        .stButton > button[kind="primary"]:hover,
        .stButton > button[data-testid="baseButton-primary"]:hover {{
            background-position: right center !important;
            box-shadow: 0 8px 32px {glow_color}, 0 0 18px {glow_hover} !important;
            transform: translateY(-2px) scale(1.02);
        }}

        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stNumberInput input:focus {{
            border-color: {g1} !important;
            box-shadow: 0 0 0 1px {g1}, 0 0 18px {glow_color} !important;
        }}

        .stTabs [data-baseweb="tab-highlight"] {{
            background: linear-gradient(90deg, {g1}, {g2}, {g3}) !important;
            height: 3px !important;
            border-radius: 3px;
            box-shadow: 0 0 12px {glow_color};
        }}

        /* ══════════════════════════════════════════════════════════════
           3D HERO SECTION
           ══════════════════════════════════════════════════════════════ */
        .hero-3d-section {{
            position: relative;
            width: 100%;
            height: 230px;
            margin-bottom: 26px;
            border-radius: 20px;
            overflow: hidden;
            background: linear-gradient(135deg,
                rgba(123,104,238,0.12) 0%,
                rgba(62,166,255,0.08) 45%,
                rgba(34,211,238,0.06) 100%);
            border: 1px solid {glass_border};
            box-shadow: 0 12px 48px {glass_shadow},
                        inset 0 1px 0 rgba(255,255,255,0.06);
            perspective: 1100px;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
        }}

        .hero-grid {{
            position: absolute;
            inset: 0;
            background-image:
                linear-gradient(rgba(123,104,238,0.14) 1px, transparent 1px),
                linear-gradient(90deg, rgba(123,104,238,0.14) 1px, transparent 1px);
            background-size: 42px 42px;
            transform: perspective(500px) rotateX(48deg) scale(2.6);
            transform-origin: center 130%;
            animation: gridScroll 16s linear infinite;
            opacity: 0.55;
        }}

        @keyframes gridScroll {{
            0%   {{ background-position: 0 0; }}
            100% {{ background-position: 0 42px; }}
        }}

        .hero-glow {{
            position: absolute;
            width: 340px; height: 340px;
            border-radius: 50%;
            background: radial-gradient(circle, {orb_color_1}, transparent 60%);
            filter: blur(40px);
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            animation: heroGlow 6s ease-in-out infinite alternate;
            pointer-events: none;
        }}

        @keyframes heroGlow {{
            0%   {{ opacity: 0.5; transform: translate(-50%,-50%) scale(1); }}
            100% {{ opacity: 0.9; transform: translate(-50%,-50%) scale(1.35); }}
        }}

        /* ── true 3D CSS cubes ── */
        .hero-cube {{
            position: absolute;
            width: 54px; height: 54px;
            transform-style: preserve-3d;
            animation: cubeSpin 14s linear infinite;
            pointer-events: none;
        }}
        .hero-cube-l {{ left: 9%;  top: 38%; }}
        .hero-cube-r {{ right: 9%; top: 30%; width: 38px; height: 38px;
                        animation-duration: 19s; animation-direction: reverse; }}

        .hero-cube .face {{
            position: absolute;
            inset: 0;
            border: 1px solid rgba(123,104,238,0.55);
            background: rgba(123,104,238,0.07);
            box-shadow: inset 0 0 18px rgba(123,104,238,0.18);
        }}
        .hero-cube-r .face {{
            border-color: rgba(34,211,238,0.5);
            background: rgba(34,211,238,0.06);
        }}
        .hero-cube .f1 {{ transform: translateZ(27px); }}
        .hero-cube .f2 {{ transform: rotateY(180deg) translateZ(27px); }}
        .hero-cube .f3 {{ transform: rotateY(90deg)  translateZ(27px); }}
        .hero-cube .f4 {{ transform: rotateY(-90deg) translateZ(27px); }}
        .hero-cube .f5 {{ transform: rotateX(90deg)  translateZ(27px); }}
        .hero-cube .f6 {{ transform: rotateX(-90deg) translateZ(27px); }}
        .hero-cube-r .f1 {{ transform: translateZ(19px); }}
        .hero-cube-r .f2 {{ transform: rotateY(180deg) translateZ(19px); }}
        .hero-cube-r .f3 {{ transform: rotateY(90deg)  translateZ(19px); }}
        .hero-cube-r .f4 {{ transform: rotateY(-90deg) translateZ(19px); }}
        .hero-cube-r .f5 {{ transform: rotateX(90deg)  translateZ(19px); }}
        .hero-cube-r .f6 {{ transform: rotateX(-90deg) translateZ(19px); }}

        @keyframes cubeSpin {{
            0%   {{ transform: rotateX(0deg)   rotateY(0deg)   rotateZ(0deg); }}
            100% {{ transform: rotateX(360deg) rotateY(720deg) rotateZ(360deg); }}
        }}

        .hero-content {{
            position: absolute;
            inset: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 2;
        }}

        .hero-badge {{
            font-family: 'Roboto', sans-serif;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.22em;
            color: {g3};
            border: 1px solid rgba(34,211,238,0.35);
            background: rgba(34,211,238,0.07);
            border-radius: 999px;
            padding: 5px 16px;
            margin-bottom: 12px;
            text-transform: uppercase;
            animation: badgePulse 3s ease-in-out infinite;
        }}

        @keyframes badgePulse {{
            0%, 100% {{ box-shadow: 0 0 0 0 rgba(34,211,238,0.25); }}
            50%      {{ box-shadow: 0 0 18px 2px rgba(34,211,238,0.25); }}
        }}

        .hero-title {{
            font-family: 'Roboto', sans-serif;
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: -0.01em;
            background: linear-gradient(120deg, {g1}, {g2} 40%, {g3} 70%, {g4});
            background-size: 250% auto;
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            text-align: center;
            animation: fxTitleShine 5s ease-in-out infinite alternate;
            filter: drop-shadow(0 0 24px {glow_color});
        }}

        .hero-subtitle {{
            font-family: 'Roboto', sans-serif;
            font-size: 0.88rem;
            color: {text_secondary};
            margin-top: 10px;
            text-align: center;
        }}

        .hero-scanline {{
            position: absolute;
            left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, {g2}, transparent);
            opacity: 0.5;
            filter: blur(1px);
            animation: scanMove 7s ease-in-out infinite;
            pointer-events: none;
        }}

        @keyframes scanMove {{
            0%, 100% {{ top: 12%; opacity: 0.15; }}
            50%      {{ top: 85%; opacity: 0.55; }}
        }}

        .hero-shape {{
            position: absolute;
            border: 1px solid rgba(123,104,238,0.25);
            border-radius: 8px;
            animation: shapeFloat 12s ease-in-out infinite alternate;
            pointer-events: none;
        }}
        .hero-shape-1 {{ width:56px;height:56px;top:18%;left:20%;transform:rotate(45deg); }}
        .hero-shape-2 {{ width:38px;height:38px;top:28%;right:20%;border-radius:50%;animation-delay:-4s;border-color:rgba(62,166,255,0.3); }}
        .hero-shape-3 {{ width:46px;height:46px;bottom:18%;left:30%;animation-delay:-8s;border-color:rgba(34,211,238,0.3); }}
        .hero-shape-4 {{ width:32px;height:32px;bottom:22%;right:28%;animation-delay:-2s;border-color:rgba(244,114,182,0.3); }}

        @keyframes shapeFloat {{
            0%   {{ transform: translateY(0)     rotate(0deg);   opacity: 0.3; }}
            50%  {{ transform: translateY(-16px) rotate(140deg); opacity: 0.65; }}
            100% {{ transform: translateY(8px)   rotate(280deg); opacity: 0.45; }}
        }}

        /* ══════════════════════════════════════════════════════════════
           CURSOR FX ELEMENTS (created by JS)
           ══════════════════════════════════════════════════════════════ */
        .fx-cursor-aura {{
            position: fixed;
            width: 480px; height: 480px;
            border-radius: 50%;
            background: radial-gradient(circle,
                {orb_color_1} 0%, {orb_color_2} 35%, transparent 70%);
            filter: blur(50px);
            pointer-events: none;
            z-index: -1;
            transform: translate(-50%, -50%);
            opacity: {'0.8' if is_dark else '0.5'};
            will-change: left, top;
        }}

        .fx-sparkle {{
            position: fixed;
            width: 5px; height: 5px;
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
            animation: sparkleFade 0.9s ease-out forwards;
        }}

        @keyframes sparkleFade {{
            0%   {{ opacity: 0.9; transform: scale(1); }}
            100% {{ opacity: 0;   transform: scale(0.15) translateY(-22px); }}
        }}

        /* ══════════════════════════════════════════════════════════════
           Z-INDEX SANITY + PAGE ENTRANCE
           ══════════════════════════════════════════════════════════════ */
        .stApp > header {{ z-index: 100 !important; background: transparent !important; }}
        [data-testid="stSidebar"] {{
            z-index: 100 !important;
            backdrop-filter: blur(24px) saturate(160%);
            -webkit-backdrop-filter: blur(24px) saturate(160%);
        }}
        .block-container {{
            position: relative;
            z-index: 5;
            animation: pageEntrance 0.8s cubic-bezier(0.23,1,0.32,1) forwards;
        }}

        @keyframes pageEntrance {{
            0%   {{ opacity: 0; transform: translateY(22px); }}
            100% {{ opacity: 1; transform: translateY(0); }}
        }}

        /* ══════════════════════════════════════════════════════════════
           ACCESSIBILITY — respect reduced motion
           ══════════════════════════════════════════════════════════════ */
        @media (prefers-reduced-motion: reduce) {{
            *, *::before, *::after {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }}
            #fx3d-canvas, .fx-cursor-aura, .fx-grain {{ display: none !important; }}
        }}
    </style>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# JS ENGINE — runs in the PARENT document (survives Streamlit reruns)
# ═══════════════════════════════════════════════════════════════════════════════

_FX_ENGINE_JS = r"""
(function () {
    if (window.__fx3dEngine) return;
    window.__fx3dEngine = true;

    var W = window, D = document;
    var reduced = W.matchMedia && W.matchMedia('(prefers-reduced-motion: reduce)').matches;

    var THEMES = {
        dark: {
            particles: ['#7B68EE', '#3EA6FF', '#22d3ee'],
            line: '#5b54c7',
            shapes: ['#7B68EE', '#3EA6FF', '#22d3ee', '#f472b6'],
            particleOpacity: 0.85,
            lineOpacity: 0.22,
            shapeOpacity: 0.26
        },
        light: {
            particles: ['#7c3aed', '#2563eb', '#0891b2'],
            line: '#818cf8',
            shapes: ['#7c3aed', '#2563eb', '#0891b2', '#db2777'],
            particleOpacity: 0.5,
            lineOpacity: 0.14,
            shapeOpacity: 0.18
        }
    };
    function theme() { return THEMES[W.__fxTheme] || THEMES.dark; }

    // ════════════════════════════════════════════════════════════
    // THREE.JS BACKGROUND — particle constellation + wire shapes
    // ════════════════════════════════════════════════════════════
    var fx = { mats: {} };

    function loadThree(cb) {
        if (W.THREE) return cb();
        var s = D.createElement('script');
        s.src = 'https://cdn.jsdelivr.net/npm/three@0.149.0/build/three.min.js';
        s.onload = cb;
        D.head.appendChild(s);
    }

    function buildScene() {
        if (fx.renderer || reduced) return;
        var T = W.THREE;

        var canvas = D.createElement('canvas');
        canvas.id = 'fx3d-canvas';
        canvas.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;z-index:0;pointer-events:none;';
        D.body.prepend(canvas);


        var renderer = new T.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
        renderer.setPixelRatio(Math.min(W.devicePixelRatio || 1, 2));
        renderer.setSize(W.innerWidth, W.innerHeight);

        var scene = new T.Scene();
        var camera = new T.PerspectiveCamera(55, W.innerWidth / W.innerHeight, 1, 3000);
        camera.position.z = 420;

        var group = new T.Group();
        scene.add(group);

        // ── particles ──
        var N = 170;
        var pos = new Float32Array(N * 3);
        var vel = [];
        var BX = 520, BY = 340, BZ = 280;
        for (var i = 0; i < N; i++) {
            pos[i * 3]     = (Math.random() - 0.5) * BX * 2;
            pos[i * 3 + 1] = (Math.random() - 0.5) * BY * 2;
            pos[i * 3 + 2] = (Math.random() - 0.5) * BZ * 2;
            vel.push({
                x: (Math.random() - 0.5) * 0.35,
                y: (Math.random() - 0.5) * 0.30,
                z: (Math.random() - 0.5) * 0.25
            });
        }
        var pGeo = new T.BufferGeometry();
        pGeo.setAttribute('position', new T.BufferAttribute(pos, 3));
        var pMat = new T.PointsMaterial({
            color: theme().particles[0], size: 2.6,
            transparent: true, opacity: theme().particleOpacity,
            sizeAttenuation: true, blending: T.AdditiveBlending, depthWrite: false
        });
        fx.mats.particles = pMat;
        group.add(new T.Points(pGeo, pMat));

        // ── connection lines ──
        var MAXSEG = N * 5;
        var lGeo = new T.BufferGeometry();
        var lPos = new Float32Array(MAXSEG * 6);
        lGeo.setAttribute('position', new T.BufferAttribute(lPos, 3));
        var lMat = new T.LineBasicMaterial({
            color: theme().line, transparent: true,
            opacity: theme().lineOpacity, blending: T.AdditiveBlending, depthWrite: false
        });
        fx.mats.line = lMat;
        var lines = new T.LineSegments(lGeo, lMat);
        group.add(lines);

        // ── wireframe geometry ──
        var c = theme();
        function wire(geom, color, x, y, z) {
            var m = new T.MeshBasicMaterial({
                color: color, wireframe: true,
                transparent: true, opacity: c.shapeOpacity
            });
            var mesh = new T.Mesh(geom, m);
            mesh.position.set(x, y, z);
            group.add(mesh);
            return { mesh: mesh, mat: m };
        }
        fx.shapes = [
            wire(new T.IcosahedronGeometry(72, 0),         c.shapes[0], -320, 130, -120),
            wire(new T.TorusKnotGeometry(46, 11, 110, 14), c.shapes[1],  330, -70, -160),
            wire(new T.OctahedronGeometry(48, 0),          c.shapes[2],  190, 175, -230),
            wire(new T.TorusGeometry(86, 1.6, 8, 72),      c.shapes[3], -270, -165, -260)
        ];

        // ── interaction ──
        var mx = 0, my = 0, cx = 0, cy = 0;
        D.addEventListener('mousemove', function (e) {
            mx = (e.clientX / W.innerWidth - 0.5) * 2;
            my = (e.clientY / W.innerHeight - 0.5) * 2;
        });

        W.addEventListener('resize', function () {
            camera.aspect = W.innerWidth / W.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(W.innerWidth, W.innerHeight);
        });

        var scroller = D.querySelector('[data-testid="stAppViewContainer"] section')
                    || D.querySelector('[data-testid="stAppViewContainer"]');

        var DIST = 105, DIST2 = DIST * DIST;
        function animate(t) {
            // drift particles
            var arr = pGeo.attributes.position.array;
            for (var i = 0; i < N; i++) {
                arr[i * 3]     += vel[i].x;
                arr[i * 3 + 1] += vel[i].y;
                arr[i * 3 + 2] += vel[i].z;
                if (Math.abs(arr[i * 3])     > BX) vel[i].x *= -1;
                if (Math.abs(arr[i * 3 + 1]) > BY) vel[i].y *= -1;
                if (Math.abs(arr[i * 3 + 2]) > BZ) vel[i].z *= -1;
            }
            pGeo.attributes.position.needsUpdate = true;

            // rebuild constellation lines
            var seg = 0;
            for (var a = 0; a < N && seg < MAXSEG; a++) {
                for (var b = a + 1; b < N && seg < MAXSEG; b++) {
                    var dx = arr[a*3]-arr[b*3], dy = arr[a*3+1]-arr[b*3+1], dz = arr[a*3+2]-arr[b*3+2];
                    if (dx*dx + dy*dy + dz*dz < DIST2) {
                        lPos[seg*6]   = arr[a*3];   lPos[seg*6+1] = arr[a*3+1]; lPos[seg*6+2] = arr[a*3+2];
                        lPos[seg*6+3] = arr[b*3];   lPos[seg*6+4] = arr[b*3+1]; lPos[seg*6+5] = arr[b*3+2];
                        seg++;
                    }
                }
            }
            lGeo.setDrawRange(0, seg * 2);
            lGeo.attributes.position.needsUpdate = true;

            // rotate shapes
            var k = t * 0.0001;
            fx.shapes.forEach(function (s, i) {
                s.mesh.rotation.x = k * (i + 1) * 1.4;
                s.mesh.rotation.y = k * (i + 1);
                s.mesh.position.y += Math.sin(t * 0.0008 + i * 2) * 0.12;
            });

            // camera parallax + scroll rotation
            cx += (mx - cx) * 0.03;
            cy += (my - cy) * 0.03;
            camera.position.x = cx * 55;
            camera.position.y = -cy * 40;
            camera.lookAt(0, 0, 0);
            if (scroller) group.rotation.y = (scroller.scrollTop || 0) * 0.00035;

            renderer.render(scene, camera);
            W.requestAnimationFrame(animate);
        }
        W.requestAnimationFrame(animate);
        fx.renderer = renderer;
    }

    // ════════════════════════════════════════════════════════════
    // CARD TILT + GLARE
    // ════════════════════════════════════════════════════════════
    var TILT_SEL = '.yt-metric-card, .yt-chart-card, .yt-video-card, [data-testid="stMetric"]';

    function initTilt() {
        if (reduced) return;
        D.querySelectorAll(TILT_SEL).forEach(function (card) {
            if (card.dataset.fxTilt) return;
            card.dataset.fxTilt = '1';

            var glare = D.createElement('div');
            glare.className = 'fx-glare';
            card.appendChild(glare);

            card.addEventListener('mousemove', function (e) {
                var r = card.getBoundingClientRect();
                var px = (e.clientX - r.left) / r.width;
                var py = (e.clientY - r.top) / r.height;
                var rx = -(py - 0.5) * 14;
                var ry =  (px - 0.5) * 14;
                card.style.transform =
                    'perspective(900px) rotateX(' + rx + 'deg) rotateY(' + ry + 'deg) translateZ(10px) scale(1.015)';
                card.style.transition = 'transform 0.08s ease-out';
                glare.style.opacity = '1';
                glare.style.background =
                    'radial-gradient(circle at ' + (px*100) + '% ' + (py*100) + '%, rgba(255,255,255,0.14), transparent 55%)';
            });

            card.addEventListener('mouseleave', function () {
                card.style.transform = 'perspective(900px) rotateX(0) rotateY(0) translateZ(0) scale(1)';
                card.style.transition = 'transform 0.6s cubic-bezier(0.23,1,0.32,1)';
                glare.style.opacity = '0';
            });
        });
    }

    // ════════════════════════════════════════════════════════════
    // COUNT-UP METRIC VALUES
    // ════════════════════════════════════════════════════════════
    function initCounters() {
        D.querySelectorAll('.yt-metric-value, [data-testid="stMetricValue"]').forEach(function (el) {
            if (el.dataset.fxCount) return;
            var txt = (el.textContent || '').trim();
            var m = txt.match(/^([\d.,]+)\s*([KMB%]?)$/);
            if (!m) { el.dataset.fxCount = '1'; return; }
            el.dataset.fxCount = '1';

            var target = parseFloat(m[1].replace(/,/g, ''));
            if (isNaN(target)) return;
            var suffix = m[2] || '';
            var decimals = (m[1].split('.')[1] || '').length;
            var useComma = m[1].indexOf(',') > -1;
            var start = null, DUR = 1100;

            function fmt(v) {
                var s = v.toFixed(decimals);
                if (useComma) s = Number(s).toLocaleString('en-US', {
                    minimumFractionDigits: decimals, maximumFractionDigits: decimals });
                return s + suffix;
            }
            function step(ts) {
                if (!start) start = ts;
                var p = Math.min((ts - start) / DUR, 1);
                var e = 1 - Math.pow(1 - p, 3); // easeOutCubic
                el.textContent = fmt(target * e);
                if (p < 1) W.requestAnimationFrame(step);
            }
            if (reduced) { el.textContent = fmt(target); return; }
            el.textContent = fmt(0);
            W.requestAnimationFrame(step);
        });
    }

    // ════════════════════════════════════════════════════════════
    // SCROLL REVEAL (staggered)
    // ════════════════════════════════════════════════════════════
    var revealObs = new IntersectionObserver(function (entries) {
        entries.forEach(function (en, i) {
            if (en.isIntersecting) {
                setTimeout(function () {
                    en.target.style.opacity = '1';
                    en.target.style.transform = 'translateY(0) rotateX(0)';
                }, i * 70);
                revealObs.unobserve(en.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    function initReveal() {
        if (reduced) return;
        D.querySelectorAll(TILT_SEL).forEach(function (el) {
            if (el.dataset.fxReveal) return;
            el.dataset.fxReveal = '1';
            el.style.opacity = '0';
            el.style.transform = 'translateY(28px) rotateX(6deg)';
            el.style.transition =
                'opacity 0.7s cubic-bezier(0.23,1,0.32,1), transform 0.7s cubic-bezier(0.23,1,0.32,1)';
            revealObs.observe(el);
        });
    }

    // ════════════════════════════════════════════════════════════
    // CURSOR AURA + SPARKLES
    // ════════════════════════════════════════════════════════════
    function initCursor() {
        if (reduced || fx.aura) return;
        var aura = D.createElement('div');
        aura.className = 'fx-cursor-aura';
        aura.style.zIndex = '-1';
        D.body.appendChild(aura);
        fx.aura = aura;

        var tx = W.innerWidth / 2, ty = W.innerHeight / 2, x = tx, y = ty, n = 0;
        var palette = ['#7B68EE', '#3EA6FF', '#22d3ee', '#f472b6'];

        D.addEventListener('mousemove', function (e) {
            tx = e.clientX; ty = e.clientY;
            if (++n % 6 === 0) {
                var sp = D.createElement('div');
                sp.className = 'fx-sparkle';
                var color = palette[Math.floor(Math.random() * palette.length)];
                sp.style.left = (e.clientX + (Math.random()-0.5)*18) + 'px';
                sp.style.top  = (e.clientY + (Math.random()-0.5)*18) + 'px';
                sp.style.background = color;
                sp.style.boxShadow = '0 0 8px ' + color;
                D.body.appendChild(sp);
                setTimeout(function () { sp.remove(); }, 950);
            }
        });

        (function follow() {
            x += (tx - x) * 0.06;
            y += (ty - y) * 0.06;
            aura.style.left = x + 'px';
            aura.style.top = y + 'px';
            W.requestAnimationFrame(follow);
        })();
    }

    // ════════════════════════════════════════════════════════════
    // HERO MOUSE TRACKING
    // ════════════════════════════════════════════════════════════
    function initHero() {
        D.querySelectorAll('.hero-3d-section').forEach(function (hero) {
            if (hero.dataset.fxHero) return;
            hero.dataset.fxHero = '1';
            var grid = hero.querySelector('.hero-grid');
            var glow = hero.querySelector('.hero-glow');
            hero.addEventListener('mousemove', function (e) {
                var r = hero.getBoundingClientRect();
                var x = (e.clientX - r.left) / r.width - 0.5;
                var y = (e.clientY - r.top) / r.height - 0.5;
                if (grid) grid.style.transform =
                    'perspective(500px) rotateX(' + (48 + y*10) + 'deg) rotateY(' + (x*8) + 'deg) scale(2.6)';
                if (glow) {
                    glow.style.left = (50 + x*35) + '%';
                    glow.style.top  = (50 + y*35) + '%';
                }
            });
        });
    }

    // ════════════════════════════════════════════════════════════
    // THEME SWITCH (live, no reload)
    // ════════════════════════════════════════════════════════════
    function applyTheme() {
        var c = theme();
        if (fx.mats.particles) {
            fx.mats.particles.color.set(c.particles[0]);
            fx.mats.particles.opacity = c.particleOpacity;
        }
        if (fx.mats.line) {
            fx.mats.line.color.set(c.line);
            fx.mats.line.opacity = c.lineOpacity;
        }
        if (fx.shapes) fx.shapes.forEach(function (s, i) {
            s.mat.color.set(c.shapes[i % c.shapes.length]);
            s.mat.opacity = c.shapeOpacity;
        });
    }

    // ════════════════════════════════════════════════════════════
    // INIT + RE-INIT ON STREAMLIT RERENDERS
    // ════════════════════════════════════════════════════════════
    function fixZIndex() {
        // Ensure .stApp has a proper background (not transparent!)
        var t = W.__fxTheme || 'dark';
        var bg = t === 'dark' ? 'rgba(3, 7, 18, 0.85)' : 'rgba(250, 245, 255, 0.88)';
        D.querySelectorAll('.stApp').forEach(function(app) {
            app.style.background = bg;
            app.style.position = 'fixed';
            app.style.inset = '0';
            app.style.zIndex = '1';
            app.style.overflow = 'auto';
        });
        var canvas = D.getElementById('fx3d-canvas');
        if (canvas) { canvas.style.zIndex = '0'; canvas.style.pointerEvents = 'none'; }
        D.querySelectorAll('.fx-aurora, .orb-container, .fx-grain, .fx-cursor-aura').forEach(function(el) {
            el.style.zIndex = '0';
            el.style.pointerEvents = 'none';
        });
    }

    function initAll() {
        fixZIndex();
        initTilt();
        initReveal();
        initCounters();
        initHero();
        applyTheme();
    }
    W.__fx3dReinit = initAll;

    loadThree(buildScene);
    initCursor();
    initAll();
    setTimeout(initAll, 600);
    setTimeout(initAll, 1800);

    var appRoot = D.querySelector('[data-testid="stAppViewContainer"]') || D.body;
    new MutationObserver(function () {
        clearTimeout(W.__fxReinitTimer);
        W.__fxReinitTimer = setTimeout(initAll, 250);
    }).observe(appRoot, { childList: true, subtree: true });
})();
"""


def inject_3d_javascript(theme='dark'):
    """Boot the 3D JS engine.

    Uses a zero-height component iframe to inject the engine script into
    the PARENT document, so animations survive Streamlit reruns. On each
    rerun only the theme is refreshed and observers are re-initialized.
    """
    bootstrap = f"""
    <script>
    (function () {{
        try {{
            var P = window.parent, D = P.document;
            P.__fxTheme = {json.dumps(theme)};

            // ── Always fix layering on every rerender ──
            // The root cause: .stApp had background:transparent making
            // content invisible over the WebGL canvas. Fix by ensuring
            // .stApp always has an opaque-enough background.
            (function fixLayers() {{
                // Give .stApp a semi-transparent dark background
                var theme = P.__fxTheme || 'dark';
                var bgColor = theme === 'dark'
                    ? 'rgba(3, 7, 18, 0.85)'
                    : 'rgba(250, 245, 255, 0.88)';
                var apps = D.querySelectorAll('.stApp');
                apps.forEach(function(app) {{
                    app.style.background = bgColor;
                    app.style.position = 'fixed';
                    app.style.inset = '0';
                    app.style.zIndex = '1';
                    app.style.overflow = 'auto';
                }});
                // Canvas and overlays stay at z-index 0 (behind z-index 1)
                var canvas = D.getElementById('fx3d-canvas');
                if (canvas) {{
                    canvas.style.zIndex = '0';
                    canvas.style.pointerEvents = 'none';
                }}
                D.querySelectorAll('.fx-aurora, .orb-container, .fx-grain, .fx-cursor-aura').forEach(function(el) {{
                    el.style.zIndex = '0';
                    el.style.pointerEvents = 'none';
                }});
            }})();

            if (P.__fx3dEngine) {{
                if (P.__fx3dReinit) P.__fx3dReinit();
                return;
            }}
            var s = D.createElement('script');
            s.textContent = {json.dumps(_FX_ENGINE_JS)};
            D.body.appendChild(s);
        }} catch (e) {{
            console.warn('3D fx engine init failed:', e);
        }}
    }})();
    </script>
    """
    components.html(bootstrap, height=0)


# ═══════════════════════════════════════════════════════════════════════════════
# BACKGROUND LAYERS (aurora + orbs + grain)
# ═══════════════════════════════════════════════════════════════════════════════

def render_floating_orbs():
    """Render the layered ambient background: aurora mesh, floating orbs,
    and a subtle film-grain overlay. The WebGL constellation canvas is
    added behind these by the JS engine."""
    st.markdown("""
    <div class="fx-aurora"></div>
    <div class="orb-container">
        <div class="floating-orb orb-1"></div>
        <div class="floating-orb orb-2"></div>
        <div class="floating-orb orb-3"></div>
        <div class="floating-orb orb-4"></div>
    </div>
    <div class="fx-grain"></div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 3D HERO SECTION
# ═══════════════════════════════════════════════════════════════════════════════

def render_hero_section(title="YouTube Analytics",
                        subtitle="Real-time insights powered by AI",
                        badge="⚡ Live Analytics Engine"):
    """Render the 3D hero banner: perspective grid floor, spinning CSS
    cubes, floating shapes, scanline sweep and holographic title."""
    st.markdown(f"""
    <div class="hero-3d-section">
        <div class="hero-grid"></div>
        <div class="hero-glow"></div>
        <div class="hero-cube hero-cube-l">
            <div class="face f1"></div><div class="face f2"></div>
            <div class="face f3"></div><div class="face f4"></div>
            <div class="face f5"></div><div class="face f6"></div>
        </div>
        <div class="hero-cube hero-cube-r">
            <div class="face f1"></div><div class="face f2"></div>
            <div class="face f3"></div><div class="face f4"></div>
            <div class="face f5"></div><div class="face f6"></div>
        </div>
        <div class="hero-shape hero-shape-1"></div>
        <div class="hero-shape hero-shape-2"></div>
        <div class="hero-shape hero-shape-3"></div>
        <div class="hero-shape hero-shape-4"></div>
        <div class="hero-scanline"></div>
        <div class="hero-content">
            <div class="hero-badge">{badge}</div>
            <h1 class="hero-title">{title}</h1>
            <p class="hero-subtitle">{subtitle}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
