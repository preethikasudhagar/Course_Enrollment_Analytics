from pydantic import BaseModel, Field
from typing import List, Optional

class CourseBase(BaseModel):
    course_name: str
    course_code: Optional[str] = None
    department: str
    faculty_assigned: Optional[str] = None
    seat_limit: int
    auto_expand_enabled: bool = True
    max_seat_limit: int = 200
    course_description: Optional[str] = None
    course_duration: Optional[str] = None
    credits: int = 3

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    course_name: Optional[str] = None
    course_code: Optional[str] = None
    department: Optional[str] = None
    faculty_assigned: Optional[str] = None
    seat_limit: Optional[int] = None
    auto_expand_enabled: Optional[bool] = None
    max_seat_limit: Optional[int] = None
    course_description: Optional[str] = None
    course_duration: Optional[str] = None
    credits: Optional[int] = None

class CourseResponse(CourseBase):
    id: int
    enrolled_count: int = 0
    enrolled_students: int = 0
    remaining_seats: int = 0
    waitlist_count: int = 0
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
