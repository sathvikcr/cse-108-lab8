"""Build the SQLite DB from the example workbook.  Run:  python seed.py"""
import os
import openpyxl
from app import create_app
from models import db, User, Course, Enrollment

DEMO_PASSWORD = "password123"
ADMIN = ("admin", "admin123", "Administrator")


def username_for(name):
    parts = name.lower().split()
    return parts[0][0] + parts[-1]

def get_user(cache, name, role):
    name = name.strip()
    key = (name, role)
    if key not in cache:
        u = User(username=username_for(name), role=role, display_name=name)
        u.set_password(DEMO_PASSWORD)
        db.session.add(u)
        db.session.flush()
        cache[key] = u
    return cache[key]


def seed(app, xlsx):
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(username=ADMIN[0], role="admin", display_name=ADMIN[2])
        admin.set_password(ADMIN[1])
        db.session.add(admin)

        users, course, cur = {}, None, {}
        ws = openpyxl.load_workbook(xlsx).active
        for name, teacher, time, cap, student, grade in ws.iter_rows(min_row=2, values_only=True):
            if name:
                cur = dict(name=name.strip(), teacher=teacher, time=time, cap=cap)
                course = Course(name=cur["name"], time=cur["time"].strip(), capacity=cap,
                                teacher=get_user(users, cur["teacher"], "teacher"))
                db.session.add(course)
                db.session.flush()
            if not student:
                continue
            db.session.add(Enrollment(student=get_user(users, student, "student"),
                                      course=course, grade=grade))
        db.session.commit()


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    seed(create_app(), os.path.join(here, "data", "enrollment_example.xlsx"))
    print("Seeded. Teachers/students use password:", DEMO_PASSWORD, "| admin:", ADMIN[0], "/", ADMIN[1])