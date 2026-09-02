from backend.bridge import api
from backend.database import Base, engine

def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_bridge_validation():
    r=api.createCourse({"semester_id": 999, "code":"", "name":"", "credits": -1})
    assert not r["ok"]

def test_bridge_overlap():
    # need semester + course then two overlapping slots
    s=api.createSemester({"name":"T","start_date":"2026-09-01","end_date":"2026-12-01"})
    assert s["ok"]
    sid=s["data"]["id"]
    c=api.createCourse({"semester_id":sid,"code":"CS101","name":"Algo","credits":3})
    assert c["ok"]; cid=c["data"]["id"]
    a=api.createSlot({"course_id":cid,"day_of_week":0,"start_time":"10:00:00","end_time":"12:00:00"})
    assert a["ok"]
    b=api.createSlot({"course_id":cid,"day_of_week":0,"start_time":"11:00:00","end_time":"13:00:00"})
    assert not b["ok"] and b["error"]["code"]=="conflict"
