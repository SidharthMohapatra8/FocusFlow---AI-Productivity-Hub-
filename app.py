"""
app.py — FocusFlow entry point / Dashboard.
Run with: streamlit run app.py
"""

from datetime import date, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db
from utils import (
    init_state,
    inject_css,
    page_header,
    metric_card,
    card,
    fmt_date,
)

st.set_page_config(
    page_title="FocusFlow — AI Productivity Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_state()
inject_css()

# Sidebar
with st.sidebar:
    st.markdown(
        '<h2 style="margin-bottom:0;">⚡ FocusFlow</h2>'
        '<p style="color:gray;font-size:13px;margin-top:2px;">Your productivity hub</p>',
        unsafe_allow_html=True,
    )
    st.divider()
    theme_label = "🌙 Dark mode" if st.session_state.theme == "light" else "☀️ Light mode"
    if st.button(theme_label, use_container_width=True):
        st.session_state.theme = (
            "dark" if st.session_state.theme == "light" else "light"
        )
        st.rerun()
    st.divider()
    st.caption("Personal edition — no multi-user auth. All data stays local.")

# --- Welcome hero ---
first_name = st.session_state.get("user_name", "")
greeting = "Good morning"
hour = datetime.now().hour
if 12 <= hour < 18:
    greeting = "Good afternoon"
elif hour >= 18:
    greeting = "Good evening"
title_name = f", {first_name}" if first_name else ""
page_header(
    f"{greeting}{title_name}! 👋",
    f"Today is {datetime.now().strftime('%A, %B %d, %Y')}",
)

# --- Quick actions ---
qa1, qa2, qa3, qa4 = st.columns(4)
with qa1:
    if st.button("➕ New Task", use_container_width=True):
        st.switch_page("pages/1_Tasks.py")
with qa2:
    if st.button("📝 New Note", use_container_width=True):
        st.switch_page("pages/2_Notes.py")
with qa3:
    if st.button("🎯 New Goal", use_container_width=True):
        st.switch_page("pages/4_Goals.py")
with qa4:
    if st.button("⏱️ Focus Timer", use_container_width=True):
        st.switch_page("pages/5_Focus_Timer.py")

st.write("")

# --- Stats ---
stats = db.get_task_stats()
s1, s2, s3, s4, s5 = st.columns(5)
for col, (value, label) in zip(
    [s1, s2, s3, s4, s5],
    [
        (stats["total"], "Total tasks"),
        (stats["completed"], "Completed"),
        (stats["pending"], "Pending"),
        (stats["overdue"], "Overdue"),
        (db.count_focus_sessions_today(), "Focus sessions today"),
    ],
):
    with col:
        st.markdown(metric_card(value, label), unsafe_allow_html=True)

st.write("")

# --- Main two-column area ---
left, right = st.columns([1.2, 1])

with left:
    st.markdown('<div class="ff-section-title">📅 Today\'s schedule</div>',
                unsafe_allow_html=True)
    today_iso = date.today().isoformat()
    activities = db.get_activities(today_iso)
    if not activities:
        card("<em>No activities scheduled for today. Add some in the Planner.</em>")
    else:
        for act in activities:
            card(
                f'<strong>{act["start_time"]} – {act["end_time"]}</strong> '
                f'&nbsp; {act["title"]}'
                + (f'<div style="color:#6B7280;font-size:13px;margin-top:4px;">'
                   f'{act["description"]}</div>' if act["description"] else "")
            )

    st.markdown('<div class="ff-section-title">✅ Tasks due today</div>',
                unsafe_allow_html=True)
    today_tasks = [t for t in db.get_tasks() if t["due_date"] == today_iso]
    if not today_tasks:
        card("<em>No tasks due today. Enjoy the breathing room.</em>")
    else:
        for t in today_tasks[:6]:
            status_icon = "✅" if t["status"] == "Completed" else "⏳"
            card(
                f'{status_icon} <strong>{t["title"]}</strong>'
                f' <span class="ff-pill">{t["priority"]}</span>'
                f'<div style="color:#6B7280;font-size:13px;">{t["category"]} · '
                f'{t["status"]}</div>'
            )

with right:
    st.markdown('<div class="ff-section-title">🗒️ Recent notes</div>',
                unsafe_allow_html=True)
    notes = db.get_notes()[:4]
    if not notes:
        card("<em>No notes yet. Capture an idea from the Notes page.</em>")
    else:
        for n in notes:
            pinned = "📌 " if n["pinned"] else ""
            card(
                f'{pinned}<strong>{n["title"]}</strong>'
                f'<div style="color:#6B7280;font-size:13px;margin-top:4px;">'
                f'{(n["content"] or "")[:120]}...</div>'
            )

    st.markdown('<div class="ff-section-title">📊 Task completion</div>',
                unsafe_allow_html=True)
    df = pd.DataFrame(db.get_tasks())
    if df.empty:
        card("<em>No task data yet — create a task to see charts.</em>")
    else:
        counts = df["status"].value_counts().reset_index()
        counts.columns = ["Status", "Count"]
        fig = px.pie(
            counts, names="Status", values="Count", hole=0.55,
            color="Status",
            color_discrete_map={
                "Pending": "#6B7280",
                "In Progress": "#3B82F6",
                "Completed": "#10B981",
            },
        )
        fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=260,
            showlegend=True,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption(
    "FocusFlow is a personal-use productivity app. Data is stored in a local "
    "SQLite file (`focusflow_data.db`). On Streamlit Community Cloud, local "
    "files may be reset on redeployments — see README for persistent database "
    "options."
)