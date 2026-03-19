-- CourseInsight Analytics – Database Schema
-- Matches the SQLAlchemy ORM models exactly.
-- Run once against a fresh MySQL database.

CREATE DATABASE IF NOT EXISTS course_analytics_db;
USE course_analytics_db;

-- ─────────────────────────────────────────────
-- Users Table
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(100) UNIQUE NOT NULL,
    password        VARCHAR(255) NOT NULL,
    role            ENUM('student', 'faculty', 'admin') DEFAULT 'student',
    phone           VARCHAR(20),
    profile_photo   TEXT,
    department      VARCHAR(100),
    year            INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- Courses Table
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS courses (
    course_id           INT AUTO_INCREMENT PRIMARY KEY,
    course_name         VARCHAR(100) NOT NULL,
    course_code         VARCHAR(50),
    department          VARCHAR(100) NOT NULL,
    faculty_assigned    VARCHAR(100),
    seat_limit          INT DEFAULT 40,
    enrolled_students   INT DEFAULT 0,
    remaining_seats     INT DEFAULT 40,
    waitlist_count      INT DEFAULT 0,
    auto_expand_enabled BOOLEAN DEFAULT TRUE,
    max_seat_limit      INT DEFAULT 200,
    course_description  TEXT,
    course_duration     VARCHAR(50),
    credits             INT DEFAULT 3,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- Enrollments Table
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS enrollments (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT,
    course_id       INT,
    enrollment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id)  REFERENCES courses(course_id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- Notifications Table
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    message     TEXT NOT NULL,
    target_role VARCHAR(50),
    course_id   INT,
    status      VARCHAR(20) DEFAULT 'unread',
    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────
-- Waitlist Table
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS waitlist (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    student_id  INT,
    course_id   INT,
    position    INT DEFAULT 1,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id)  REFERENCES courses(course_id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- System Settings
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS system_settings (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    default_seat_increase   INT DEFAULT 10,
    auto_seat_expansion     BOOLEAN DEFAULT TRUE,
    enable_notifications    BOOLEAN DEFAULT TRUE,
    enable_email_alerts     BOOLEAN DEFAULT FALSE,
    max_seat_limit          INT DEFAULT 100,
    seat_expansion_threshold INT DEFAULT 10
);

-- ─────────────────────────────────────────────
-- System Activity Log
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS system_activities (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    action    VARCHAR(255) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- OTP Records (for password reset)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS otp_records (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    email      VARCHAR(100) NOT NULL,
    otp        VARCHAR(10)  NOT NULL,
    expires_at DATETIME     NOT NULL
);

-- ─────────────────────────────────────────────
-- Suggestions
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS suggestions (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    message   TEXT NOT NULL,
    course_id INT,
    status    VARCHAR(20) DEFAULT 'pending',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────
-- Faculty Performance
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS faculty_performance (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    faculty_id       INT,
    courses_taught   INT DEFAULT 0,
    total_students   INT DEFAULT 0,
    rating           VARCHAR(10) DEFAULT '0.0',
    popularity_score INT DEFAULT 0,
    FOREIGN KEY (faculty_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- Analytics (demand forecasts)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS analytics (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    course_id               INT,
    demand_score            INT DEFAULT 0,
    growth_rate             VARCHAR(50) DEFAULT '0%',
    forecast                VARCHAR(100),
    historical_enrollments  TEXT,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- Realistic Course Seed Data
-- ─────────────────────────────────────────────
INSERT IGNORE INTO courses (course_name, course_code, department, seat_limit, enrolled_students, remaining_seats)
VALUES
    ('Data Structures',       'CS201', 'Computer Science',     50, 0, 50),
    ('Database Systems',      'CS210', 'Computer Science',     50, 0, 50),
    ('Machine Learning',      'CS305', 'Artificial Intelligence', 45, 0, 45),
    ('Artificial Intelligence','CS401','Artificial Intelligence', 45, 0, 45),
    ('Computer Networks',     'CS320', 'Computer Science',     40, 0, 40),
    ('Operating Systems',     'CS330', 'Computer Science',     40, 0, 40),
    ('Cloud Computing',       'CS450', 'Information Technology', 40, 0, 40),
    ('Cyber Security',        'CS460', 'Information Technology', 40, 0, 40),
    ('Data Analytics',        'CS470', 'Data Science',         40, 0, 40),
    ('Software Engineering',  'CS480', 'Software Engineering', 40, 0, 40);
