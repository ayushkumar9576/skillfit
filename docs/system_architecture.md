# SkillFit System Architecture

## Project Name

**SkillFit – AI-Powered Student Placement Intelligence Platform**

---

# 1. Architecture Overview

SkillFit follows a multi-layer architecture consisting of:

1. Presentation Layer (Frontend)
2. Application Layer (Backend APIs)
3. Data Layer (PostgreSQL Database)
4. Analysis Layer (CV Analysis & Drive Analysis Engines)
5. Recommendation Layer (Matching Engine)

The architecture is designed to support the prototype milestone first and later allow integration of Machine Learning, RAG, and Agentic AI components without major restructuring.

---

# 2. High-Level Architecture Diagram

```text
                    ┌───────────────────┐
                    │      Students      │
                    └─────────┬─────────┘
                              │
                              │
                    ┌─────────▼─────────┐
                    │      Faculty      │
                    └─────────┬─────────┘
                              │
                              ▼

                 ┌─────────────────────────┐
                 │     Frontend Layer      │
                 │      Next.js App        │
                 └───────────┬─────────────┘
                             │ REST APIs
                             ▼

                 ┌─────────────────────────┐
                 │     Backend Layer       │
                 │        FastAPI          │
                 └──────┬──────┬───────────┘
                        │      │
                        │      │
                        ▼      ▼

            ┌─────────────────────────┐
            │      PostgreSQL DB      │
            └─────────────────────────┘

                        ▲
                        │
          ┌─────────────┼─────────────┐
          │                           │
          ▼                           ▼

 ┌──────────────────┐      ┌──────────────────┐
 │  CV Analysis     │      │ Drive Analysis   │
 │     Engine       │      │     Engine       │
 └────────┬─────────┘      └────────┬─────────┘
          │                         │
          └──────────┬──────────────┘
                     ▼

          ┌─────────────────────────┐
          │     Matching Engine     │
          └──────────┬──────────────┘
                     ▼

          ┌─────────────────────────┐
          │ Recommendation Results  │
          └─────────────────────────┘
```

---

# 3. Frontend Layer

## Technology

- Next.js
- React
- TypeScript
- Tailwind CSS

## Responsibilities

The frontend provides user interfaces for students and faculty.

### Student Module

Features:

- Login
- Profile Management
- Resume Upload
- Placement Dashboard
- Drive Recommendations
- Placement Insights

### Faculty Module

Features:

- Login
- Mentor Dashboard
- Student Analysis
- Student Progress Monitoring
- At-Risk Student Identification

### Responsibilities

- Collect user input
- Upload resumes
- Display recommendations
- Display analysis reports
- Communicate with backend APIs

---

# 4. Backend Layer

## Technology

- FastAPI

## Responsibilities

The backend acts as the central processing layer.

It handles:

- Authentication
- API Requests
- Business Logic
- Database Operations
- Analysis Workflow Management
- Recommendation Generation

### Main Components

#### API Layer

Handles incoming requests.

Examples:

```http
POST /students/register
POST /students/login
POST /students/upload-cv

GET /students/profile

POST /drives/create
GET /drives

POST /recommendations/generate
GET /recommendations/{student_id}
```

#### Service Layer

Contains business logic such as:

- Student management
- Drive management
- Recommendation generation
- Resume processing

#### Database Layer

Communicates with PostgreSQL using SQLAlchemy ORM.

---

# 5. Database Layer

## Technology

- PostgreSQL
- SQLAlchemy ORM

## Purpose

Store all platform data.

### Core Tables

#### students

Stores:

- Student information
- Resume details
- Placement status

#### faculty

Stores:

- Faculty information
- Mentor information

#### drives

Stores:

- Placement drive details
- Eligibility requirements

#### student_projects

Stores:

- Student projects
- Project complexity information

#### student_skills

Stores:

- Skills extracted from resumes
- Confidence scores

#### certifications

Stores:

- Certification details
- Certification providers

#### recommendations

Stores:

- Generated recommendations
- Match scores
- Recommendation status

---

# 6. CV Analysis Engine

## Purpose

Analyze uploaded resumes and create structured student profiles.

## Input

Resume PDF

## Processing

Extract:

- Personal Information
- Technical Skills
- Projects
- Certifications
- Experience
- Achievements

Analyze:

- Project Complexity
- Skill Evidence
- Experience Strength

## Output

Structured student profile including:

- Skills
- Projects
- Certifications
- Placement Readiness Indicators

---

# 7. Drive Analysis Engine

## Purpose

Analyze placement drive descriptions.

## Input

Drive Description

## Processing

Extract:

- Required Skills
- Preferred Skills
- Eligibility Criteria
- Role Information
- Company Requirements

## Output

Structured drive profile.

---

# 8. Matching Engine

## Purpose

Match student profiles with placement drives.

## Inputs

### Student Profile

Includes:

- Skills
- Projects
- Certifications
- CGPA
- Experience

### Drive Profile

Includes:

- Required Skills
- Eligibility Criteria
- Preferred Qualifications

## Processing

Compare:

- Skill Match
- Project Relevance
- Certification Relevance
- Eligibility Satisfaction

Generate:

- Match Score
- Recommendation Reason

## Output

Drive recommendations ranked by suitability.

---

# 9. Prototype Workflow

## Step 1

Student uploads resume.

↓

## Step 2

Resume is analyzed.

↓

## Step 3

Student profile is generated.

↓

## Step 4

Placement drive is analyzed.

↓

## Step 5

Matching engine compares:

- Student Profile
- Drive Requirements

↓

## Step 6

Match score is generated.

↓

## Step 7

Recommendations are stored in PostgreSQL.

↓

## Step 8

Recommendations are displayed on the dashboard.

---

# 10. Faculty Workflow

## Step 1

Faculty logs in.

↓

## Step 2

Faculty views assigned students.

↓

## Step 3

System displays:

- Student strengths
- Student weaknesses
- Placement readiness

↓

## Step 4

Faculty identifies students needing guidance.

---

# 11. Future Architecture Extensions (Phase 2)

The following components will be added after the prototype milestone.

## Machine Learning Layer

Purpose:

- Placement Success Prediction
- At-Risk Student Prediction

Technologies:

- Scikit-Learn
- XGBoost
- LightGBM

---

## RAG Layer

Purpose:

- Skill Gap Detection
- Learning Roadmaps
- Context-Aware Placement Guidance

Technologies:

- ChromaDB
- FAISS
- Sentence Transformers

---

## Agentic AI Layer

Purpose:

- Placement Advisor Assistant
- Faculty Assistant
- Multi-Step Placement Guidance

Technology:

- LangGraph

---

## External Profile Integrations

Future Sources:

- GitHub
- LeetCode
- Codeforces
- GeeksforGeeks

These platforms will provide additional evidence for skill assessment.

---

# 12. Technology Stack Summary

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

## Backend

- FastAPI

## Database

- PostgreSQL
- SQLAlchemy

## NLP

- spaCy

## LLM

- Gemini 3.1 Pro
- Claude Sonnet 4.6

## Machine Learning (Phase 2)

- Scikit-Learn
- XGBoost
- LightGBM

## RAG (Phase 2)

- ChromaDB
- FAISS
- Sentence Transformers

## Agentic AI (Phase 2)

- LangGraph

## Deployment

- Docker
- VPS

---

# Current Status

Phase: **Phase 1 – Project Foundation & System Setup**

Completed:

- Repository Setup
- Project Structure Setup
- Database Schema Design

Next:

- API Design
- UI Wireframes
- Prototype Development