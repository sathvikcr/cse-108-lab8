import { useEffect, useState } from "react";
import { api } from "./api.js";

export default function App() {
  const [user, setUser] = useState(undefined);

  useEffect(() => {
    api.me().then(setUser).catch(() => setUser(null));
  }, []);

  if (user === undefined) return null;
  if (!user) return <Login onLogin={setUser} />;

  const signOut = async () => {
    await api.logout();
    setUser(null);
  };
  const greeting = user.role === "teacher" ? `Dr ${user.display_name.split(" ").pop()}` : user.display_name.split(" ")[0];

  return (
    <>
      <header className="bar">
        <span>Welcome {greeting}!</span>
        <strong>ACME University</strong>
        <button className="link" onClick={signOut}>Sign out</button>
      </header>
      <main>
        {user.role === "student" && <Student />}
        {user.role === "teacher" && <Teacher />}
        {user.role === "admin" && <Admin />}
      </main>
    </>
  );
}

function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      onLogin(await api.login(username, password));
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <form className="card login" onSubmit={submit}>
      <h1>ACME University</h1>
      <input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
      <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
      {error && <p className="error">{error}</p>}
      <button type="submit">Sign in</button>
    </form>
  );
}

function CourseTable({ courses, action }) {
  return (
    <table>
      <thead>
        <tr><th>Course Name</th><th>Teacher</th><th>Time</th><th>Students Enrolled</th>{action && <th />}</tr>
      </thead>
      <tbody>
        {courses.map((c) => (
          <tr key={c.id}>
            <td>{c.name}</td><td>{c.teacher}</td><td>{c.time}</td>
            <td>{c.enrolled}/{c.capacity}</td>
            {action && <td>{action(c)}</td>}
          </tr>
        ))}
        {courses.length === 0 && <tr><td colSpan="5" className="muted">No courses.</td></tr>}
      </tbody>
    </table>
  );
}

function Student() {
  const [tab, setTab] = useState("mine");
  const [mine, setMine] = useState([]);
  const [all, setAll] = useState([]);
  const [msg, setMsg] = useState(null);

  const load = async () => {
    const [m, a] = await Promise.all([api.myCourses(), api.allCourses()]);
    setMine(m);
    setAll(a);
  };
  useEffect(() => { load(); }, []);

  const run = async (fn, okText) => {
    try {
      await fn();
      setMsg({ ok: true, text: okText });
    } catch (err) {
      setMsg({ ok: false, text: err.message });
    }
    load();
  };

  return (
    <>
      <nav className="tabs">
        <button className={tab === "mine" ? "on" : ""} onClick={() => setTab("mine")}>Your Courses</button>
        <button className={tab === "all" ? "on" : ""} onClick={() => setTab("all")}>Add Courses</button>
      </nav>
      {msg && <p className={msg.ok ? "ok" : "error"}>{msg.text}</p>}
      {tab === "mine" ? (
        <CourseTable
          courses={mine}
          action={(c) => <button className="danger" onClick={() => run(() => api.drop(c.id), `Dropped ${c.name}.`)}>Drop</button>}
        />
      ) : (
        <CourseTable
          courses={all}
          action={(c) =>
            c.is_enrolled ? <span className="muted">Enrolled</span>
            : c.enrolled >= c.capacity ? <span className="muted">Full</span>
            : <button onClick={() => run(() => api.enroll(c.id), `Enrolled in ${c.name}.`)}>Add class</button>
          }
        />
      )}
    </>
  );
}

function Teacher() {
  const [courses, setCourses] = useState([]);
  const [open, setOpen] = useState(null);

  useEffect(() => { api.teacherCourses().then(setCourses); }, []);

  if (open) return <Roster data={open} onBack={() => setOpen(null)} />;
  return (
    <>
      <h2>Your Courses</h2>
      <table>
        <thead><tr><th>Course Name</th><th>Teacher</th><th>Time</th><th>Students Enrolled</th><th /></tr></thead>
        <tbody>
          {courses.map((c) => (
            <tr key={c.id}>
              <td>{c.name}</td><td>{c.teacher}</td><td>{c.time}</td><td>{c.enrolled}/{c.capacity}</td>
              <td><button className="link" onClick={async () => setOpen(await api.roster(c.id))}>View roster</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

function Roster({ data, onBack }) {
  const [students, setStudents] = useState(data.students);
  const [msg, setMsg] = useState(null);

  const save = async (s, value) => {
    try {
      const res = await api.setGrade(s.enrollment_id, value);
      setStudents((list) => list.map((x) => (x.enrollment_id === s.enrollment_id ? { ...x, grade: res.grade } : x)));
      setMsg({ ok: true, text: `Saved ${s.name}'s grade.` });
    } catch (err) {
      setMsg({ ok: false, text: err.message });
      const fresh = await api.roster(data.course.id);
      setStudents(fresh.students);
    }
  };

  return (
    <>
      <button className="link" onClick={onBack}>&larr; Back to courses</button>
      <h2>{data.course.name}</h2>
      {msg && <p className={msg.ok ? "ok" : "error"}>{msg.text}</p>}
      <table>
        <thead><tr><th>Student Name</th><th>Grade</th></tr></thead>
        <tbody>
          {students.map((s) => (
            <tr key={s.enrollment_id}>
              <td>{s.name}</td>
              <td><GradeInput student={s} onSave={save} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

function GradeInput({ student, onSave }) {
  const [value, setValue] = useState(student.grade ?? "");
  useEffect(() => setValue(student.grade ?? ""), [student.grade]);
  const commit = () => { if (String(value) !== String(student.grade ?? "")) onSave(student, value); };
  return (
    <input
      className="grade" type="number" min="0" max="100" value={value}
      onChange={(e) => setValue(e.target.value)}
      onBlur={commit}
      onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
    />
  );
}

function Admin() {
  return (
    <iframe
      title="Admin"
      src="/admin/"
      style={{ width: "100%", height: "80vh", border: "1px solid #d5dbe1", borderRadius: 8, background: "#fff" }}
    />
  );
}