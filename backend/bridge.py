"""Typed JS Bridge — single entry for pywebview."""
from typing import Any
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models, schemas
from .services import gpa as gpa_svc
from .services.files import save_material
from .services.search import search, parse_quick_add, init_fts, index_item
from datetime import datetime

def _ok(data: Any): return {"ok": True, "data": data}
def _err(code: str, msg: str, field: str | None = None): return {"ok": False, "error": {"code": code, "message": msg, "field": field}}

class Api:
    # semesters
    def createSemester(self, payload: dict):
        try:
            d = schemas.SemesterCreate(**payload)
        except Exception as e:
            return _err("validation", str(e))
        db: Session = SessionLocal()
        try:
            s = models.Semester(name=d.name, start_date=d.start_date, end_date=d.end_date, is_active=d.is_active)
            db.add(s); db.commit(); db.refresh(s)
            return _ok({"id": s.id})
        except Exception as e:
            db.rollback(); return _err("db", str(e))
        finally: db.close()

    def listSemesters(self, _=None):
        db = SessionLocal()
        try:
            rows = db.query(models.Semester).all()
            return _ok([{"id": r.id, "name": r.name, "is_active": r.is_active} for r in rows])
        finally: db.close()

    # courses
    def createCourse(self, payload: dict):
        try: d = schemas.CourseCreate(**payload)
        except Exception as e: return _err("validation", str(e))
        db = SessionLocal()
        try:
            c = models.Course(**d.model_dump())
            db.add(c); db.commit(); db.refresh(c)
            init_fts(); index_item("course", c.id, f"{c.code} {c.name}")
            return _ok({"id": c.id})
        except Exception as e:
            db.rollback(); return _err("db", str(e), "code" if "uq_course" in str(e) else None)
        finally: db.close()

    def listCourses(self, payload: dict | None = None):
        sem_id = (payload or {}).get("semester_id")
        db = SessionLocal()
        try:
            q = db.query(models.Course)
            if sem_id: q = q.filter(models.Course.semester_id == sem_id)
            rows = q.all()
            return _ok([{"id": r.id, "code": r.code, "name": r.name, "color": r.color, "credits": r.credits} for r in rows])
        finally: db.close()

    # assignments — thin wrapper, due_date iso
    def createAssignment(self, payload: dict):
        try: d = schemas.AssignmentCreate(**payload)
        except Exception as e: return _err("validation", str(e))
        db = SessionLocal()
        try:
            a = models.Assignment(course_id=d.course_id, title=d.title, due_date=d.due_date, status=d.status)
            db.add(a); db.commit(); db.refresh(a)
            init_fts(); index_item("assignment", a.id, a.title)
            return _ok({"id": a.id})
        except Exception as e:
            db.rollback(); return _err("db", str(e))
        finally: db.close()

    def listAssignments(self, payload: dict | None = None):
        db = SessionLocal()
        try:
            q = db.query(models.Assignment)
            if payload and payload.get("course_id"): q = q.filter(models.Assignment.course_id == payload["course_id"])
            rows = q.order_by(models.Assignment.due_date).all()
            return _ok([{"id": r.id, "title": r.title, "due": r.due_date.isoformat(), "status": r.status, "late": r.is_late} for r in rows])
        finally: db.close()

    # timetable with overlap guard
    def createSlot(self, payload: dict):
        try: d = schemas.TimetableSlotCreate(**payload)
        except Exception as e: return _err("validation", str(e))
        db = SessionLocal()
        try:
            # overlap check
            overlap = db.query(models.TimetableSlot).filter(
                models.TimetableSlot.day_of_week == d.day_of_week,
                models.TimetableSlot.start_time < d.end_time,
                models.TimetableSlot.end_time > d.start_time,
            ).first()
            if overlap:
                return _err("conflict", f"Overlaps with slot {overlap.id} — try another time", "start_time")
            s = models.TimetableSlot(**d.model_dump())
            db.add(s); db.commit(); db.refresh(s)
            return _ok({"id": s.id})
        except Exception as e:
            db.rollback(); return _err("db", str(e))
        finally: db.close()

    # grades + gpa
    def addGrade(self, payload: dict):
        try: d = schemas.GradeCreate(**payload)
        except Exception as e: return _err("validation", str(e))
        db = SessionLocal()
        try:
            g = models.Grade(**d.model_dump()); db.add(g); db.commit(); db.refresh(g)
            return _ok({"id": g.id})
        finally: db.close()

    def getGpa(self, payload: dict):
        cid = payload.get("course_id") if payload else None
        db = SessionLocal()
        try:
            q = db.query(models.Grade)
            if cid: q = q.filter(models.Grade.course_id == cid)
            rows = q.all()
            data = [{"weight": r.weight, "score": r.score, "max_score": r.max_score} for r in rows]
            return _ok({"gpa": gpa_svc.compute_gpa(data), "count": len(data)})
        finally: db.close()

    # search + quick-add
    def search(self, payload: dict):
        q = payload.get("q","")
        if len(q) < 2: return _ok([])
        init_fts()
        return _ok(search(q))

    def quickAdd(self, payload: dict):
        text = payload.get("text","")
        db = SessionLocal()
        try:
            codes = [r.code for r in db.query(models.Course).all()]
        finally: db.close()
        return _ok(parse_quick_add(text, codes))

    # backup
    def createBackup(self, _=None):
        from .services.backup import create_snapshot_zip
        try:
            z = create_snapshot_zip()
            return _ok({"size": len(z)})
        except Exception as e:
            return _err("backup", str(e))

api = Api()
