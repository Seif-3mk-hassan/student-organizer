# Changelog

All notable changes to this project will be documented in this file.

## [0.3.0] - 2026-09-02

### Added
- Exams with countdown, Tasks + Pomodoro 25:00 + progress/streak, Digest This week, Snooze ?
- Timetable weekly grid 08-20 with overlap banner, Holidays, Global links pin, Expenses tracker
- CSV import (dedup, active semester), Credit 144 progress, Files/Notes UIs, Attendance cap
- Auto-migrate existing DB (allowed_absences, snoozed_until + 4 tables)

### Fixed
- Review was cancelled (no findings) — prior high/high2/design fixes already landed in 0.2.2
- feat branch now 10 commits ahead of main
## [0.2.2] - 2026-09-02

### Fixed
- GPA/edit: 5 courses != GPA until grades, add per-course Add grade + Delete course + delete/done on assignments
- Late: end-of-day grace (due today shows today green, tomorrow, in Nd) + pill Math.floor midnight fix
- High review: addGrade rollback, updateAssignment ISO + status validation, FTS quote escape + dedup, is_late local
- High2: logger handlers, quickAdd isoformat, XSS esc on course/assignment/palette, resolve_material relative_to
- Design: palette 200ms debounce, h1 text-wrap:balance + focus-visible ring, quickAdd once-flag leak
## [0.2.1] - 2026-09-02

### Fixed
- White window — create frontend/index.html and load via file:// URL so pywebview resolves css/js (app.py html string could not)
## [0.2.0] - 2026-09-02

### Added
- App scaffold: DB (platformdirs + WAL + Alembic + CHECKs), timetable_slots rename, 5 indexes + overlap guard
- Typed JS Bridge window.pywebview.api + wrapper {ok,error} + file jail materials/<course>/<uuid>
- FTS5 + palette Ctrl+K / / + quick-add N / CS101 HW3 due Friday parser
- Design system: tokens, sidebar 240->56, 5-state warm empties, 6 hues, 44px/kbd, DESIGN.md
- ICS import/export (5MB cap, transactional), attendance/links/notes, backup snapshot zip, one-dir + CI Win+Linux
- Notifications windows-toasts/notifypy + APScheduler stub, 6 test suites (gpa/bridge/files/ics/search/backup)

### Changed
- Spec bridge now implemented — pywebview HTML shell loads frontend/js/app.js

## [0.1.0] - 2026-09-02

### Added
- Student Organizer spec (docs/spec.md) — courses, timetable, assignments, GPA, files, notifications, ICS sync, pywebview+JS Bridge architecture
- CEO review (SELECTIVE, D1:B JS Bridge, 4 expansions accepted: palette, FTS5 search, overlap guard, quick-add; 2 deferred)
- Eng review (9 issues resolved: user-data DB + Alembic/WAL, typed bridge, file jail, one-dir+snapshot CI, CHECK constraints, timetable_slots rename, full test gap, indexes)
- Design review (3/10 -> 9/10: sidebar IA, 5-state table, storyboard, tokens + App UI anti-slop, 6-primitive vocab, window/kbd/a11y, 6 hues)

### Changed
- Spec now {ok,error} typed bridge contract (window.pywebview.api) — replaces threaded FastAPI thread
