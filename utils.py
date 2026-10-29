"""
utils.py — Shared UI helpers: theme injection, card styling, formatting.
"""

import streamlit as st

THEMES = {
    "light": {
        "bg": "#FFFFFF",
        "surface": "#F9FAFB",
        "border": "#E5E7EB",
        "text": "#111827",
        "muted": "#6B7280",
        "accent": "#6366F1",
        "accent_soft": "#EEF2FF",
    },
    "dark": {
        "bg": "#0F172A",
        "surface": "#1E293B",
        "border": "#334155",
        "text": "#F1F5F9",
        "muted": "#94A3B8",
        "accent": "#818CF8",
        "accent_soft": "#1E1B4B",
    },
}


def init_state() -> None:
    st.session_state.setdefault("theme", "light")


def toggle_theme() -> None:
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"


def inject_css() -> None:
    """Inject theme-aware CSS. Uses CSS variables so other components adapt."""
    theme = THEMES[st.session_state.get("theme", "light")]
    st.markdown(
        f"""
        <style>
        :root {{
            --ff-bg: {theme['bg']};
            --ff-surface: {theme['surface']};
            --ff-border: {theme['border']};
            --ff-text: {theme['text']};
            --ff-muted: {theme['muted']};
            --ff-accent: {theme['accent']};
            --ff-accent-soft: {theme['accent_soft']};
        }}

        .stApp {{
            background-color: var(--ff-bg);
            color: var(--ff-text);
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] > div {{
            background-color: var(--ff-surface) !important;
            border-right: 1px solid var(--ff-border);
        }}

        /* Cards */
        .ff-card {{
            background: var(--ff-surface);
            border: 1px solid var(--ff-border);
            border-radius: 14px;
            padding: 18px 20px;
            margin-bottom: 14px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }}
        .ff-metric {{
            background: var(--ff-surface);
            border: 1px solid var(--ff-border);
            border-radius: 14px;
            padding: 18px;
            text-align: center;
        }}
        .ff-metric h3 {{
            margin: 0;
            font-size: 28px;
            color: var(--ff-accent);
        }}
        .ff-metric p {{
            margin: 4px 0 0 0;
            font-size: 13px;
            color: var(--ff-muted);
        }}
        .ff-section-title {{
            font-size: 15px;
            font-weight: 600;
            color: var(--ff-text);
            margin: 8px 0 12px 0;
        }}
        .ff-pill {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 12px;
            background: var(--ff-accent-soft);
            color: var(--ff-accent);
            font-weight: 600;
        }}
        .ff-note {{
            border-left: 3px solid var(--ff-accent);
            padding-left: 10px;
            margin: 6px 0;
        }}
        .ff-hero {{
            background: linear-gradient(135deg, var(--ff-accent-soft), transparent);
            border: 1px solid var(--ff-border);
            border-radius: 16px;
            padding: 22px 24px;
            margin-bottom: 18px;
        }}
        .ff-hero h1 {{
            font-size: 26px;
            margin: 0 0 4px 0;
            color: var(--ff-text);
        }}
        .ff-hero p {{
            margin: 0;
            color: var(--ff-muted);
            font-size: 14px;
        }}

        /* Buttons */
        .stButton > button {{
            border-radius: 10px;
            font-weight: 500;
        }}

        /* Headings */
        h1, h2, h3, h4 {{ color: var(--ff-text); }}
        label, p, span, div {{ color: var(--ff-text); }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(value, label) -> str:
    return f'<div class="ff-metric"><h3>{value}</h3><p>{label}</p></div>'


def card(inner_html: str) -> None:
    st.markdown(f'<div class="ff-card">{inner_html}</div>', unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="ff-hero"><h1>{title}</h1>'
        f'<p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def priority_color(priority: str) -> str:
    return {"Low": "#10B981", "Medium": "#F59E0B", "High": "#EF4444"}.get(priority, "#6B7280")


def status_color(status: str) -> str:
    return {
        "Pending": "#6B7280",
        "In Progress": "#3B82F6",
        "Completed": "#10B981",
    }.get(status, "#6B7280")


def fmt_date(value):
    if not value:
        return "—"
    return str(value)[:10]