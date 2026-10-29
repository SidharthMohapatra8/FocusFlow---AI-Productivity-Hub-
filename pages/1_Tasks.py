"""Tasks page — create, edit, complete, delete, filter tasks."""

from datetime import date

import streamlit as st

import database as db
from utils import init_state, inject_css, page_header, fmt_date, priority_color

st.set_page_config(page_title="Tasks · FocusFlow", page_icon="✅", layout="wide")
init_state()
inject_css()

page_header("✅ Task Manager", "Create, organize, and complete your tasks.")

PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["Pending", "In Progress", "Completed"]

# --- Create new task ---
with st.expander("➕ Add a new task", expanded=False):
    with st.form("new_task_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        title = c1.text_input("Title *")
        category = c2.text_input("Category", value="General")
        priority = c3.selectbox("Priority", PRIORITIES, index=1)
        c4, c5 = st.columns(2)
        due_date = c4.date_input("Due date", value=date.today())
        status = c5.selectbox("Status", STATUSES)
        description = st.text_area("Description", height=80)
        submitted = st.form_submit_button("Create task", use_container_width=True)
        if submitted:
            if not title.strip():
                st.error("Title is required.")
            else:
                db.add_task(
                    title.strip(), description.strip(),
                    due_date.isoformat() if due_date else None,
                    priority, category.strip() or "General", status,
                )
                st.success(f"Task “{title}” created.")
                st.rerun()

# --- Filters ---
st.markdown("### 🔎 Search & filter")
f1, f2, f3 = st.columns([2, 1, 1])
search = f1.text_input("Search", placeholder="Search title or description…")
filter_status = f2.selectbox("Status", ["All"] + STATUSES)
categories = db.distinct_values("category", "tasks")
filter_cat = f3.selectbox("Category", ["All"] + categories)

tasks = db.get_tasks(
    status=None if filter_status == "All" else filter_status,
    search=search or None,
    category=None if filter_cat == "All" else filter_cat,
)

# --- Today view ---
show_today = st.checkbox("Show only today's tasks")
if show_today:
    today_iso = date.today().isoformat()
    tasks = [t for t in tasks if t["due_date"] == today_iso]

st.markdown(f"### 📋 {len(tasks)} task(s)")

if not tasks:
    st.info("No tasks match your filters. Create one above or adjust the filters.")

for t in tasks:
    overdue = (
        t["status"] != "Completed"
        and t["due_date"]
        and t["due_date"] < date.today().isoformat()
    )
    header = (
        f'<span class="ff-pill" style="background:{priority_color(t["priority"])}22;'
        f'color:{priority_color(t["priority"])};">{t["priority"]}</span> '
        f'<strong>{t["title"]}</strong>'
        + (' <span style="color:#EF4444;font-weight:600;">· OVERDUE</span>'
           if overdue else "")
    )
    with st.container(border=True):
        st.markdown(header, unsafe_allow_html=True)
        st.caption(
            f"Category: {t['category']} · Status: {t['status']} · "
            f"Due: {fmt_date(t['due_date'])} · Created: {fmt_date(t['created_at'])}"
        )
        if t["description"]:
            st.write(t["description"])

        edit_col, complete_col, delete_col = st.columns([2, 1, 1])

        with edit_col:
            with st.expander("✏️ Edit"):
                with st.form(f"edit_task_{t['id']}"):
                    new_title = st.text_input("Title", value=t["title"],
                                              key=f"t_title_{t['id']}")
                    new_desc = st.text_area("Description",
                                            value=t["description"] or "",
                                            key=f"t_desc_{t['id']}")
                    ec1, ec2 = st.columns(2)
                    new_priority = ec1.selectbox(
                        "Priority", PRIORITIES,
                        index=PRIORITIES.index(t["priority"])
                        if t["priority"] in PRIORITIES else 1,
                        key=f"t_pri_{t['id']}",
                    )
                    new_category = ec2.text_input(
                        "Category", value=t["category"], key=f"t_cat_{t['id']}"
                    )
                    ec3, ec4 = st.columns(2)
                    new_status = ec3.selectbox(
                        "Status", STATUSES,
                        index=STATUSES.index(t["status"])
                        if t["status"] in STATUSES else 0,
                        key=f"t_status_{t['id']}",
                    )
                    try:
                        current_due = (date.fromisoformat(t["due_date"])
                                       if t["due_date"] else date.today())
                    except ValueError:
                        current_due = date.today()
                    new_due = ec4.date_input("Due date", value=current_due,
                                             key=f"t_due_{t['id']}")
                    if st.form_submit_button("Save changes"):
                        db.update_task(
                            t["id"],
                            title=new_title.strip() or t["title"],
                            description=new_desc.strip(),
                            priority=new_priority,
                            category=new_category.strip() or "General",
                            status=new_status,
                            due_date=new_due.isoformat() if new_due else None,
                        )
                        st.success("Task updated.")
                        st.rerun()

        with complete_col:
            if t["status"] != "Completed":
                if st.button("✅ Complete", key=f"done_{t['id']}",
                             use_container_width=True):
                    db.update_task(t["id"], status="Completed")
                    st.rerun()
            else:
                if st.button("↩️ Reopen", key=f"reopen_{t['id']}",
                             use_container_width=True):
                    db.update_task(t["id"], status="Pending")
                    st.rerun()

        with delete_col:
            if st.button("🗑️ Delete", key=f"del_{t['id']}",
                         use_container_width=True):
                st.session_state[f"confirm_del_{t['id']}"] = True

        if st.session_state.get(f"confirm_del_{t['id']}"):
            st.warning(f"Permanently delete “{t['title']}”? This cannot be undone.")
            cc1, cc2 = st.columns(2)
            if cc1.button("Yes, delete", key=f"yes_{t['id']}",
                          use_container_width=True):
                db.delete_task(t["id"])
                st.session_state.pop(f"confirm_del_{t['id']}", None)
                st.rerun()
            if cc2.button("Cancel", key=f"no_{t['id']}", use_container_width=True):
                st.session_state.pop(f"confirm_del_{t['id']}", None)
                st.rerun()