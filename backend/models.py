"""SQLAlchemy models — single source for GPA, timetable, FTS guard rails."""
from datetime import date, datetime, time
from sqlalchemy import (
    String, Integer, Float, Date, DateTime, Time, ForeignKey, Text, Boolean,
    CheckConstraint, UniqueConstraint, Index, event
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from .database import Base

class Semester(Base):
    __tablename__ = "semesters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (CheckConstraint("start_date < end_date", name="ck_semester_dates"),)
    courses: Mapped[list["Course"]] = relationship(back_populates="semester", cascade="all, delete-orphan")

class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    instructor: Mapped[str] = mapped_column(String(200), default="")
    room: Mapped[str] = mapped_column(String(100), default="")
    color: Mapped[str] = mapped_column(String(20), default="forest")  # constrained 6 hues in Pydantic
    semester: Mapped[Semester] = relationship(back_populates="courses")
    links: Mapped[list["CourseLink"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    timetable_slots: Mapped[list["TimetableSlot"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    grades: Mapped[list["Grade"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    attendance: Mapped[list["Attendance"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    notes: Mapped[list["Note"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    files: Mapped[list["File"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    __table_args__ = (
        CheckConstraint("credits > 0", name="ck_course_credits"),
        UniqueConstraint("semester_id", "code", name="uq_course_code_per_semester"),
        Index("ix_courses_semester", "semester_id"),
    )

class CourseLink(Base):
    __tablename__ = "course_links"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(40), default="other")
    course: Mapped[Course] = relationship(back_populates="links")

class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="todo", nullable=False)  # todo/done
    course: Mapped[Course] = relationship(back_populates="assignments")
    @hybrid_property
    def is_late(self) -> bool:
        # end-of-day grace, local time (not UTC) to match frontend pillFor
        if self.status != "todo":
            return False
        # compare date only — assignment due today is not late until tomorrow
        return self.due_date.date() < datetime.now().date()
    __table_args__ = (Index("ix_assignments_due_status", "due_date", "status"), Index("ix_assignments_course", "course_id"))

class TimetableSlot(Base):
    __tablename__ = "timetable_slots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Mon
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    room: Mapped[str] = mapped_column(String(100), default="")
    course: Mapped[Course] = relationship(back_populates="timetable_slots")
    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="ck_day"),
        CheckConstraint("start_time < end_time", name="ck_time"),
        UniqueConstraint("course_id", "day_of_week", "start_time", name="uq_slot"),
        Index("ix_slots_day", "day_of_week"),
    )

class Grade(Base):
    __tablename__ = "grades"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, nullable=False)
    course: Mapped[Course] = relationship(back_populates="grades")
    __table_args__ = (
        CheckConstraint("weight BETWEEN 0 AND 100", name="ck_weight"),
        CheckConstraint("max_score > 0", name="ck_max"),
        CheckConstraint("score >= 0 AND score <= max_score", name="ck_score"),
        Index("ix_grades_course", "course_id"),
    )

class Attendance(Base):
    __tablename__ = "attendance"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # present/absent/excused
    course: Mapped[Course] = relationship(back_populates="attendance")
    __table_args__ = (UniqueConstraint("course_id", "date", name="uq_attendance"),)

class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    course: Mapped[Course] = relationship(back_populates="notes")

class File(Base):
    __tablename__ = "files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(300), nullable=False)
    local_path: Mapped[str] = mapped_column(String(500), nullable=False)  # relative materials/<course>/<uuid>.<ext>
    tags: Mapped[str] = mapped_column(String(300), default="")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    course: Mapped[Course] = relationship(back_populates="files")

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    course: Mapped[Course | None] = relationship(back_populates="tasks")
