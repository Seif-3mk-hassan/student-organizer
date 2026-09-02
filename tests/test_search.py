from backend.services.search import parse_quick_add, search, init_fts, index_item
from backend.database import Base, engine

def setup_module():
    Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine); init_fts()

def test_parse_tomorrow():
    r=parse_quick_add("HW3 due tomorrow", ["CS101"])
    assert r["due_date"] is not None

def test_parse_friday():
    r=parse_quick_add("CS101 HW3 due Friday", ["CS101"])
    assert r["course_code"]=="CS101"

def test_search_rank():
    index_item("note", 1, "midterm review algorithms")
    index_item("note", 2, "midterm review databases")
    res=search("midterm")
    assert len(res)>=1
