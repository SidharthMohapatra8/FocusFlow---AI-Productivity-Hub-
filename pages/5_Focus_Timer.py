"""Pomodoro focus timer with reliable persistence across reruns.

Timer state lives in st.session_state. Elapsed time is computed from a
timestamp anchor (so pausing/resuming works) rather than counting down
inside a blocking loop — this means the timer keeps *logical* time even
if the user switches tabs or Streamlit reruns.

Limitation: because Streamlit cannot push updates to the browser in the
background, the display only refreshes when the tab is active / a widget
is interacted with. When you return, elapsed time is computed correctly.
Use the "Refresh now" button to force a re-render.
"""

from datetime import datetime

import streamlit as st

import database as db
from utils import init_state, inject_css, page_header, metric_card

st.set_page_config(page_title="Focus · FocusFlow", page_icon="⏱️", layout="wide")
init_state()
inject_css()

page_header("⏱️ Pomodoro Focus Timer",
            "25 min focus · 5 min short break · 15 min long break")

# --- Timer state ---
st.session_state.setdefault("ff_mode", "Focus")          # Focus / Short / Long
st.session_state.setdefault("ff_duration", 25 * 60)      # seconds
st.session_state.setdefault("ff_started_at", None)       # ISO or None
st.session_state.setdefault("ff_elapsed_before", 0)      # seconds accumulated
st.session_state.setdefault("ff_running", False)
st.session_state.setdefault("ff_completed", False)       # signals completion

MODES = {
    "Focus": 25 * 60,
    "Short Break": 5 * 60,
    "Long Break": 15 * 60,
}


def _current_elapsed() -> int:
    """Total elapsed seconds this session (running or paused)."""
    base = st.session_state.ff_elapsed_before
    if st.session_state.ff_running and st.session_state.ff_started_at:
        try:
            started = datetime.fromisoformat(st.session_state.ff_started_at)
            base += int((datetime.now() - started).total_seconds())
        except ValueError:
            pass
    return min(base, st.session_state.ff_duration)


def _reset(mode: str | None = None) -> None:
    if mode is not None:
        st.session_state.ff_mode = mode
        st.session_state.ff_duration = MODES[mode]
    st.session_state.ff_started_at = None
    st.session_state.ff_elapsed_before = 0
    st.session_state.ff_running = False
    st.session_state.ff_completed = False


# --- Mode buttons ---
mc1, mc2, mc3 = st.columns(3)
if mc1.button("🎯 Focus (25m)", use_container_width=True):
    _reset("Focus")
    st.rerun()
if mc2.button("☕ Short break (5m)", use_container_width=True):
    _reset("Short Break")
    st.rerun()
if mc3.button("🌿 Long break (15m)", use_container_width=True):
    _reset("Long Break")
    st.rerun()

elapsed = _current_elapsed()
remaining = max(0, st.session_state.ff_duration - elapsed)
minutes, seconds = divmod(remaining, 60)

# --- Completion detection ---
if st.session_state.ff_running and remaining == 0:
    st.session_state.ff_running = False
    st.session_state.ff_started_at = None
    st.session_state.ff_elapsed_before = st.session_state.ff_duration
    st.session_state.ff_completed = True
    if st.session_state.ff_mode == "Focus":
        db.add_focus_session(25)

# --- Display ---
st.markdown(
    f"""
    <div style="text-align:center; padding:30px 0;">
      <div style="font-size:14px; letter-spacing:2px; color:#6B7280;">
        {st.session_state.ff_mode.upper()}
      </div>
      <div style="font-size:88px; font-weight:700; color:#6366F1;
                  font-variant-numeric: tabular-nums;">
        {minutes:02d}:{seconds:02d}
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

progress_fraction = elapsed / st.session_state.ff_duration if st.session_state.ff_duration else 0
st.progress(min(1.0, max(0.0, progress_fraction)))

# --- Controls ---
c1, c2, c3, c4 = st.columns(4)

if not st.session_state.ff_running and elapsed < st.session_state.ff_duration:
    if c1.button("▶️ Start / Resume", use_container_width=True, type="primary"):
        st.session_state.ff_started_at = datetime.now().isoformat(timespec="seconds")
        st.session_state.ff_running = True
        st.rerun()

if st.session_state.ff_running:
    if c1.button("⏸️ Pause", use_container_width=True, type="primary"):
        st.session_state.ff_elapsed_before = elapsed
        st.session_state.ff_started_at = None
        st.session_state.ff_running = False
        st.rerun()

if c2.button("🔄 Reset", use_container_width=True):
    _reset()
    st.rerun()

if c3.button("🔃 Refresh", use_container_width=True):
    st.rerun()

# --- Completion message ---
if st.session_state.ff_completed:
    st.success("✅ Session complete! Take a break.")
    if st.button("Dismiss"):
        st.session_state.ff_completed = False
        st.rerun()

st.divider()

# --- Stats ---
st.markdown("### 📈 Focus stats")
sessions_today = db.count_focus_sessions_today()
sessions_all = len(db.get_focus_sessions())
m1, m2 = st.columns(2)
with m1:
    st.markdown(metric_card(sessions_today, "Focus sessions today"),
                unsafe_allow_html=True)
with m2:
    st.markdown(metric_card(sessions_all, "Focus sessions all-time"),
                unsafe_allow_html=True)

st.info(
    "💡 **Timer limitation:** Streamlit cannot push live updates to a "
    "background tab. The timer keeps accurate *logical* time using "
    "timestamps, so when you return the display is correct — but it won't "
    "tick live while the tab is hidden. Click **Refresh** to sync the display "
    "if the tab has been inactive."
)