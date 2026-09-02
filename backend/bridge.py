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

    def deleteCourse(self, payload: dict):
        db = SessionLocal()
        try:
            c = db.query(models.Course).filter(models.Course.id == payload["id"]).first()
            if not c: return _err("not_found", "course not found")
            db.delete(c); db.commit()
            return _ok({})
        except Exception as e:
            db.rollback(); return _err("db", str(e))
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
            return _ok([{"id": r.id, "title": r.title, "due": r.due_date.isoformat(), "status": r.status, "late": r.is_late, "course_id": r.course_id} for r in rows])
        finally: db.close()

    def updateAssignment(self, payload: dict):
        db = SessionLocal()
        try:
            a = db.query(models.Assignment).filter(models.Assignment.id == payload["id"]).first()
            if not a: return _err("not_found", "assignment not found")
            if "title" in payload: a.title = payload["title"]
            if "due_date" in payload: a.due_date = payload["due_date"]
            if "status" in payload: a.status = payload["status"]
            db.commit(); return _ok({})
        except Exception as e:
            db.rollback(); return _err("db", str(e))
        finally: db.close()

    def deleteAssignment(self, payload: dict):
        db = SessionLocal()
        try:
            a = db.query(models.Assignment).filter(models.Assignment.id == payload["id"]).first()
            if not a: return _err("not_found", "assignment not found")
            db.delete(a); db.commit(); return _ok({})
        except Exception as e:
            db.rollback(); return _err("db", str(e))
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

    def listGrades(self, payload: dict):
        db = SessionLocal()
        try:
            rows = db.query(models.Grade).filter(models.Grade.course_id == payload["course_id"]).all()
            return _ok([{"id": r.id, "item": r.item_name, "weight": r.weight, "score": r.score, "max": r.max_score} for r in rows])
        finally: db.close()

    def deleteGrade(self, payload: dict):
        db = SessionLocal()
        try:
            r = db.query(models.Grade).filter(models.Grade.id == payload["id"]).first()
            if not r: return _err("not_found","grade not found")
            db.delete(r); db.commit(); return _ok({})
        except Exception as e:
            db.rollback(); return _err("db", str(e))
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

    # attendance / links / notes
    def markAttendance(self, payload: dict):
        try: d = schemas.AttendanceCreate(**payload)
        except Exception as e: return _err("validation", str(e))
        db = SessionLocal()
        try:
            a = models.Attendance(**d.model_dump()); db.add(a); db.commit(); db.refresh(a)
            return _ok({"id": a.id})
        except Exception as e:
            db.rollback(); return _err("db", str(e), "date" if "uq_attendance" in str(e) else None)
        finally: db.close()

    def addLink(self, payload: dict):
        try: d = schemas.CourseLinkCreate(**payload)
        except Exception as e: return _err("validation", str(e))
        db = SessionLocal()
        try:
            l = models.CourseLink(**d.model_dump()); db.add(l); db.commit(); db.refresh(l)
            return _ok({"id": l.id})
        except Exception as e:
            db.rollback(); return _err("db", str(e))
        finally: db.close()

    def listLinks(self, payload: dict):
        db = SessionLocal()
        try:
            rows = db.query(models.CourseLink).filter(models.CourseLink.course_id == payload["course_id"]).all()
            return _ok([{"id": r.id, "label": r.label, "url": r.url} for r in rows])
        finally: db.close()

    def addNote(self, payload: dict):
        try: d = schemas.NoteCreate(**payload)
        except Exception as e: return _err("validation", str(e))
        db = SessionLocal()
        try:
            n = models.Note(**d.model_dump()); db.add(n); db.commit(); db.refresh(n)
            init_fts(); index_item("note", n.id, n.content)
            return _ok({"id": n.id})
        except Exception as e:
            db.rollback(); return _err("db", str(e))
        finally: db.close()

    def exportIcs(self, payload: dict | None = None):
        from .services.ics import export_ics
        db = SessionLocal()
        try:
            assigns = [{"title": r.title, "due_date": r.due_date, "course_id": r.course_id} for r in db.query(models.Assignment).all()]
            slots = []  # timetable not needed for export v1
            data = export_ics(assigns, slots)
            return _ok({"ics": data.decode()})
        finally: db.close()

    def importIcs(self, payload: dict):
        from .services.ics import parse_ics
        raw = payload.get("ics","").encode() if isinstance(payload.get("ics"), str) else payload.get("data", b"")
        try:
            items = parse_ics(raw)
        except Exception as e:
            return _err("ics", str(e))
        # transactional: create assignments for first course or need course_id
        db = SessionLocal()
        try:
            course_id = payload.get("course_id")
            if not course_id:
                c = db.query(models.Course).first()
                if not c: return _err("ics", "create a course first to import into")
                course_id = c.id
            for it in items:
                db.add(models.Assignment(course_id=course_id, title=it["title"], due_date=it["due_date"], status="todo"))
            db.commit()
            return _ok({"imported": len(items)})
        except Exception as e:
            db.rollback(); return _err("db", str(e))
        finally: db.close()

    def previewCarryOver(self, payload: dict):
        """Dry-run CEO D3.4 — what would copy from semester src -> dst name."""
        src_id = payload.get("semester_id")
        db = SessionLocal()
        try:
            src = db.query(models.Semester).filter(models.Semester.id == src_id).first()
            if not src: return _err("semester", "not found")
            courses = db.query(models.Course).filter(models.Course.semester_id == src_id).all()
            slots = sum(len(c.timetable_slots) for c in courses)
            assigns = sum(len(c.assignments) for c in courses)
            return _ok({"courses": len(courses), "slots": slots, "assignments": assigns, "would_copy": [c.code for c in courses]})
        finally: db.close()

    def carryOver(self, payload: dict):
        src_id = payload.get("semester_id"); new_name = payload.get("new_name")
        only_codes = set(payload.get("codes") or [])
        db = SessionLocal()
        try:
            src = db.query(models.Semester).filter(models.Semester.id == src_id).first()
            if not src: return _err("semester", "not found")
            dst = models.Semester(name=new_name or f"{src.name} (copy)", start_date=src.start_date, end_date=src.end_date)
            db.add(dst); db.flush()
            for c in db.query(models.Course).filter(models.Course.semester_id == src_id).all():
                if only_codes and c.code not in only_codes: continue
                nc = models.Course(semester_id=dst.id, name=c.name, code=c.code, credits=c.credits, instructor=c.instructor, room=c.room, color=c.color)
                db.add(nc); db.flush()
                for s in c.timetable_slots:
                    db.add(models.TimetableSlot(course_id=nc.id, day_of_week=s.day_of_week, start_time=s.start_time, end_time=s.end_time, room=s.room))
                for a in c.assignments:
                    db.add(models.Assignment(course_id=nc.id, title=a.title, due_date=a.due_date, status="todo"))
            db.commit()
            return _ok({"new_semester_id": dst.id})
        except Exception as e:
            db.rollback(); return _err("db", str(e))
        finally: db.close()

    def reportBug(self, _=None):
        from .services.logger import report_zip
        try:
            z = report_zip()
            return _ok({"size": len(z)})
        except Exception as e:
            return _err("report", str(e))

api = Api()
