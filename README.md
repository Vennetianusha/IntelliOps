# IntelliOps – AI-Powered Engineering Operations Platform

IntelliOps is a full-stack engineering operations platform designed to simplify technical issue management, automated issue triage, and performance-aware data retrieval for engineering teams.

The platform allows users to create, track, update, filter, and delete technical issues while using AI-assisted analysis to suggest issue category, priority, responsible team, technical keywords, and recommended actions.

---

## 📌 Problem Statement

Engineering teams often spend significant time manually reviewing, categorizing, prioritizing, and assigning technical issues.

Without standardized issue classification:

- Critical issues may not receive appropriate priority.
- Issues can be assigned to the wrong engineering team.
- Repetitive triage work increases the team's workload.
- Frequently accessed issue data can increase database read traffic.

IntelliOps addresses these challenges through:

1. **AI-Assisted Triage**: Analyzes issue titles and descriptions to suggest category, priority, team ownership, keywords, and recommended actions.
2. **Redis Caching**: Uses the Cache-Aside pattern to reduce repeated PostgreSQL queries for frequently requested issue data.
3. **Graceful Failure Handling**: If Redis or the external AI service is unavailable, the core issue-management APIs continue using fallback mechanisms.

---

## 🏗️ Architecture & Request Flow

```text
+------------------------------------------------------------------+
|                      React Frontend (Nginx)                      |
+----------------------------------+-------------------------------+
                                   |
                                   | HTTP / REST API (Port 80 / 5173)
                                   v
+------------------------------------------------------------------+
|                      FastAPI Backend (Python)                    |
+--------------+-------------------+-------------------+-----------+
               |                   |                   |
               | (Cache-Aside)     | (AI Analysis)     | (SQLAlchemy ORM)
               v                   v                   v
+--------------+----+ +------------+-------+ +---------+---------+
|    Redis 7        | | Google Gemini API  | | PostgreSQL 15    |
| (Cache Layer with | | (Heuristic Rule    | | (Database       |
|  Failover)        | |  Fallback Engine)  | |  Persistence)   |
+-------------------+ +--------------------+ +-------------------+
```

### End-to-End Request Processing Flow

1. **Request Ingestion**: Requests enter via the React frontend or direct REST API calls (`POST /api/v1/issues`).
2. **AI-Assisted Issue Analysis**: The backend invokes the AI service (`app/services/ai_service.py`). If unprovided or left as defaults, issue metadata is enriched with predicted `category`, `priority`, `assigned_team`, `keywords`, and `suggested_action`.
3. **PostgreSQL Persistence**: The enriched issue entity is persisted to PostgreSQL using SQLAlchemy 2.0 ORM (`app/models/issue.py`).
4. **Redis Cache Invalidation**: Following a successful write (`POST`, `PUT`, `DELETE`), invalidation logic purges stale Redis list and detail cache keys (`app/cache/service.py`).
5. **Redis Cache-Aside Read Path**: Read queries (`GET /api/v1/issues`) inspect Redis first. On a Cache Hit, data is returned directly from memory. On a Cache Miss, the backend fetches rows from PostgreSQL, writes the result to Redis with a 300-second TTL, and returns the response.
6. **PostgreSQL Fallback**: If Redis is offline or fails, error handlers suppress the connection failure, log a warning, and fetch data directly from PostgreSQL.

---

## ✨ Key Features

- **Issue Creation**: Submit technical issues with title, description, category, priority, status, and team assignment.
- **Issue Listing**: View all engineering issues ordered by creation timestamp.
- **Issue Update**: Edit issue details, change statuses (`open`, `in_progress`, `resolved`, `closed`), and update team assignments.
- **Issue Deletion**: Remove resolved or invalid issues with confirmation.
- **Issue Filtering**: Filter issues by status (`open`, `in_progress`, `resolved`, `closed`) and priority (`low`, `medium`, `high`, `critical`).
- **Issue Dashboard**: Overview cards displaying total, open, in-progress, resolved, and high/critical issue counts.
- **Status and Priority Tracking**: Color-coded status and priority badges.
- **AI-Assisted Issue Analysis**: Real-time issue analysis via `POST /api/v1/issues/analyze`.
- **Automatic Issue Enrichment**: Automatically fills category, priority, and team assignments during issue creation.
- **Redis Cache-Aside Caching**: Caches list and detail queries in Redis.
- **Redis Failure Fallback**: Continues API operations via PostgreSQL if Redis is unavailable.
- **AI Heuristic Fallback**: Rule-based pattern matching when the Gemini API key is unconfigured or unreachable.
- **FastAPI REST APIs**: Modular API routes built with FastAPI and Pydantic.
- **Swagger/OpenAPI Documentation**: Interactive documentation accessible at `/docs`.
- **Docker Compose Setup**: Containerized multi-service environment (`postgres`, `redis`, `backend`, `frontend`).

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, JavaScript, Vite 5, Nginx |
| **Backend** | Python 3.10, FastAPI, Uvicorn, Pydantic v2 |
| **Database** | PostgreSQL 15, SQLAlchemy 2.0 ORM |
| **Caching** | Redis 7 |
| **AI** | Google Gemini (`google-genai`), Heuristic Rule Engine |
| **Containerization** | Docker, Docker Compose |
| **Testing / API** | Postman, Swagger UI, OpenAPI |
| **Development** | Git, GitHub |

---

## 🤖 AI Analysis Engine

The AI analysis service (`app/services/ai_service.py`) analyzes the title and description of an issue and produces structured analysis containing:

- `category`: `"bug" | "feature" | "incident" | "task" | "tech_debt"`
- `priority`: `"low" | "medium" | "high" | "critical"`
- `assigned_team`: `"backend" | "frontend" | "devops" | "platform" | "data"`
- `keywords`: List of extracted technical keywords.
- `suggested_action`: Actionable remediation guidance.

### AI Fallback Mechanism

When `GEMINI_API_KEY` is not provided in environment settings, or if an API request to Google Gemini fails (e.g. network timeout or API error):

1. The service logs a warning detailing the failure.
2. The service executes an internal heuristic rule engine (`_fallback_heuristic_analysis`).
3. The heuristic engine uses pattern matching on technical terms (e.g. "crash", "timeout", "react", "docker", "query") to assign a category, priority, team, keywords, and suggested action.
4. The issue creation or analysis endpoint completes without breaking.

---

## ⚡ Redis Caching Strategy

IntelliOps uses the **Cache-Aside** pattern for data retrieval.

### Read Path

```text
Request (GET /api/v1/issues)
   |
   v
Check Redis Cache
   |
   +---- Cache Hit --------> Return Cached Data
   |
   +---- Cache Miss
             |
             v
       Query PostgreSQL
             |
             v
        Store in Redis (TTL: 300s)
             |
             v
        Return Data
```

### Write Path

When an issue is created (`POST`), updated (`PUT`), or deleted (`DELETE`):
1. The backend modifies the database record in PostgreSQL.
2. The backend invalidates cached list keys (`issues:list:*`) and specific detail keys (`issues:detail:<id>`) using `invalidate_issue_caches()`.
3. Subsequent `GET` requests fetch fresh data from PostgreSQL and re-populate the cache.

### Redis Failure Handling

Redis operations in `app/cache/client.py` are wrapped in exception handlers. If Redis is down or unreachable:
- Connection errors are caught and logged as warnings.
- Cache read calls return `None`, causing requests to fall back directly to PostgreSQL.
- API endpoints continue processing without returning HTTP 500 errors to clients.

---

## 🗄️ Database Design

The database schema is defined using SQLAlchemy 2.0 in `app/models/issue.py` mapping to the `issues` table:

| Column | Type | Description |
| :--- | :--- | :--- |
| **`id`** | `INTEGER` | Primary key, auto-incrementing integer |
| **`title`** | `VARCHAR(255)` | Short summary of the issue (Indexed, Non-nullable) |
| **`description`** | `TEXT` | Detailed technical description (Nullable) |
| **`category`** | `VARCHAR(50)` | Category classification (Indexed, Non-nullable) |
| **`priority`** | `VARCHAR(50)` | Priority level, default: `"medium"` (Indexed, Non-nullable) |
| **`status`** | `VARCHAR(50)` | Workflow state, default: `"open"` (Indexed, Non-nullable) |
| **`assigned_team`** | `VARCHAR(100)` | Assigned team name (Indexed, Nullable) |
| **`created_at`** | `TIMESTAMPTZ` | Timestamp when record was created (Server default: `NOW()`) |
| **`updated_at`** | `TIMESTAMPTZ` | Timestamp when record was last updated (Server default: `NOW()`) |

---

## 🌐 REST API Endpoints

FastAPI router endpoints defined in `app/api/v1/router.py` and `app/api/v1/endpoints/issues.py`:

| Method | Route | Description |
| :--- | :--- | :--- |
| **`GET`** | `/` | Root endpoint displaying API welcome message |
| **`GET`** | `/api/v1/health` | Health check endpoint returning backend status |
| **`POST`** | `/api/v1/issues/analyze` | Analyzes issue text and returns AI classification preview |
| **`POST`** | `/api/v1/issues` | Creates a new issue with AI enrichment |
| **`GET`** | `/api/v1/issues` | Lists all issues with optional `status` and `priority` query filters |
| **`GET`** | `/api/v1/issues/{issue_id}` | Retrieves a single issue by primary key ID |
| **`PUT`** | `/api/v1/issues/{issue_id}` | Updates issue attributes by ID |
| **`DELETE`** | `/api/v1/issues/{issue_id}` | Deletes an issue by ID |

Interactive Swagger API documentation is available at `http://localhost:8000/docs` when the backend is running.

---

## 📁 Project Structure

```text
IntelliOps/
├── docker-compose.yml
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── .env.example
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── api/
│       │   └── v1/
│       │       ├── router.py
│       │       └── endpoints/
│       │           └── issues.py
│       ├── cache/
│       │   ├── client.py
│       │   └── service.py
│       ├── core/
│       │   └── config.py
│       ├── db/
│       │   ├── base_class.py
│       │   └── session.py
│       ├── models/
│       │   └── issue.py
│       ├── schemas/
│       │   └── issue.py
│       └── services/
│           └── ai_service.py
└── frontend/
    ├── Dockerfile
    ├── .dockerignore
    ├── .env.example
    ├── index.html
    ├── nginx.conf
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx
        ├── main.jsx
        ├── index.css
        ├── components/
        │   ├── CreateIssueModal.jsx
        │   ├── IssueDetailModal.jsx
        │   ├── IssueFilters.jsx
        │   ├── IssueTable.jsx
        │   ├── Navbar.jsx
        │   ├── PriorityBadge.jsx
        │   ├── StatusBadge.jsx
        │   └── StatsOverview.jsx
        └── services/
            └── api.js
```

---

## 🚀 How to Run

### Docker Compose

#### Prerequisites
- Docker & Docker Compose installed

#### Environment Setup
Copy the environment template file:
```bash
cp backend/.env.example .env
```

Optionally set `GEMINI_API_KEY` in `.env`:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
```

#### Commands
Start all containerized services:
```bash
docker compose up --build -d
```

Service URLs:
- **React Frontend**: `http://localhost` (Port 80)
- **FastAPI Backend**: `http://localhost:8000`
- **Swagger Documentation**: `http://localhost:8000/docs`

Stop services:
```bash
docker compose down
```

Stop services and remove PostgreSQL volume:
```bash
docker compose down -v
```

---

### Local Development

#### 1. Backend Setup
Prerequisites: Python 3.10+ and running PostgreSQL/Redis instances.

```bash
cd backend
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# Run development server
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup
Prerequisites: Node.js 18+ and npm.

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The frontend development server runs at `http://localhost:5173`.

---

## 🧪 Testing & Verification

The following verification steps were performed on the application:

- **Backend**:
  - API endpoint testing using FastAPI `TestClient` and HTTP requests.
  - Health check endpoint (`/api/v1/health`) verification returning status 200.
  - Issue CRUD operations (`POST`, `GET`, `PUT`, `DELETE`).
  - Request validation using Pydantic schemas.
- **PostgreSQL**:
  - CRUD persistence verification in table `issues`.
  - Query filtering by `status` and `priority`.
  - Column defaults and timestamp generation verification.
- **Redis**:
  - Cache hit and cache miss path execution.
  - Cache invalidation verification following write operations.
  - Redis connection failure test confirming automatic fallback to PostgreSQL.
- **AI**:
  - Structured output verification from `/api/v1/issues/analyze`.
  - Fallback rule engine execution test when API key is unconfigured.
- **Frontend**:
  - Dashboard component rendering and state updates.
  - Issue creation, detail modal, and filtering UI interactions.
  - Production build execution (`npm run build`) via Vite compiler.
- **Docker**:
  - Validation of `docker-compose.yml` structure using YAML parser.
  - Multi-container startup and service dependency configuration.
  - Networking and PostgreSQL health check configuration.

---

## 🔍 Example Use Case

### Input Issue
- **Title**: `Database connection pool timeout during load spike`
- **Description**: `FastAPI application threw 500 internal server error due to exhausted PostgreSQL connections.`

### AI Analysis Output
- **Category**: `incident`
- **Priority**: `high`
- **Assigned Team**: `backend`
- **Keywords**: `["timeout", "spike", "database", "exhausted", "fastapi"]`
- **Suggested Action**: `Identify root cause in server/error logs, check recent deployments, and page relevant on-call engineers.`

---

## 🎯 Engineering Concepts Demonstrated

- REST API Design & HTTP status codes
- Full CRUD operations
- FastAPI async/sync request handling
- Relational Database Management with PostgreSQL
- ORM mapping with SQLAlchemy 2.0
- In-memory caching with Redis
- Cache-Aside caching pattern
- Cache invalidation strategies
- Graceful degradation & failure handling
- AI API integration (`google-genai`)
- Heuristic rule-based fallback classification
- Decoupled Frontend-Backend architecture
- Multi-container orchestrations with Docker Compose
- Nginx reverse proxying
- End-to-end API testing & debugging

---

## 📌 Project Highlights

IntelliOps combines:

$$\text{React} + \text{FastAPI} + \text{PostgreSQL} + \text{Redis} + \text{AI} + \text{Docker}$$

It demonstrates full-stack software engineering principles, clean separation of concerns, caching strategies, and AI integration with fallback handling.

---

## 👩‍💻 Author

**Anusha Pavani Venneti**

- **GitHub**: [https://github.com/Vennetianusha](https://github.com/Vennetianusha)
- **Project Repository**: [https://github.com/Vennetianusha/IntelliOps](https://github.com/Vennetianusha/IntelliOps)
