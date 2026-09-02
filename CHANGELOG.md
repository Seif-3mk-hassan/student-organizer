# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-09-02

### Added
- Student Organizer spec (docs/spec.md) — courses, timetable, assignments, GPA, files, notifications, ICS sync, pywebview+JS Bridge architecture
- CEO review (SELECTIVE, D1:B JS Bridge, 4 expansions accepted: palette, FTS5 search, overlap guard, quick-add; 2 deferred)
- Eng review (9 issues resolved: user-data DB + Alembic/WAL, typed bridge, file jail, one-dir+snapshot CI, CHECK constraints, timetable_slots rename, full test gap, indexes)
- Design review (3/10 -> 9/10: sidebar IA, 5-state table, storyboard, tokens + App UI anti-slop, 6-primitive vocab, window/kbd/a11y, 6 hues)

### Changed
- Spec now {ok,error} typed bridge contract (window.pywebview.api) — replaces threaded FastAPI thread

### Notes
- No application code yet — this is the plan checkpoint. Next: T1-T9 + design tokens implementation on same branch.

