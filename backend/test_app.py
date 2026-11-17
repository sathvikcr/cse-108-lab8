import os, tempfile
from app import create_app
from seed import seed
from models import db, User, Enrollment, Course

fd, path = tempfile.mkstemp(suffix=".db")
os.close(fd)
app = create_app("sqlite:///" + path)
seed(app, os.path.join(os.path.dirname(__file__), "data", "enrollment_example.xlsx"))


def login(u, p="password123"):
    c = app.test_client()
    assert c.post("/api/login", json=dict(username=u, password=p)).status_code == 200
    return c


def counts(c):
    return {x["name"]: f'{x["enrolled"]}/{x["capacity"]}' for x in c.get("/api/courses").json}

s = login("mnorris")
assert counts(s) == {"CS 106": "4/10", "CS 162": "4/4", "Math 101": "4/8", "Physics 121": "5/10"}, counts(s)
assert [c["name"] for c in s.get("/api/student/courses").json] == ["CS 106", "Physics 121"]
assert app.test_client().post("/api/login", json=dict(username="mnorris", password="x")).status_code == 401
cid = {c["name"]: c["id"] for c in s.get("/api/courses").json}
assert s.post(f"/api/courses/{cid['Math 101']}/enroll").status_code == 200
assert counts(s)["Math 101"] == "5/8"
assert s.post(f"/api/courses/{cid['Math 101']}/enroll").status_code == 409
assert s.post(f"/api/courses/{cid['CS 162']}/enroll").status_code == 409
assert counts(s)["CS 162"] == "4/4"
assert s.delete(f"/api/courses/{cid['Math 101']}/enroll").status_code == 200
assert counts(s)["Math 101"] == "4/8"
assert s.get("/api/teacher/courses").status_code == 403
assert app.test_client().get("/api/courses").status_code == 401
t = login("ahepworth")
assert sorted(c["name"] for c in t.get("/api/teacher/courses").json) == ["CS 106", "CS 162"]
r = t.get(f"/api/teacher/courses/{cid['CS 162']}").json
assert len(r["students"]) == 4
e = next(x for x in r["students"] if x["name"] == "Nancy Little")
assert t.put(f"/api/teacher/enrollments/{e['enrollment_id']}", json=dict(grade=88)).json["grade"] == 88
assert t.put(f"/api/teacher/enrollments/{e['enrollment_id']}", json=dict(grade=101)).status_code == 400
with app.app_context():
    grades = {x.course.name: x.grade for x in Enrollment.query.filter(Enrollment.student.has(display_name="Nancy Little"))}
    assert grades == {"Physics 121": 53, "CS 106": 57, "CS 162": 88}, grades
other = login("swalker")
assert other.get(f"/api/teacher/courses/{cid['CS 162']}").status_code == 404
assert other.put(f"/api/teacher/enrollments/{e['enrollment_id']}", json=dict(grade=1)).status_code == 404
assert s.get("/admin/").status_code == 403
a = login("admin", "admin123")
assert a.get("/admin/").status_code == 302
for p in ["/admin/user/", "/admin/course/", "/admin/enrollment/", "/admin/user/new/"]:
    assert a.get(p).status_code == 200, p

# Test deleting a student via admin doesn't break teacher roster
with app.app_context():
    nancy = User.query.filter_by(display_name="Nancy Little").first()
    nancy_id = nancy.id

del_res = a.post("/admin/user/delete/", data=dict(id=nancy_id), follow_redirects=True)
assert del_res.status_code == 200

# Verify teacher roster loads without error and Nancy is gone
r2 = t.get(f"/api/teacher/courses/{cid['CS 162']}").json
assert len(r2["students"]) == 3
assert all(x["name"] != "Nancy Little" for x in r2["students"])

print("All tests passed")
with app.app_context():
    db.session.remove()
    db.engine.dispose()
try:
    os.remove(path)
except OSError:
    pass
