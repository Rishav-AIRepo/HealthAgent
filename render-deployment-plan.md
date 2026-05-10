# Render Deployment Plan — Healthcare + Fitness Agent
> **Target platform:** Render.com via GitHub  
> **Current setup:** Local Docker Compose (backend + frontend + Redis)  
> **Estimated deployment time:** 45–90 minutes

---

## Table of Contents

1. [Architecture Mapping: Docker → Render](#1-architecture-mapping)
2. [Pre-Deployment Code Changes](#2-pre-deployment-code-changes)
3. [GitHub Repository Preparation](#3-github-repository-preparation)
4. [render.yaml — Infrastructure as Code](#4-renderyaml)
5. [Step-by-Step Render Setup](#5-step-by-step-render-setup)
6. [Environment Variables Reference](#6-environment-variables-reference)
7. [Persistent Storage (Critical)](#7-persistent-storage-critical)
8. [Deployment Order & Verification](#8-deployment-order--verification)
9. [Known Limitations & Mitigations](#9-known-limitations--mitigations)
10. [Cost Estimate](#10-cost-estimate)

---

## 1. Architecture Mapping

### Docker Compose → Render Services

| Docker Compose Service | Render Equivalent | Render Type |
|---|---|---|
| `backend` (FastAPI, port 8000) | `hfa-backend` | **Web Service** (Docker) |
| `frontend` (React + Nginx, port 3000) | `hfa-frontend` | **Static Site** (Vite build) |
| `redis` | `hfa-redis` | **Redis** (Managed) |
| `./data` bind mount (SQLite + FAISS + PDFs) | Render **Disk** on backend | 10 GB persistent disk |

### Why Static Site for Frontend (not Docker)?

The current `Dockerfile.frontend` builds React and serves via Nginx, which internally proxies `/api/` to `http://backend:8000` — a Docker-internal hostname that doesn't exist on Render. Using Render's **Static Site** type:
- Render builds the React app natively with `npm run build`
- The frontend calls the backend by its public Render URL (configured via env var)
- No Nginx proxy needed — simpler, faster, free tier eligible

---

## 2. Pre-Deployment Code Changes

### 2.1 Update API Client to use environment variable (REQUIRED)

**File:** `frontend/src/services/api.ts`

Add a `baseURL` that reads from a Vite build-time environment variable. When `VITE_API_BASE_URL` is not set (local dev), it falls back to empty string and the Vite proxy handles it.

**Current** (top of api.ts):
```typescript
import axios from 'axios';

const api = axios.create({
  // no baseURL — relies on Vite proxy for local dev
});
```

**Change to:**
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
});
```

> **Why:** In production on Render, the frontend is a static site served from a CDN. It has no proxy — all API calls must go to the backend's full URL (e.g., `https://hfa-backend.onrender.com`). This one line handles both local dev and production without touching anything else.

---

### 2.2 Add a `.render-env` type declaration for TypeScript (OPTIONAL but clean)

**File:** `frontend/src/vite-env.d.ts` (already exists from Vite scaffold)

Add the custom variable:
```typescript
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

---

### 2.3 Ensure DATABASE_URL uses an absolute path (REQUIRED for Render Disk)

**File:** `config/settings.py`

Render mounts the persistent disk at `/app/data`. SQLite's relative path `sqlite:///./data/health.db` can resolve inconsistently inside a container. Override with an absolute path via the environment variable.

No code change needed — just set the env var on Render to:
```
DATABASE_URL=sqlite:////app/data/health.db
```
(Four slashes = absolute path in SQLAlchemy's SQLite URL format.)

---

### 2.4 Add `render.yaml` to project root (REQUIRED)

See full content in [Section 4](#4-renderyaml).

---

### Summary of file changes

| File | Change | Required |
|---|---|---|
| `frontend/src/services/api.ts` | Add `baseURL` from env var | **YES** |
| `frontend/src/vite-env.d.ts` | Type declaration for `VITE_API_BASE_URL` | Recommended |
| `render.yaml` (new file) | Infrastructure as code | **YES** |
| `config/.env.example` | Add `VITE_API_BASE_URL` comment | Recommended |

---

## 3. GitHub Repository Preparation

### 3.1 Verify .gitignore excludes secrets

Confirm `config/.env` is in `.gitignore` — it should already be. Never commit the real `.env` file.

```gitignore
# Already in .gitignore — verify these are present:
config/.env
*.db
data/
node_modules/
__pycache__/
```

### 3.2 Commit and push the code changes

```bash
git add render.yaml
git add frontend/src/services/api.ts
git add frontend/src/vite-env.d.ts
git commit -m "chore: add Render deployment config and production API base URL"
git push origin main
```

### 3.3 Repository structure Render expects

```
project-root/
├── render.yaml                    ← Render reads this automatically
├── docker/
│   ├── Dockerfile.backend         ← Used by backend web service
│   └── Dockerfile.frontend        ← NOT used (static site instead)
├── frontend/
│   ├── package.json               ← Render runs npm ci + npm run build here
│   └── src/services/api.ts        ← Updated with baseURL
├── backend/
│   └── ...
└── config/
    └── .env.example               ← For reference only, not deployed
```

---

## 4. render.yaml

Create this file at the **project root** (`render.yaml`).

```yaml
# render.yaml — Render Infrastructure as Code
# Docs: https://render.com/docs/blueprint-spec

services:
  # ── Backend: FastAPI ─────────────────────────────────────
  - type: web
    name: hfa-backend
    runtime: docker
    dockerfilePath: ./docker/Dockerfile.backend
    dockerContext: .            # Build context is project root (imports backend/)
    plan: standard              # Minimum for persistent disk support
    region: oregon              # Choose closest to your users

    healthCheckPath: /health

    disk:
      name: hfa-app-data
      mountPath: /app/data      # Matches where uvicorn writes SQLite + FAISS + PDFs
      sizeGB: 10

    envVars:
      # Azure OpenAI — set values in Render dashboard (sync: false = secret)
      - key: AZURE_OPENAI_API_KEY
        sync: false
      - key: AZURE_OPENAI_ENDPOINT
        sync: false
      - key: AZURE_OPENAI_API_VERSION
        value: "2024-02-01"
      - key: AZURE_OPENAI_DEPLOYMENT_NAME
        value: gpt-4o
      - key: AZURE_OPENAI_EMBEDDING_DEPLOYMENT
        value: text-embedding-3-small

      # Application
      - key: APP_ENV
        value: production
      - key: APP_DEBUG
        value: "false"
      - key: APP_LOG_LEVEL
        value: INFO
      - key: APP_SECRET_KEY
        sync: false             # Generate with: openssl rand -hex 32

      # Storage — absolute paths matching the disk mountPath
      - key: DATABASE_URL
        value: sqlite:////app/data/health.db    # 4 slashes = absolute path
      - key: PDF_STORAGE_PATH
        value: /app/data/pdfs
      - key: FAISS_INDEX_PATH
        value: /app/data/faiss_index
      - key: DRUG_KNOWLEDGE_PATH
        value: /app/data/drug_knowledge

      # Embedding config
      - key: EMBEDDING_CHUNK_SIZE
        value: "500"
      - key: EMBEDDING_CHUNK_OVERLAP
        value: "50"
      - key: FAISS_TOP_K
        value: "5"

      # CORS — update with actual frontend URL after first deploy
      - key: CORS_ORIGINS
        value: '["https://hfa-frontend.onrender.com"]'

      # Redis — from the managed Redis service below
      - key: REDIS_URL
        fromService:
          type: redis
          name: hfa-redis
          property: connectionString

  # ── Frontend: React Static Site ──────────────────────────
  - type: web
    name: hfa-frontend
    runtime: static
    buildCommand: cd frontend && npm ci && npm run build
    staticPublishPath: ./frontend/dist
    region: oregon

    headers:
      # Security headers
      - path: /*
        name: X-Frame-Options
        value: DENY
      - path: /*
        name: X-Content-Type-Options
        value: nosniff

    routes:
      # SPA fallback — all routes serve index.html (React Router)
      - type: rewrite
        source: /*
        destination: /index.html

    envVars:
      # Must be set AFTER backend is deployed — use actual backend URL
      # Format: https://hfa-backend.onrender.com
      - key: VITE_API_BASE_URL
        sync: false

# ── Redis ─────────────────────────────────────────────────
databases:
  - name: hfa-redis
    type: redis
    plan: free
    region: oregon
    maxmemoryPolicy: noeviction
```

> **Note on `CORS_ORIGINS` and `VITE_API_BASE_URL`:** These reference each other (backend needs frontend URL for CORS, frontend needs backend URL for API calls). After first deploy, both URLs will be assigned by Render. Update both env vars in the dashboard and redeploy. This is a one-time bootstrapping step — see [Section 5 Step 6](#step-6-update-cross-service-urls).

---

## 5. Step-by-Step Render Setup

### Step 1: Create a Render account and connect GitHub

1. Go to [https://render.com](https://render.com) → Sign up
2. Dashboard → **Account Settings** → **GitHub** → Connect your GitHub account
3. Grant access to the repository containing this project

---

### Step 2: Deploy via Blueprint (render.yaml)

1. Render Dashboard → **New** → **Blueprint**
2. Select your GitHub repository
3. Render detects `render.yaml` automatically
4. Click **Apply** — Render creates all 3 services (backend, frontend, redis)
5. You'll be prompted to enter values for `sync: false` env vars — **skip for now** (you'll fill them after the backend URL is known)

---

### Step 3: Set secret environment variables on Backend

Navigate to **hfa-backend** → **Environment** → add these manually:

| Key | Value |
|---|---|
| `AZURE_OPENAI_API_KEY` | Your Azure key |
| `AZURE_OPENAI_ENDPOINT` | `https://your-resource.openai.azure.com/` |
| `APP_SECRET_KEY` | Run `openssl rand -hex 32` locally, paste result |

Click **Save Changes** — backend redeploys automatically.

---

### Step 4: Note the Backend URL

After the backend deploys successfully:
- Go to **hfa-backend** → top of the page shows the public URL
- It will be something like `https://hfa-backend.onrender.com`
- Copy this URL

---

### Step 5: Set the Frontend environment variable

Navigate to **hfa-frontend** → **Environment**:

| Key | Value |
|---|---|
| `VITE_API_BASE_URL` | `https://hfa-backend.onrender.com` (your actual backend URL) |

Click **Save Changes** — frontend rebuilds and redeploys.

---

### Step 6: Update Cross-Service URLs

Now that you have both URLs, update two more env vars:

**On hfa-backend → Environment:**

| Key | Value |
|---|---|
| `CORS_ORIGINS` | `["https://hfa-frontend.onrender.com"]` |

Save → backend redeploys.

---

### Step 7: Verify the Disk is mounted

1. Go to **hfa-backend** → **Disks**
2. Confirm `hfa-app-data` is mounted at `/app/data` with 10 GB
3. In **Logs**, look for the SQLAlchemy startup message confirming `health.db` creation

---

### Step 8: Smoke test

```bash
# 1. Health check
curl https://hfa-backend.onrender.com/health
# Expected: {"status":"ok","version":"1.0.0"}

# 2. Create a test user
curl -X POST https://hfa-backend.onrender.com/users/ \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test-001","age":30,"gender":"male","height_cm":175,"weight_kg":75}'

# 3. Get insights (no records yet — should return Low risk)
curl https://hfa-backend.onrender.com/insights/test-001

# 4. Open frontend
open https://hfa-frontend.onrender.com
# Upload a PDF and verify parameter extraction works
```

---

## 6. Environment Variables Reference

### Backend (`hfa-backend`) — Full List

| Variable | Value | Secret? |
|---|---|---|
| `AZURE_OPENAI_API_KEY` | Your key | **YES** |
| `AZURE_OPENAI_ENDPOINT` | `https://your-resource.openai.azure.com/` | **YES** |
| `AZURE_OPENAI_API_VERSION` | `2024-02-01` | No |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | `gpt-4o` | No |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | `text-embedding-3-small` | No |
| `APP_ENV` | `production` | No |
| `APP_DEBUG` | `false` | No |
| `APP_SECRET_KEY` | 32-byte hex string | **YES** |
| `DATABASE_URL` | `sqlite:////app/data/health.db` | No |
| `PDF_STORAGE_PATH` | `/app/data/pdfs` | No |
| `FAISS_INDEX_PATH` | `/app/data/faiss_index` | No |
| `DRUG_KNOWLEDGE_PATH` | `/app/data/drug_knowledge` | No |
| `EMBEDDING_CHUNK_SIZE` | `500` | No |
| `EMBEDDING_CHUNK_OVERLAP` | `50` | No |
| `FAISS_TOP_K` | `5` | No |
| `CORS_ORIGINS` | `["https://hfa-frontend.onrender.com"]` | No |
| `REDIS_URL` | Auto-injected from Redis service | No |

### Frontend (`hfa-frontend`) — Build-time only

| Variable | Value | Notes |
|---|---|---|
| `VITE_API_BASE_URL` | `https://hfa-backend.onrender.com` | Must be set before build |

> Vite bakes `VITE_*` variables into the static bundle at build time. If you change `VITE_API_BASE_URL`, the frontend service must be **redeployed** (not just restarted) to pick up the new value.

---

## 7. Persistent Storage (Critical)

### Why this matters

Render's Docker containers use an **ephemeral filesystem** — any file written inside the container (SQLite DB, FAISS indexes, uploaded PDFs) is **destroyed on every redeploy or restart** unless stored on a mounted Disk.

The `render.yaml` attaches a 10 GB Disk to `hfa-backend` at `/app/data`. This survives:
- Service restarts
- Redeployments
- Render infrastructure maintenance

### What is stored on the Disk

| Path | Contents | Lost without Disk? |
|---|---|---|
| `/app/data/health.db` | All user profiles, health records, chat history | **YES** |
| `/app/data/faiss_index/` | Per-user vector embeddings | **YES** |
| `/app/data/pdfs/` | Uploaded PDF files | **YES** |
| `/app/data/drug_knowledge/` | Static reference files | No (can be rebuilt) |

### Disk plan requirement

Persistent Disks on Render require a **paid plan** on the service they're attached to (`standard` or higher). The free plan does not support Disks. The `render.yaml` already sets `plan: standard` on the backend service.

### Backup strategy (recommended for production)

Set up a periodic script to copy `/app/data/health.db` to Azure Blob Storage or S3 as a backup. Render Disks are durable but not versioned.

---

## 8. Deployment Order & Verification

Deploy in this order to avoid dependency issues:

```
1. hfa-redis     → deploy first (no dependencies)
2. hfa-backend   → deploy second (reads REDIS_URL from redis service)
3. hfa-frontend  → deploy last (needs backend URL for VITE_API_BASE_URL)
```

Render Blueprint deploys all services in parallel by default. If you use Blueprint, just wait for all three to be healthy, then manually set `VITE_API_BASE_URL` and trigger a frontend redeploy.

### Verification checklist

- [ ] `GET /health` returns `{"status": "ok"}`
- [ ] Swagger UI accessible at `https://hfa-backend.onrender.com/docs`
- [ ] Frontend loads at `https://hfa-frontend.onrender.com`
- [ ] PDF upload returns `parameters_extracted > 0`
- [ ] `/insights/{user_id}` returns a valid `InsightResponse`
- [ ] `/chat/` returns grounded answers from uploaded PDF
- [ ] `/fitness/plan` generates a plan
- [ ] After a restart, check that SQLite data persists (Disk is working)

---

## 9. Known Limitations & Mitigations

### 9.1 Free tier spins down (cold start)

Render free-tier Web Services spin down after 15 minutes of inactivity and take ~30 seconds to spin back up on the next request. Since the backend is on the `standard` plan (needed for the Disk), it stays warm. The frontend is a Static Site (always-on CDN — no spin-down).

**Mitigation:** The `standard` plan keeps the backend always running. No action needed.

---

### 9.2 FAISS is single-process only

FAISS indexes are not safe for concurrent writes from multiple processes. On Render's `standard` plan, Uvicorn runs as a single process by default (matching the current Docker setup). This is safe.

**If you scale to multiple instances later:** Migrate FAISS to Qdrant or Azure AI Search (the `embedding_service.py` interface is already abstracted for this). Do not enable multiple instances with the current FAISS setup.

---

### 9.3 SQLite write concurrency

SQLite handles concurrent reads well but serialises writes. For a single-instance deployment (current), this is fine. For high traffic, migrate to PostgreSQL (Render has managed Postgres).

---

### 9.4 Long-running LLM calls and Render's 30-second timeout

Render Web Services have a default **30-second request timeout** for the health check, but API requests themselves don't have a hard timeout at the platform level. However, the load balancer will close connections after prolonged inactivity.

**Mitigation:** The current Nginx config sets `proxy_read_timeout 300s`. On Render, there's no Nginx between Render's load balancer and your service — add a timeout on the Azure OpenAI client side in `llm_factory.py`:

```python
# In backend/utils/llm_factory.py
AzureChatOpenAI(
    ...
    request_timeout=120,  # seconds
)
```

---

### 9.5 Render Static Sites cannot set cookies on a different domain (CORS)

The frontend (`hfa-frontend.onrender.com`) and backend (`hfa-backend.onrender.com`) are on different subdomains. Cross-origin cookies won't work without `SameSite=None; Secure`. Since the current app uses `user_id` passed in request bodies (not cookies), this is not an issue.

---

### 9.6 Render Build Cache

Render caches `node_modules` between builds. If you add a new NPM package and the build fails, clear the cache: **hfa-frontend** → **Settings** → **Clear build cache** → Trigger manual deploy.

---

## 10. Cost Estimate

| Service | Render Plan | Monthly Cost (USD) |
|---|---|---|
| `hfa-backend` | Standard (512 MB RAM, 0.5 CPU) | ~$7 |
| `hfa-frontend` | Static Site | **Free** |
| `hfa-redis` | Free Redis | **Free** (25 MB limit) |
| `hfa-app-data` | 10 GB Disk | ~$1.50/month |
| **Total** | | **~$8.50/month** |

Upgrade backend to `standard-plus` ($25/month) if:
- PDF ingestion causes memory errors (PyMuPDF + FAISS in-memory indexing can be RAM-heavy)
- You add rate limiting with Redis and see performance issues

---

## Quick Reference — URLs After Deployment

| Resource | URL |
|---|---|
| Frontend (user-facing) | `https://hfa-frontend.onrender.com` |
| Backend API | `https://hfa-backend.onrender.com` |
| Swagger UI | `https://hfa-backend.onrender.com/docs` |
| Health Check | `https://hfa-backend.onrender.com/health` |
| Render Dashboard | `https://dashboard.render.com` |

---

*Prepared for developer handoff. All paths are relative to the project root. Follow the deployment order in Section 8 and verify with the checklist before going live.*
