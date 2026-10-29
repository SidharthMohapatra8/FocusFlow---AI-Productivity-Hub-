# ⚡ FocusFlow — AI Productivity Hub

A modern, single-user productivity dashboard built with **Python + Streamlit**.
Manage tasks, notes, a daily planner, goals, and Pomodoro focus sessions from
one clean interface — with productivity analytics and optional AI helpers.

---

## ✨ Features

- **Dashboard** — welcome hero, live stats, today's schedule, tasks due
  today, recent notes, and a task-completion donut chart.
- **Task Manager** — full CRUD, due dates, priority, category, status,
  search, filters, overdue highlighting, "today only" view, and confirm-
  before-delete.
- **Notes** — create / edit / pin / search / delete, category filters,
  persisted across restarts.
- **Daily Planner** — schedule activities per day; automatic **overlap
  warnings** and chronological display.
- **Goals** — create goals with target dates, track progress via sliders and
  progress bars, auto-complete at 100%, progress chart.
- **Pomodoro Focus Timer** — 25/5/15 modes, start / pause / resume / reset,
  session logging, and a documented limitation note about background tabs.
- **Analytics** — tasks completed today / week / month, 14-day completion
  trend, status distribution, goal progress, focus-session line chart —
  all built to degrade gracefully on empty data.
- **Settings** — light/dark theme, display-name preference, data summary,
  and a confirmation-gated "clear all data" control.
- **SQLite persistence** — auto-created DB and schema, parameterized
  queries, isolated DB module, graceful error handling.

> **Privacy:** FocusFlow is a **personal-use** app. It is not a multi-user
> service and does not implement authentication. Do not deploy it publicly
> if you need per-user isolation.

---

## 🗂️ Project structure
