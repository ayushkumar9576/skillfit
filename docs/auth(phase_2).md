# Authentication

SkillFit uses **JWT (JSON Web Token) Bearer Authentication** to secure API access. Users authenticate using their **registration number** and **password**, then receive a short-lived access token that must be included in requests to protected endpoints.

---

## Overview

### Authentication Method
- JWT Bearer Tokens
- OAuth2 Password Flow
- Registration Number + Password Login
- Stateless Authentication

### Supported Roles
- Student
- Faculty
- Admin (reserved for future use)

---

## Authentication Flow

### 1. Register an Account

Create a new Student or Faculty account.

#### Student Registration

```http
POST /auth/register/student
```

#### Faculty Registration

```http
POST /auth/register/faculty
```

The system validates:

- Email uniqueness
- Registration number uniqueness
- Required profile fields
- Password requirements

A successful registration creates both:

1. User identity record
2. Associated profile record

---

### 2. Login

Authenticate using your registration number and password.

```http
POST /auth/login
```

#### Request

```json
{
  "registration_number": "2024CS001",
  "password": "your_password"
}
```

#### Response

```json
{
  "access_token": "<jwt_token>",
  "token_type": "bearer"
}
```

---

### 3. Access Protected Endpoints

Include the JWT token in the Authorization header.

```http
Authorization: Bearer <jwt_token>
```

Example:

```http
GET /auth/me
Authorization: Bearer eyJhbGciOi...
```

---

### 4. Retrieve Current User

Returns information about the currently authenticated user.

```http
GET /auth/me
```

#### Example Response

```json
{
  "id": "b8d7c1f2-1234-5678-9012-abcdef123456",
  "full_name": "John Doe",
  "email": "john@example.com",
  "registration_number": "2024CS001",
  "role": "student",
  "is_active": true
}
```

---

## User Roles

SkillFit currently supports the following roles:

| Role | Description |
|--------|------------|
| Student | Placement candidate profile |
| Faculty | Faculty and mentor profile |
| Admin | Reserved for platform administration |

Role-based authorization is supported by the backend and can be applied to protected endpoints.

---

## Rate Limits

To protect against abuse and brute-force attacks, authentication endpoints are rate limited.

| Endpoint | Limit |
|-----------|---------|
| POST /auth/login | 5 requests per 15 minutes |
| POST /auth/register/student | 10 requests per hour |
| POST /auth/register/faculty | 10 requests per hour |

When a limit is exceeded:

```http
429 Too Many Requests
```

---

## Error Responses

### Invalid Credentials

```http
401 Unauthorized
```

```json
{
  "detail": "Invalid credentials."
}
```

---

### Invalid or Expired Token

```http
401 Unauthorized
```

```json
{
  "detail": "Could not validate credentials"
}
```

---

### Forbidden Access

```http
403 Forbidden
```

```json
{
  "detail": "Forbidden"
}
```

---

### Duplicate Email

```http
409 Conflict
```

```json
{
  "detail": "Email is already in use."
}
```

---

### Duplicate Registration Number

```http
409 Conflict
```

```json
{
  "detail": "Registration number is already in use."
}
```

---

### Rate Limit Exceeded

```http
429 Too Many Requests
```

```json
{
  "detail": "Rate limit exceeded"
}
```

---

## OpenAPI Documentation

Interactive API documentation is automatically generated and available at:

```text
/docs
```

OpenAPI specification:

```text
/openapi.json
```

The Swagger UI supports authentication directly from the browser using the OAuth2 authorization flow.

---

## Best Practices

### Store Tokens Securely

Recommended locations:

- HTTP-only cookies
- Secure browser storage
- Mobile secure storage

Avoid:

- Exposing tokens in URLs
- Logging tokens
- Sharing tokens between users

---

### Protect Authenticated Requests

Always include:

```http
Authorization: Bearer <jwt_token>
```

on protected endpoints.

---

### Handle Expired Sessions

When receiving:

```http
401 Unauthorized
```

the client should:

1. Redirect the user to login
2. Request a new token if refresh-token support exists
3. Clear invalid authentication state

---

## Authentication Endpoints Summary

| Method | Endpoint | Description |
|----------|------------|-------------|
| POST | /auth/register/student | Register a student account |
| POST | /auth/register/faculty | Register a faculty account |
| POST | /auth/login | Authenticate and receive JWT |
| GET | /auth/me | Retrieve current authenticated user |

---

## Status

Authentication system is stable and production-ready.