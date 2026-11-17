from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        pass


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(16), nullable=False)
    display_name = db.Column(db.String(128), nullable=False)

    enrollments = db.relationship(
        "Enrollment", back_populates="student", cascade="all, delete-orphan", passive_deletes=True
    )
    courses_taught = db.relationship(
        "Course", back_populates="teacher", cascade="all, delete-orphan", passive_deletes=True
    )

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def __str__(self):
        return f"{self.display_name} ({self.role})"


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    time = db.Column(db.String(64), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)

    teacher = db.relationship("User", foreign_keys=[teacher_id], back_populates="courses_taught")
    enrollments = db.relationship(
        "Enrollment", back_populates="course", cascade="all, delete-orphan", passive_deletes=True
    )

    def __str__(self):
        return self.name


class Enrollment(db.Model):
    __table_args__ = (db.UniqueConstraint("student_id", "course_id"),)
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    grade = db.Column(db.Integer, nullable=True)

    student = db.relationship("User", foreign_keys=[student_id], back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")

    def __str__(self):
        s_name = self.student.display_name if self.student else f"User #{self.student_id}"
        c_name = self.course.name if self.course else f"Course #{self.course_id}"
        return f"{s_name} in {c_name}"
