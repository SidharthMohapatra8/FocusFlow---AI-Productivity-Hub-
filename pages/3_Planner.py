"""Daily Planner — schedule activities per day with overlap warnings."""

from datetime import date, datetime, time

import streamlit as st

import database as db
from utils import init_state, inject_css, page_header, fmt_date, card

st.set_page_config(page_title="Planner · FocusFlow", page_icon="📅", layout="wide")
init_state()
inject_css()

page_header("📅 Daily Planner", "Organize your day. Overlaps are flagged automatically.")


def _to_minutes(t: str) -> int:
    """Convert 'HH:MM' to minutes since midnight. Returns -1 on error."""
    try:
        h, m = t.split(":")[:2]
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        return -1


def _has_overlap(start_a: str, end_a: str,
                 start_b: str, end_b: str) -> bool:
    sa, ea = _to_minutes(start_a), _to_minutes(end_a)
    sb, eb = _to_minutes(start_b), _to_minutes(end_b)
    if min(sa, ea, sb, eb) < 0:
        return False
    return sa < eb and sb < ea


# --- Create ---
with st.expander("➕ Add activity", expanded=False):
    with st.form("new_activity_form", clear_on_submit=True):
        title = st.text_input("Activity title *")
        act_date = st.date_input("Date", value=date.today())
        c1, c2 = st.columns(2)
        start_t = c1.time_input("Start time", value=time(9, 0))
        end_t = c2.time_input("End time", value=time(10, 0))
        description = st.text_area("Description", height=70)
        submitted = st.form_submit_button("Add to planner", use_container_width=True)
        if submitted:
            if not title.strip():
                st.error("Title is required.")
            elif end_t <= start_t:
                st.error("End time must be after start time.")
            else:
                existing = db.get_activities(act_date.isoformat())
                overlap = any(
                    _has_overlap(
                        start_t.strftime("%H:%M"), end_t.strftime("%H:%M"),
                        a["start_time"], a["end_time"],
                    )
                    for a in existing
                )
                db.add_activity(
                    title.strip(),
                    act_date.isoformat(),
                    start_t.strftime("%H:%M"),
                    end_t.strftime("%H:%M"),
                    description.strip(),
                )
                if overlap:
                    st.warning("Activity saved, but it overlaps another one.")
                else:
                    st.success("Activity added.")
                st.rerun()

# --- Date selector ---
selected_date = st.date_input("View schedule for", value=date.today(),
                              key="planner_view_date")
activities = db.get_activities(selected_date.isoformat())

st.markdown(f"### 🗓️ {selected_date.strftime('%A, %B %d, %Y')}")

if not activities:
    st.info("No activities scheduled for this day.")

# Detect all overlapping pairs for highlighting
overlap_ids = set()
for i, a in enumerate(activities):
    for b in activities[i + 1:]:
        if _has_overlap(a["start_time"], a["end_time"],
                        b["start_time"], b["end_time"]):
            overlap_ids.add(a["id"])
            overlap_ids.add(b["id"])

for act in activities:
    overlap_badge = (
        ' <span class="ff-pill" style="background:#FEE2E2;color:#B91C1C;">'
        "⚠ Overlap</span>"
        if act["id"] in overlap_ids else ""
    )
    with st.container(border=True):
        st.markdown(
            f'**{act["start_time"]} – {act["end_time"]}** &nbsp; '
            f'### {act["title"]}{overlap_badge}',
            unsafe_allow_html=True,
        )
        if act["description"]:
            st.caption(act["description"])

        col_edit, col_del = st.columns([3, 1])

        with col_edit:
            with st.expander("✏️ Edit"):
                with st.form(f"edit_activity_{act['id']}"):
                    new_title = st.text_input("Title", value=act["title"],
                                              key=f"a_title_{act['id']}")
                    try:
                        old_date = date.fromisoformat(act["activity_date"])
                    except ValueError:
                        old_date = date.today()
                    new_date = st.date_input("Date", value=old_date,
                                             key=f"a_date_{act['id']}")
                    c1, c2 = st.columns(2)
                    try:
                        s_t = datetime.strptime(act["start_time"], "%H:%M").time()
                        e_t = datetime.strptime(act["end_time"], "%H:%M").time()
                    except ValueError:
                        s_t, e_t = time(9, 0), time(10, 0)
                    new_start = c1.time_input("Start", value=s_t,
                                              key=f"a_start_{act['id']}")
                    new_end = c2.time_input("End", value=e_t,
                                            key=f"a_end_{act['id']}")
                    new_desc = st.text_area("Description",
                                            value=act["description"] or "",
                                            key=f"a_desc_{act['id']}")
                    if st.form_submit_button("Save changes"):
                        if new_end <= new_start:
                            st.error("End time must be after start time.")
                        else:
                            db.update_activity(
                                act["id"],
                                title=new_title.strip() or act["title"],
                                activity_date=new_date.isoformat(),
                                start_time=new_start.strftime("%H:%M"),
                                end_time=new_end.strftime("%H:%M"),
                                description=new_desc.strip(),
                            )
                            st.success("Activity updated.")
                            st.rerun()

        with col_del:
            if st.button("🗑️ Delete", key=f"adel_{act['id']}",
                         use_container_width=True):
                st.session_state[f"confirm_act_{act['id']}"] = True

        if st.session_state.get(f"confirm_act_{act['id']}"):
            st.warning(f"Delete “{act['title']}”?")
            c1, c2 = st.columns(2)
            if c1.button("Yes, delete", key=f"ayes_{act['id']}",
                         use_container_width=True):
                db.delete_activity(act["id"])
                st.session_state.pop(f"confirm_act_{act['id']}", None)
                st.rerun()
            if c2.button("Cancel", key=f"ano_{act['id']}",
                         use_container_width=True):
                st.session_state.pop(f"confirm_act_{act['id']}", None)
                st.rerun()