# CariFin Data & Engagement Dashboard

[![Render](https://img.shields.io/badge/Render-Deployed-brightgreen)](https://carifin-dashboard.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.10-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-red)](https://flask.palletsprojects.com/)

A comprehensive data dashboard for tracking participation and engagement across CariFin Games events. Built with Flask, SQLite, and modern web technologies.

---

## Overview

The **CariFin Data & Engagement Dashboard** provides a centralized platform for administrators, HR managers, and scorers to manage participants, track event registrations, upload results, and generate detailed performance reports. The system supports role-based access, CSV/Excel imports, and real-time analytics.

### Key Features

- **Role-based Authentication** – Admin, HR, and Scorer roles with distinct permissions
- **Admin Dashboard** – Real-time metrics, filters, and interactive charts (participation by institution, stage completion, gender split, age groups)
- **User Management** – Create, edit, deactivate/activate users with temporary password generation
- **Institution Management** – Add, edit, and manage institutions
- **Event & Season Management** – Create events, seasons, and link them together
- **HR Dashboard** – View institution-specific metrics and participant roster
- **Participant Management** – Add participants manually or import via CSV/Excel
- **Event Registration** – Register participants for events with search and filter capabilities
- **Scorer Dashboard** – Upload results via CSV, flag errors, and manage result entries
- **Admin Score Approval** – Review, approve, or reject uploaded results (respects closed seasons)
- **PDF Reporting** – Generate professional, chart-rich PDF reports (Admin & HR)
- **CSV Exports** – Export participant rosters and results data
- **Bulk Import** – Import participant master lists and season registration files (Excel/CSV)

---

## Technology Stack

| Layer | Technologies |
|-------|--------------|
| **Backend** | Python 3.10, Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Werkzeug |
| **Frontend** | HTML5, CSS3, JavaScript, Jinja2 Templates |
| **Database** | SQLite (SQLAlchemy ORM) |
| **Authentication** | JWT (JSON Web Tokens) with HTTP-only cookies |
| **Reporting** | ReportLab (PDF generation), Matplotlib (charts) |
| **File Processing** | Pandas, openpyxl (Excel/CSV imports) |
| **Deployment** | Render, Gunicorn |

---

## Live Demo

The application is deployed on Render and available at:  
[https://carifin-dashboard.onrender.com](https://carifin-dashboard.onrender.com)

### Test Credentials

| Role | Email | Password |
|------|-------|----------|
| **Admin** | `admin@carifin.com` | `Admin123!` |
| **HR (CBTT)** | `hr@cbtt.com` | `Hr123!` |
| **Scorer** | `scorer@carifin.com` | `Scorer123!` |

> **Note:** This is a prototype. Please do not use real data.

---

## Installation

### Prerequisites

- Python 3.10 or higher
- pip
- virtualenv (recommended)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/JasMintTea/Data-Engagement-Dashboard.git
cd Data-Engagement-Dashboard

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
export FLASK_APP=wsgi.py
export FLASK_ENV=development

# 5. Initialize the database and seed initial data
flask shell
>>> from App.database import db
>>> db.create_all()
>>> exit()
python seed.py

# 6. Run the application
flask run

```

### Running Tests

```bash
pytest App/tests/ -v
```

---

### Project Structure

Data-Engagement-Dashboard/
├── App/
│   ├── controllers/          # Business logic
│   ├── models/               # Database models (SQLAlchemy)
│   ├── views/                # Route handlers (blueprints)
│   ├── templates/            # Jinja2 HTML templates
│   ├── static/               # CSS, JavaScript, images
│   ├── pdf_report.py         # Admin PDF report generator
│   ├── hr_pdf_report.py      # HR PDF report generator
│   └── __init__.py           # Flask app factory
├── instance/                 # SQLite database file
├── tests/                    # Unit and integration tests
├── seed.py                   # Database seeding script
├── wsgi.py                   # Application entry point
├── requirements.txt          # Python dependencies
├── render.yaml               # Render deployment configuration
└── README.md

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | `your-secret-key` |
| `JWT_SECRET_KEY` | JWT signing key | `your-jwt-secret` |
| `FLASK_ENV` | Environment (development/production) | `production` |
| `SQLALCHEMY_DATABASE_URI` | Database URL | `sqlite:///carifin.db` |

---

## API Endpoints (Selected)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/login` | GET, POST | User login (session + JWT) |
| `/logout` | GET | Logout and clear JWT cookie |
| `/admin/dashboard` | GET | Admin dashboard with metrics & filters |
| `/admin/users` | GET | User management page |
| `/admin/institutions` | GET | Institution management |
| `/admin/scores` | GET | Score approval page |
| `/hr/dashboard` | GET | HR dashboard (institution-specific) |
| `/hr/register` | GET, POST | Register participants for events |
| `/hr/report` | GET | Download HR PDF report |
| `/scorer/upload-results` | GET, POST | Upload results CSV |
| `/scorer/flag-result/<id>` | POST | Toggle result error flag |
| `/admin/export/roster` | GET | Export participant roster as CSV |
| `/admin/export/results` | GET | Export results as CSV |
| `/admin/import/participants-csv` | POST | Import participants from CSV |
| `/admin/import-season` | POST | Import season registration Excel file |

---

### Team

- **Jasmin Hippolyte** – Project Lead, Backend, UI/UX
- **Andrea Birjah-Rampersad** – Frontend, Templates, Scorer Features
- **Vinayak Maharaj** – Backend, Admin Features, Excel Imports
