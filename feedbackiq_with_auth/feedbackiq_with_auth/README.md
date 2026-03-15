# 🧠 FeedbackIQ — with Database & Auth

## Default Login Credentials
| Username  | Password     | Role    |
|-----------|-------------|---------|
| admin     | admin123    | admin   |
| analyst1  | analyst123  | analyst |
| analyst2  | analyst456  | analyst |

## Quick Start
```bash
cd feedback_analysis
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python run.py
```
Visit: http://localhost:5000

## What's New (vs base project)

### Database (SQLite — `instance/feedbackiq_dev.db`)
| Table           | Purpose                                      |
|-----------------|----------------------------------------------|
| `users`         | Login accounts, hashed passwords, roles      |
| `analyses`      | Every analysis session with aggregated stats |
| `feedback_items`| Individual feedback rows per session         |
| `audit_log`     | INSERT / DELETE operations with user + time  |

### Auth Pages
| Route               | Description                          |
|---------------------|--------------------------------------|
| `/login`            | Sign in                              |
| `/register`         | Self-registration (analyst role)     |
| `/logout`           | Sign out + flash message             |
| `/profile`          | Change name & password               |
| `/admin/users`      | Admin: create/delete/reset users     |

### Protected Routes
All main pages (`/`, `/upload`, `/results`, `/history`, `/audit-log`) 
now require login. Unauthenticated requests redirect to `/login`.

### New Pages
- `/history` — Browse all past analyses from the DB
- `/audit-log` — See all INSERT/DELETE operations

### API Endpoints Added
| Method | Endpoint                    | Description              |
|--------|-----------------------------|--------------------------|
| GET    | `/api/analyses`             | List all analyses        |
| GET    | `/api/analyses/<id>`        | Get single analysis      |
| DELETE | `/api/analyses/<id>`        | Delete analysis          |
| GET    | `/api/stats`                | Aggregated DB stats      |
| GET    | `/api/audit-log`            | Audit log entries        |
| GET    | `/api/users`                | User list (login req.)   |

## Production
```bash
gunicorn run:app --workers 4 --bind 0.0.0.0:8000
```
