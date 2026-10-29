"""Productivity Analytics — tasks completed, trends, goal progress."""

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db
from utils import init_state, inject_css, page_header, metric_card

st.set_page_config(page_title="Analytics · FocusFlow", page_icon="📊", layout="wide")
init_state()
inject_css()

page_header("📊 Productivity Analytics", "See how you're doing over time.")

tasks = db.get_tasks()
goals = db.get_goals()
sessions = db.get_focus_sessions()

if not tasks and not goals and not sessions:
    st.info(
        "No data yet. Create some tasks, goals, or focus sessions and "
        "analytics will appear here."
    )
    st.stop()

# --- Completion counts ---
today = date.today()
week_start = today - timedelta(days=today.weekday())
month_start = today.replace(day=1)

def _count_completed_since(since_date: date) -> int:
    df = pd.DataFrame(tasks) if tasks else pd.DataFrame()
    if df.empty or "status" not in df.columns:
        return 0
    completed = df[df["status"] == "Completed"]
    if completed.empty or "created_at" not in completed.columns:
        return 0
    completed = completed.copy()
    completed["created_at_dt"] = pd.to_datetime(
        completed["created_at"], errors="coerce"
    )
    return int((completed["created_at_dt"].dt.date >= since_date).sum())

completed_today = _count_completed_since(today)
completed_week = _count_completed_since(week_start)
completed_month = _count_completed_since(month_start)

m1, m2, m3, m4 = st.columns(4)
for col, (v, l) in zip(
    [m1, m2, m3, m4],
    [
        (completed_today, "Completed today"),
        (completed_week, "This week"),
        (completed_month, "This month"),
        (len(sessions), "Focus sessions"),
    ],
):
    with col:
        st.markdown(metric_card(v, l), unsafe_allow_html=True)

st.write("")

# --- Trend chart ---
st.markdown("### 📈 Completion trend (last 14 days)")
if tasks:
    df = pd.DataFrame(tasks)
    df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df.dropna(subset=["created_at_dt"])
    if not df.empty:
        completed = df[df["status"] == "Completed"].copy()
        if not completed.empty:
            completed["day"] = completed["created_at_dt"].dt.date
            trend = completed.groupby("day").size().reset_index(name="Completed")
        else:
            trend = pd.DataFrame({"day": [], "Completed": []})

        all_days = pd.date_range(end=today, periods=14, freq="D").date
        trend_full = pd.DataFrame({"day": all_days})
        if not trend.empty:
            trend_full = trend_full.merge(trend, on="day", how="left").fillna(0)
        else:
            trend_full["Completed"] = 0

        fig = px.bar(
            trend_full, x="day", y="Completed",
            labels={"day": "Date", "Completed": "Tasks completed"},
        )
        fig.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough dated tasks to show a trend.")
else:
    st.info("No tasks yet.")

# --- Status distribution + goal progress side by side ---
left, right = st.columns(2)

with left:
    st.markdown("### ✅ Completed vs pending")
    if tasks:
        df = pd.DataFrame(tasks)
        counts = df["status"].value_counts().reset_index()
        counts.columns = ["Status", "Count"]
        fig = px.pie(
            counts, names="Status", values="Count", hole=0.5,
            color="Status",
            color_discrete_map={
                "Pending": "#6B7280",
                "In Progress": "#3B82F6",
                "Completed": "#10B981",
            },
        )
        fig.update_layout(
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tasks yet.")

with right:
    st.markdown("### 🎯 Goal progress")
    if goals:
        gdf = pd.DataFrame(goals)[["title", "progress"]].sort_values(
            "progress", ascending=True
        )
        fig = px.bar(
            gdf, x="progress", y="title", orientation="h",
            labels={"progress": "Progress (%)", "title": ""},
        )
        fig.update_layout(
            height=max(220, 34 * len(gdf)),
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(range=[0, 100]),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No goals yet.")

# --- Focus sessions by day ---
st.markdown("### ⏱️ Focus sessions (last 14 days)")
if sessions:
    sdf = pd.DataFrame(sessions)
    sdf["completed_at_dt"] = pd.to_datetime(sdf["completed_at"], errors="coerce")
    sdf = sdf.dropna(subset=["completed_at_dt"])
    if not sdf.empty:
        sdf["day"] = sdf["completed_at_dt"].dt.date
        by_day = sdf.groupby("day").size().reset_index(name="Sessions")
        all_days = pd.date_range(end=today, periods=14, freq="D").date
        full = pd.DataFrame({"day": all_days}).merge(
            by_day, on="day", how="left"
        ).fillna(0)
        fig = px.line(
            full, x="day", y="Sessions", markers=True,
            labels={"day": "Date", "Sessions": "Sessions"},
        )
        fig.update_layout(
            height=240,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No dated focus sessions.")
else:
    st.info("No focus sessions recorded yet.")