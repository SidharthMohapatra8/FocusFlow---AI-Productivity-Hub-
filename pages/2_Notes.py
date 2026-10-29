"""Notes page — create, edit, pin, search, delete notes."""

from datetime import datetime

import streamlit as st

import database as db
from utils import init_state, inject_css, page_header, fmt_date

st.set_page_config(page_title="Notes · FocusFlow", page_icon="📝", layout="wide")
init_state()
inject_css()

page_header("📝 Notes", "Capture ideas, meeting notes, and reminders.")

# --- Create ---
with st.expander("➕ Add a new note", expanded=False):
    with st.form("new_note_form", clear_on_submit=True):
        title = st.text_input("Title *")
        category = st.text_input("Category", value="General")
        content = st.text_area("Content", height=140)
        pinned = st.checkbox("📌 Pin this note")
        submitted = st.form_submit_button("Save note", use_container_width=True)
        if submitted:
            if not title.strip():
                st.error("Title is required.")
            else:
                db.add_note(
                    title.strip(),
                    content.strip(),
                    category.strip() or "General",
                    pinned,
                )
                st.success("Note saved.")
                st.rerun()

# --- Filters ---
f1, f2 = st.columns([2, 1])
search = f1.text_input("Search notes", placeholder="Search title or content…")
categories = db.distinct_values("category", "notes")
filter_cat = f2.selectbox("Category", ["All"] + categories)

notes = db.get_notes(
    search=search or None,
    category=None if filter_cat == "All" else filter_cat,
)

st.markdown(f"### 🗒️ {len(notes)} note(s)")

if not notes:
    st.info("No notes yet — create one above, or adjust your filters.")

for n in notes:
    with st.container(border=True):
        pin_icon = "📌 " if n["pinned"] else ""
        st.markdown(
            f'{pin_icon}### {n["title"]}  '
            f'<span class="ff-pill">{n["category"]}</span>',
            unsafe_allow_html=True,
        )
        st.caption(
            f"Created {fmt_date(n['created_at'])} · "
            f"Updated {fmt_date(n['updated_at'])}"
        )
        if n["content"]:
            st.write(n["content"])

        col_edit, col_pin, col_del = st.columns([2, 1, 1])

        with col_edit:
            with st.expander("✏️ Edit"):
                with st.form(f"edit_note_{n['id']}"):
                    new_title = st.text_input("Title", value=n["title"],
                                              key=f"n_title_{n['id']}")
                    new_cat = st.text_input("Category", value=n["category"],
                                            key=f"n_cat_{n['id']}")
                    new_content = st.text_area("Content",
                                               value=n["content"] or "",
                                               height=140,
                                               key=f"n_content_{n['id']}")
                    new_pinned = st.checkbox("Pinned", value=bool(n["pinned"]),
                                             key=f"n_pin_{n['id']}")
                    if st.form_submit_button("Save changes"):
                        db.update_note(
                            n["id"],
                            title=new_title.strip() or n["title"],
                            content=new_content,
                            category=new_cat.strip() or "General",
                            pinned=new_pinned,
                        )
                        st.success("Note updated.")
                        st.rerun()

        with col_pin:
            label = "Unpin" if n["pinned"] else "📌 Pin"
            if st.button(label, key=f"pin_{n['id']}", use_container_width=True):
                db.update_note(n["id"], pinned=not bool(n["pinned"]))
                st.rerun()

        with col_del:
            if st.button("🗑️ Delete", key=f"ndel_{n['id']}",
                         use_container_width=True):
                st.session_state[f"confirm_note_{n['id']}"] = True

        if st.session_state.get(f"confirm_note_{n['id']}"):
            st.warning(f"Delete note “{n['title']}”? This cannot be undone.")
            c1, c2 = st.columns(2)
            if c1.button("Yes, delete", key=f"nyes_{n['id']}",
                         use_container_width=True):
                db.delete_note(n["id"])
                st.session_state.pop(f"confirm_note_{n['id']}", None)
                st.rerun()
            if c2.button("Cancel", key=f"nno_{n['id']}",
                         use_container_width=True):
                st.session_state.pop(f"confirm_note_{n['id']}", None)
                st.rerun()