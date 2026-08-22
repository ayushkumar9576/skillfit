# SkillFit API Design

## Project Name

**SkillFit – AI-Powered Student Placement Intelligence Platform**

---

# 1. API Overview

The SkillFit backend exposes REST APIs that allow communication between the frontend and backend services.

The APIs support:

- Student Management
- Faculty Management
- Resume Upload
- Placement Drive Management
- Recommendation Generation
- Dashboard Data Retrieval

---

# 2. Base URL

## Development

```text
http://localhost:8000/api/v1
```

## Production

```text
https://api.skillfit.com/api/v1
```

---

# 3. Authentication Strategy

## Prototype Phase

Authentication will use:

- Email
- Password

Authentication can initially be implemented using simple session/JWT-based login.

---

# 4. Student APIs

---

## 4.1 Register Student

### Endpoint

```http
POST /students/register
```

### Description

Creates a new student account.

### Request Body

```json
{
  "name": "Rahul Sharma",
  "email": "rahul@gmail.com",
  "password": "password123",
  "branch": "CSE",
  "cgpa": 8.5,
  "phone": "9876543210"
}
```

### Success Response

```json
{
  "message": "Student registered successfully",
  "student_id": 1
}
```

### Status Codes

| Code | Meaning |
|--------|----------|
| 201 | Created |
| 400 | Invalid Input |
| 409 | Email Already Exists |

---

## 4.2 Student Login

### Endpoint

```http
POST /students/login
```

### Request Body

```json
{
  "email": "rahul@gmail.com",
  "password": "password123"
}
```

### Success Response

```json
{
  "access_token": "jwt_token",
  "token_type": "bearer"
}
```

### Status Codes

| Code | Meaning |
|--------|----------|
| 200 | Success |
| 401 | Invalid Credentials |

---

## 4.3 Get Student Profile

### Endpoint

```http
GET /students/profile/{student_id}
```

### Description

Returns complete student profile information.

### Success Response

```json
{
  "id": 1,
  "name": "Rahul Sharma",
  "email": "rahul@gmail.com",
  "branch": "CSE",
  "cgpa": 8.5,
  "placement_status": "Not Started"
}
```

### Status Codes

| Code | Meaning |
|--------|----------|
| 200 | Success |
| 404 | Student Not Found |

---

## 4.4 Upload Resume

### Endpoint

```http
POST /students/upload-cv
```

### Description

Uploads student resume PDF.

### Request

```multipart/form-data
resume.pdf
```

### Success Response

```json
{
  "message": "Resume uploaded successfully",
  "resume_path": "/uploads/resume.pdf"
}
```

### Status Codes

| Code | Meaning |
|--------|----------|
| 200 | Success |
| 400 | Invalid File |
| 413 | File Too Large |

---

## 4.5 Get Student Recommendations

### Endpoint

```http
GET /students/{student_id}/recommendations
```

### Description

Returns recommended placement drives.

### Success Response

```json
[
  {
    "drive_id": 5,
    "company_name": "Infosys",
    "role": "Software Engineer",
    "match_score": 88
  }
]
```

---

# 5. Faculty APIs

---

## 5.1 Register Faculty

### Endpoint

```http
POST /faculty/register
```

### Request Body

```json
{
  "name": "Dr. Sharma",
  "email": "sharma@college.edu",
  "password": "password123",
  "department": "Computer Science"
}
```

### Success Response

```json
{
  "message": "Faculty registered successfully",
  "faculty_id": 1
}
```

---

## 5.2 Faculty Login

### Endpoint

```http
POST /faculty/login
```

### Request Body

```json
{
  "email": "sharma@college.edu",
  "password": "password123"
}
```

### Success Response

```json
{
  "access_token": "jwt_token"
}
```

---

## 5.3 Get Faculty Dashboard

### Endpoint

```http
GET /faculty/dashboard/{faculty_id}
```

### Description

Returns faculty dashboard information.

### Success Response

```json
{
  "total_students": 50,
  "placement_ready": 20,
  "at_risk_students": 10
}
```

---

## 5.4 Get Assigned Students

### Endpoint

```http
GET /faculty/{faculty_id}/students
```

### Description

Returns students assigned to a faculty mentor.

### Success Response

```json
[
  {
    "student_id": 1,
    "name": "Rahul Sharma",
    "cgpa": 8.5
  }
]
```

---

# 6. Placement Drive APIs

---

## 6.1 Create Placement Drive

### Endpoint

```http
POST /drives/create
```

### Description

Creates a new placement drive.

### Request Body

```json
{
  "company_name": "Infosys",
  "role": "Software Engineer",
  "job_type": "Full Time",
  "location": "Bangalore",
  "package": "8 LPA",
  "description": "Hiring software engineers."
}
```

### Success Response

```json
{
  "message": "Drive created successfully",
  "drive_id": 1
}
```

---

## 6.2 Get All Drives

### Endpoint

```http
GET /drives
```

### Description

Returns all placement drives.

### Success Response

```json
[
  {
    "id": 1,
    "company_name": "Infosys",
    "role": "Software Engineer"
  }
]
```

---

## 6.3 Get Drive Details

### Endpoint

```http
GET /drives/{drive_id}
```

### Description

Returns complete drive information.

### Success Response

```json
{
  "id": 1,
  "company_name": "Infosys",
  "role": "Software Engineer",
  "description": "Hiring software engineers."
}
```

---

# 7. Recommendation APIs

---

## 7.1 Generate Recommendations

### Endpoint

```http
POST /recommendations/generate/{student_id}
```

### Description

Generates drive recommendations for a student.

### Workflow

1. Load Student Profile
2. Load Available Drives
3. Analyze Requirements
4. Compute Match Scores
5. Store Recommendations

### Success Response

```json
{
  "message": "Recommendations generated successfully"
}
```

---

## 7.2 Get Recommendations

### Endpoint

```http
GET /recommendations/{student_id}
```

### Description

Returns stored recommendations.

### Success Response

```json
[
  {
    "drive_id": 10,
    "company_name": "TCS",
    "match_score": 82,
    "status": "Recommended"
  }
]
```

---

# 8. CV Analysis APIs

---

## 8.1 Analyze Resume

### Endpoint

```http
POST /analysis/cv/{student_id}
```

### Description

Extracts information from uploaded resumes.

### Output

- Skills
- Projects
- Certifications
- Experience

### Success Response

```json
{
  "skills": ["Python", "SQL"],
  "projects": 3,
  "certifications": 2
}
```

---

# 9. Health Check APIs

---

## 9.1 Health Check

### Endpoint

```http
GET /health
```

### Success Response

```json
{
  "status": "ok"
}
```

---

# 10. Error Response Format

All APIs should return errors in a consistent format.

Example:

```json
{
  "error": true,
  "message": "Student not found"
}
```

---

# 11. Prototype Scope APIs

The following APIs are required for the August 30 prototype:

### Student

- Register
- Login
- Profile
- Upload Resume

### Drive

- Create Drive
- Get Drives
- Get Drive Details

### Recommendations

- Generate Recommendations
- Get Recommendations

### Faculty

- Login
- Dashboard
- Student List

### Utility

- Health Check

---

# 12. Future APIs (Phase 2)

The following APIs will be added after the prototype milestone.

## GitHub Analysis

```http
POST /integrations/github
```

## LeetCode Analysis

```http
POST /integrations/leetcode
```

## Codeforces Analysis

```http
POST /integrations/codeforces
```

## GeeksforGeeks Analysis

```http
POST /integrations/gfg
```

## Skill Gap Analysis

```http
POST /analysis/skill-gap
```

## Learning Roadmap Generation

```http
POST /roadmap/generate
```

## Placement Advisor Chat

```http
POST /advisor/chat
```

---

# Current Status

Phase: **Phase 1 – Project Foundation & System Setup**

Completed:
- Project Setup
- Database Design
- System Architecture
- API Design

Next:
- UI Wireframes
- Prototype Development