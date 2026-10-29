"""Goals page — create, update, complete, delete goals with progress bars."""

from datetime import date

import plotly.express as px
import pandas as pd
import streamlit as st

import database as db
from utils import init_state, inject_css, page_header, metric_card, fmt_date

st.set_page_config(page_title="Goals · FocusFlow", page_icon="🎯", layout="wide")
init_state()
inject_css()

page_header("🎯 Goals", "Set personal and productivity goals. Track progress visually.")

# --- Create ---
with st.expander("➕ Add a new goal", expanded=False):
    with st.form("new_goal_form", clear_on_submit=True):
        title = st.text_input("Goal title *")
        description = st.text_area("Description", height=70)
        c1, c2 = st.columns(2)
        target_date = c1.date_input("Target date", value=date.today())
        progress = c2.slider("Initial progress (%)", 0, 100, 0, 5)
        submitted = st.form_submit_button("Create goal", use_container_width=True)
        if submitted:
            if not title.strip():
                st.error("Title is required.")
            else:
                db.add_goal(
                    title.strip(),
                    description.strip(),
                    target_date.isoformat() if target_date else None,
                    progress,
                )
                st.success("Goal created.")
                st.rerun()

goals = db.get_goals()

if not goals:
    st.info("No goals yet. Create one above to start tracking progress.")
    st.stop()

# --- Summary metrics ---
active_goals = [g for g in goals if not g["completed"]]
completed_goals = [g for g in goals if g["completed"]]
avg_progress = (
    int(sum(g["progress"] for g in goals) / len(goals)) if goals else 0
)

m1, m2, m3, m4 = st.columns(4)
for col, (v, l) in zip(
    [m1, m2, m3, m4],
    [
        (len(goals), "Total goals"),
        (len(active_goals), "Active"),
        (len(completed_goals), "Completed"),
        (f"{avg_progress}%", "Avg. progress"),
    ],
):
    with col:
        st.markdown(metric_card(v, l), unsafe_allow_html=True)

st.write("")

# --- Progress chart ---
df = pd.DataFrame(goals)
if not df.empty:
    fig = px.bar(
        df.sort_values("progress", ascending=True),
        x="progress",
        y="title",
        orientation="h",
        color="completed",
        color_discrete_map={0: "#6366F1", 1: "#10B981"},
        labels={"progress": "Progress (%)", "title": "", "completed": "Completed"},
    )
    fig.update_layout(
        height=max(220, 40 * len(df)),
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(range=[0, 100]),
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### 🧭 All goals")

for g in goals:
    done_badge = " ✅" if g["completed"] else ""
    with st.container(border=True):
        st.markdown(f"#### {g['title']}{done_badge}")
        if g["description"]:
            st.caption(g["description"])
        st.caption(
            f"Target: {fmt_date(g['target_date'])} · "
            f"Progress: {g['progress']}%"
        )
        st.progress(min(100, max(0, g["progress"])) / 100)

        col_update, col_edit, col_del = st.columns([2, 1, 1])

        with col_update:
            new_progress = st.slider(
                "Update progress",
                0, 100, int(g["progress"]), 5,
                key=f"g_prog_{g['id']}",
            )
            if st.button("💾 Save progress", key=f"g_save_{g['id']}",
                         use_container_width=True):
                # Auto-complete if progress hits 100
                auto_complete = 1 if new_progress == 100 else 0
                db.update_goal(
                    g["id"],
                    progress=new_progress,
                    completed=auto_complete,
                )
                st.success("Progress updated.")
                st.rerun()

        with col_edit:
            with st.expander("✏️ Edit"):
                with st.form(f"edit_goal_{g['id']}"):
                    new_title = st.text_input("Title", value=g["title"],
                                              key=f"g_title_{g['id']}")
                    new_desc = st.text_area("Description",
                                            value=g["description"] or "",
                                            key=f"g_desc_{g['id']}")
                    try:
                        old_td = (date.fromisoformat(g["target_date"])
                                  if g["target_date"] else date.today())
                    except ValueError:
                        old_td = date.today()
                    new_td = st.date_input("Target date", value=old_td,
                                           key=f"g_td_{g['id']}")
                    if st.form_submit_button("Save changes"):
                        db.update_goal(
                            g["id"],
                            title=new_title.strip() or g["title"],
                            description=new_desc.strip(),
                            target_date=new_td.isoformat() if new_td else None,
                        )
                        st.success("Goal updated.")
                        st.rerun()

        with col_del:
            if not g["completed"]:
                if st.button("✅ Mark done", key=f"g_done_{g['id']}",
                             use_container_width=True):
                    db.update_goal(g["id"], completed=1, progress=100)
                    st.rerun()
            else:
                if st.button("↩️ Reopen", key=f"g_reopen_{g['id']}",
                             use_container_width=True):
                    db.update_goal(g["id"], completed=0)
                    st.rerun()
            if st.button("🗑️ Delete", key=f"g_del_{g['id']}",
                         use_container_width=True):
                st.session_state[f"confirm_goal_{g['id']}"] = True

        if st.session_state.get(f"confirm_goal_{g['id']}"):
            st.warning(f"Delete goal “{g['title']}”? This cannot be undone.")
            c1, c2 = st.columns(2)
            if c1.button("Yes, delete", key=f"g_yes_{g['id']}",
                         use_container_width=True):
                db.delete_goal(g["id"])
                st.session_state.pop(f"confirm_goal_{g['id']}", None)
                st.rerun()
            if c2.button("Cancel", key=f"g_no_{g['id']}",
                         use_container_width=True):
                st.session_state.pop(f"confirm_goal_{g['id']}", None)
                st.rerun()