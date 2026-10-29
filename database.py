"""
database.py — SQLite persistence layer for FocusFlow.
All DB access goes through this module. Uses parameterized queries only.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from typing import Any, Optional

# Allow the DB path to be overridden (e.g. for tests or cloud mounts).
DB_PATH = os.environ.get("FOCUSFLOW_DB_PATH", "focusflow_data.db")


@contextmanager
def get_connection():
    """Yield a SQLite connection with row access by name; always close it."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        raise RuntimeError(f"Database error: {exc}") from exc
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they do not exist. Safe to call on every launch."""
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                due_date TEXT,
                priority TEXT NOT NULL DEFAULT 'Medium',
                category TEXT DEFAULT 'General',
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT DEFAULT '',
                category TEXT DEFAULT 'General',
                pinned INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS planner (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                activity_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                target_date TEXT,
                progress INTEGER NOT NULL DEFAULT 0,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS focus_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                duration_minutes INTEGER NOT NULL,
                completed_at TEXT NOT NULL
            );
            """
        )


# ---------- helpers ----------
def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _rows_to_dicts(rows) -> list[dict[str, Any]]:
    return [dict(r) for r in rows]


# ---------- TASKS ----------
def add_task(title, description="", due_date=None, priority="Medium",
             category="General", status="Pending") -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO tasks
               (title, description, due_date, priority, category, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, description, due_date, priority, category, status, _now()),
        )
        return cur.lastrowid


def get_tasks(status: Optional[str] = None, search: Optional[str] = None,
              category: Optional[str] = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM tasks WHERE 1=1"
    params: list[Any] = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if category:
        sql += " AND category = ?"
        params.append(category)
    if search:
        sql += " AND (title LIKE ? OR description LIKE ?)"
        like = f"%{search}%"
        params += [like, like]
    sql += " ORDER BY created_at DESC"
    with get_connection() as conn:
        return _rows_to_dicts(conn.execute(sql, params).fetchall())


def update_task(task_id: int, **fields) -> None:
    allowed = {"title", "description", "due_date", "priority", "category", "status"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    with get_connection() as conn:
        conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?",
                     list(updates.values()) + [task_id])


def delete_task(task_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def get_task_stats() -> dict[str, int]:
    today = date.today().isoformat()
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        completed = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status = 'Completed'").fetchone()[0]
        pending = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status != 'Completed'").fetchone()[0]
        overdue = conn.execute(
            """SELECT COUNT(*) FROM tasks
               WHERE status != 'Completed'
                 AND due_date IS NOT NULL AND due_date < ?""", (today,)).fetchone()[0]
        today_tasks = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE due_date = ?", (today,)).fetchone()[0]
    return {"total": total, "completed": completed,
            "pending": pending, "overdue": overdue, "today": today_tasks}


# ---------- NOTES ----------
def add_note(title, content="", category="General", pinned=False) -> int:
    now = _now()
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO notes (title, content, category, pinned, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, content, category, int(pinned), now, now),
        )
        return cur.lastrowid


def get_notes(search: Optional[str] = None,
              category: Optional[str] = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM notes WHERE 1=1"
    params: list[Any] = []
    if search:
        sql += " AND (title LIKE ? OR content LIKE ?)"
        like = f"%{search}%"
        params += [like, like]
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY pinned DESC, updated_at DESC"
    with get_connection() as conn:
        return _rows_to_dicts(conn.execute(sql, params).fetchall())


def update_note(note_id: int, **fields) -> None:
    allowed = {"title", "content", "category", "pinned"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if "pinned" in updates:
        updates["pinned"] = int(updates["pinned"])
    if not updates:
        return
    updates["updated_at"] = _now()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    with get_connection() as conn:
        conn.execute(f"UPDATE notes SET {set_clause} WHERE id = ?",
                     list(updates.values()) + [note_id])


def delete_note(note_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))


# ---------- PLANNER ----------
def add_activity(title, activity_date, start_time, end_time, description="") -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO planner
               (title, activity_date, start_time, end_time, description, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, activity_date, start_time, end_time, description, _now()),
        )
        return cur.lastrowid


def get_activities(activity_date: Optional[str] = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM planner"
    params: list[Any] = []
    if activity_date:
        sql += " WHERE activity_date = ?"
        params.append(activity_date)
    sql += " ORDER BY start_time ASC"
    with get_connection() as conn:
        return _rows_to_dicts(conn.execute(sql, params).fetchall())


def update_activity(activity_id: int, **fields) -> None:
    allowed = {"title", "activity_date", "start_time", "end_time", "description"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    with get_connection() as conn:
        conn.execute(f"UPDATE planner SET {set_clause} WHERE id = ?",
                     list(updates.values()) + [activity_id])


def delete_activity(activity_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM planner WHERE id = ?", (activity_id,))


# ---------- GOALS ----------
def add_goal(title, description="", target_date=None, progress=0) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO goals (title, description, target_date, progress, completed, created_at)
               VALUES (?, ?, ?, ?, 0, ?)""",
            (title, description, target_date, max(0, min(100, progress)), _now()),
        )
        return cur.lastrowid


def get_goals() -> list[dict[str, Any]]:
    with get_connection() as conn:
        return _rows_to_dicts(
            conn.execute("SELECT * FROM goals ORDER BY completed ASC, created_at DESC").fetchall())


def update_goal(goal_id: int, **fields) -> None:
    allowed = {"title", "description", "target_date", "progress", "completed"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if "progress" in updates:
        updates["progress"] = max(0, min(100, int(updates["progress"])))
    if not updates:
        return
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    with get_connection() as conn:
        conn.execute(f"UPDATE goals SET {set_clause} WHERE id = ?",
                     list(updates.values()) + [goal_id])


def delete_goal(goal_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))


# ---------- FOCUS SESSIONS ----------
def add_focus_session(duration_minutes: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO focus_sessions (duration_minutes, completed_at) VALUES (?, ?)",
            (duration_minutes, _now()),
        )


def get_focus_sessions() -> list[dict[str, Any]]:
    with get_connection() as conn:
        return _rows_to_dicts(
            conn.execute("SELECT * FROM focus_sessions ORDER BY completed_at DESC").fetchall())


def count_focus_sessions_today() -> int:
    today = date.today().isoformat()
    with get_connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM focus_sessions WHERE completed_at LIKE ?",
            (f"{today}%",)).fetchone()[0]


# ---------- UTILITIES ----------
def clear_all_data() -> None:
    """Wipe all user data (tables kept, rows removed)."""
    with get_connection() as conn:
        for table in ("tasks", "notes", "planner", "goals", "focus_sessions"):
            conn.execute(f"DELETE FROM {table}")


def distinct_values(column: str, table: str) -> list[str]:
    """Return distinct non-empty values for a whitelisted column/table pair."""
    whitelist = {
        ("category", "tasks"): "category",
        ("category", "notes"): "category",
    }
    if (column, table) not in whitelist:
        return []
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT DISTINCT {column} FROM {table} "
            f"WHERE {column} IS NOT NULL AND {column} != '' ORDER BY {column}"
        ).fetchall()
    return [r[0] for r in rows]


init_db()