# JWT Authentication REST API

A production-structured Flask REST API with JWT access/refresh tokens, bcrypt password hashing, SQLite storage, and rate-limited login.

## Tech stack

- Python 3.11+
- Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-Bcrypt, Flask-Limiter
- SQLite (`auth.db`, created automatically on first run)
- python-dotenv for secrets

## Project structure

```
jwt-auth-api/
├── app/
│   ├── __init__.py          # App factory, extensions, health route
│   ├── models.py            # User model
│   ├── routes/
│   │   ├── auth.py          # Register, login, refresh, logout
│   │   └── user.py          # Profile GET/PUT
│   └── utils/
│       ├── validators.py    # Input validation
│       └── errors.py        # Standard JSON responses + error handlers
├── config.py
├── run.py
├── requirements.txt
├── .env.example
└── auth.db                  # Created on first run (project root)
```

## Setup

### 1. Prerequisites

- Python 3.11 or newer
- pip

No database server installation is required. SQLite is file-based and ships with Python.

### 2. Clone or open the project

```bash
cd jwt-auth-api
```

### 3. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env` and set strong random values:

```env
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

Never commit `.env` to version control.

## Run locally

```bash
python run.py
```

The API listens at `http://127.0.0.1:5000` by default.

Open **`http://127.0.0.1:5000`** in a browser for the minimal frontend (login, register, profile).

On the first run, `auth.db` is created in the project root and the `users` table is created automatically.

## Response format

Every endpoint returns JSON in this shape:

```json
{
  "status": "success",
  "message": "Human readable message",
  "data": {}
}
```

On errors, `status` is `"error"` and `data` is usually `null`.

## Authentication

Protected routes require a valid **access** token in the header:

```
Authorization: Bearer <access_token>
```

| Token   | Lifetime | Use |
|---------|----------|-----|
| Access  | 15 minutes | Profile routes, logout |
| Refresh | 7 days     | `POST /api/auth/refresh` only |

Send the refresh token (not the access token) to the refresh endpoint:

```
Authorization: Bearer <refresh_token>
```

## Validation rules

| Field    | Rules |
|----------|--------|
| Username | 3–30 characters; letters, numbers, underscores only |
| Email    | Valid format; unique across users |
| Password | Minimum 8 characters; at least one digit |

## HTTP status codes

| Code | Meaning |
|------|---------|
| 200  | Success |
| 201  | Resource created (register) |
| 400  | Validation or duplicate email/username |
| 401  | Missing, expired, or revoked token; invalid login |
| 404  | Route not found |
| 422  | Malformed JWT |
| 429  | Login rate limit exceeded (5 requests/minute per IP) |
| 500  | Internal server error |
| 503  | Health check: API up, database unavailable |

---

## API endpoints

Base URL: `http://127.0.0.1:5000`

### Health check

**`GET /api/health`** — Public

**Response `200`**

```json
{
  "status": "success",
  "message": "API is healthy",
  "data": {
    "api": "ok",
    "database": "connected"
  }
}
```

**Response `503`** (database error)

```json
{
  "status": "success",
  "message": "API is up but database is unavailable",
  "data": {
    "api": "ok",
    "database": "disconnected"
  }
}
```

---

### Register

**`POST /api/auth/register`** — Public

**Request body**

```json
{
  "username": "jane_doe",
  "email": "jane@example.com",
  "password": "securepass1"
}
```

**Response `201`**

```json
{
  "status": "success",
  "message": "User registered successfully",
  "data": {
    "id": 1,
    "username": "jane_doe",
    "email": "jane@example.com",
    "created_at": "2026-06-01T12:00:00",
    "updated_at": "2026-06-01T12:00:00"
  }
}
```

**Response `400`** (validation)

```json
{
  "status": "error",
  "message": "password: Password must contain at least one number",
  "data": null
}
```

**Response `400`** (duplicate email)

```json
{
  "status": "error",
  "message": "Email is already registered",
  "data": null
}
```

---

### Login

**`POST /api/auth/login`** — Public (rate limited: **5 requests/minute per IP**)

**Request body**

```json
{
  "email": "jane@example.com",
  "password": "securepass1"
}
```

**Response `200`**

```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Response `401`**

```json
{
  "status": "error",
  "message": "Invalid email or password",
  "data": null
}
```

**Response `429`**

```json
{
  "status": "error",
  "message": "Too many requests. Please try again later.",
  "data": null
}
```

---

### Refresh access token

**`POST /api/auth/refresh`** — Requires refresh token

**Headers**

```
Authorization: Bearer <refresh_token>
```

**Response `200`**

```json
{
  "status": "success",
  "message": "Access token refreshed successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Response `401`** (expired refresh token)

```json
{
  "status": "error",
  "message": "Token has expired",
  "data": null
}
```

---

### Logout

**`POST /api/auth/logout`** — Requires access token

**Headers**

```
Authorization: Bearer <access_token>
```

**Response `200`**

```json
{
  "status": "success",
  "message": "Successfully logged out",
  "data": null
}
```

The current token is blacklisted and cannot be reused.

---

### Get profile

**`GET /api/user/profile`** — Requires access token

**Headers**

```
Authorization: Bearer <access_token>
```

**Response `200`**

```json
{
  "status": "success",
  "message": "Profile retrieved successfully",
  "data": {
    "id": 1,
    "username": "jane_doe",
    "email": "jane@example.com",
    "created_at": "2026-06-01T12:00:00",
    "updated_at": "2026-06-01T12:00:00"
  }
}
```

**Response `401`** (missing token)

```json
{
  "status": "error",
  "message": "Missing or invalid authorization token",
  "data": null
}
```

---

### Update profile

**`PUT /api/user/profile`** — Requires access token

Send at least one of `username` or `email`.

**Headers**

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request body**

```json
{
  "username": "jane_smith",
  "email": "jane.smith@example.com"
}
```

**Response `200`**

```json
{
  "status": "success",
  "message": "Profile updated successfully",
  "data": {
    "id": 1,
    "username": "jane_smith",
    "email": "jane.smith@example.com",
    "created_at": "2026-06-01T12:00:00",
    "updated_at": "2026-06-01T14:30:00"
  }
}
```

**Response `400`**

```json
{
  "status": "error",
  "message": "username: Username must be 3-30 characters and contain only letters, numbers, and underscores",
  "data": null
}
```

---

## Typical flow

1. `POST /api/auth/register` — create an account  
2. `POST /api/auth/login` — receive access + refresh tokens  
3. `GET /api/user/profile` — call with access token  
4. `POST /api/auth/refresh` — when access token expires, use refresh token  
5. `POST /api/auth/logout` — blacklist the access token  

## Testing with curl

```bash
# Health
curl http://127.0.0.1:5000/api/health

# Register
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"test_user\",\"email\":\"test@example.com\",\"password\":\"password1\"}"

# Login (save access_token from response)
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"password\":\"password1\"}"

# Profile
curl http://127.0.0.1:5000/api/user/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Postman

Import `postman_collection.json` into Postman:

1. **File → Import** → select `postman_collection.json`
2. Start the API: `python run.py`
3. Run **Health Check**, then **Register**, then **Login**
4. Login automatically saves `access_token` and `refresh_token` to collection variables
5. Run **Get Profile**, **Update Profile**, **Refresh Token**, or **Logout**

Collection variables:

| Variable        | Default                  |
|-----------------|--------------------------|
| `base_url`      | `http://127.0.0.1:5000`  |
| `access_token`  | Set after login          |
| `refresh_token` | Set after login          |

## Security notes

- Passwords are stored as bcrypt hashes only.  
- Secrets are loaded from `.env`, not hardcoded in source.  
- Login is rate limited to reduce brute-force attempts.  
- Logout blacklists the JWT `jti` so the token cannot be reused (in-memory store; tokens are cleared on server restart).
