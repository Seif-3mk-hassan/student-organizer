# Design System — Student Organizer
> Promoted from CEO plan 2026-09-02 — SELECTIVE, JS Bridge

## Tokens
- `--bg #faf9f6` / dark `#0f1110`, `--surface #fff` / `#1a1d1c`, `--text #1a1a1a` / `#f2ede6`, `--border #e8e6e1`, `--accent #0e4d45` (forest), `--accent-2 #c45a2b` (rust)
- `--radius 8px`, `--radius-lg 12px`, `--space 4/8/12/24/32`, `Sora 600` headings, `Inter 400` body, 14/16/20, 4.5:1, visited distinct
- 6 hues: forest/rust/ink/amber/slate/plum — 12px dot + left border only

## IA
Sidebar 240→56px <1100px: Dashboard → Timetable → Courses → Assignments → Files → Grades → Settings. Dashboard order: Due today/tomorrow → This week → Quick-add+palette hint → GPA/attendance muted. Course tabs: Overview|Schedule|Assignments|Files+Notes|Links|Grades.

## Primitives
Sidebar, CourseCard (only card), AssignmentRow, TimelineSlot, EmptyState (warm CTA), Banner (retry)

## States
Loading=skeleton, Empty=warm CTA, Error=inline banner+retry, Partial=1-course, Success=list/timeline populated. See frontend/js/app.js warm copy.

## Responsive/kbd
min 1024×640, timetable sticky header + h-scroll, global Ctrl+K / / / N / Esc, Tab sidebar→main→quick-add, 44px targets
