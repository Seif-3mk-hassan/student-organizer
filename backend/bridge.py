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
            # snoozed items hidden until snoozed_until passes
            q = q.filter((models.Assignment.snoozed_until == None) | (models.Assignment.snoozed_until < datetime.now()))  # type: ignore
            rows = q.order_by(models.Assignment.due_date).all()
            return _ok([{"id": r.id, "title": r.title, "due": r.due_date.isoformat(), "status": r.status, "late": r.is_late, "course_id": r.course_id} for r in rows])
        finally: db.close()

    def updateAssignment(self, payload: dict):
        db = SessionLocal()
        try:
            a = db.query(models.Assignment).filter(models.Assignment.id == payload["id"]).first()
            if not a: return _err("not_found", "assignment not found")
            if "title" in payload:
                t = payload["title"]
                if not t or len(t) > 300: return _err("validation", "title 1-300", "title")
                a.title = t
            if "due_date" in payload:
                try:
                    a.due_date = datetime.fromisoformat(str(payload["due_date"]).replace("Z","+00:00"))
                except Exception:
                    return _err("validation", "due_date must be ISO datetime", "due_date")
            if "status" in payload:
                if payload["status"] not in ("todo","done"): return _err("validation", "status todo/done", "status")
                a.status = payload["status"]
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

    def listSlots(self, _=None):
        db = SessionLocal()
        try:
            rows = db.query(models.TimetableSlot).all()
            # join course for label
            out=[]
            for r in rows:
                c = db.query(models.Course).filter(models.Course.id==r.course_id).first()
                out.append({"id":r.id,"course_id":r.course_id,"code":c.code if c else "?", "name":c.name if c else "?", "day":r.day_of_week,"start":r.start_time.isoformat()[:5],"end":r.end_time.isoformat()[:5],"room":r.room})
            return _ok(out)
        finally: db.close()

    def deleteSlot(self, payload: dict):
        db = SessionLocal()
        try:
            r = db.query(models.TimetableSlot).filter(models.TimetableSlot.id==payload["id"]).first()
            if not r: return _err("not_found","slot not found")
            db.delete(r); db.commit(); return _ok({})
        except Exception as e:
            db.rollback(); return _err("db",str(e))
        finally: db.close()

    # grades + gpa
    def addGrade(self, payload: dict):
        try: d = schemas.GradeCreate(**payload)
        except Exception as e: return _err("validation", str(e))
        db = SessionLocal()
        try:
            g = models.Grade(**d.model_dump()); db.add(g); db.commit(); db.refresh(g)
            return _ok({"id": g.id})
        except Exception as e:
            db.rollback(); return _err("db", str(e))
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

    # exams
    def createExam(self, payload: dict):
        try: d = schemas.ExamCreate(**payload)
        except Exception as e: return _err("validation", str(e))
        db = SessionLocal()
        try:
            ex = models.Exam(**d.model_dump()); db.add(ex); db.commit(); db.refresh(ex); return _ok({"id": ex.id})
        except Exception as e: db.rollback(); return _err("db", str(e))
        finally: db.close()
    def listExams(self, _=None):
        db = SessionLocal()
        try:
            rows = db.query(models.Exam).order_by(models.Exam.date).all()
            out=[]
            for r in rows:
                delta = (r.date.date() - datetime.now().date()).days
                out.append({"id":r.id,"course_id":r.course_id,"title":r.title,"date":r.date.isoformat(),"location":r.location,"countdown": f"{delta}d" if delta>=0 else "past"})
            return _ok(out)
        finally: db.close()
    def deleteExam(self, payload: dict):
        _id = payload.get("id")
        if not _id: return _err("validation","id required","id")
        db = SessionLocal()
        try:
            r=db.query(models.Exam).filter(models.Exam.id==_id).first()
            if not r: return _err("not_found","exam")
            db.delete(r); db.commit(); return _ok({})
        except Exception as e: db.rollback(); return _err("db",str(e))
        finally: db.close()

    # tasks + pomodoro (frontend timer, just CRUD)
    def createTask(self, payload: dict):
        try: d = schemas.TaskCreate(**payload)
        except Exception as e: return _err("validation",str(e))
        db=SessionLocal()
        try:
            t=models.Task(**d.model_dump()); db.add(t); db.commit(); db.refresh(t); return _ok({"id":t.id})
        except Exception as e: db.rollback(); return _err("db",str(e))
        finally: db.close()
    def listTasks(self, _=None):
        db=SessionLocal()
        try: return _ok([{"id":r.id,"title":r.title,"done":r.done,"course_id":r.course_id} for r in db.query(models.Task).all()])
        finally: db.close()
    def toggleTask(self, payload: dict):
        _id = payload.get("id")
        if not _id: return _err("validation","id required","id")
        db=SessionLocal()
        try:
            r=db.query(models.Task).filter(models.Task.id==_id).first()
            if not r: return _err("not_found","task")
            r.done = not r.done; db.commit(); return _ok({"done":r.done})
        except Exception as e: db.rollback(); return _err("db", str(e))
        finally: db.close()
    def deleteTask(self, payload: dict):
        _id = payload.get("id")
        if not _id: return _err("validation","id required","id")
        db=SessionLocal()
        try:
            r=db.query(models.Task).filter(models.Task.id==_id).first()
            if not r: return _err("not_found","task")
            db.delete(r); db.commit()
            return _ok({})
        except Exception as e: db.rollback(); return _err("db", str(e))
        finally: db.close()

    # snooze/dismiss
    def snoozeAssignment(self, payload: dict):
        _id = payload.get("id")
        if not _id: return _err("validation","id required","id")
        db=SessionLocal()
        try:
            a=db.query(models.Assignment).filter(models.Assignment.id==_id).first()
            if not a: return _err("not_found","assignment")
            # snooze 1 day
            from datetime import timedelta
            a.snoozed_until = datetime.now() + timedelta(days=1); db.commit(); return _ok({})
        except Exception as e: db.rollback(); return _err("db", str(e))
        finally: db.close()
    def dismissAssignment(self, payload: dict):
        return self.updateAssignment({"id": payload["id"], "status":"done"})

    # digest
    def getDigest(self, _=None):
        from datetime import timedelta
        db=SessionLocal()
        try:
            today=datetime.now().date()
            week=today+timedelta(days=7)
            # push due filter to SQL + exclude snoozed
            due_week=db.query(models.Assignment).filter(
                models.Assignment.status=="todo",
                models.Assignment.due_date >= datetime.combine(today, datetime.min.time()),
                models.Assignment.due_date <= datetime.combine(week, datetime.max.time()),
                (models.Assignment.snoozed_until == None) | (models.Assignment.snoozed_until < datetime.now())  # type: ignore
            ).count()
            exams=db.query(models.Exam).count()
            return _ok({"due_week": due_week, "exams": exams, "tasks": db.query(models.Task).filter(models.Task.done==False).count()})
        finally: db.close()

    # holidays / academic calendar
    def addHoliday(self, payload: dict):
        try: d=schemas.HolidayCreate(**payload)
        except Exception as e: return _err("validation",str(e))
        db=SessionLocal()
        try: h=models.Holiday(**d.model_dump()); db.add(h); db.commit(); return _ok({"id":h.id})
        except Exception as e: db.rollback(); return _err("db", str(e))
        finally: db.close()
    def listHolidays(self, _=None):
        db=SessionLocal()
        try: return _ok([{"id":r.id,"name":r.name,"date":r.date.isoformat()} for r in db.query(models.Holiday).order_by(models.Holiday.date).all()])
        finally: db.close()

    # global links
    def addGlobalLink(self, payload: dict):
        try: d=schemas.GlobalLinkCreate(**payload)
        except Exception as e: return _err("validation",str(e))
        db=SessionLocal()
        try: gl=models.GlobalLink(**d.model_dump()); db.add(gl); db.commit(); return _ok({"id":gl.id})
        except Exception as e: db.rollback(); return _err("db", str(e))
        finally: db.close()
    def listGlobalLinks(self, _=None):
        db=SessionLocal()
        try: return _ok([{"id":r.id,"label":r.label,"url":r.url,"pinned":r.pinned} for r in db.query(models.GlobalLink).all()])
        finally: db.close()
    def togglePinLink(self, payload: dict):
        _id = payload.get("id")
        if not _id: return _err("validation","id required","id")
        db=SessionLocal()
        try:
            r=db.query(models.GlobalLink).filter(models.GlobalLink.id==_id).first()
            if not r: return _err("not_found","link")
            r.pinned=not r.pinned; db.commit(); return _ok({"pinned":r.pinned})
        except Exception as e: db.rollback(); return _err("db", str(e))
        finally: db.close()

    # expenses
    def addExpense(self, payload: dict):
        try: d=schemas.ExpenseCreate(**payload)
        except Exception as e: return _err("validation",str(e))
        db=SessionLocal()
        try: ex=models.Expense(**d.model_dump()); db.add(ex); db.commit(); return _ok({"id":ex.id})
        except Exception as e: db.rollback(); return _err("db", str(e))
        finally: db.close()
    def listExpenses(self, _=None):
        db=SessionLocal()
        try:
            rows=db.query(models.Expense).order_by(models.Expense.date.desc()).all()
            total=sum(r.amount for r in rows)
            return _ok({"items":[{"id":r.id,"title":r.title,"amount":r.amount,"date":r.date.isoformat(),"category":r.category} for r in rows],"total":total})
        finally: db.close()

    # credit progress
    def getCreditProgress(self, _=None):
        TOTAL_CREDITS = 144
        db=SessionLocal()
        try:
            done=sum(c.credits for c in db.query(models.Course).all())
            return _ok({"done":done,"total":TOTAL_CREDITS,"pct": round(done/TOTAL_CREDITS*100,1) if TOTAL_CREDITS else 0})
        finally: db.close()

    # CSV import
    def importCsv(self, payload: dict):
        import csv, io
        text=payload.get("csv","")
        if not text.strip(): return _err("csv","empty")
        f=io.StringIO(text)
        reader=csv.DictReader(f)
        db=SessionLocal()
        try:
            sem=db.query(models.Semester).filter(models.Semester.is_active==True).first() or db.query(models.Semester).first()
            if not sem:
                sem=models.Semester(name="Imported", start_date=datetime.now().date(), end_date=datetime.now().date()); db.add(sem); db.flush()
            count=0; seen=set()
            for row in reader:
                code=(row.get("code") or row.get("Code") or "").strip()
                name=(row.get("name") or row.get("Name") or code).strip()
                if not code: continue
                if code in seen: continue
                seen.add(code)
                try:
                    credits=int(float(row.get("credits") or row.get("Credits") or 3))
                except ValueError:
                    return _err("csv", f"bad credits for {code}", "credits")
                # dedup against DB
                if db.query(models.Course).filter(models.Course.semester_id==sem.id, models.Course.code==code).first():
                    continue
                db.add(models.Course(semester_id=sem.id, name=name, code=code, credits=credits))
                count+=1
            db.commit(); return _ok({"imported":count})
        except Exception as e: db.rollback(); return _err("csv",str(e))
        finally: db.close()

    # files/notes helpers already exist; add list
    def listFiles(self, payload: dict):
        db=SessionLocal()
        try: return _ok([{"id":r.id,"filename":r.filename,"tags":r.tags} for r in db.query(models.File).filter(models.File.course_id==payload["course_id"]).all()])
        finally: db.close()
    def listNotes(self, payload: dict):
        db=SessionLocal()
        try: return _ok([{"id":r.id,"content":r.content} for r in db.query(models.Note).filter(models.Note.course_id==payload["course_id"]).all()])
        finally: db.close()

api = Api()
