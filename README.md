# SkillFit

## Project Overview
SkillFit is an AI-powered student placement intelligence platform designed for students and faculty mentors. Our main objective is to provide an evidence-based placement intelligence approach to help students prepare for their careers and assist faculty in mentoring them effectively.

## Tech Stack
**Frontend:**
* Next.js
* React
* TypeScript
* Tailwind CSS

**Backend:**
* FastAPI

**Database:**
* PostgreSQL

**NLP:**
* spaCy

**LLM:**
* Gemini 3.1 Pro
* Sonnet 4.6

**Future:**
* Scikit-Learn
* XGBoost
* ChromaDB
* LangGraph

## Current Phase
Phase 5 – Intelligent Placement Matching Engine & Unified Analytics

## Current Status
- Phase 1 (Project Foundation & System Setup): Completed
- Phase 2 (Authentication & Role-Based Access Control): Completed
- Phase 3 (Evidence-Based CV Analysis & Intelligence Extraction): Completed
- Phase 4 (Drive Intelligence Extraction & Snapshot Architecture): Completed
- Phase 5 (Vectorized Matching Engine & Academic Eligibility): Completed

## Backend SQL Query Logging

SQLAlchemy query logging is disabled by default and is configured independently
from FastAPI request logs and application logs. The setting is stored as
`SQL_LOGGING=true` or `SQL_LOGGING=false` in `backend/.env`, so it persists
across backend restarts.

Run the CLI from the backend directory with the project virtual environment
activated:

```powershell
cd backend
python -m app.cli sql-logging status
python -m app.cli sql-logging enable
python -m app.cli sql-logging disable
```

Available commands:

| Command | Purpose |
| --- | --- |
| `python -m app.cli sql-logging status` | Show whether SQL query logging is enabled or disabled in `backend/.env`. |
| `python -m app.cli sql-logging enable` | Persist `SQL_LOGGING=true`. |
| `python -m app.cli sql-logging disable` | Persist `SQL_LOGGING=false`. |

Example debugging workflow:

```powershell
cd backend
python -m app.cli sql-logging enable
uvicorn app.main:app --reload
```

The SQLAlchemy engine reads this setting only when the backend starts. Restart
the backend after enabling or disabling SQL logging. Invalid commands are
rejected by the CLI, and values other than `true` or `false` cause a clear
configuration error instead of silently changing logging behavior.
