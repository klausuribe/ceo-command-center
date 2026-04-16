"""Global theme — design tokens + CSS injection.

Usage: call apply_theme() once per page right after st.set_page_config().
Safe to call multiple times (Streamlit caches the head). Variables are
exposed as CSS custom properties under :root, so every component can use
var(--ccc-surface-1) etc.

Design system: Financial Dashboard (BI/Analytics) + Dark Mode OLED.
Typography: Fira Sans (body) + Fira Code (numbers, tabular).
"""

from __future__ import annotations

import streamlit as st

# ── Design tokens ────────────────────────────────────────────────────────
TOKENS = {
    # Surfaces
    "bg":          "#020617",   # slate-950 — deepest background
    "surface_1":   "#0F172A",   # slate-900 — cards
    "surface_2":   "#1E293B",   # slate-800 — elevated / hover
    "surface_3":   "#334155",   # slate-700 — borders, dividers
    # Text
    "text":        "#F8FAFC",   # slate-50
    "text_muted":  "#94A3B8",   # slate-400
    "text_subtle": "#64748B",   # slate-500
    # Semantic
    "positive":    "#22C55E",   # green-500 — profit, growth
    "negative":    "#EF4444",   # red-500 — loss, alert
    "warning":     "#F59E0B",   # amber-500 — variance, caution
    "info":        "#38BDF8",   # sky-400 — neutral info
    "accent":      "#6366F1",   # indigo-500 — AI / primary actions
    # Data series (Plotly palette)
    "series": [
        "#38BDF8",  # sky-400
        "#6366F1",  # indigo-500
        "#22C55E",  # green-500
        "#F59E0B",  # amber-500
        "#EC4899",  # pink-500
        "#14B8A6",  # teal-500
        "#F97316",  # orange-500
        "#A855F7",  # purple-500
    ],
}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');

:root {
    --ccc-bg:          #020617;
    --ccc-surface-1:   #0F172A;
    --ccc-surface-2:   #1E293B;
    --ccc-surface-3:   #334155;
    --ccc-text:        #F8FAFC;
    --ccc-text-muted:  #94A3B8;
    --ccc-text-subtle: #64748B;
    --ccc-positive:    #22C55E;
    --ccc-negative:    #EF4444;
    --ccc-warning:     #F59E0B;
    --ccc-info:        #38BDF8;
    --ccc-accent:      #6366F1;
    --ccc-accent-soft: rgba(99, 102, 241, 0.12);
    --ccc-radius:      14px;
    --ccc-radius-sm:   8px;
    --ccc-shadow:      0 1px 0 rgba(255,255,255,0.03) inset, 0 1px 3px rgba(0,0,0,0.4);
    --ccc-border:      1px solid rgba(148, 163, 184, 0.12);
    --ccc-duration:    200ms;
}

html, body, [class*="css"], .stApp, .stMarkdown, div[data-testid="stMarkdownContainer"] {
    font-family: 'Fira Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    color: var(--ccc-text);
}
.stApp { background: var(--ccc-bg); }

/* Tabular numbers anywhere we want perfectly aligned digits */
.ccc-num, .ccc-kpi__value, .ccc-kpi__delta,
[data-testid="stMetricValue"], [data-testid="stMetricDelta"] {
    font-family: 'Fira Code', ui-monospace, SFMono-Regular, monospace !important;
    font-variant-numeric: tabular-nums;
    font-feature-settings: "tnum";
}

/* ── Hide Streamlit chrome ──────────────────────────────────────────── */
#MainMenu { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; height: 0; }
footer { visibility: hidden; }
div[data-testid="stToolbar"] { visibility: hidden; }

/* ── Page container ─────────────────────────────────────────────────── */
section.main > div.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}

/* ── Headings ───────────────────────────────────────────────────────── */
h1, h2, h3, h4 { color: var(--ccc-text); letter-spacing: -0.01em; font-weight: 600; }
h1 { font-size: 1.9rem; margin-bottom: 1.25rem; }
h2 { font-size: 1.35rem; }
h3 { font-size: 1.1rem; }
.ccc-page-title {
    display: flex; align-items: center; gap: 0.65rem;
    font-size: 1.9rem; font-weight: 700; color: var(--ccc-text);
    letter-spacing: -0.02em; margin-bottom: 0.25rem;
}
.ccc-page-subtitle {
    color: var(--ccc-text-muted); font-size: 0.92rem; margin-bottom: 1.5rem;
}
.ccc-page-title .ccc-icon { color: var(--ccc-accent); }

/* ── Section titles (st.subheader replacement) ──────────────────────── */
.ccc-section-title {
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 1.05rem; font-weight: 600; color: var(--ccc-text);
    margin: 0.75rem 0 0.75rem 0;
}
.ccc-section-title .ccc-icon { color: var(--ccc-text-muted); }

/* ── Divider ────────────────────────────────────────────────────────── */
hr, div[data-testid="stDivider"] hr {
    border: none !important;
    border-top: 1px solid rgba(148, 163, 184, 0.10) !important;
    margin: 1.25rem 0 !important;
}

/* ── KPI card (custom HTML) ─────────────────────────────────────────── */
.ccc-kpi {
    background: var(--ccc-surface-1);
    border: var(--ccc-border);
    border-radius: var(--ccc-radius);
    padding: 1.1rem 1.2rem 1rem;
    display: flex; flex-direction: column; gap: 0.4rem;
    min-height: 128px;
    transition: border-color var(--ccc-duration) ease,
                transform var(--ccc-duration) ease;
    box-shadow: var(--ccc-shadow);
}
.ccc-kpi:hover { border-color: rgba(99, 102, 241, 0.35); }
.ccc-kpi__header {
    display: flex; align-items: center; justify-content: space-between;
    color: var(--ccc-text-muted);
    font-size: 0.78rem; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.05em;
}
.ccc-kpi__header .ccc-icon { color: var(--ccc-text-subtle); }
.ccc-kpi__value {
    font-size: 1.75rem; font-weight: 600; color: var(--ccc-text);
    line-height: 1.1;
}
.ccc-kpi__delta {
    display: inline-flex; align-items: center; gap: 0.3rem;
    font-size: 0.82rem; font-weight: 500;
    padding: 2px 0;
}
.ccc-kpi__delta--pos { color: var(--ccc-positive); }
.ccc-kpi__delta--neg { color: var(--ccc-negative); }
.ccc-kpi__delta--warn { color: var(--ccc-warning); }
.ccc-kpi__delta--neutral { color: var(--ccc-text-muted); }
.ccc-kpi__help {
    color: var(--ccc-text-subtle); font-size: 0.72rem;
}

/* ── Alert card ─────────────────────────────────────────────────────── */
.ccc-alert {
    background: var(--ccc-surface-1);
    border: var(--ccc-border);
    border-left: 3px solid var(--ccc-info);
    border-radius: var(--ccc-radius-sm);
    padding: 0.8rem 1rem;
    margin-bottom: 0.55rem;
    display: flex; gap: 0.75rem; align-items: flex-start;
}
.ccc-alert--critical { border-left-color: var(--ccc-negative); }
.ccc-alert--warning  { border-left-color: var(--ccc-warning); }
.ccc-alert--info     { border-left-color: var(--ccc-info); }
.ccc-alert--positive { border-left-color: var(--ccc-positive); }
.ccc-alert__icon { flex: 0 0 auto; margin-top: 2px; }
.ccc-alert--critical .ccc-alert__icon { color: var(--ccc-negative); }
.ccc-alert--warning  .ccc-alert__icon { color: var(--ccc-warning); }
.ccc-alert--info     .ccc-alert__icon { color: var(--ccc-info); }
.ccc-alert--positive .ccc-alert__icon { color: var(--ccc-positive); }
.ccc-alert__body { flex: 1 1 auto; }
.ccc-alert__title { font-weight: 600; color: var(--ccc-text); font-size: 0.92rem; }
.ccc-alert__desc  { color: var(--ccc-text-muted); font-size: 0.85rem; margin-top: 3px; }
.ccc-alert__action {
    color: var(--ccc-accent); font-size: 0.82rem; margin-top: 5px;
    display: inline-flex; align-items: center; gap: 0.3rem;
}

/* ── AI analysis box ────────────────────────────────────────────────── */
details[data-testid="stExpander"] {
    background: var(--ccc-surface-1);
    border: var(--ccc-border);
    border-radius: var(--ccc-radius);
    overflow: hidden;
}
details[data-testid="stExpander"] > summary {
    padding: 0.75rem 1rem;
    background: linear-gradient(
        90deg, rgba(99,102,241,0.08) 0%, rgba(99,102,241,0) 60%
    );
    border-bottom: 1px solid rgba(148, 163, 184, 0.08);
    font-weight: 500;
}
details[data-testid="stExpander"] > div { padding: 0.5rem 1rem 1rem; }

/* ── Sidebar ────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--ccc-surface-1);
    border-right: 1px solid rgba(148, 163, 184, 0.08);
}
section[data-testid="stSidebar"] .block-container { padding-top: 1.25rem; }
.ccc-sidebar-brand {
    display: flex; align-items: center; gap: 0.6rem;
    padding: 0 0.25rem 0.25rem;
    font-size: 1.1rem; font-weight: 700; color: var(--ccc-text);
    letter-spacing: -0.01em;
}
.ccc-sidebar-brand .ccc-icon { color: var(--ccc-accent); }
.ccc-sidebar-brand__sub {
    font-size: 0.78rem; font-weight: 400;
    color: var(--ccc-text-muted); margin-left: 1.8rem; margin-top: -2px;
}
.ccc-sidebar-group {
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em;
    color: var(--ccc-text-subtle); font-weight: 600;
    margin: 1.1rem 0.25rem 0.45rem;
}
/* Page links: subtle pill; active state via pseudo-selector handled by URL match */
section[data-testid="stSidebar"] a[data-testid="stPageLink"] {
    border-radius: var(--ccc-radius-sm) !important;
    padding: 0.45rem 0.6rem !important;
    color: var(--ccc-text-muted) !important;
    transition: background var(--ccc-duration) ease, color var(--ccc-duration) ease;
}
section[data-testid="stSidebar"] a[data-testid="stPageLink"]:hover {
    background: rgba(99, 102, 241, 0.08) !important;
    color: var(--ccc-text) !important;
}

/* ── Buttons ────────────────────────────────────────────────────────── */
div.stButton > button {
    background: var(--ccc-surface-2);
    color: var(--ccc-text);
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: var(--ccc-radius-sm);
    font-weight: 500;
    transition: all var(--ccc-duration) ease;
    cursor: pointer;
}
div.stButton > button:hover {
    background: var(--ccc-accent-soft);
    border-color: var(--ccc-accent);
    color: var(--ccc-text);
}
div.stButton > button:focus-visible {
    outline: 2px solid var(--ccc-accent);
    outline-offset: 2px;
}

/* ── Inputs ─────────────────────────────────────────────────────────── */
div[data-baseweb="select"] > div,
div[data-testid="stTextInput"] input,
div[data-testid="stDateInput"] input,
div[data-testid="stNumberInput"] input {
    background: var(--ccc-surface-2) !important;
    border-color: rgba(148, 163, 184, 0.15) !important;
    color: var(--ccc-text) !important;
    border-radius: var(--ccc-radius-sm) !important;
}

/* ── DataFrame / tables ─────────────────────────────────────────────── */
div[data-testid="stDataFrame"] {
    border-radius: var(--ccc-radius);
    overflow: hidden;
    border: var(--ccc-border);
}

/* ── Native st.metric fallback styling ──────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--ccc-surface-1);
    border: var(--ccc-border);
    border-radius: var(--ccc-radius);
    padding: 0.9rem 1rem;
}
[data-testid="stMetricLabel"] {
    color: var(--ccc-text-muted);
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ── Focus (keyboard) ───────────────────────────────────────────────── */
:focus-visible {
    outline: 2px solid var(--ccc-accent);
    outline-offset: 2px;
    border-radius: 4px;
}

/* ── Animations ─────────────────────────────────────────────────────── */
@keyframes ccc-fade-in {
    from { opacity: 0; transform: translateY(4px); }
    to   { opacity: 1; transform: translateY(0); }
}
.ccc-kpi, .ccc-alert { animation: ccc-fade-in var(--ccc-duration) ease; }

@keyframes ccc-skeleton {
    0%   { background-position: -200px 0; }
    100% { background-position: 200px 0; }
}
.ccc-skeleton {
    background: linear-gradient(
        90deg,
        var(--ccc-surface-1) 0%,
        var(--ccc-surface-2) 50%,
        var(--ccc-surface-1) 100%
    );
    background-size: 400px 100%;
    animation: ccc-skeleton 1.4s ease-in-out infinite;
    border-radius: var(--ccc-radius-sm);
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.001ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.001ms !important;
    }
}
</style>
<script>
// ── Count-up animation for KPI values ───────────────────────────────────
// Streamlit re-renders markdown on every rerun; we idempotently animate any
// .ccc-kpi__value we haven't touched yet. Respects prefers-reduced-motion.
(function(){
    if (window.__cccCountupInstalled) return;
    window.__cccCountupInstalled = true;

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const DURATION = 600;

    function parseTarget(text) {
        const m = String(text).match(/-?\\d[\\d.,]*/);
        if (!m) return null;
        const raw = m[0].replace(/\\./g, '').replace(',', '.');
        const n = parseFloat(raw);
        return isFinite(n) ? { value: n, match: m[0], full: text } : null;
    }

    function animate(el) {
        if (el.__cccAnimated) return;
        el.__cccAnimated = true;
        if (prefersReduced) return;
        const target = parseTarget(el.textContent);
        if (!target || Math.abs(target.value) < 1) return;
        const final = el.textContent;
        const start = performance.now();
        const from = 0;
        const to = target.value;

        function frame(now) {
            const t = Math.min(1, (now - start) / DURATION);
            const eased = 1 - Math.pow(1 - t, 3);
            const current = from + (to - from) * eased;
            el.textContent = final.replace(
                target.match,
                Math.round(current).toLocaleString('es-AR')
            );
            if (t < 1) requestAnimationFrame(frame);
            else el.textContent = final;
        }
        requestAnimationFrame(frame);
    }

    function scan() {
        document.querySelectorAll('.ccc-kpi__value').forEach(animate);
    }

    const observer = new MutationObserver(() => scan());
    observer.observe(document.body, { childList: true, subtree: true });
    scan();
})();
</script>
"""


def apply_theme() -> None:
    """Inject global CSS. Call once per page after st.set_page_config()."""
    st.markdown(_CSS, unsafe_allow_html=True)


def skeleton(height: int = 120, count: int = 1) -> None:
    """Render shimmer skeleton placeholders while content is loading."""
    blocks = "".join(
        f'<div class="ccc-skeleton" style="height:{height}px;margin-bottom:8px;"></div>'
        for _ in range(count)
    )
    st.markdown(blocks, unsafe_allow_html=True)


def plotly_template() -> dict:
    """Return a Plotly layout template matching the theme.

    Use as: fig.update_layout(**plotly_template())
    """
    return dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Fira Sans, sans-serif",
            color=TOKENS["text"],
            size=12,
        ),
        colorway=TOKENS["series"],
        xaxis=dict(
            gridcolor="rgba(148, 163, 184, 0.08)",
            zerolinecolor="rgba(148, 163, 184, 0.15)",
            linecolor="rgba(148, 163, 184, 0.20)",
            tickfont=dict(color=TOKENS["text_muted"]),
        ),
        yaxis=dict(
            gridcolor="rgba(148, 163, 184, 0.08)",
            zerolinecolor="rgba(148, 163, 184, 0.15)",
            linecolor="rgba(148, 163, 184, 0.20)",
            tickfont=dict(color=TOKENS["text_muted"]),
        ),
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.6)",
            bordercolor="rgba(148, 163, 184, 0.15)",
            borderwidth=1,
            font=dict(color=TOKENS["text"]),
        ),
        hoverlabel=dict(
            bgcolor=TOKENS["surface_2"],
            bordercolor=TOKENS["surface_3"],
            font=dict(family="Fira Code, monospace", color=TOKENS["text"]),
        ),
        margin=dict(l=20, r=20, t=50, b=20),
    )
