import os
from flask import Flask, jsonify, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, current_user
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from wtforms import PasswordField

from models import db, User, Course, Enrollment

BASE = os.path.dirname(os.path.abspath(__file__))


def create_app(db_uri=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri or "sqlite:///" + os.path.join(
        BASE, "enrollment.db"
    )
    db.init_app(app)

    login = LoginManager(app)

    @login.user_loader
    def load_user(uid):
        return db.session.get(User, int(uid))

    @login.unauthorized_handler
    def unauthorized():
        return jsonify(error="Not logged in"), 401

    def role_required(role):
        def deco(fn):
            def wrapper(*a, **kw):
                if not current_user.is_authenticated:
                    return jsonify(error="Not logged in"), 401
                if current_user.role != role:
                    return jsonify(error="Forbidden"), 403
                return fn(*a, **kw)
            wrapper.__name__ = fn.__name__
            return wrapper
        return deco

    def course_json(c, enrolled_ids=()):
        teacher_name = c.teacher.display_name if c.teacher else "Unknown Teacher"
        valid_enrollments = [e for e in c.enrollments if e.student]
        return dict(
            id=c.id, name=c.name, teacher=teacher_name, time=c.time,
            capacity=c.capacity, enrolled=len(valid_enrollments),
            is_enrolled=c.id in enrolled_ids,
        )

    def user_json(u):
        return dict(id=u.id, username=u.username, role=u.role, display_name=u.display_name)

    @app.post("/api/login")
    def api_login():
        d = request.get_json(silent=True) or {}
        u = User.query.filter_by(username=(d.get("username") or "").strip()).first()
        if not u or not u.check_password(d.get("password") or ""):
            return jsonify(error="Invalid username or password"), 401
        login_user(u)
        return jsonify(user_json(u))

    @app.post("/api/logout")
    def api_logout():
        logout_user()
        return jsonify(ok=True)

    @app.get("/api/me")
    def api_me():
        if not current_user.is_authenticated:
            return jsonify(error="Not logged in"), 401
        return jsonify(user_json(current_user))

    def my_course_ids():
        return {e.course_id for e in Enrollment.query.filter_by(student_id=current_user.id)}

    @app.get("/api/student/courses")
    @role_required("student")
    def student_my_courses():
        ids = my_course_ids()
        cs = Course.query.filter(Course.id.in_(ids)).order_by(Course.name).all() if ids else []
        return jsonify([course_json(c, ids) for c in cs])

    @app.get("/api/courses")
    @role_required("student")
    def student_all_courses():
        ids = my_course_ids()
        return jsonify([course_json(c, ids) for c in Course.query.order_by(Course.name)])

    @app.post("/api/courses/<int:cid>/enroll")
    @role_required("student")
    def enroll(cid):
        if not db.session.get(Course, cid):
            return jsonify(error="Course not found"), 404
        try:
            res = db.session.execute(
                text(
                    "INSERT INTO enrollment (student_id, course_id) "
                    "SELECT :s, :c WHERE (SELECT COUNT(*) FROM enrollment WHERE course_id=:c) "
                    "< (SELECT capacity FROM course WHERE id=:c)"
                ),
                {"s": current_user.id, "c": cid},
            )
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify(error="You are already enrolled in this course"), 409
        if res.rowcount == 0:
            return jsonify(error="This course is full"), 409
        return jsonify(ok=True)

    @app.delete("/api/courses/<int:cid>/enroll")
    @role_required("student")
    def drop(cid):
        e = Enrollment.query.filter_by(student_id=current_user.id, course_id=cid).first()
        if not e:
            return jsonify(error="You are not enrolled in this course"), 404
        db.session.delete(e)
        db.session.commit()
        return jsonify(ok=True)

    @app.get("/api/teacher/courses")
    @role_required("teacher")
    def teacher_courses():
        cs = Course.query.filter_by(teacher_id=current_user.id).order_by(Course.name)
        return jsonify([course_json(c) for c in cs])

    def own_course_or_404(cid):
        c = db.session.get(Course, cid)
        if not c or c.teacher_id != current_user.id:
            return None
        return c

    @app.get("/api/teacher/courses/<int:cid>")
    @role_required("teacher")
    def teacher_roster(cid):
        c = own_course_or_404(cid)
        if not c:
            return jsonify(error="Course not found"), 404
        valid_enrollments = [e for e in c.enrollments if e.student]
        roster = sorted(valid_enrollments, key=lambda e: e.student.display_name)
        return jsonify(
            course=course_json(c),
            students=[dict(enrollment_id=e.id, name=e.student.display_name, grade=e.grade)
                      for e in roster],
        )

    @app.put("/api/teacher/enrollments/<int:eid>")
    @role_required("teacher")
    def edit_grade(eid):
        e = db.session.get(Enrollment, eid)
        if not e or e.course.teacher_id != current_user.id:
            return jsonify(error="Enrollment not found"), 404
        g = (request.get_json(silent=True) or {}).get("grade")
        if g in (None, ""):
            e.grade = None
        else:
            try:
                g = int(g)
            except (TypeError, ValueError):
                return jsonify(error="Grade must be a whole number"), 400
            if not 0 <= g <= 100:
                return jsonify(error="Grade must be between 0 and 100"), 400
            e.grade = g
        db.session.commit()
        return jsonify(enrollment_id=e.id, grade=e.grade)

    class SecureMixin:
        def is_accessible(self):
            return current_user.is_authenticated and current_user.role == "admin"

        def inaccessible_callback(self, name, **kw):
            return "Admin login required. Sign in as an admin at the app's home page first.", 403

    class SecureIndex(SecureMixin, AdminIndexView):
        @expose("/")
        def index(self):
            return redirect(url_for("user.index_view"))

    class SecureView(SecureMixin, ModelView):
        pass

    class UserView(SecureView):
        column_exclude_list = ["password_hash"]
        form_excluded_columns = ["password_hash"]
        form_extra_fields = {"password": PasswordField("New password (leave blank to keep)")}
        form_choices = {"role": [("student", "student"), ("teacher", "teacher"), ("admin", "admin")]}

        def on_model_change(self, form, model, is_created):
            if form.password.data:
                model.set_password(form.password.data)
            elif is_created:
                raise ValueError("A password is required for new users")

        def on_model_delete(self, model):
            Enrollment.query.filter_by(student_id=model.id).delete()
            Course.query.filter_by(teacher_id=model.id).delete()

    class CourseView(SecureView):
        column_list = ["name", "teacher", "time", "capacity"]

    class EnrollmentView(SecureView):
        column_list = ["student", "course", "grade"]

    admin = Admin(app, name="ACME Admin", index_view=SecureIndex(), url="/admin")
    admin.add_view(UserView(User, db.session))
    admin.add_view(CourseView(Course, db.session))
    admin.add_view(EnrollmentView(Enrollment, db.session))

    with app.app_context():
        try:
            db.session.execute(text("DELETE FROM enrollment WHERE student_id NOT IN (SELECT id FROM user)"))
            db.session.execute(text("DELETE FROM enrollment WHERE course_id NOT IN (SELECT id FROM course)"))
            db.session.execute(text("DELETE FROM course WHERE teacher_id NOT IN (SELECT id FROM user)"))
            db.session.commit()
        except Exception:
            db.session.rollback()

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)