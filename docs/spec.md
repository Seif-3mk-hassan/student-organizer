# Student Organizer App

Feature list and infrastructure plan — personal desktop app for a single student (no institutional/org layer)

## 1. Core Features

### Courses & Schedule
- Course list: name, code, credit hours, instructor, room
- Weekly timetable auto-generated from enrolled courses
- Exam schedule: dates, locations, countdown
- Semester/term management — archive past terms, keep history
- Course carry-over: repeat a template schedule next term

### Assignments & Deadlines
- Per-course assignments with due date and status (todo / done / late)
- Priority view: what's due soon across all courses
- Desktop notifications for upcoming deadlines, exams, class start times
- Daily/weekly digest view: "this week at a glance"
- Snooze/dismiss for reminders

### Grades & GPA
- Grade tracker per course (assignments, quizzes, exams, weighted)
- GPA calculator: per-semester and cumulative
- "What grade do I need on the final" calculator
- Semester comparison: GPA trend across terms

### Tasks & Productivity
- To-do list, optionally linked to a course
- Study session timer (Pomodoro-style)
- Streaks for task completion (optional gamification)
- Progress bars per course toward a passing grade (optional gamification)

### University-Linked Info
- Academic calendar, holidays, registration deadlines
- Manual or CSV import of courses/grades from the university portal
- Credit progress toward graduation (e.g. X / 144 credits done)

### Attendance (Self-Tracked)
- Mark your own attendance per class
- Absence counter vs. allowed limit
- Warning when nearing the absence cap

### Quick Links
- Per-course link fields: Drive folder, LMS/portal, assignment submission link, Zoom/Meet link, group chat
- Global links section: university portal, library, email, WiFi/VPN login, ID card system
- One-click open in default browser
- Icons/labels for scannability; pin frequently used links to a sidebar

### Files & Materials
- Local file storage per course (lecture PDFs, slides), not just links
- Simple search across filenames/notes
- Tagging materials (e.g. lecture 3, midterm review)

### Personal Layer
- Notes per course
- Optional expense/budget tracker for student life

### Calendar Integration
- Export schedule/deadlines to Google Calendar or .ics file
- Import university calendar (holidays, exam weeks) via .ics

### Customization
- Dark/light theme
- Customizable dashboard widgets (GPA, next deadline, today's classes)
- Color-coding per course

### Backup & Sync
- Local backup/export of the whole database (JSON/SQLite file)
- Optional cloud sync via Dropbox/Google Drive file sync (no backend needed)

### Social / Collaboration (optional, adds complexity)
- Shared course view with classmates (compare deadlines, not grades)
- Study group scheduling

## 2. Chosen Tech Stack & Infrastructure

### Application Shell
- pywebview renders the frontend (HTML/CSS/JS) in a native window — no browser chrome, lighter than Electron
- FastAPI backend (Python) runs locally, launched in a background thread from the same entrypoint that opens the pywebview window
- Single-user, offline-first — backend runs on localhost, no external server required
- Same FastAPI backend could later serve a mobile or web version

### Data Layer
- Local SQLite database via SQLAlchemy
- Pydantic schemas for request/response validation between frontend and API
- Local file storage folder for attached materials, organized per course

### Suggested Schema (starting point)
- `semesters` (id, name, start_date, end_date, is_active)
- `courses` (id, semester_id, name, code, credits, instructor, room)
- `course_links` (id, course_id, label, url, type)
- `assignments` (id, course_id, title, due_date, status)
- `schedule` (id, course_id, day_of_week, start_time, end_time)
- `grades` (id, course_id, item_name, weight, score, max_score)
- `attendance` (id, course_id, date, status)
- `notes` (id, course_id, content, created_at)
- `files` (id, course_id, filename, local_path, tags, uploaded_at)
- `tasks` (id, course_id nullable, title, due_date, done)

### Notifications
- plyer for a cross-platform notification wrapper, or native APIs directly: notify-send (Linux) / win10toast (Windows)
- Background scheduler in the FastAPI backend for deadline/reminder checks

### Calendar Import/Export
- ICS file generation for export (icalendar / ical-generator libraries)
- ICS parsing for import of university calendars

### Backup & Sync
- Manual export/import of the SQLite file or a JSON snapshot
- Optional: store the SQLite file inside a synced Dropbox/Drive folder for multi-device use

### Cross-Platform Target: Windows & Linux
- PyInstaller bundles app.py + backend + frontend assets into a single executable
- Build once on Windows and once on Linux — no true cross-compiling between OSes
- No macOS target in scope

### Project Structure

```
student-organizer/
  backend/
    main.py         — FastAPI app entrypoint
    database.py      — SQLite connection/session setup
    models.py         — SQLAlchemy models
    schemas.py         — Pydantic request/response schemas
    routers/            — courses, assignments, grades, schedule, attendance, links, files
    services/             — gpa.py, notifications.py, ics.py
    data/app.db             — SQLite file (created at runtime)
  frontend/
    index.html, css/style.css
    js/app.js, api.js, views/ (dashboard, courses, grades, schedule)
  app.py — pywebview entrypoint: launches FastAPI in a thread, opens window
  requirements.txt
  build/pyinstaller.spec
```

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | /plan-ceo-review | Scope & strategy | 1 | clean | 2 resolved (D1:B JS Bridge, D2:B SELECTIVE), 6 cherry-picks: 4 accepted / 2 deferred, 18 findings |
| Eng Review | /plan-eng-review | Architecture & tests (required) | 1 | clean | 9 issues (4 arch + 2 quality + 1 test + 1 perf + scope gate), 0 critical gaps, 9 tasks |
| Design Review | /plan-design-review | UI/UX gaps | 1 | clean | score: 3/10 -> 9/10, 7 decisions, 7 tasks (mockups N/A) |
| DX Review | /plan-devex-review | Developer experience gaps | 0 | — | not run |

**VERDICT:** CEO + ENG + DESIGN CLEAR — ready to implement. All required reviews complete.

NO UNRESOLVED DECISIONS

