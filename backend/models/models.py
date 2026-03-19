from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum

class UserRole(enum.Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, values_callable=lambda obj: [e.value for e in obj]), default=UserRole.STUDENT)
    phone = Column(String(20), nullable=True)
    profile_photo = Column(Text, nullable=True)
    department = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    
    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")

class Course(Base):
    __tablename__ = "courses"
    id = Column("course_id", Integer, primary_key=True, index=True, autoincrement=True)
    course_name = Column(String(100), nullable=False)
    course_code = Column(String(50), nullable=True)
    department = Column(String(100), nullable=False)
    faculty_assigned = Column(String(100), nullable=True)
    seat_limit = Column(Integer, default=40)
    enrolled_students = Column(Integer, default=0)
    remaining_seats = Column(Integer, default=40)
    waitlist_count = Column(Integer, default=0)
    auto_expand_enabled = Column(Boolean, default=True)
    max_seat_limit = Column(Integer, default=200)
    course_description = Column(Text, nullable=True)
    course_duration = Column(String(50), nullable=True)
    credits = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    enrollments = relationship("Enrollment", back_populates="course")

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.course_id"))
    enrollment_date = Column(DateTime, default=datetime.utcnow)
    
    student = relationship("User", back_populates="enrollments", foreign_keys=[student_id])
    course = relationship("Course", back_populates="enrollments", foreign_keys=[course_id])

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=False)
    target_role = Column(String(50), nullable=True)
    course_id = Column(Integer, ForeignKey("courses.course_id"), nullable=True)
    status = Column(String(20), default="unread")
    timestamp = Column(DateTime, default=datetime.utcnow)

class SystemSetting(Base):
    __tablename__ = "system_settings"
    id = Column(Integer, primary_key=True, index=True)
    default_seat_increase = Column(Integer, default=10)
    auto_seat_expansion = Column(Boolean, default=True)
    enable_notifications = Column(Boolean, default=True)
    enable_email_alerts = Column(Boolean, default=False)
    max_seat_limit = Column(Integer, default=100)
    seat_expansion_threshold = Column(Integer, default=10)

class SystemActivity(Base):
    __tablename__ = "system_activities"
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class OTPRecord(Base):
    __tablename__ = "otp_records"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), index=True, nullable=False)
    otp = Column(String(10), nullable=False)
    expires_at = Column(DateTime, nullable=False)

class Suggestion(Base):
    __tablename__ = "suggestions"
    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.course_id"), nullable=True)
    status = Column(String(20), default="pending")
    timestamp = Column(DateTime, default=datetime.utcnow)

class Waitlist(Base):
    __tablename__ = "waitlist"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.course_id"))
    position = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    student = relationship("User")
    course = relationship("Course")

class FacultyPerformance(Base):
    __tablename__ = "faculty_performance"
    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("users.id"))
    courses_taught = Column(Integer, default=0)
    total_students = Column(Integer, default=0)
    rating = Column(String(10), default="0.0")
    popularity_score = Column(Integer, default=0)
    
    faculty = relationship("User")

class Analytics(Base):
    __tablename__ = "analytics"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.course_id"))
    demand_score = Column(Integer, default=0)
    growth_rate = Column(String(50), default="0%")
    forecast = Column(String(100), nullable=True)
    historical_enrollments = Column(Text, nullable=True) # JSON string of monthly data
    
    course = relationship("Course")
