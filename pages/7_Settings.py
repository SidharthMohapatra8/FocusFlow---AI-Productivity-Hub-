"""Settings — theme, preferences, clear data (with confirmation)."""

import streamlit as st

import database as db
from utils import init_state, inject_css, page_header, card

st.set_page_config(page_title="Settings · FocusFlow", page_icon="⚙️", layout="wide")
init_state()
inject_css()

page_header("⚙️ Settings", "Personalize FocusFlow and manage your data.")

# --- Appearance ---
st.markdown("### 🎨 Appearance")
current = st.session_state.get("theme", "light")
new_theme = st.radio(
    "Theme",
    options=["light", "dark"],
    index=0 if current == "light" else 1,
    horizontal=True,
    format_func=lambda x: "☀️ Light" if x == "light" else "🌙 Dark",
)
if new_theme != current:
    st.session_state.theme = new_theme
    st.rerun()

# --- Preferences ---
st.markdown("### 🧩 Preferences")
st.session_state.setdefault("user_name", "")
st.session_state.user_name = st.text_input(
    "Display name (used in the welcome message)",
    value=st.session_state.user_name,
    placeholder="e.g. Alex",
)
st.caption("Stored only in your browser session — not persisted to the database.")

# --- Data summary ---
st.markdown("### 💾 Your data")
tasks = db.get_tasks()
notes = db.get_notes()
goals = db.get_goals()
acts = db.get_activities()
sessions = db.get_focus_sessions()

card(
    f"""
    <ul style="margin:0;padding-left:18px;line-height:1.9;">
      <li><strong>{len(tasks)}</strong> task(s)</li>
      <li><strong>{len(notes)}</strong> note(s)</li>
      <li><strong>{len(goals)}</strong> goal(s)</li>
      <li><strong>{len(acts)}</strong> planner activity(ies)</li>
      <li><strong>{len(sessions)}</strong> focus session(s)</li>
    </ul>
    """
)

# --- Danger zone ---
st.markdown("### ⚠️ Danger zone")
st.warning(
    "**Clear all data** permanently deletes every task, note, goal, planner "
    "activity, and focus session from your local SQLite database "
    "(`focusflow_data.db`). This cannot be undone. The database file and "
    "schema remain intact; only the rows are removed."
)

confirm_text = st.text_input(
    'Type "DELETE" to enable the button below',
    key="clear_confirm_text",
)
if st.button(
    "🗑️ Permanently clear all data",
    disabled=confirm_text.strip().upper() != "DELETE",
    type="primary",
):
    db.clear_all_data()
    st.success("All application data has been cleared.")
    st.session_state.clear_confirm_text = ""
    st.rerun()

# --- About ---
st.divider()
st.markdown(
    """
    ### ℹ️ About FocusFlow

    **FocusFlow** is a personal productivity hub built with Streamlit and SQLite.
    This edition is **single-user / local by design** — there is no
    authentication layer and no server-side multi-user support. All data lives
    in a local SQLite file on the machine (or Streamlit Cloud container) that
    runs the app.

    **Optional AI features** can be enabled by adding an API key to
    `.streamlit/secrets.toml`. When no key is present, AI helpers are hidden
    and the rest of the app works normally.
    """
)

st.caption(
    "FocusFlow · Personal edition · Built with Streamlit, SQLite, Pandas, and Plotly."
)