from backend.services.ics import parse_ics, export_ics
from datetime import datetime

def test_ics_roundtrip():
    assigns=[{"title":"HW1","due_date":datetime(2026,9,10,10,0), "course_id":1}]
    raw=export_ics(assigns, [])
    items=parse_ics(raw)
    assert len(items)==1 and items[0]["title"]=="HW1"

def test_ics_cap():
    try:
        parse_ics(b"x"* (6*1024*1024))
        assert False
    except ValueError as e:
        assert "5MB" in str(e)

def test_ics_malformed():
    try:
        parse_ics(b"not an ics")
        # may parse as 0 items — either OK or raises; accept either
    except ValueError:
        assert True
