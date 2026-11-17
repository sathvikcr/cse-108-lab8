from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(16), nullable=False)
    display_name = db.Column(db.String(128), nullable=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def __str__(self):
        return f"{self.display_name} ({self.role})"


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    time = db.Column(db.String(64), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)

    teacher = db.relationship("User", foreign_keys=[teacher_id])
    enrollments = db.relationship(
        "Enrollment", back_populates="course", cascade="all, delete-orphan"
    )

    def __str__(self):
        return self.name


class Enrollment(db.Model):
    __table_args__ = (db.UniqueConstraint("student_id", "course_id"),)
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    grade = db.Column(db.Integer, nullable=True)

    student = db.relationship("User", foreign_keys=[student_id])
    course = db.relationship("Course", back_populates="enrollments")

    def __str__(self):
        return f"{self.student.display_name} in {self.course.name}"