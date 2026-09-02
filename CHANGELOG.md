# Changelog

All notable changes to this project will be documented in this file.

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
