# Healthcare + Fitness Agent — Developer Guide

> **Version:** 1.0.0 — DEV MODE  
> **Stack:** FastAPI · LangGraph · FAISS · SQLite · React 18 · Docker Compose  
> **Phase 1:** Local Docker Container  
> **Phase 2 (future):** Azure Container Instances (ACI)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [File Hierarchy](#3-file-hierarchy)
4. [Backend — Detailed Walkthrough](#4-backend--detailed-walkthrough)
   - [Entry Point](#41-entry-point--backendapppy)
   - [Configuration](#42-configuration)
   - [Database Layer](#43-database-layer)
   - [Pydantic Schemas](#44-pydantic-schemas)
   - [Utility Modules](#45-utility-modules)
   - [Agents](#46-agents)
   - [LangGraph State Graph](#47-langgraph-state-graph)
   - [Services](#48-services)
   - [Routes (API Endpoints)](#49-routes-api-endpoints)
5. [Frontend — Detailed Walkthrough](#5-frontend--detailed-walkthrough)
   - [Project Config](#51-project-config)
   - [Types](#52-types)
   - [Store (Zustand)](#53-store-zustand)
   - [API Client](#54-api-client)
   - [Components](#55-components)
   - [Pages](#56-pages)
6. [Docker Infrastructure](#6-docker-infrastructure)
7. [Data Flows](#7-data-flows)
8. [API Reference](#8-api-reference)
9. [Python Dependencies](#9-python-dependencies)
10. [Testing](#10-testing)
11. [Environment Variables](#11-environment-variables)
12. [Running the Project](#12-running-the-project)
13. [Security Checklist](#13-security-checklist)
14. [Phase 2 — Azure Migration Notes](#14-phase-2--azure-migration-notes)
15. [Troubleshooting](#15-troubleshooting)

---

## 1. Project Overview

The **Healthcare + Fitness Agent** is a multi-agent AI system that:

- Ingests medical lab reports (PDFs)
- Extracts structured health parameters using GPT-4o
- Detects disease risk patterns through rule-based and LLM-powered analysis
- Generates personalised fitness and diet plans
- Exposes a RAG-powered chat interface grounded in the user's own health data

All AI inference is delegated to **Azure OpenAI**. The system runs fully offline in Phase 1 (local Docker). Every user's data is isolated via `user_id` namespacing across SQLite and FAISS.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────┐
│  Tier 1 — Browser (React SPA on port 3000)          │
│           ↕ REST + fetch                            │
├─────────────────────────────────────────────────────┤
│  Tier 2 — Nginx reverse proxy                       │
│           /api/* → backend:8000                     │
├─────────────────────────────────────────────────────┤
│  Tier 3 — FastAPI (port 8000, Python 3.11)          │
│           Routing · File upload · Auth scaffold     │
├─────────────────────────────────────────────────────┤
│  Tier 4 — LangGraph Orchestrator                    │
│           StateGraph: disease → risk → fitness      │
├──────────────────────────┬──────────────────────────┤
│  Tier 5 — Agent Layer    │  Tier 5 — Services       │
│  • Intake (no LLM)       │  • pdf_service           │
│  • Doc Analysis (GPT-4o) │  • embedding_service     │
│  • Risk Scoring          │  • risk_service          │
│  • Disease Patterns      │  • fitness_service       │
│  • Fitness Plan (GPT-4o) │                          │
├──────────────────────────┴──────────────────────────┤
│  Tier 6 — Storage                                   │
│  • SQLite (health.db) — structured records          │
│  • FAISS (data/faiss_index/{user_id}/) — vectors    │
│  • Filesystem (data/pdfs/) — raw PDFs               │
├─────────────────────────────────────────────────────┤
│  External — Azure OpenAI                            │
│  • GPT-4o (chat / extraction / plan generation)     │
│  • text-embedding-3-small (vector embeddings)       │
└─────────────────────────────────────────────────────┘
```

**Request flow:** Browser → Nginx → FastAPI → Service → Agent(s) → Azure OpenAI  
**Response flow:** Azure OpenAI → Agent → Service → FastAPI → Nginx → Browser

---

## 3. File Hierarchy

```
d:/Fitness Planner Agent/
│
├── backend/                          # FastAPI application root
│   ├── __init__.py
│   ├── app.py                        # Entry point — FastAPI app, lifespan, routers
│   │
│   ├── agents/                       # Five LangGraph agents
│   │   ├── __init__.py
│   │   ├── intake_agent.py           # Agent 1: BMI / BMR (no LLM)
│   │   ├── doc_agent.py              # Agent 2: PDF parameter extraction (GPT-4o)
│   │   ├── risk_agent.py             # Agent 3: Risk scoring + LLM summary
│   │   ├── disease_agent.py          # Agent 4: Rule-based pattern detection
│   │   ├── fitness_agent.py          # Agent 5: Personalised plan (GPT-4o)
│   │   └── graph.py                  # LangGraph StateGraph wiring
│   │
│   ├── db/                           # Database layer
│   │   ├── __init__.py
│   │   ├── database.py               # SQLAlchemy engine + session + get_db()
│   │   ├── models.py                 # ORM models: User, HealthRecord, ChatSession, ChatMessage
│   │   └── init_db.py                # Standalone schema creation script
│   │
│   ├── models/                       # Pydantic v2 schemas
│   │   ├── __init__.py
│   │   └── schemas.py                # Request/response contracts for all endpoints
│   │
│   ├── routes/                       # FastAPI routers
│   │   ├── __init__.py
│   │   ├── upload.py                 # POST /upload/{user_id}
│   │   ├── chat.py                   # POST /chat/
│   │   ├── insights.py               # GET  /insights/{user_id}
│   │   ├── fitness.py                # POST /fitness/plan
│   │   └── users.py                  # POST /users/ · GET /users/{user_id}
│   │
│   ├── services/                     # Orchestration layer (calls agents)
│   │   ├── __init__.py
│   │   ├── pdf_service.py            # Full PDF ingestion pipeline
│   │   ├── embedding_service.py      # FAISS index management (upsert + retrieve)
│   │   ├── risk_service.py           # Health analysis orchestration for /insights
│   │   └── fitness_service.py        # Fitness plan orchestration for /fitness/plan
│   │
│   └── utils/                        # Shared utilities
│       ├── __init__.py
│       ├── llm_factory.py            # lru_cached AzureChatOpenAI instance
│       ├── prompt_templates.py       # All LLM prompt strings
│       ├── guardrails.py             # Medical disclaimer + critical keyword detection
│       └── pdf_parser.py             # PyMuPDF + pdfplumber extraction helpers
│
├── config/
│   ├── .env                          # Runtime secrets (git-ignored)
│   ├── .env.example                  # Template — copy to .env and fill in
│   └── settings.py                   # Pydantic BaseSettings (lru_cached)
│
├── data/                             # Persistent data (Docker bind-mounted)
│   ├── pdfs/                         # Uploaded PDF files: {user_id}_{file_id}.pdf
│   ├── faiss_index/                  # Per-user FAISS indexes: {user_id}/index.faiss
│   └── drug_knowledge/               # Static drug interaction text files
│
├── docker/
│   ├── Dockerfile.backend            # python:3.11-slim-bookworm, uvicorn --reload
│   ├── Dockerfile.frontend           # node:20-alpine build → nginx:1.25-alpine serve
│   └── nginx.conf                    # SPA fallback + /api/ proxy to backend:8000
│
├── frontend/                         # React 18 + Vite + TypeScript + Tailwind
│   ├── index.html                    # Vite entry HTML
│   ├── package.json                  # NPM dependencies
│   ├── vite.config.ts                # Vite config with /api proxy to :8000
│   ├── tsconfig.json                 # TypeScript strict mode
│   ├── tsconfig.node.json
│   ├── tailwind.config.js            # Tailwind with custom health colour tokens
│   ├── postcss.config.js
│   └── src/
│       ├── main.tsx                  # ReactDOM.createRoot entry
│       ├── App.tsx                   # BrowserRouter + all Routes
│       ├── index.css                 # Tailwind base/components/utilities
│       │
│       ├── types/
│       │   └── index.ts              # Shared TypeScript interfaces
│       │
│       ├── store/
│       │   └── index.ts              # Zustand global state store
│       │
│       ├── services/
│       │   └── api.ts                # Typed Axios API client
│       │
│       ├── components/               # Reusable UI components
│       │   ├── Navbar.tsx            # Top navigation bar
│       │   ├── Card.tsx              # Generic card wrapper
│       │   ├── RiskBadge.tsx         # Coloured risk level pill
│       │   └── Spinner.tsx           # Animated loading spinner
│       │
│       └── pages/                    # Route-level page components
│           ├── Dashboard.tsx         # Home — quick links + summary panels
│           ├── UploadPage.tsx        # Drag-and-drop PDF uploader
│           ├── ChatPage.tsx          # RAG chat interface
│           ├── InsightsPage.tsx      # Risk score + flagged parameters table
│           ├── FitnessPage.tsx       # 4-section fitness plan display
│           └── ProfilePage.tsx       # User profile form (age/gender/height/weight)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # In-memory SQLite session fixture
│   ├── fixtures/                     # Sample PDFs for integration tests
│   │
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_risk_scoring.py      # compute_risk_score: 6 test cases
│   │   ├── test_intake_agent.py      # BMI / BMR: 5 test cases
│   │   ├── test_disease_agent.py     # Rule engine: 7 test cases
│   │   └── test_guardrails.py        # Disclaimer / critical detection: 5 tests
│   │
│   └── integration/
│       ├── __init__.py
│       └── test_upload_pipeline.py   # Full HTTP stack: 5 async test cases
│
├── docker-compose.yml                # Orchestrates backend + frontend + redis
├── requirements.txt                  # Production Python dependencies
├── requirements.dev.txt              # + pytest, httpx, anyio
├── pytest.ini                        # asyncio_mode=auto, testpaths=tests
└── .gitignore                        # Excludes .env, *.db, data/, node_modules/
```

---

## 4. Backend — Detailed Walkthrough

### 4.1 Entry Point — `backend/app.py`

Creates the FastAPI application with:

- **Lifespan context manager** — runs `Base.metadata.create_all()` on startup so SQLite tables are created automatically on first boot.
- **CORS middleware** — origins loaded from `settings.cors_origins` (defaults to `localhost:3000`).
- **Five routers** mounted at `/upload`, `/chat`, `/insights`, `/fitness`, `/users`.
- **`GET /health`** — Docker healthcheck endpoint returning `{"status": "ok", "version": "1.0.0"}`.

```python
# Startup sequence
models.Base.metadata.create_all(bind=engine)   # idempotent — safe to run every boot
```

---

### 4.2 Configuration

#### `config/settings.py`

Uses **Pydantic `BaseSettings`** — values are read from environment variables, falling back to defaults. The `@lru_cache()` decorator means `get_settings()` returns the same singleton instance throughout the process lifetime.

| Setting | Default | Description |
|---|---|---|
| `azure_openai_api_key` | `""` | Azure OpenAI secret key |
| `azure_openai_endpoint` | `""` | e.g. `https://your-resource.openai.azure.com/` |
| `azure_openai_api_version` | `2024-02-01` | API version string |
| `azure_openai_deployment_name` | `gpt-4o` | Chat model deployment name |
| `azure_openai_embedding_deployment` | `text-embedding-3-small` | Embedding deployment |
| `app_env` | `development` | Environment tag |
| `app_debug` | `False` | Enables SQLAlchemy echo logging |
| `database_url` | `sqlite:///./data/health.db` | SQLAlchemy URL |
| `pdf_storage_path` | `./data/pdfs` | Where uploaded PDFs are saved |
| `faiss_index_path` | `./data/faiss_index` | Root of per-user FAISS indexes |
| `embedding_chunk_size` | `500` | Characters per text chunk |
| `embedding_chunk_overlap` | `50` | Overlap between adjacent chunks |
| `faiss_top_k` | `5` | Top-k chunks retrieved for RAG |
| `cors_origins` | `["http://localhost:3000"]` | Allowed CORS origins |

---

### 4.3 Database Layer

#### `backend/db/database.py`

```
SQLite engine (check_same_thread=False)
    └── SessionLocal (autocommit=False, autoflush=False)
         └── get_db() — FastAPI dependency (yields one session per request)
```

#### `backend/db/models.py` — Four SQLAlchemy ORM Tables

| Table | Primary Key | Key Columns |
|---|---|---|
| `users` | `user_id` (String) | email, age, gender, height_cm, weight_kg, created_at, updated_at |
| `health_records` | `id` (autoincrement) | user_id (indexed), parameter, value, unit, reference_range, status, file_id, recorded_at |
| `chat_sessions` | `session_id` (String) | user_id (indexed), started_at |
| `chat_messages` | `id` (autoincrement) | session_id (indexed), user_id, role (`user`/`assistant`), content, created_at |

**`status` values** for `health_records`: `Normal` · `Low` · `High` · `Critical`

#### `backend/db/init_db.py`

Standalone script callable as `python -m backend.db.init_db`. The same operation runs automatically at FastAPI startup via `lifespan`.

---

### 4.4 Pydantic Schemas

`backend/models/schemas.py` defines all request and response contracts using **Pydantic v2**.

| Schema | Direction | Purpose |
|---|---|---|
| `UserProfile` | Request | age (1–120), gender, height_cm (50–250), weight_kg (20–300) |
| `UserProfileResponse` | Response | Extends UserProfile with optional email |
| `HealthParameter` | Embedded | test_name, value, unit, reference_range, status |
| `UploadResponse` | Response | message, file_id, parameters_extracted |
| `ChatRequest` | Request | user_id, session_id, query |
| `ChatResponse` | Response | answer, disclaimer, sources[] |
| `InsightResponse` | Response | user_id, risk_score, risk_level, flagged_parameters[], conditions[], recommendation |
| `FitnessPlanRequest` | Request | user_id, include_diet, include_workout |
| `FitnessPlanResponse` | Response | workout[], diet[], restrictions[], lifestyle[], disclaimer |

---

### 4.5 Utility Modules

#### `backend/utils/llm_factory.py`

Returns a single `AzureChatOpenAI` instance via `@lru_cache(maxsize=1)`.

```python
temperature = 0.3    # low creativity for medical context
max_tokens  = 2000
```

#### `backend/utils/prompt_templates.py`

Three prompt strings used across agents:

| Constant | Used by | Purpose |
|---|---|---|
| `SYSTEM_GUARDRAIL` | risk_agent, fitness_agent | Safety system message — no diagnosis, flag critical values |
| `DOC_EXTRACTION_PROMPT` | doc_agent | Instructs GPT-4o to return a JSON array of lab parameters |
| `RISK_ANALYSIS_PROMPT` | risk_agent | Patient profile + flagged params → 3–4 sentence risk summary |
| `FITNESS_PLAN_PROMPT` | fitness_agent | Age/BMI/risk/restrictions → JSON `{workout, diet, restrictions, lifestyle}` |

#### `backend/utils/guardrails.py`

| Function | Behaviour |
|---|---|
| `wrap_with_disclaimer(response)` | Appends the full medical disclaimer string |
| `check_critical(response)` | Returns `True` if response contains any critical keyword (`diabetes`, `cardiac`, `kidney failure`, etc.) |
| `apply_guardrails(response)` | Combines both — prepends "URGENT" prefix if critical, always appends disclaimer |

#### `backend/utils/pdf_parser.py`

| Function | Library | Purpose |
|---|---|---|
| `extract_text_pymupdf(file_path)` | PyMuPDF (fitz) | Extracts embedded text from every page |
| `extract_tables_pdfplumber(file_path)` | pdfplumber | Extracts tabular data (lab grids) as pipe-separated rows |
| `combine_pdf_text(file_path)` | Both | Joins both outputs: `raw_text + "\n\n[TABLES]\n" + table_data` |

---

### 4.6 Agents

#### Agent 1 — `backend/agents/intake_agent.py`

**No LLM call.** Pure Python calculation.

- **BMI** = `weight_kg / (height_cm / 100)²`
- **BMI categories**: Underweight (<18.5) · Normal (<25) · Overweight (<30) · Obese (≥30)
- **BMR** (Basal Metabolic Rate) via **Mifflin-St Jeor equation**:
  - Male: `10w + 6.25h - 5a + 5`
  - Female: `10w + 6.25h - 5a - 161`
- Returns `IntakeResult(bmi, bmi_category, bmr)`

---

#### Agent 2 — `backend/agents/doc_agent.py`

Sends the first 6,000 characters of PDF text to GPT-4o and parses the returned JSON array.

**GPT-4o output contract** (enforced by `DOC_EXTRACTION_PROMPT`):
```json
[
  {
    "test_name": "Glucose",
    "value": 108,
    "unit": "mg/dL",
    "reference_range": "70-100 mg/dL",
    "status": "High"
  }
]
```

Handles markdown fences (` ```json `) automatically. Returns `[]` on `JSONDecodeError` rather than crashing.

---

#### Agent 3 — `backend/agents/risk_agent.py`

**Two functions:**

`compute_risk_score(records)` — deterministic, no LLM:

| Parameter | High | Low | Critical |
|---|---|---|---|
| glucose | 30 | 20 | 60 |
| hba1c | 35 | 15 | 70 |
| cholesterol | 20 | 10 | 40 |
| triglycerides | 20 | 10 | 40 |
| creatinine | 25 | 15 | 50 |
| hemoglobin | 15 | 25 | 45 |

Score thresholds: `0` = Low · `<40` = Moderate · `<70` = High · `≥70` = Critical · capped at 100.

`run_risk_agent(...)` — sends patient profile + flagged parameters to GPT-4o, returns a 3–4 sentence risk summary string.

---

#### Agent 4 — `backend/agents/disease_agent.py`

**Rule-based only. Zero LLM cost.**

Checks 7 clinical conditions using fixed numeric thresholds:

| Condition | Criteria |
|---|---|
| Metabolic Syndrome Risk | ≥3 of: glucose>100, triglycerides>150, HDL<40, systolic>130 |
| Pre-diabetes (IFG) | glucose 100–125 mg/dL |
| Pre-diabetes (HbA1c) | HbA1c 5.7–6.4% |
| Possible Diabetes | glucose > 126 mg/dL |
| High LDL — Dyslipidemia Risk | LDL > 160 mg/dL |
| Possible Anemia | hemoglobin < 12 g/dL |
| Elevated Creatinine | creatinine > 1.4 mg/dL |

Parameter matching is **substring-based and case-insensitive** (e.g. `"triglyceride"` matches `"Triglycerides Total"`).

---

#### Agent 5 — `backend/agents/fitness_agent.py`

Determines fitness level from BMI and risk level:

| Condition | Fitness Level |
|---|---|
| risk == Critical | Sedentary Recovery |
| BMI < 25 AND risk == Low | Intermediate |
| BMI ≥ 30 OR risk == High | Beginner |
| Everything else | Beginner-Intermediate |

Sends to GPT-4o, parses JSON. Falls back to a safe hardcoded plan on `JSONDecodeError`.

**GPT-4o output contract:**
```json
{
  "workout": ["..."],
  "diet": ["..."],
  "restrictions": ["..."],
  "lifestyle": ["..."]
}
```

---

### 4.7 LangGraph State Graph

`backend/agents/graph.py` defines a **sequential StateGraph** that threads all context through a typed dictionary:

```
AgentState {
  user_id, age, gender, bmi, records[]
  conditions[], risk_score, risk_level, risk_summary
  fitness_plan{}
}

disease_detection  →  risk_analysis  →  fitness_planning  →  END
     │                     │                   │
run_disease_agent    compute_risk_score   run_fitness_agent
(rule-based)       + run_risk_agent       (GPT-4o)
                     (GPT-4o)
```

Built by calling `build_health_graph()` which returns a compiled `StateGraph`. Agents are imported lazily inside the builder function to avoid circular imports.

---

### 4.8 Services

#### `backend/services/pdf_service.py` — `process_pdf(file_path, user_id, file_id, db)`

Full ingestion pipeline in 4 steps:
1. `combine_pdf_text()` — run both PDF parsers
2. `extract_parameters()` — send to doc_agent (GPT-4o), receive structured JSON
3. Persist each parameter as a `HealthRecord` row in SQLite
4. Chunk text with `RecursiveCharacterTextSplitter(chunk_size=500, overlap=50)` → embed → upsert to FAISS

Returns `{"count": len(parameters), "chunks": len(chunks)}`.

---

#### `backend/services/embedding_service.py`

| Function | Description |
|---|---|
| `get_embeddings()` | Returns `AzureOpenAIEmbeddings` using `text-embedding-3-small` |
| `get_index_path(user_id)` | Returns `data/faiss_index/{user_id}/`, creating it if needed |
| `upsert_to_faiss(user_id, chunks)` | Loads existing index and adds texts, or creates new one |
| `load_retriever(user_id)` | Returns a LangChain `VectorStoreRetriever` with `top_k=5`, or `None` if no index |

---

#### `backend/services/risk_service.py` — `get_full_risk_analysis(user_id, db)`

Orchestrates the full insight pipeline for `GET /insights/{user_id}`:
1. Load user profile and health records from SQLite
2. Compute BMI via `run_intake_agent` (if user profile exists)
3. Call `run_disease_agent` (rule-based conditions)
4. Call `compute_risk_score` (weighted scoring)
5. Call `run_risk_agent` (GPT-4o narrative summary)
6. Build and return the `InsightResponse` dict

---

#### `backend/services/fitness_service.py` — `get_fitness_plan(user_id, db)`

Orchestrates plan generation for `POST /fitness/plan`:
1. Load user profile → BMI
2. Load health records → conditions + risk level
3. Call `run_fitness_agent` (GPT-4o)

Returns the raw plan dict which is validated by `FitnessPlanResponse`.

---

### 4.9 Routes (API Endpoints)

| Method | Path | File | Description |
|---|---|---|---|
| `GET` | `/health` | `app.py` | Docker healthcheck |
| `GET` | `/docs` | FastAPI auto | Swagger UI |
| `POST` | `/upload/{user_id}` | `routes/upload.py` | Upload PDF — validates extension + 20 MB limit, calls `process_pdf` |
| `POST` | `/chat/` | `routes/chat.py` | RAG chat — loads FAISS retriever, runs `RetrievalQA`, persists messages |
| `GET` | `/insights/{user_id}` | `routes/insights.py` | Returns `InsightResponse` from `get_full_risk_analysis` |
| `POST` | `/fitness/plan` | `routes/fitness.py` | Returns `FitnessPlanResponse` from `get_fitness_plan` |
| `POST` | `/users/` | `routes/users.py` | Create or update user profile (upsert) |
| `GET` | `/users/{user_id}` | `routes/users.py` | Retrieve user profile |

#### RAG Prompt (in `routes/chat.py`)

```
You are a healthcare AI assistant. Use ONLY the context below to answer.
If the context does not contain the answer, say "I cannot find that in your health records."
Never provide a medical diagnosis. Always recommend consulting a physician for concerning values.

Context from health records:
{context}

Patient Question: {question}

Answer:
```

---

## 5. Frontend — Detailed Walkthrough

### 5.1 Project Config

| File | Purpose |
|---|---|
| `vite.config.ts` | Vite on port 3000; proxies `/api/*` → `http://localhost:8000` (strips `/api` prefix) |
| `tsconfig.json` | `strict: true`, `noUnusedLocals`, `noUnusedParameters`, targets ES2020 |
| `tailwind.config.js` | Scans `src/**/*.{ts,tsx}`; custom `primary` blue scale + `health` colour tokens (`low`/`moderate`/`high`/`critical`) |
| `postcss.config.js` | Runs `tailwindcss` + `autoprefixer` |

---

### 5.2 Types

`frontend/src/types/index.ts` — all shared TypeScript interfaces mirroring the backend Pydantic schemas:

```typescript
UserProfile · HealthParameter · UploadResponse
ChatMessage · InsightResponse · FitnessPlan
```

---

### 5.3 Store (Zustand)

`frontend/src/store/index.ts` — single global `AppState`:

| State Field | Type | Description |
|---|---|---|
| `userId` | `string` | Active user ID (default: `"user-001"`) |
| `sessionId` | `string` | Chat session UUID (generated with `crypto.randomUUID()`) |
| `user` | `UserProfile \| null` | Loaded user profile |
| `insights` | `InsightResponse \| null` | Last fetched insights |
| `fitnessPlan` | `FitnessPlan \| null` | Last generated plan |
| `chatMessages` | `ChatMessage[]` | Full conversation history |
| `isLoading` | `boolean` | Global loading flag |
| `error` | `string \| null` | Global error message |

Actions: `setUserId` · `setUser` · `setInsights` · `setFitnessPlan` · `addChatMessage` · `setLoading` · `setError` · `clearChat`

---

### 5.4 API Client

`frontend/src/services/api.ts` — typed Axios functions, all returning the parsed `data` field:

| Function | Method | Endpoint | Notes |
|---|---|---|---|
| `createUser(profile)` | POST | `/api/users/` | |
| `getUser(userId)` | GET | `/api/users/{userId}` | |
| `uploadPdf(userId, file)` | POST | `/api/upload/{userId}` | `multipart/form-data` |
| `getInsights(userId)` | GET | `/api/insights/{userId}` | |
| `getFitnessPlan(userId)` | POST | `/api/fitness/plan` | |
| `sendChat(userId, sessionId, query)` | POST | `/api/chat/` | |

---

### 5.5 Components

| Component | File | Description |
|---|---|---|
| `Navbar` | `components/Navbar.tsx` | Top bar with icon links to all 5 routes; active route highlighted |
| `Card` | `components/Card.tsx` | White rounded panel with optional `title` prop |
| `RiskBadge` | `components/RiskBadge.tsx` | Coloured pill for `Low`/`Moderate`/`High`/`Critical` |
| `Spinner` | `components/Spinner.tsx` | Animated SVG spinner using Tailwind `animate-spin` |

---

### 5.6 Pages

| Page | Route | Key features |
|---|---|---|
| `Dashboard` | `/` | Quick-action grid → other routes; shows latest InsightResponse and fitness plan snippet if loaded |
| `UploadPage` | `/upload` | Drag-and-drop zone (also click to browse); file type validation; calls `uploadPdf`; shows extracted parameter count |
| `ChatPage` | `/chat` | Full chat UI with auto-scroll; user/assistant bubbles with icons; Enter to send; disclaimer shown under each assistant reply |
| `InsightsPage` | `/insights` | Risk score progress bar; condition pills; flagged parameters sortable table with colour-coded status |
| `FitnessPage` | `/fitness` | 4-card grid: Workout · Diet · Restrictions · Lifestyle Tips; fallback disclaimer |
| `ProfilePage` | `/profile` | Controlled form for age/gender/height/weight; upserts via `POST /users/` |

---

## 6. Docker Infrastructure

### `docker-compose.yml`

Three services on a shared bridge network (`hfa-network`):

```
backend   (hfa-backend)   → port 8000:8000
frontend  (hfa-frontend)  → port 3000:80
redis     (hfa-redis)     → port 6379:6379
```

**Volume mounts on backend:**
- `./data:/app/data` — persists PDFs and FAISS indexes across container restarts
- `./backend:/app/backend` — enables Uvicorn `--reload` hot-reload in development

**Healthcheck:** `curl -f http://localhost:8000/health` every 30 s, 3 retries.

---

### `docker/Dockerfile.backend`

```
Base:  python:3.11-slim-bookworm
Deps:  build-essential, libmupdf-dev, curl (for PyMuPDF native libs)
CMD:   uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload --log-level info
```

---

### `docker/Dockerfile.frontend`

Two-stage build:
```
Stage 1 (builder):  node:20-alpine  → npm ci → npm run build → /app/dist
Stage 2 (server):   nginx:1.25-alpine → copies dist + nginx.conf
```

---

### `docker/nginx.conf`

```nginx
location /          # SPA fallback: try_files → /index.html
location /api/      # Proxy to http://backend:8000/
                    # proxy_read_timeout 300s  (long LLM calls)
                    # proxy_buffering off       (SSE support)
```

---

## 7. Data Flows

### PDF Ingestion (`POST /upload/{user_id}`)

```
1.  Validate file extension (.pdf) and size (≤ 20 MB)
2.  Generate UUID → save to data/pdfs/{user_id}_{file_id}.pdf
3.  combine_pdf_text():
      ├── PyMuPDF  → raw text (all pages)
      └── pdfplumber → table rows (pipe-separated)
4.  extract_parameters(combined[:6000]) → GPT-4o → JSON array
5.  Persist each parameter → SQLite health_records
6.  RecursiveCharacterTextSplitter(500 chars, 50 overlap)
7.  Embed chunks via text-embedding-3-small
8.  Upsert into FAISS data/faiss_index/{user_id}/
9.  Return {message, file_id, parameters_extracted}
```

### RAG Chat (`POST /chat/`)

```
1.  load_retriever(user_id) → FAISS retriever (top-k=5)
2.  Embed user query → similarity search → 5 text chunks
3.  Build RetrievalQA prompt: [RAG_PROMPT] + context + question
4.  GPT-4o generates grounded answer
5.  Persist user + assistant messages to chat_messages table
6.  Return {answer, disclaimer}
```

### Insights (`GET /insights/{user_id}`)

```
1.  Load User + HealthRecords from SQLite
2.  run_intake_agent() → BMI (if user profile exists)
3.  run_disease_agent() → conditions[] (rule-based, no LLM)
4.  compute_risk_score() → (score: int, level: str)  (no LLM)
5.  run_risk_agent() → recommendation string (GPT-4o)
6.  Return InsightResponse
```

### Fitness Plan (`POST /fitness/plan`)

```
1.  Load User + HealthRecords
2.  run_intake_agent() → BMI
3.  run_disease_agent() → conditions[]
4.  compute_risk_score() → risk_level
5.  get_fitness_level(bmi, risk_level) → fitness tier
6.  run_fitness_agent() → GPT-4o → JSON plan
7.  Validate with FitnessPlanResponse, return
```

---

## 8. API Reference

### `POST /upload/{user_id}`
```
Content-Type: multipart/form-data
Body: file (PDF, ≤ 20 MB)

Response 200:
{
  "message": "PDF processed successfully",
  "file_id": "uuid-string",
  "parameters_extracted": 14
}

Error 400: Only PDF files accepted
Error 413: File too large (max 20 MB)
```

### `POST /chat/`
```json
// Request
{ "user_id": "user-001", "session_id": "uuid", "query": "What is my glucose level?" }

// Response
{ "answer": "...", "disclaimer": "This is not medical advice...", "sources": [] }
```

### `GET /insights/{user_id}`
```json
{
  "user_id": "user-001",
  "risk_score": 55,
  "risk_level": "High",
  "flagged_parameters": [
    { "test_name": "Glucose", "value": 130, "unit": "mg/dL", "reference_range": "70-100 mg/dL", "status": "High" }
  ],
  "conditions": ["Possible Diabetes — Refer to physician"],
  "recommendation": "..."
}
```

### `POST /fitness/plan`
```json
// Request
{ "user_id": "user-001", "include_diet": true, "include_workout": true }

// Response
{
  "workout": ["30 min brisk walking", "..."],
  "diet": ["Reduce refined carbs", "..."],
  "restrictions": ["Avoid high-impact exercise", "..."],
  "lifestyle": ["7-8 hours sleep", "..."],
  "disclaimer": "Consult a physician before starting any new exercise regimen."
}
```

### `POST /users/`
```json
// Request
{ "user_id": "user-001", "age": 35, "gender": "male", "height_cm": 175, "weight_kg": 75 }

// Response: same fields + optional email
```

---

## 9. Python Dependencies

| Package | Version | Purpose |
|---|---|---|
| `fastapi` | 0.111.0 | Async REST framework |
| `uvicorn[standard]` | 0.29.0 | ASGI server |
| `python-multipart` | 0.0.9 | File upload support |
| `pydantic` | 2.7.1 | Schema validation |
| `pydantic-settings` | 2.2.1 | `BaseSettings` env var loading |
| `sqlalchemy` | 2.0.30 | ORM + SQLite engine |
| `langchain` | 0.2.0 | LLM chains, RAG, memory |
| `langchain-openai` | 0.1.7 | Azure OpenAI integrations |
| `langchain-community` | 0.2.0 | FAISS vector store wrapper |
| `langchain-text-splitters` | 0.2.0 | `RecursiveCharacterTextSplitter` |
| `langgraph` | 0.1.5 | Multi-agent state graph |
| `faiss-cpu` | 1.8.0 | Vector similarity search |
| `pymupdf` | 1.24.3 | PDF text extraction |
| `pdfplumber` | 0.11.0 | PDF table extraction |
| `python-dotenv` | 1.0.1 | `.env` file loading |
| `structlog` | 24.1.0 | Structured JSON logging |
| `httpx` | 0.27.0 | Async HTTP (test client) |
| `python-jose[cryptography]` | 3.3.0 | JWT scaffold (Phase 2) |
| `passlib[bcrypt]` | 1.7.4 | Password hashing scaffold |

**Dev extras** (`requirements.dev.txt`): `pytest==8.2.0`, `pytest-asyncio==0.23.6`, `pytest-cov==5.0.0`, `anyio==4.3.0`

---

## 10. Testing

### Configuration — `pytest.ini`
```ini
asyncio_mode = auto
testpaths = tests
```

### `tests/conftest.py`

Provides a **session-scoped in-memory SQLite engine** and a **function-scoped `db_session`** fixture that rolls back after each test — no side effects between tests.

### Unit Tests

#### `tests/unit/test_risk_scoring.py` (6 cases)
- All-normal records → score 0, level Low
- Single High cholesterol → score 20, level Moderate
- High glucose + High HbA1c → score ≥ 40, level High/Critical
- Two Critical records → score capped at 100, level Critical
- Unknown parameter → no contribution (score 0)
- Empty records → score 0, level Low

#### `tests/unit/test_intake_agent.py` (5 cases)
- Normal BMI calculation (≈22.86 for 70 kg / 175 cm)
- Obese, Underweight, Overweight category classification
- Male BMR > Female BMR (Mifflin-St Jeor constant difference)

#### `tests/unit/test_disease_agent.py` (7 cases)
- Pre-diabetes IFG (glucose 100–125)
- Possible Diabetes (glucose > 126)
- High LDL Dyslipidemia (LDL > 160)
- Possible Anemia (hemoglobin < 12)
- Elevated Creatinine (> 1.4)
- Metabolic Syndrome (≥ 3 criteria met)
- Normal glucose → empty conditions list

#### `tests/unit/test_guardrails.py` (5 cases)
- Disclaimer is appended
- Critical keyword detection: True / False
- `apply_guardrails` for critical → `requires_doctor=True` + "URGENT" prefix
- `apply_guardrails` for normal → `requires_doctor=False`

### Integration Tests

#### `tests/integration/test_upload_pipeline.py` (5 async cases)

Uses `httpx.AsyncClient` with `ASGITransport` — runs against the real FastAPI app with an in-memory DB:
- `GET /health` → 200, `{"status": "ok"}`
- `POST /upload/{user_id}` with a `.txt` file → 400 (validation)
- `POST /chat/` for a user with no FAISS index → 200, message contains "No health records found"
- `GET /insights/nonexistent-user` → 200, risk_level = "Low", risk_score = 0
- `POST /users/` → 200, echoes back user fields

### Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# With coverage
pytest tests/ --cov=backend --cov-report=html

# Inside Docker
docker compose exec backend pytest tests/ -v
```

---

## 11. Environment Variables

Copy `config/.env.example` to `config/.env` and fill in your values:

```bash
# ── Azure OpenAI ───────────────────────────────────────────
AZURE_OPENAI_API_KEY=your_azure_openai_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

# ── Application ────────────────────────────────────────────
APP_ENV=development
APP_SECRET_KEY=change-me-in-production-use-openssl-rand
APP_DEBUG=true
APP_LOG_LEVEL=INFO

# ── Database ───────────────────────────────────────────────
DATABASE_URL=sqlite:///./data/health.db

# ── Storage ────────────────────────────────────────────────
PDF_STORAGE_PATH=./data/pdfs
FAISS_INDEX_PATH=./data/faiss_index
DRUG_KNOWLEDGE_PATH=./data/drug_knowledge

# ── Embedding ──────────────────────────────────────────────
EMBEDDING_CHUNK_SIZE=500
EMBEDDING_CHUNK_OVERLAP=50
FAISS_TOP_K=5

# ── CORS ───────────────────────────────────────────────────
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

**Never commit `config/.env`.** It is listed in `.gitignore`.

---

## 12. Running the Project

### Option A — Docker (recommended)

```bash
# 1. Configure environment
cp config/.env.example config/.env
#    Fill in AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT

# 2. Build and start all services
docker compose up --build

# 3. Access
#    Frontend:   http://localhost:3000
#    Backend:    http://localhost:8000
#    Swagger UI: http://localhost:8000/docs
#    ReDoc:      http://localhost:8000/redoc

# 4. View logs
docker compose logs -f backend
docker compose logs -f frontend

# 5. Stop
docker compose down

# 6. Full reset (removes volumes)
docker compose down -v

# 7. Rebuild single service
docker compose up -d --build backend
```

### Option B — Local Development (no Docker)

```bash
# Backend
cp config/.env.example config/.env
pip install -r requirements.dev.txt
uvicorn backend.app:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:3000  (proxies /api → localhost:8000)
```

### First-Run Notes

- SQLite tables are **auto-created** on first backend startup via `Base.metadata.create_all()`.
- `data/pdfs/`, `data/faiss_index/`, `data/drug_knowledge/` are created by Docker on startup and by `os.makedirs(..., exist_ok=True)` in code.
- No seed data is required. Upload a PDF to begin.

---

## 13. Security Checklist

| Item | Status | Notes |
|---|---|---|
| User data isolation | Done | All queries and FAISS paths are namespaced by `user_id` |
| API key management | Done | Stored in `config/.env`, excluded from git |
| File validation | Done | Extension check + 20 MB limit, server-side |
| Input sanitisation | Done | All inputs pass Pydantic v2 validators |
| Medical guardrails | Done | Every LLM response: disclaimer appended + critical keyword detection |
| Prompt injection defence | Done | User input passed as `HumanMessage`, never interpolated into system prompts |
| Rate limiting | Scaffolded | Redis container is running; `slowapi` integration is the next step |
| JWT authentication | Scaffolded | `python-jose` + `passlib` installed; auth middleware not yet wired |

### Phase 2 Production Security (before Azure deployment)

- Implement JWT auth middleware with Azure AD B2C
- Enable HTTPS via Azure Application Gateway
- Rotate `APP_SECRET_KEY` → `openssl rand -hex 32`
- Migrate all secrets to Azure Key Vault (remove `.env` entirely)
- Enable Application Insights for distributed tracing

---

## 14. Phase 2 — Azure Migration Notes

| Component | Phase 1 | Phase 2 replacement |
|---|---|---|
| Database | SQLite (`data/health.db`) | Azure SQL (PostgreSQL) or Cosmos DB |
| Vector store | FAISS (local files) | Qdrant on ACI or Azure AI Search |
| PDF storage | Local filesystem | Azure Blob Storage |
| Secrets | `config/.env` | Azure Key Vault |
| TLS / routing | Nginx (plain HTTP) | Azure Application Gateway |
| Observability | structlog (stdout) | Application Insights |
| Auth | None | JWT + Azure AD B2C |

**FAISS concurrency note:** FAISS is single-process. Under multi-worker Uvicorn or multi-container ACI, migrate to Qdrant or Azure AI Search. The `embedding_service.py` interface is already abstracted — only `upsert_to_faiss` and `load_retriever` need to change.

### Container Registry Push (Phase 2)

```bash
az acr login --name yourregistry
docker tag hfa-backend yourregistry.azurecr.io/hfa-backend:v1.0
docker tag hfa-frontend yourregistry.azurecr.io/hfa-frontend:v1.0
docker push yourregistry.azurecr.io/hfa-backend:v1.0
docker push yourregistry.azurecr.io/hfa-frontend:v1.0
```

---

## 15. Troubleshooting

### Container fails to start
```bash
docker compose logs backend
```
Common causes: missing `config/.env`, invalid Azure OpenAI credentials, port 8000 or 3000 already in use.
```bash
docker compose down && docker compose up --build
```

### PDF extraction returns zero parameters
The PDF may be image-based (scanned). PyMuPDF extracts **embedded text only**. Verify by opening the PDF and pressing Ctrl+A — if no text is selected, the file is scanned. Add `pytesseract` for OCR pre-processing.

### FAISS index not found
The user has not uploaded a PDF yet. `load_retriever()` returns `None` and `/chat/` responds with `"No health records found. Please upload a PDF first."`.

### Azure OpenAI 429 Rate Limit
Add exponential backoff using `tenacity`:
```python
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
async def call_llm(...):
    ...
```

### SQLite database locked
SQLite has limited write concurrency. Ensure all DB writes use `get_db()` dependency injection (one session per request). Migrate to PostgreSQL for production multi-worker setups.

### Frontend shows blank page
Check browser console. Most likely cause: Vite proxy not running (backend is down) or the `/api` prefix is misconfigured. Ensure `vite.config.ts` proxy target matches the backend port.

---

*This guide documents the codebase as built. All file paths are relative to the project root: `d:\Fitness Planner Agent\`.*
