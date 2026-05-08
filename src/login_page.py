"""
3D Animated Login Page
A stunning login/signup page with:
- 3D rotating geometric crystal
- Floating gradient orbs
- Glassmorphism login card
- Animated form fields with glow
- Smooth login ↔ signup transitions
- Error shake & success animations
"""
import streamlit as st
from auth import login, register_user, is_logged_in


# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE STYLES (3D + Glassmorphism)
# ═══════════════════════════════════════════════════════════════════════════════

def _inject_login_styles():
    """Inject all CSS for the 3D animated login page."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        /* ── Hide sidebar on login page ──────────────────────── */
        [data-testid="stSidebar"] { display: none !important; }
        .stApp > header { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }

        /* ── Full-screen dark background ─────────────────────── */
        .stApp {
            background: #030712 !important;
            overflow: hidden;
        }

        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }

        /* ═══════════════════════════════════════════════════════
           SCENE WRAPPER
           ═══════════════════════════════════════════════════════ */
        .login-scene {
            position: fixed;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10;
            perspective: 1200px;
            font-family: 'Inter', sans-serif;
        }


        /* ═══════════════════════════════════════════════════════
           FLOATING ORBS BACKGROUND
           ═══════════════════════════════════════════════════════ */
        .login-orbs {
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 0;
            overflow: hidden;
        }

        .login-orb {
            position: absolute;
            border-radius: 50%;
            filter: blur(100px);
            opacity: 0.5;
            will-change: transform;
        }

        .login-orb-1 {
            width: 500px; height: 500px;
            background: radial-gradient(circle, rgba(123, 104, 238, 0.3), transparent 70%);
            top: -10%; left: -5%;
            animation: loginOrb1 20s ease-in-out infinite alternate;
        }
        .login-orb-2 {
            width: 400px; height: 400px;
            background: radial-gradient(circle, rgba(62, 166, 255, 0.25), transparent 70%);
            bottom: -10%; right: -5%;
            animation: loginOrb2 25s ease-in-out infinite alternate;
        }
        .login-orb-3 {
            width: 350px; height: 350px;
            background: radial-gradient(circle, rgba(34, 211, 238, 0.2), transparent 70%);
            top: 40%; left: 50%;
            animation: loginOrb3 18s ease-in-out infinite alternate;
        }
        .login-orb-4 {
            width: 300px; height: 300px;
            background: radial-gradient(circle, rgba(167, 139, 250, 0.2), transparent 70%);
            top: 10%; right: 20%;
            animation: loginOrb4 22s ease-in-out infinite alternate;
        }

        @keyframes loginOrb1 {
            0%   { transform: translate(0, 0) scale(1); }
            50%  { transform: translate(80px, 60px) scale(1.15); }
            100% { transform: translate(-40px, 30px) scale(0.95); }
        }
        @keyframes loginOrb2 {
            0%   { transform: translate(0, 0) scale(1); }
            50%  { transform: translate(-70px, -50px) scale(1.1); }
            100% { transform: translate(50px, -30px) scale(0.9); }
        }
        @keyframes loginOrb3 {
            0%   { transform: translate(0, 0) scale(1); }
            50%  { transform: translate(60px, -80px) scale(1.2); }
            100% { transform: translate(-50px, 40px) scale(0.85); }
        }
        @keyframes loginOrb4 {
            0%   { transform: translate(0, 0) scale(1); }
            50%  { transform: translate(-40px, 70px) scale(1.08); }
            100% { transform: translate(30px, -60px) scale(0.92); }
        }


        /* ═══════════════════════════════════════════════════════
           STAR FIELD (CSS particles)
           ═══════════════════════════════════════════════════════ */
        .star-field {
            position: fixed;
            inset: 0;
            z-index: 1;
            pointer-events: none;
        }
        .star {
            position: absolute;
            width: 2px; height: 2px;
            background: #fff;
            border-radius: 50%;
            animation: starTwinkle 3s ease-in-out infinite;
        }


        @keyframes starTwinkle {
            0%, 100% { opacity: 0.2; }
            50%      { opacity: 0.8; }
        }


        /* ═══════════════════════════════════════════════════════
           3D ROTATING CRYSTAL
           ═══════════════════════════════════════════════════════ */
        .crystal-container {
            position: fixed;
            top: 50%; left: 25%;
            transform: translate(-50%, -50%);
            z-index: 2;
            pointer-events: none;
        }

        .crystal {
            width: 280px; height: 280px;
            transform-style: preserve-3d;
            animation: crystalSpin 25s linear infinite;
        }

        .crystal-face {
            position: absolute;
            width: 280px; height: 280px;
            border: 1px solid rgba(123, 104, 238, 0.15);
            background: linear-gradient(135deg,
                rgba(123, 104, 238, 0.06) 0%,
                rgba(62, 166, 255, 0.04) 50%,
                rgba(34, 211, 238, 0.02) 100%);
            backdrop-filter: blur(2px);
            border-radius: 16px;
        }

        .crystal-face:nth-child(1) { transform: rotateY(0deg) translateZ(140px); }
        .crystal-face:nth-child(2) { transform: rotateY(60deg) translateZ(140px); }
        .crystal-face:nth-child(3) { transform: rotateY(120deg) translateZ(140px); }
        .crystal-face:nth-child(4) { transform: rotateY(180deg) translateZ(140px); }
        .crystal-face:nth-child(5) { transform: rotateY(240deg) translateZ(140px); }
        .crystal-face:nth-child(6) { transform: rotateY(300deg) translateZ(140px); }

        /* Inner ring */
        .crystal-inner {
            position: absolute;
            width: 160px; height: 160px;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            transform-style: preserve-3d;
            animation: crystalSpin 15s linear infinite reverse;
        }

        .crystal-inner-face {
            position: absolute;
            width: 160px; height: 160px;
            border: 1px solid rgba(62, 166, 255, 0.2);
            background: linear-gradient(135deg,
                rgba(62, 166, 255, 0.08) 0%,
                rgba(167, 139, 250, 0.04) 100%);
            border-radius: 12px;
        }

        .crystal-inner-face:nth-child(1) { transform: rotateX(0deg) rotateY(0deg) translateZ(80px); }
        .crystal-inner-face:nth-child(2) { transform: rotateX(0deg) rotateY(90deg) translateZ(80px); }
        .crystal-inner-face:nth-child(3) { transform: rotateX(0deg) rotateY(180deg) translateZ(80px); }
        .crystal-inner-face:nth-child(4) { transform: rotateX(0deg) rotateY(270deg) translateZ(80px); }
        .crystal-inner-face:nth-child(5) { transform: rotateX(90deg) translateZ(80px); }
        .crystal-inner-face:nth-child(6) { transform: rotateX(-90deg) translateZ(80px); }

        /* Glow core */
        .crystal-glow {
            position: absolute;
            width: 100px; height: 100px;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            border-radius: 50%;
            background: radial-gradient(circle,
                rgba(123, 104, 238, 0.6) 0%,
                rgba(62, 166, 255, 0.3) 40%,
                transparent 70%);
            filter: blur(20px);
            animation: coreGlow 4s ease-in-out infinite alternate;
        }

        @keyframes crystalSpin {
            0%   { transform: rotateX(15deg) rotateY(0deg); }
            100% { transform: rotateX(15deg) rotateY(360deg); }
        }

        @keyframes coreGlow {
            0%   { opacity: 0.5; transform: translate(-50%, -50%) scale(1); }
            100% { opacity: 1; transform: translate(-50%, -50%) scale(1.4); }
        }


        /* ═══════════════════════════════════════════════════════
           ORBITAL RINGS
           ═══════════════════════════════════════════════════════ */
        .orbital-ring {
            position: absolute;
            border: 1px solid rgba(123, 104, 238, 0.12);
            border-radius: 50%;
            top: 50%; left: 50%;
            pointer-events: none;
        }

        .orbital-ring-1 {
            width: 400px; height: 400px;
            transform: translate(-50%, -50%) rotateX(75deg) rotateZ(0deg);
            animation: orbitalSpin1 20s linear infinite;
        }
        .orbital-ring-2 {
            width: 460px; height: 460px;
            transform: translate(-50%, -50%) rotateX(65deg) rotateZ(45deg);
            animation: orbitalSpin2 28s linear infinite reverse;
            border-color: rgba(62, 166, 255, 0.1);
        }
        .orbital-ring-3 {
            width: 520px; height: 520px;
            transform: translate(-50%, -50%) rotateX(80deg) rotateZ(90deg);
            animation: orbitalSpin3 35s linear infinite;
            border-color: rgba(34, 211, 238, 0.08);
        }

        /* Dot on ring */
        .orbital-dot {
            position: absolute;
            width: 6px; height: 6px;
            background: #7B68EE;
            border-radius: 50%;
            top: -3px; left: 50%;
            box-shadow: 0 0 12px rgba(123, 104, 238, 0.8);
        }

        .orbital-ring-2 .orbital-dot {
            background: #3EA6FF;
            box-shadow: 0 0 12px rgba(62, 166, 255, 0.8);
        }

        .orbital-ring-3 .orbital-dot {
            background: #22d3ee;
            box-shadow: 0 0 12px rgba(34, 211, 238, 0.8);
        }

        @keyframes orbitalSpin1 {
            0%   { transform: translate(-50%, -50%) rotateX(75deg) rotateZ(0deg); }
            100% { transform: translate(-50%, -50%) rotateX(75deg) rotateZ(360deg); }
        }
        @keyframes orbitalSpin2 {
            0%   { transform: translate(-50%, -50%) rotateX(65deg) rotateZ(45deg); }
            100% { transform: translate(-50%, -50%) rotateX(65deg) rotateZ(405deg); }
        }
        @keyframes orbitalSpin3 {
            0%   { transform: translate(-50%, -50%) rotateX(80deg) rotateZ(90deg); }
            100% { transform: translate(-50%, -50%) rotateX(80deg) rotateZ(450deg); }
        }


        /* ═══════════════════════════════════════════════════════
           GLASSMORPHISM LOGIN CARD
           ═══════════════════════════════════════════════════════ */
        .login-card {
            position: relative;
            z-index: 20;
            width: 420px;
            max-width: 90vw;
            padding: 48px 40px;
            background: rgba(15, 15, 25, 0.75);
            backdrop-filter: blur(40px) saturate(200%);
            -webkit-backdrop-filter: blur(40px) saturate(200%);
            border: 1px solid rgba(123, 104, 238, 0.15);
            border-radius: 24px;
            box-shadow:
                0 32px 64px rgba(0, 0, 0, 0.5),
                0 0 80px rgba(123, 104, 238, 0.08),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
            animation: cardEntrance 1s cubic-bezier(0.23, 1, 0.32, 1) forwards;
            margin-left: auto;
            margin-right: 10%;
        }

        @keyframes cardEntrance {
            0%   { opacity: 0; transform: translateY(40px) scale(0.95); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }

        /* Animated border glow */
        .login-card::before {
            content: '';
            position: absolute;
            inset: -1px;
            border-radius: 25px;
            background: linear-gradient(135deg,
                rgba(123, 104, 238, 0.3),
                transparent 40%,
                transparent 60%,
                rgba(62, 166, 255, 0.3));
            z-index: -1;
            animation: borderGlow 6s ease-in-out infinite alternate;
        }

        @keyframes borderGlow {
            0%   { opacity: 0.3; }
            50%  { opacity: 0.7; }
            100% { opacity: 0.3; }
        }


        /* ═══════════════════════════════════════════════════════
           LOGIN CARD CONTENT STYLES
           ═══════════════════════════════════════════════════════ */
        .login-logo {
            text-align: center;
            margin-bottom: 8px;
        }

        .login-logo-icon {
            width: 56px; height: 56px;
            margin: 0 auto 12px;
            background: linear-gradient(135deg, #7B68EE, #3EA6FF);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            box-shadow: 0 8px 24px rgba(123, 104, 238, 0.3);
            animation: logoFloat 3s ease-in-out infinite alternate;
        }

        @keyframes logoFloat {
            0%   { transform: translateY(0); }
            100% { transform: translateY(-6px); }
        }

        .login-title {
            font-family: 'Inter', sans-serif;
            font-size: 1.6rem;
            font-weight: 700;
            background: linear-gradient(135deg, #fff, #c4b5fd);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
            text-align: center;
        }

        .login-subtitle {
            font-family: 'Inter', sans-serif;
            font-size: 0.85rem;
            color: #888;
            text-align: center;
            margin: 8px 0 28px;
        }

        /* ── Streamlit Input Overrides inside login ──────────── */
        .stApp .block-container .stTextInput > div > div > input {
            background: rgba(255, 255, 255, 0.04) !important;
            border: 1px solid rgba(123, 104, 238, 0.2) !important;
            border-radius: 14px !important;
            color: #f1f1f1 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.95rem !important;
            padding: 14px 18px !important;
            height: auto !important;
            transition: all 0.3s ease !important;
        }

        .stApp .block-container .stTextInput > div > div > input:focus {
            border-color: #7B68EE !important;
            box-shadow: 0 0 0 3px rgba(123, 104, 238, 0.15),
                        0 0 20px rgba(123, 104, 238, 0.1) !important;
            background: rgba(255, 255, 255, 0.06) !important;
        }

        .stApp .block-container .stTextInput > div > div > input::placeholder {
            color: #555 !important;
        }

        .stApp .block-container .stTextInput > label {
            color: #aaa !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 0.82rem !important;
            font-weight: 500 !important;
        }

        /* ── Login Button Override ──────────────────────────── */
        .stApp .block-container .stButton > button {
            width: 100% !important;
            background: linear-gradient(135deg, #7B68EE, #3EA6FF) !important;
            border: none !important;
            border-radius: 14px !important;
            color: #fff !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 1rem !important;
            font-weight: 600 !important;
            padding: 14px 24px !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 8px 24px rgba(123, 104, 238, 0.25) !important;
            text-transform: none !important;
            letter-spacing: 0 !important;
        }

        .stApp .block-container .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 12px 32px rgba(123, 104, 238, 0.35) !important;
            background: linear-gradient(135deg, #8B7BF0, #4EB6FF) !important;
        }

        .stApp .block-container .stButton > button:active {
            transform: translateY(0) !important;
        }

        /* ── Toggle Link Style ─────────────────────────────── */
        .login-toggle {
            text-align: center;
            margin-top: 20px;
            font-family: 'Inter', sans-serif;
            font-size: 0.85rem;
            color: #888;
        }

        .login-toggle a {
            color: #7B68EE;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.2s;
        }

        .login-toggle a:hover {
            color: #3EA6FF;
        }

        /* ── Divider ───────────────────────────────────────── */
        .login-divider {
            display: flex;
            align-items: center;
            margin: 24px 0;
            gap: 16px;
        }
        .login-divider::before,
        .login-divider::after {
            content: '';
            flex: 1;
            height: 1px;
            background: rgba(255, 255, 255, 0.08);
        }
        .login-divider span {
            font-family: 'Inter', sans-serif;
            font-size: 0.75rem;
            color: #555;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* ── Error/Success Messages ────────────────────────── */
        .login-error {
            background: rgba(255, 68, 68, 0.1);
            border: 1px solid rgba(255, 68, 68, 0.3);
            border-radius: 12px;
            padding: 12px 16px;
            color: #ff6b6b;
            font-family: 'Inter', sans-serif;
            font-size: 0.85rem;
            margin-bottom: 16px;
            animation: shakeError 0.5s ease-in-out;
        }

        .login-success {
            background: rgba(43, 166, 64, 0.1);
            border: 1px solid rgba(43, 166, 64, 0.3);
            border-radius: 12px;
            padding: 12px 16px;
            color: #4ade80;
            font-family: 'Inter', sans-serif;
            font-size: 0.85rem;
            margin-bottom: 16px;
            animation: successPulse 0.6s ease-in-out;
        }

        @keyframes shakeError {
            0%, 100% { transform: translateX(0); }
            20%      { transform: translateX(-8px); }
            40%      { transform: translateX(8px); }
            60%      { transform: translateX(-5px); }
            80%      { transform: translateX(5px); }
        }

        @keyframes successPulse {
            0%   { opacity: 0; transform: scale(0.95); }
            50%  { opacity: 1; transform: scale(1.02); }
            100% { opacity: 1; transform: scale(1); }
        }

        /* ── Demo Credentials Chip ─────────────────────────── */
        .demo-chip {
            background: rgba(123, 104, 238, 0.08);
            border: 1px solid rgba(123, 104, 238, 0.15);
            border-radius: 12px;
            padding: 12px 16px;
            font-family: 'Inter', sans-serif;
            font-size: 0.78rem;
            color: #aaa;
            text-align: center;
            margin-bottom: 20px;
        }

        .demo-chip strong {
            color: #c4b5fd;
        }

        /* ── Feature Pills ─────────────────────────────────── */
        .feature-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: center;
            margin-top: 16px;
        }

        .feature-pill {
            background: rgba(123, 104, 238, 0.08);
            border: 1px solid rgba(123, 104, 238, 0.12);
            border-radius: 20px;
            padding: 6px 14px;
            font-family: 'Inter', sans-serif;
            font-size: 0.72rem;
            color: #aaa;
            white-space: nowrap;
        }

        /* ═══════════════════════════════════════════════════════
           GRID FLOOR (perspective grid)
           ═══════════════════════════════════════════════════════ */
        .grid-floor {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 40%;
            background-image:
                linear-gradient(rgba(123, 104, 238, 0.06) 1px, transparent 1px),
                linear-gradient(90deg, rgba(123, 104, 238, 0.06) 1px, transparent 1px);
            background-size: 60px 60px;
            transform: perspective(400px) rotateX(55deg);
            transform-origin: center bottom;
            mask-image: linear-gradient(to top, rgba(0,0,0,0.4), transparent);
            -webkit-mask-image: linear-gradient(to top, rgba(0,0,0,0.4), transparent);
            z-index: 1;
            pointer-events: none;
            animation: gridFloorScroll 30s linear infinite;
        }

        @keyframes gridFloorScroll {
            0%   { background-position: 0 0; }
            100% { background-position: 0 60px; }
        }

    </style>
    """, unsafe_allow_html=True)


def _inject_login_javascript():
    """Inject interactive JavaScript for the login page."""
    st.markdown("""
    <script>
    (function() {
        if (window.__loginEffectsInit) return;
        window.__loginEffectsInit = true;

        // ── Mouse parallax on crystal ──
        let mx = 0, my = 0, cx = 0, cy = 0;

        document.addEventListener('mousemove', function(e) {
            mx = (e.clientX / window.innerWidth - 0.5) * 2;
            my = (e.clientY / window.innerHeight - 0.5) * 2;
        });

        function animateCrystal() {
            cx += (mx - cx) * 0.04;
            cy += (my - cy) * 0.04;

            const crystal = document.querySelector('.crystal-container');
            if (crystal) {
                crystal.style.transform = `translate(calc(-50% + ${cx * 30}px), calc(-50% + ${cy * 20}px))`;
            }

            // Orb parallax
            const orbs = document.querySelectorAll('.login-orb');
            orbs.forEach((orb, i) => {
                const depth = (i + 1) * 15;
                orb.style.transform = `translate(${cx * depth}px, ${cy * depth}px)`;
            });

            requestAnimationFrame(animateCrystal);
        }
        animateCrystal();

        // ── Subtle particle emit from cursor ──
        let pCount = 0;
        document.addEventListener('mousemove', function(e) {
            pCount++;
            if (pCount % 6 !== 0) return;

            const p = document.createElement('div');
            p.style.cssText = `
                position: fixed;
                width: 3px; height: 3px;
                border-radius: 50%;
                pointer-events: none;
                z-index: 9999;
                left: ${e.clientX}px;
                top: ${e.clientY}px;
                opacity: 0.6;
                animation: loginParticleFade 0.8s ease-out forwards;
            `;

            const colors = ['#7B68EE', '#3EA6FF', '#22d3ee', '#a78bfa'];
            const c = colors[Math.floor(Math.random() * colors.length)];
            p.style.background = c;
            p.style.boxShadow = `0 0 6px ${c}`;

            document.body.appendChild(p);
            setTimeout(() => { if (p.parentNode) p.remove(); }, 800);
        });

        // Add particle fade animation dynamically
        if (!document.getElementById('loginParticleStyle')) {
            const s = document.createElement('style');
            s.id = 'loginParticleStyle';
            s.textContent = `
                @keyframes loginParticleFade {
                    0%   { opacity: 0.6; transform: scale(1) translateY(0); }
                    100% { opacity: 0; transform: scale(0.3) translateY(-15px); }
                }
            `;
            document.head.appendChild(s);
        }
    })();
    </script>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 3D SCENE HTML
# ═══════════════════════════════════════════════════════════════════════════════

def _render_3d_scene():
    """Render the 3D crystal, orbs, stars, grid floor."""
    import random
    
    # Generate star positions
    stars_html = ''
    for i in range(80):
        x = random.randint(0, 100)
        y = random.randint(0, 100)
        size = random.choice([1, 2, 2, 3])
        delay = round(random.uniform(0, 5), 1)
        duration = round(random.uniform(2, 5), 1)
        stars_html += f'<div class="star" style="left:{x}%;top:{y}%;width:{size}px;height:{size}px;animation-delay:{delay}s;animation-duration:{duration}s;"></div>'

    # Floating Orbs
    st.markdown('<div class="login-orbs"><div class="login-orb login-orb-1"></div><div class="login-orb login-orb-2"></div><div class="login-orb login-orb-3"></div><div class="login-orb login-orb-4"></div></div>', unsafe_allow_html=True)

    # Star Field
    st.markdown(f'<div class="star-field">{stars_html}</div>', unsafe_allow_html=True)

    # Perspective Grid Floor
    st.markdown('<div class="grid-floor"></div>', unsafe_allow_html=True)

    # Orbital Rings (rendered outside crystal-container, positioned the same via CSS)
    st.markdown("""<div class="crystal-container"><div class="orbital-ring orbital-ring-1"><div class="orbital-dot"></div></div><div class="orbital-ring orbital-ring-2"><div class="orbital-dot"></div></div><div class="orbital-ring orbital-ring-3"><div class="orbital-dot"></div></div><div class="crystal"><div class="crystal-face"></div><div class="crystal-face"></div><div class="crystal-face"></div><div class="crystal-face"></div><div class="crystal-face"></div><div class="crystal-face"></div></div><div class="crystal-inner"><div class="crystal-inner-face"></div><div class="crystal-inner-face"></div><div class="crystal-inner-face"></div><div class="crystal-inner-face"></div><div class="crystal-inner-face"></div><div class="crystal-inner-face"></div></div><div class="crystal-glow"></div></div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE RENDER
# ═══════════════════════════════════════════════════════════════════════════════

def render_login_page():
    """Render the complete 3D animated login page."""

    # Inject styles & 3D scene
    _inject_login_styles()
    _render_3d_scene()
    _inject_login_javascript()

    # Initialize mode state
    if 'login_mode' not in st.session_state:
        st.session_state['login_mode'] = 'login'

    # ── Layout: push login card to the right ──
    spacer_left, card_col = st.columns([3, 2])

    with card_col:
        # Logo & Title
        if st.session_state['login_mode'] == 'login':
            st.markdown("""
            <div class="login-logo">
                <div class="login-logo-icon">📊</div>
            </div>
            <h1 class="login-title">Welcome Back</h1>
            <p class="login-subtitle">Sign in to YouTube Analytics Dashboard</p>
            """, unsafe_allow_html=True)

            # Demo credentials chip
            st.markdown("""
            <div class="demo-chip">
                🎯 Demo: <strong>demo@youtube.com</strong> / <strong>demo123</strong>
            </div>
            """, unsafe_allow_html=True)

            # Show messages
            if 'login_error' in st.session_state and st.session_state['login_error']:
                st.markdown(f'<div class="login-error">⚠️ {st.session_state["login_error"]}</div>',
                            unsafe_allow_html=True)
                st.session_state['login_error'] = ''  # Clear after showing

            if 'login_success' in st.session_state and st.session_state['login_success']:
                st.markdown(f'<div class="login-success">✅ {st.session_state["login_success"]}</div>',
                            unsafe_allow_html=True)
                st.session_state['login_success'] = ''

            # Login form
            email = st.text_input("Email", placeholder="Enter your email", key="login_email")
            password = st.text_input("Password", placeholder="Enter your password",
                                     type="password", key="login_password")

            if st.button("🚀  Sign In", key="login_btn", type="primary"):
                if email and password:
                    success, message = login(email, password)
                    if success:
                        st.rerun()
                    else:
                        st.session_state['login_error'] = message
                        st.rerun()
                else:
                    st.session_state['login_error'] = "Please fill in all fields."
                    st.rerun()

            # Divider
            st.markdown('<div class="login-divider"><span>or</span></div>', unsafe_allow_html=True)

            # Switch to signup
            if st.button("Create an Account", key="switch_to_signup"):
                st.session_state['login_mode'] = 'signup'
                st.session_state['login_error'] = ''
                st.session_state['login_success'] = ''
                st.rerun()

            # Feature pills
            st.markdown("""
            <div class="feature-pills">
                <span class="feature-pill">📊 Analytics</span>
                <span class="feature-pill">🔍 Video Explorer</span>
                <span class="feature-pill">📈 Trend Analysis</span>
                <span class="feature-pill">⚔️ Multi-Channel</span>
                <span class="feature-pill">🆓 100% Free</span>
            </div>
            """, unsafe_allow_html=True)

        else:
            # ── SIGNUP MODE ──
            st.markdown("""
            <div class="login-logo">
                <div class="login-logo-icon">🚀</div>
            </div>
            <h1 class="login-title">Create Account</h1>
            <p class="login-subtitle">Sign up for free — no credit card needed</p>
            """, unsafe_allow_html=True)

            # Messages
            if 'login_error' in st.session_state and st.session_state['login_error']:
                st.markdown(f'<div class="login-error">⚠️ {st.session_state["login_error"]}</div>',
                            unsafe_allow_html=True)
                st.session_state['login_error'] = ''

            if 'login_success' in st.session_state and st.session_state['login_success']:
                st.markdown(f'<div class="login-success">✅ {st.session_state["login_success"]}</div>',
                            unsafe_allow_html=True)
                st.session_state['login_success'] = ''

            # Signup form
            display_name = st.text_input("Display Name", placeholder="Your name",
                                         key="signup_name")
            email = st.text_input("Email", placeholder="Enter your email",
                                  key="signup_email")
            password = st.text_input("Password", placeholder="Min 5 characters",
                                     type="password", key="signup_password")
            confirm = st.text_input("Confirm Password", placeholder="Re-enter password",
                                    type="password", key="signup_confirm")

            if st.button("🎯  Create Account", key="signup_btn", type="primary"):
                if not all([email, password, confirm]):
                    st.session_state['login_error'] = "Please fill in all fields."
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

            if st.button("Back to Sign In", key="switch_to_login"):
                st.session_state['login_mode'] = 'login'
                st.session_state['login_error'] = ''
                st.session_state['login_success'] = ''
                st.rerun()
