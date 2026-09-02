"""FTS5 virtual table + quick-add parser."""
import re
from datetime import datetime, timedelta
from sqlalchemy import text
from ..database import engine

FTS_INIT = """
CREATE VIRTUAL TABLE IF NOT EXISTS fts_index USING fts5(
  kind, ref_id, content, tokenize='porter'
);
"""

def init_fts():
    with engine.begin() as c:
        c.execute(text(FTS_INIT))

def index_item(kind: str, ref_id: int, content: str):
    with engine.begin() as c:
        c.execute(text("INSERT INTO fts_index(kind, ref_id, content) VALUES (:k,:r,:c)"),
                  {"k": kind, "r": ref_id, "c": content})

def search(query: str, limit: int = 20):
    with engine.connect() as c:
        rows = c.execute(text("SELECT kind, ref_id, content, rank FROM fts_index WHERE fts_index MATCH :q ORDER BY rank LIMIT :lim"),
                         {"q": query, "lim": limit}).fetchall()
        return [{"kind": r[0], "id": r[1], "snippet": r[2][:120], "rank": r[3]} for r in rows]

# quick-add: "CS101 HW3 due Friday" -> course_code, title, due
def parse_quick_add(text: str, known_codes: list[str]) -> dict:
    m = re.search(r"(due\s+(.+))$", text, re.I)
    title = text
    due = None
    code = None
    for c in known_codes:
        if c.lower() in text.lower():
            code = c; break
    if m:
        title = text[:m.start()].strip()
        due_str = m.group(2).strip().lower()
        now = datetime.now()
        if "today" in due_str: due = now
        elif "tomorrow" in due_str: due = now + timedelta(days=1)
        elif "friday" in due_str:
            # next Friday
            delta = (4 - now.weekday()) % 7 or 7
            due = now + timedelta(days=delta)
    return {"title": title or text, "course_code": code, "due_date": due}
