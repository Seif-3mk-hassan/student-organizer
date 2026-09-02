"""ICS import/export — 5MB cap, transactional, timezone-aware."""
from datetime import datetime, timedelta
from pathlib import Path
from icalendar import Calendar, Event
import io

MAX_BYTES = 5 * 1024 * 1024

def export_ics(assignments: list[dict], timetable: list[dict]) -> bytes:
    cal = Calendar()
    cal.add("prodid", "-//student-organizer//EN")
    cal.add("version", "2.0")
    for a in assignments:
        e = Event()
        e.add("summary", a["title"])
        e.add("dtstart", a["due_date"])
        e.add("dtend", a["due_date"] + timedelta(hours=1))
        e.add("description", f"course:{a.get('course_id','')}")
        cal.add_component(e)
    return cal.to_ical()

def parse_ics(data: bytes) -> list[dict]:
    if len(data) > MAX_BYTES:
        raise ValueError("ICS too large — 5MB cap")
    try:
        cal = Calendar.from_ical(data)
    except Exception as e:
        raise ValueError(f"parse failed line 0: {e}")
    out = []
    for comp in cal.walk():
        if comp.name == "VEVENT":
            try:
                summary = str(comp.get("summary", ""))
                dt = comp.get("dtstart").dt  # type: ignore
                if not isinstance(dt, datetime):
                    # date → midnight
                    dt = datetime(dt.year, dt.month, dt.day)
                out.append({"title": summary, "due_date": dt})
            except Exception as e:
                raise ValueError(f"bad VEVENT {summary}: {e}")
    return out
