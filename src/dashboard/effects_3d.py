"""
3D Interactive Effects Module
Provides immersive 3D effects for the YouTube Analytics Dashboard:
- 3D perspective tilt cards on mouse hover
- Floating animated background orbs with mouse tracking
- Scroll-triggered reveal animations
- Glassmorphism card styling
- Parallax depth layers
"""
import streamlit as st


def inject_3d_effects(theme='dark'):
    """Inject all 3D interactive effects into the Streamlit app.
    
    This injects CSS animations, glassmorphism styles, and JavaScript
    for mouse-tracking 3D tilt and scroll-reveal effects.
    """
    is_dark = theme == 'dark'

    # ── Theme-aware color tokens ──
    orb_color_1 = 'rgba(123, 104, 238, 0.15)' if is_dark else 'rgba(123, 104, 238, 0.08)'
    orb_color_2 = 'rgba(62, 166, 255, 0.12)' if is_dark else 'rgba(62, 166, 255, 0.06)'
    orb_color_3 = 'rgba(34, 211, 238, 0.10)' if is_dark else 'rgba(34, 211, 238, 0.05)'
    orb_color_4 = 'rgba(167, 139, 250, 0.12)' if is_dark else 'rgba(167, 139, 250, 0.06)'
    
    glass_bg = 'rgba(39, 39, 39, 0.6)' if is_dark else 'rgba(255, 255, 255, 0.7)'
    glass_border = 'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 0, 0, 0.06)'
    glass_shadow = 'rgba(0, 0, 0, 0.3)' if is_dark else 'rgba(0, 0, 0, 0.08)'
    
    glow_color = 'rgba(123, 104, 238, 0.4)' if is_dark else 'rgba(99, 102, 241, 0.2)'
    glow_hover = 'rgba(62, 166, 255, 0.3)' if is_dark else 'rgba(62, 166, 255, 0.15)'
    
    hero_gradient_1 = '#7B68EE' if is_dark else '#818cf8'
    hero_gradient_2 = '#3EA6FF' if is_dark else '#60a5fa'
    hero_gradient_3 = '#22d3ee' if is_dark else '#67e8f9'

    st.markdown(f"""
    <style>
        /* ══════════════════════════════════════════════════════════════
           3D FLOATING ORBS BACKGROUND
           ══════════════════════════════════════════════════════════════ */
        .orb-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            pointer-events: none;
            z-index: 0;
            overflow: hidden;
        }}

        .floating-orb {{
            position: absolute;
            border-radius: 50%;
            filter: blur(80px);
            opacity: 0.7;
            animation-timing-function: ease-in-out;
            animation-iteration-count: infinite;
            animation-direction: alternate;
            will-change: transform;
        }}

        .orb-1 {{
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, {orb_color_1}, transparent 70%);
            top: -5%;
            left: 10%;
            animation: orbFloat1 18s ease-in-out infinite alternate;
        }}

        .orb-2 {{
            width: 350px;
            height: 350px;
            background: radial-gradient(circle, {orb_color_2}, transparent 70%);
            top: 30%;
            right: -5%;
            animation: orbFloat2 22s ease-in-out infinite alternate;
        }}

        .orb-3 {{
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, {orb_color_3}, transparent 70%);
            bottom: 10%;
            left: 20%;
            animation: orbFloat3 15s ease-in-out infinite alternate;
        }}

        .orb-4 {{
            width: 250px;
            height: 250px;
            background: radial-gradient(circle, {orb_color_4}, transparent 70%);
            top: 60%;
            left: 60%;
            animation: orbFloat4 20s ease-in-out infinite alternate;
        }}

        .orb-5 {{
            width: 180px;
            height: 180px;
            background: radial-gradient(circle, {orb_color_1}, transparent 70%);
            top: 15%;
            right: 25%;
            animation: orbFloat5 25s ease-in-out infinite alternate;
        }}

        @keyframes orbFloat1 {{
            0%   {{ transform: translate(0, 0) scale(1); }}
            33%  {{ transform: translate(60px, 40px) scale(1.1); }}
            66%  {{ transform: translate(-30px, 80px) scale(0.95); }}
            100% {{ transform: translate(40px, -20px) scale(1.05); }}
        }}

        @keyframes orbFloat2 {{
            0%   {{ transform: translate(0, 0) scale(1); }}
            33%  {{ transform: translate(-50px, 60px) scale(1.08); }}
            66%  {{ transform: translate(40px, -40px) scale(0.92); }}
            100% {{ transform: translate(-20px, 30px) scale(1.03); }}
        }}

        @keyframes orbFloat3 {{
            0%   {{ transform: translate(0, 0) scale(1); }}
            50%  {{ transform: translate(70px, -50px) scale(1.12); }}
            100% {{ transform: translate(-40px, 20px) scale(0.97); }}
        }}

        @keyframes orbFloat4 {{
            0%   {{ transform: translate(0, 0) scale(1); }}
            50%  {{ transform: translate(-60px, -70px) scale(1.06); }}
            100% {{ transform: translate(30px, 50px) scale(0.94); }}
        }}

        @keyframes orbFloat5 {{
            0%   {{ transform: translate(0, 0) scale(1); }}
            33%  {{ transform: translate(40px, 50px) scale(1.15); }}
            66%  {{ transform: translate(-50px, -30px) scale(0.9); }}
            100% {{ transform: translate(20px, -40px) scale(1.05); }}
        }}


        /* ══════════════════════════════════════════════════════════════
           GLASSMORPHISM CARD UPGRADE
           ══════════════════════════════════════════════════════════════ */
        .yt-metric-card {{
            background: {glass_bg} !important;
            backdrop-filter: blur(20px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
            border: 1px solid {glass_border} !important;
            box-shadow: 0 8px 32px {glass_shadow},
                        inset 0 1px 0 rgba(255,255,255,0.05) !important;
            position: relative;
            overflow: hidden;
            transform-style: preserve-3d;
            transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1) !important;
        }}

        .yt-metric-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(255, 255, 255, 0.03),
                transparent
            );
            transition: left 0.6s ease;
            pointer-events: none;
        }}

        .yt-metric-card:hover::before {{
            left: 100%;
        }}

        .yt-metric-card:hover {{
            box-shadow: 0 16px 48px {glass_shadow},
                        0 0 30px {glow_color},
                        inset 0 1px 0 rgba(255,255,255,0.1) !important;
            border-color: rgba(123, 104, 238, 0.3) !important;
        }}

        .yt-chart-card {{
            background: {glass_bg} !important;
            backdrop-filter: blur(16px) saturate(160%) !important;
            -webkit-backdrop-filter: blur(16px) saturate(160%) !important;
            border: 1px solid {glass_border} !important;
            box-shadow: 0 4px 24px {glass_shadow} !important;
            transform-style: preserve-3d;
            transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1) !important;
        }}

        .yt-chart-card:hover {{
            box-shadow: 0 12px 40px {glass_shadow},
                        0 0 20px {glow_hover} !important;
            border-color: rgba(62, 166, 255, 0.2) !important;
        }}

        .yt-video-card {{
            background: {glass_bg} !important;
            backdrop-filter: blur(12px) saturate(150%) !important;
            -webkit-backdrop-filter: blur(12px) saturate(150%) !important;
            border: 1px solid {glass_border} !important;
            transform-style: preserve-3d;
            transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1) !important;
        }}

        .yt-video-card:hover {{
            box-shadow: 0 8px 32px {glass_shadow},
                        0 0 15px {glow_hover} !important;
        }}

        [data-testid="stMetric"] {{
            background: {glass_bg} !important;
            backdrop-filter: blur(16px) saturate(160%) !important;
            -webkit-backdrop-filter: blur(16px) saturate(160%) !important;
            border: 1px solid {glass_border} !important;
            box-shadow: 0 4px 24px {glass_shadow} !important;
            transform-style: preserve-3d;
            transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1) !important;
        }}


        /* ══════════════════════════════════════════════════════════════
           SCROLL REVEAL ANIMATIONS
           ══════════════════════════════════════════════════════════════ */
        .scroll-reveal {{
            opacity: 0;
            transform: translateY(40px) rotateX(8deg);
            transition: opacity 0.8s cubic-bezier(0.23, 1, 0.32, 1),
                        transform 0.8s cubic-bezier(0.23, 1, 0.32, 1);
        }}

        .scroll-reveal.revealed {{
            opacity: 1;
            transform: translateY(0) rotateX(0deg);
        }}

        /* Stagger delays for child cards */
        .scroll-reveal:nth-child(1) {{ transition-delay: 0s; }}
        .scroll-reveal:nth-child(2) {{ transition-delay: 0.1s; }}
        .scroll-reveal:nth-child(3) {{ transition-delay: 0.2s; }}
        .scroll-reveal:nth-child(4) {{ transition-delay: 0.3s; }}
        .scroll-reveal:nth-child(5) {{ transition-delay: 0.4s; }}


        /* ══════════════════════════════════════════════════════════════
           3D HERO MESH SECTION
           ══════════════════════════════════════════════════════════════ */
        .hero-3d-section {{
            position: relative;
            width: 100%;
            height: 200px;
            margin-bottom: 24px;
            border-radius: 16px;
            overflow: hidden;
            background: linear-gradient(135deg, 
                rgba(123, 104, 238, 0.1) 0%,
                rgba(62, 166, 255, 0.08) 50%,
                rgba(34, 211, 238, 0.06) 100%);
            border: 1px solid {glass_border};
            perspective: 1000px;
        }}

        .hero-grid {{
            position: absolute;
            inset: 0;
            background-image:
                linear-gradient(rgba(123, 104, 238, 0.12) 1px, transparent 1px),
                linear-gradient(90deg, rgba(123, 104, 238, 0.12) 1px, transparent 1px);
            background-size: 40px 40px;
            transform: perspective(500px) rotateX(45deg) scale(2.5);
            transform-origin: center 120%;
            animation: gridScroll 20s linear infinite;
            opacity: 0.5;
        }}

        @keyframes gridScroll {{
            0%   {{ background-position: 0 0; }}
            100% {{ background-position: 0 40px; }}
        }}

        .hero-glow {{
            position: absolute;
            width: 300px;
            height: 300px;
            border-radius: 50%;
            background: radial-gradient(circle, {orb_color_1}, transparent 60%);
            filter: blur(40px);
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            animation: heroGlow 6s ease-in-out infinite alternate;
            pointer-events: none;
        }}

        @keyframes heroGlow {{
            0%   {{ opacity: 0.5; transform: translate(-50%, -50%) scale(1); }}
            100% {{ opacity: 0.8; transform: translate(-50%, -50%) scale(1.3); }}
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

        .hero-title {{
            font-family: 'Roboto', sans-serif;
            font-size: 1.6rem;
            font-weight: 700;
            background: linear-gradient(135deg, {hero_gradient_1}, {hero_gradient_2}, {hero_gradient_3});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
            text-align: center;
        }}

        .hero-subtitle {{
            font-family: 'Roboto', sans-serif;
            font-size: 0.85rem;
            color: {'#AAAAAA' if is_dark else '#606060'};
            margin-top: 8px;
            text-align: center;
        }}

        /* Floating geometric shapes in hero */
        .hero-shape {{
            position: absolute;
            border: 1px solid rgba(123, 104, 238, 0.2);
            border-radius: 8px;
            animation: shapeFloat 12s ease-in-out infinite alternate;
            pointer-events: none;
        }}

        .hero-shape-1 {{
            width: 60px;
            height: 60px;
            top: 20%;
            left: 10%;
            transform: rotate(45deg);
            animation-delay: 0s;
            border-color: rgba(123, 104, 238, 0.25);
        }}

        .hero-shape-2 {{
            width: 40px;
            height: 40px;
            top: 30%;
            right: 15%;
            border-radius: 50%;
            animation-delay: -4s;
            border-color: rgba(62, 166, 255, 0.25);
        }}

        .hero-shape-3 {{
            width: 50px;
            height: 50px;
            bottom: 20%;
            left: 25%;
            transform: rotate(20deg);
            animation-delay: -8s;
            border-color: rgba(34, 211, 238, 0.25);
        }}

        .hero-shape-4 {{
            width: 35px;
            height: 35px;
            bottom: 25%;
            right: 20%;
            transform: rotate(-30deg);
            animation-delay: -2s;
            border-color: rgba(167, 139, 250, 0.25);
        }}

        @keyframes shapeFloat {{
            0%   {{ transform: translateY(0) rotate(0deg); opacity: 0.3; }}
            33%  {{ transform: translateY(-15px) rotate(90deg); opacity: 0.6; }}
            66%  {{ transform: translateY(10px) rotate(180deg); opacity: 0.4; }}
            100% {{ transform: translateY(-8px) rotate(270deg); opacity: 0.5; }}
        }}


        /* ══════════════════════════════════════════════════════════════
           PARTICLE TRAIL ON MOUSE (cursor sparkle)
           ══════════════════════════════════════════════════════════════ */
        .mouse-particle {{
            position: fixed;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: {hero_gradient_1};
            pointer-events: none;
            z-index: 9999;
            opacity: 0;
            animation: particleFade 1s ease-out forwards;
            box-shadow: 0 0 8px {glow_color};
        }}

        @keyframes particleFade {{
            0%   {{ opacity: 0.8; transform: scale(1); }}
            100% {{ opacity: 0; transform: scale(0.2) translateY(-20px); }}
        }}


        /* ══════════════════════════════════════════════════════════════
           STAPP CONTAINER Z-INDEX FIX (so orbs render behind)
           ══════════════════════════════════════════════════════════════ */
        .stApp > header {{
            z-index: 100 !important;
        }}

        .block-container {{
            position: relative;
            z-index: 1;
        }}

        [data-testid="stSidebar"] {{
            z-index: 100 !important;
        }}


        /* ══════════════════════════════════════════════════════════════
           SMOOTH PAGE ENTRANCE ANIMATION
           ══════════════════════════════════════════════════════════════ */
        .block-container {{
            animation: pageEntrance 0.8s cubic-bezier(0.23, 1, 0.32, 1) forwards;
        }}

        @keyframes pageEntrance {{
            0%   {{ opacity: 0; transform: translateY(20px); }}
            100% {{ opacity: 1; transform: translateY(0); }}
        }}

    </style>
    """, unsafe_allow_html=True)


def inject_3d_javascript():
    """Inject JavaScript for interactive 3D mouse-tracking effects.
    
    This adds:
    - 3D tilt effect on metric/chart cards
    - Mouse parallax on floating orbs
    - Scroll-triggered reveal animations
    - Subtle cursor particle trail
    """
    st.markdown("""
    <script>
    (function() {
        // ── Prevent double initialization ──
        if (window.__3dEffectsInitialized) return;
        window.__3dEffectsInitialized = true;

        // ══════════════════════════════════════════════════════════
        // 3D TILT EFFECT ON CARDS
        // ══════════════════════════════════════════════════════════
        function initTiltCards() {
            const selectors = [
                '.yt-metric-card',
                '.yt-chart-card',
                '.yt-video-card',
                '[data-testid="stMetric"]'
            ];

            const allCards = document.querySelectorAll(selectors.join(', '));

            allCards.forEach(card => {
                if (card.dataset.tiltInit) return;
                card.dataset.tiltInit = 'true';
                card.style.transformStyle = 'preserve-3d';
                card.style.perspective = '800px';

                card.addEventListener('mousemove', function(e) {
                    const rect = card.getBoundingClientRect();
                    const centerX = rect.left + rect.width / 2;
                    const centerY = rect.top + rect.height / 2;
                    const mouseX = e.clientX - centerX;
                    const mouseY = e.clientY - centerY;

                    const rotateX = -(mouseY / rect.height) * 12;
                    const rotateY = (mouseX / rect.width) * 12;

                    card.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(8px)`;
                    card.style.transition = 'transform 0.1s ease-out';

                    // Dynamic glow effect following mouse
                    const glowX = ((e.clientX - rect.left) / rect.width) * 100;
                    const glowY = ((e.clientY - rect.top) / rect.height) * 100;
                    card.style.background = card.style.background; // preserve existing
                    card.style.boxShadow = `
                        0 16px 48px rgba(0,0,0,0.2),
                        0 0 40px rgba(123, 104, 238, 0.15),
                        inset 0 0 60px rgba(123, 104, 238, 0.03)
                    `;
                });

                card.addEventListener('mouseleave', function() {
                    card.style.transform = 'perspective(800px) rotateX(0deg) rotateY(0deg) translateZ(0px)';
                    card.style.transition = 'transform 0.6s cubic-bezier(0.23, 1, 0.32, 1)';
                    card.style.boxShadow = '';
                });
            });
        }


        // ══════════════════════════════════════════════════════════
        // MOUSE PARALLAX ON FLOATING ORBS
        // ══════════════════════════════════════════════════════════
        let mouseX = 0, mouseY = 0;
        let currentOrbX = 0, currentOrbY = 0;

        document.addEventListener('mousemove', function(e) {
            mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
            mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
        });

        function animateOrbs() {
            // Smooth lerp
            currentOrbX += (mouseX - currentOrbX) * 0.03;
            currentOrbY += (mouseY - currentOrbY) * 0.03;

            const orbs = document.querySelectorAll('.floating-orb');
            orbs.forEach((orb, index) => {
                const depth = (index + 1) * 12;
                const offsetX = currentOrbX * depth;
                const offsetY = currentOrbY * depth;
                orb.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
            });

            requestAnimationFrame(animateOrbs);
        }
        animateOrbs();


        // ══════════════════════════════════════════════════════════
        // SCROLL-TRIGGERED REVEAL
        // ══════════════════════════════════════════════════════════
        function initScrollReveal() {
            const targets = document.querySelectorAll(
                '.yt-metric-card, .yt-chart-card, .yt-video-card, [data-testid="stMetric"]'
            );

            const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry, index) => {
                    if (entry.isIntersecting) {
                        setTimeout(() => {
                            entry.target.style.opacity = '1';
                            entry.target.style.transform = 'translateY(0) rotateX(0)';
                        }, index * 80);
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

            targets.forEach(el => {
                if (!el.dataset.scrollInit) {
                    el.dataset.scrollInit = 'true';
                    el.style.opacity = '0';
                    el.style.transform = 'translateY(30px) rotateX(5deg)';
                    el.style.transition = 'opacity 0.7s cubic-bezier(0.23, 1, 0.32, 1), transform 0.7s cubic-bezier(0.23, 1, 0.32, 1)';
                    observer.observe(el);
                }
            });
        }


        // ══════════════════════════════════════════════════════════
        // CURSOR PARTICLE TRAIL (subtle sparkle)
        // ══════════════════════════════════════════════════════════
        let particleCounter = 0;
        document.addEventListener('mousemove', function(e) {
            particleCounter++;
            if (particleCounter % 4 !== 0) return; // Only every 4th move

            const particle = document.createElement('div');
            particle.className = 'mouse-particle';
            particle.style.left = e.clientX + 'px';
            particle.style.top = e.clientY + 'px';

            // Random offset
            const offsetX = (Math.random() - 0.5) * 20;
            const offsetY = (Math.random() - 0.5) * 20;
            particle.style.transform = `translate(${offsetX}px, ${offsetY}px)`;

            // Random color from palette
            const colors = ['#7B68EE', '#3EA6FF', '#22d3ee', '#a78bfa'];
            particle.style.background = colors[Math.floor(Math.random() * colors.length)];
            particle.style.boxShadow = `0 0 6px ${particle.style.background}`;

            document.body.appendChild(particle);

            setTimeout(() => {
                if (particle.parentNode) particle.parentNode.removeChild(particle);
            }, 1000);
        });


        // ══════════════════════════════════════════════════════════
        // SCROLL PARALLAX ON BACKGROUND
        // ══════════════════════════════════════════════════════════
        const mainContent = document.querySelector('[data-testid="stAppViewContainer"]') 
                         || document.querySelector('.main');
        if (mainContent) {
            mainContent.addEventListener('scroll', function() {
                const scrollY = mainContent.scrollTop;
                const orbs = document.querySelectorAll('.floating-orb');
                orbs.forEach((orb, index) => {
                    const speed = (index + 1) * 0.05;
                    const offset = scrollY * speed;
                    orb.style.marginTop = -offset + 'px';
                });
            });
        }


        // ══════════════════════════════════════════════════════════
        // HERO SECTION MOUSE TRACKING
        // ══════════════════════════════════════════════════════════
        function initHeroTracking() {
            const hero = document.querySelector('.hero-3d-section');
            if (!hero || hero.dataset.heroInit) return;
            hero.dataset.heroInit = 'true';

            const grid = hero.querySelector('.hero-grid');
            const glow = hero.querySelector('.hero-glow');

            hero.addEventListener('mousemove', function(e) {
                const rect = hero.getBoundingClientRect();
                const x = (e.clientX - rect.left) / rect.width - 0.5;
                const y = (e.clientY - rect.top) / rect.height - 0.5;

                if (grid) {
                    grid.style.transform = `perspective(500px) rotateX(${45 + y * 10}deg) rotateY(${x * 8}deg) scale(2.5)`;
                }
                if (glow) {
                    glow.style.left = `${50 + x * 30}%`;
                    glow.style.top = `${50 + y * 30}%`;
                }
            });
        }


        // ══════════════════════════════════════════════════════════
        // MUTATION OBSERVER (re-init on Streamlit re-renders)
        // ══════════════════════════════════════════════════════════
        function initAll() {
            initTiltCards();
            initScrollReveal();
            initHeroTracking();
        }

        // Run on load
        setTimeout(initAll, 500);
        setTimeout(initAll, 1500);
        setTimeout(initAll, 3000);

        // Watch for Streamlit re-renders
        const appContainer = document.querySelector('[data-testid="stAppViewContainer"]') 
                          || document.querySelector('.main')
                          || document.body;

        const mutationObserver = new MutationObserver(() => {
            clearTimeout(window.__reinitTimer);
            window.__reinitTimer = setTimeout(initAll, 300);
        });

        mutationObserver.observe(appContainer, {
            childList: true,
            subtree: true
        });
    })();
    </script>
    """, unsafe_allow_html=True)


def render_floating_orbs():
    """Render the floating background orbs HTML."""
    st.markdown("""
    <div class="orb-container" id="orbContainer">
        <div class="floating-orb orb-1"></div>
        <div class="floating-orb orb-2"></div>
        <div class="floating-orb orb-3"></div>
        <div class="floating-orb orb-4"></div>
        <div class="floating-orb orb-5"></div>
    </div>
    """, unsafe_allow_html=True)


def render_hero_section(title="YouTube Analytics", subtitle="Real-time insights powered by AI"):
    """Render the 3D hero section with animated grid and floating shapes."""
    st.markdown(f"""
    <div class="hero-3d-section">
        <div class="hero-grid"></div>
        <div class="hero-glow"></div>
        <div class="hero-shape hero-shape-1"></div>
        <div class="hero-shape hero-shape-2"></div>
        <div class="hero-shape hero-shape-3"></div>
        <div class="hero-shape hero-shape-4"></div>
        <div class="hero-content">
            <h1 class="hero-title">{title}</h1>
            <p class="hero-subtitle">{subtitle}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
