async function request(method, url, body) {
  const res = await fetch(url, {
    method,
    credentials: "same-origin",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(data.error || "Request failed"), { status: res.status });
  return data;
}

export const api = {
  me: () => request("GET", "/api/me"),
  login: (username, password) => request("POST", "/api/login", { username, password }),
  logout: () => request("POST", "/api/logout"),
  myCourses: () => request("GET", "/api/student/courses"),
  allCourses: () => request("GET", "/api/courses"),
  enroll: (id) => request("POST", `/api/courses/${id}/enroll`),
  drop: (id) => request("DELETE", `/api/courses/${id}/enroll`),
  teacherCourses: () => request("GET", "/api/teacher/courses"),
  roster: (id) => request("GET", `/api/teacher/courses/${id}`),
  setGrade: (eid, grade) => request("PUT", `/api/teacher/enrollments/${eid}`, { grade }),
};