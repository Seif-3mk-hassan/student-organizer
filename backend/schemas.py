from datetime import date, datetime, time
from typing import Optional, Literal
from pydantic import BaseModel, field_validator

ColorHue = Literal["forest","rust","ink","amber","slate","plum"]

class SemesterCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    is_active: bool = True

class CourseCreate(BaseModel):
    semester_id: int
    name: str
    code: str
    credits: int
    instructor: str = ""
    room: str = ""
    color: ColorHue = "forest"
    allowed_absences: int = 3
    @field_validator("credits")
    def _credits(cls, v):
        if v <= 0: raise ValueError("credits > 0")
        return v

class ExamCreate(BaseModel):
    course_id: int
    title: str
    date: datetime
    location: str = ""

class GlobalLinkCreate(BaseModel):
    label: str
    url: str
    pinned: bool = False
    @field_validator("url")
    def _url(cls, v):
        if not v.startswith(("https://","http://")): raise ValueError("url must be http(s)")
        return v

class ExpenseCreate(BaseModel):
    title: str
    amount: float
    date: date
    category: str = "other"

class HolidayCreate(BaseModel):
    name: str
    date: date

class CourseLinkCreate(BaseModel):
    course_id: int
    label: str
    url: str
    type: str = "other"
    @field_validator("url")
    def _url(cls, v):
        if not v.startswith(("https://","http://")): raise ValueError("url must be http(s)")
        if "javascript:" in v.lower(): raise ValueError("forbidden url")
        return v

class AssignmentCreate(BaseModel):
    course_id: int
    title: str
    due_date: datetime
    status: Literal["todo","done"] = "todo"

class TimetableSlotCreate(BaseModel):
    course_id: int
    day_of_week: int
    start_time: time
    end_time: time
    room: str = ""
    @field_validator("day_of_week")
    def _day(cls, v):
        if not 0 <= v <= 6: raise ValueError("0-6")
        return v

class GradeCreate(BaseModel):
    course_id: int
    item_name: str
    weight: float
    score: float
    max_score: float

class AttendanceCreate(BaseModel):
    course_id: int
    date: date
    status: Literal["present","absent","excused"]

class NoteCreate(BaseModel):
    course_id: int
    content: str

class FileCreate(BaseModel):
    course_id: int
    filename: str
    tags: str = ""

class TaskCreate(BaseModel):
    course_id: Optional[int] = None
    title: str
    due_date: Optional[datetime] = None

class QuickAddRequest(BaseModel):
    text: str
