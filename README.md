# CSE 108 - Lab 8: Course Enrollment System

A full-stack Course Enrollment application featuring role-based access control (Student, Teacher, Admin), built with a Flask REST API backend and a React + Vite frontend.

## Tech Stack

- **Backend**: Python, Flask, Flask-SQLAlchemy, Flask-Login, Flask-Admin, SQLite
- **Frontend**: React, Vite, CSS
- **Testing**: Pytest

## Project Structure

```
Lab8/
├── backend/
│   ├── app.py             # Flask application & API routes
│   ├── models.py          # SQLAlchemy models (User, Course, Enrollment)
│   ├── seed.py            # Database initialization & seed data
│   ├── test_app.py        # Backend test suite
│   ├── requirements.txt   # Python dependencies
│   └── data/
│       └── enrollment_example.xlsx
├── frontend/
│   ├── src/
│   │   ├── App.jsx        # Main React component
│   │   ├── api.js         # API client helpers
│   │   ├── styles.css     # Styling
│   │   └── main.jsx       # React entry point
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Getting Started

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
python seed.py
python app.py
```

The Flask backend runs at `http://127.0.0.1:5000`.

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The React frontend runs at `http://localhost:5173`.
