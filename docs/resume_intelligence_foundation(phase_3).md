# Resume Intelligence

SkillFit's Resume Intelligence system allows students to securely upload resumes, automatically process them, extract structured information, and prepare them for AI-powered placement analysis.

The Resume Intelligence Foundation includes:

- Secure Resume Upload
- Resume Type Management
- Automatic Resume Replacement
- Resume Text Extraction
- Resume Section Detection
- Analysis Data Models
- Analysis Pipeline Foundation

---

## Overview

### Supported Resume Types

SkillFit supports two resume categories:

- Generic Resume
- Specialized Resume

Each student may maintain:

```text
1 Generic Resume
1 Specialized Resume
```

Maximum active resumes:

```text
2 resumes
```

---

### Automatic Resume Replacement

When a student uploads a new resume of an existing type, the previous resume is automatically replaced.

Example:

```text
Generic Resume V1
        ↓
Upload Generic Resume V2
        ↓
V1 Removed
V2 Active
```

This ensures analysis is always performed on the latest resume version.

---

## Resume Upload Workflow

### 1. Upload Resume

```http
POST /resume/upload
```

#### Request

```multipart
file=<resume.pdf>
resume_type=generic
```

Supported formats:

- PDF
- DOCX

---

### 2. Automatic Processing

After upload, the backend automatically begins processing.

```text
Upload
   ↓
Validation
   ↓
Text Extraction
   ↓
Section Detection
   ↓
Analysis Preparation
```

Students do not need to manually trigger any processing stage.

---

## Resume Management

### List Resumes

```http
GET /resume
```

Returns all resumes belonging to the authenticated student.

---

### Get Resume

```http
GET /resume/{resume_id}
```

Returns metadata for a specific resume.

---

### Delete Resume

```http
DELETE /resume/{resume_id}
```

Deletes the selected resume.

---

## Resume Types

### Generic Resume

A general-purpose resume suitable for multiple opportunities.

```text
resume_type = generic
```

---

### Specialized Resume

A role-specific resume optimized for a particular domain or position.

```text
resume_type = specialized
```

---

## Resume Processing

### Text Extraction

The platform automatically extracts machine-readable text from:

- PDF documents
- DOCX documents

This extracted text becomes the foundation for future AI analysis.

---

### Section Detection

The platform automatically identifies major resume sections, including:

- Skills
- Projects
- Internships
- Education
- Certifications
- Experience

The resulting structured data is used by future analysis engines.

---

### Analysis Preparation

Resume content is transformed into structured analysis-ready formats.

Prepared domains include:

- Skills Analysis
- Project Analysis
- Internship Analysis
- Certification Analysis
- Resume Readiness Analysis

These models will be consumed by future AI and LLM-based evaluation engines.

---

## Security Features

### File Type Validation

Only approved document formats are accepted.

Allowed:

```text
.pdf
.docx
```

Blocked:

```text
.exe
.bat
.scr
.dll
.js
```

and all unsupported formats.

---

### MIME Type Verification

The backend validates the actual content type of the uploaded file.

Example:

```text
virus.exe
     ↓ renamed to
resume.pdf
```

Rejected.

---

### Magic Byte Verification

The system validates file signatures.

Examples:

```text
PDF  → %PDF
DOCX → PK
```

Files with invalid signatures are rejected even if renamed.

---

### Deep File Structure Validation

Uploaded documents must be structurally valid.

Rejected examples:

- Corrupted PDFs
- Corrupted DOCX archives
- Malformed documents

This prevents invalid files from entering the processing pipeline.

---

### Empty File Protection

Zero-byte files are rejected.

---

### File Size Protection

Maximum upload size:

```text
10 MB
```

Files exceeding the limit are rejected.

---

### Path Traversal Protection

Unsafe filenames are sanitized before storage.

Example:

```text
../../../system/file.pdf
```

The original path is never trusted.

This prevents attempts to write files outside approved storage locations.

---

### Duplicate Resume Detection

Every uploaded file is hashed using SHA-256.

Benefits:

- Prevents duplicate uploads
- Prevents duplicate processing
- Reduces storage consumption
- Avoids redundant future AI analysis

---

### Resume Ownership Protection

Students can only access resumes that belong to their own account.

Blocked actions:

- Reading another student's resume
- Deleting another student's resume

---

### Role-Based Resume Access

Resume operations are restricted to student accounts.

Faculty users cannot:

- Upload resumes
- View student resumes
- Delete student resumes

---

### Database Integrity Protection

The database enforces:

```text
Maximum 1 Generic Resume per Student
Maximum 1 Specialized Resume per Student
```

This prevents duplicate resume types from being stored simultaneously.

---

## Error Responses

### Invalid File Type

```http
400 Bad Request
```

```json
{
  "detail": "Unsupported file type."
}
```

---

### Invalid Resume Type

```http
422 Unprocessable Entity
```

```json
{
  "detail": "Invalid resume_type."
}
```

---

### Duplicate Resume Content

```http
409 Conflict
```

```json
{
  "detail": "Duplicate resume detected."
}
```

---

### Unauthorized

```http
401 Unauthorized
```

Returned when authentication credentials are missing or invalid.

---

### Forbidden

```http
403 Forbidden
```

Returned when a user attempts to access a resume they do not own or does not have permission to access.

---

### Resume Not Found

```http
404 Not Found
```

Returned when the requested resume does not exist.

---

## API Summary

| Method | Endpoint | Description |
|----------|------------|-------------|
| POST | `/resume/upload` | Upload a resume |
| GET | `/resume` | List student resumes |
| GET | `/resume/{id}` | Retrieve resume metadata |
| DELETE | `/resume/{id}` | Delete a resume |

---

## Testing & Verification

The Resume Intelligence Foundation has been verified through:

### Functional Testing

- Resume upload validation
- Resume retrieval
- Resume deletion
- Resume replacement workflow
- Resume type enforcement
- Ownership enforcement

### Security Testing

- Fake PDF detection
- Fake DOCX detection
- Executable upload blocking
- Corrupted file rejection
- Path traversal protection
- Duplicate detection verification
- Authentication enforcement
- Authorization enforcement

All Phase 3.1 – 3.5 validation and security tests pass successfully.

---
