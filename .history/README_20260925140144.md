# An Bình Chemtech — Quotation Automation Prototype

Prototype end-to-end: **Internal Web UI → FastAPI → Automation Worker (Mock Mac mini) → optional AI note → DOCX**.

Assessment deadline: **25/09/2026**.

## Documentation

Tất cả tài liệu nằm trong [`docs/`](docs/README.md):

| File | Nội dung |
|------|----------|
| [Describle.txt](docs/Describle.txt) | Đề bài |
| [solution-plan.md](docs/solution-plan.md) / [VI](docs/solution-plan-vi.md) | Solution plan as-built |
| [architecture-diagrams.md](docs/architecture-diagrams.md) | Sơ đồ |
| [tech-stack.md](docs/tech-stack.md) | Tech stack |
| [roadmap.md](docs/roadmap.md) | Phase status |
| [samples/](docs/samples/README.md) | DOCX mẫu |

---

## 1. Project overview

An Bình Chemtech needs a controlled way to create customer quotations from the internal management system, hand work off to an automation agent (Mac mini), and return a standardized DOCX with trackable status.

This repository is a **working prototype**, not a production CRM. It demonstrates:

- Clear separation: UI / API / worker
- Quotation lifecycle with status, history, attempts
- Deterministic DOCX generation from a template
- Optional AI only for free-text **note** normalization
- Retry after failure, idempotent create, safe file download

---

## 2. Architecture

```text
┌─────────────────────────────────────┐
│  Internal Management System (FE)    │
│  React + TypeScript + Vite          │
│  Customer · Quotation form · Status │
└─────────────────┬───────────────────┘
                  │ REST (/api)
                  ▼
┌─────────────────────────────────────┐
│  Backend API                        │
│  FastAPI + Pydantic + SQLAlchemy    │
│  Validation · Quotation jobs · SQLite│
│  History · Attempts · Audit         │
└─────────────────┬───────────────────┘
                  │ poll claim / complete / fail
                  ▼
┌─────────────────────────────────────┐
│  Automation Worker (= Mock Mac mini)│
│  Python process                     │
│                                     │
│  Optional AI (note only)            │
│    MockAI (default) | CodexRunner   │
│           │                         │
│           ▼                         │
│  Deterministic TemplateService      │
│           │                         │
│           ▼                         │
│  Output Validator → DOCX            │
└─────────────────────────────────────┘
```

| Layer | Responsibility |
|-------|----------------|
| Frontend | Forms, status polling, download/retry UX |
| Backend | Authz-free CRUD, validation, job state machine, file allowlist |
| Worker | Claim jobs, optional note AI, fill template, validate, report result |

---

## 3. Main workflow

1. User opens **Customer detail** → **Tạo báo giá** (blocked if customer inactive).
2. Form submits `POST /api/quotations` with header `Idempotency-Key`.
3. Backend stores quotation as **PENDING** (events + audit).
4. Worker polls `GET /api/internal/jobs/next` → claim → **PROCESSING**.
5. Optional AI normalizes **note** only (MockAI by default).
6. TemplateService fills DOCX; Validator checks file.
7. Worker `POST .../complete` → **COMPLETED** (or `.../fail` → **FAILED**).
8. UI polls until **COMPLETED** or **FAILED**; Download / Retry accordingly.

```text
PENDING → PROCESSING → COMPLETED
                    ↘ FAILED → (retry) → PENDING → …
```

---

## 4. Tech stack

| Area | Choice |
|------|--------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS 4, React Router |
| Backend | FastAPI, Pydantic, SQLAlchemy, SQLite |
| Worker | Python, httpx, python-docx |
| AI (demo) | MockAI rule-based note cleanup |
| AI (prod boundary) | `CodexRunner` → Codex CLI on Mac mini |
| Tests | pytest (backend + worker) |

---

## 5. Project structure

```text
Project_AnBinhChemtech/
├── frontend/          # Internal management UI
├── backend/           # FastAPI + SQLite
├── worker/            # Automation agent (Mock Mac mini)
│   ├── ai/            # MockAI + AIService + note validation
│   ├── codex/         # Codex CLI integration boundary
│   ├── jobs/          # Template + validator
│   └── output/        # Generated DOCX
├── docs/              # All docs: brief, solution plan, diagrams, samples
├── .env.example
└── README.md          # Runbook (this file)
```

---

## 6. Setup / installation

**Requirements:** Python 3.11+, Node.js 20+.

```powershell
# From repo root
copy .env.example .env

cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

cd ..\worker
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

cd ..\frontend
npm install
```

---

## 7. Run backend / worker / frontend

**Three terminals are required.** Without the worker, jobs stay `PENDING` and the UI keeps polling.

```powershell
# Terminal 1 — Backend API
cd backend
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — Automation Worker (Mock Mac mini)
cd worker
.\.venv\Scripts\python.exe main.py

# Terminal 3 — Frontend
cd frontend
npm run dev
```

| URL | Purpose |
|-----|---------|
| http://localhost:5173 | Demo UI (Vite proxies `/api` → `:8000`) |
| http://127.0.0.1:8000/docs | OpenAPI / Swagger |
| http://127.0.0.1:8000/health | Health check |

### Exact demo commands (copy-paste)

```powershell
# Setup (once)
copy .env.example .env
cd backend; python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt
cd ..\worker; python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt
cd ..\frontend; npm install

# Run (3 terminals)
cd backend;  .\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
cd worker;   .\.venv\Scripts\python.exe main.py
cd frontend; npm run dev

# Tests
cd backend;  .\.venv\Scripts\python.exe -m pytest tests -q
cd worker;   .\.venv\Scripts\python.exe -m pytest tests -q
cd frontend; npm run build
```

---

## 8. Demo flow

1. Open http://localhost:5173 → pick an **active** customer (or create one).
2. **Tạo báo giá** → fill items / terms / note (e.g. `giao gấp, cần mẫu`) → **Gửi**.
3. Status page shows **PENDING** then **PROCESSING** then **COMPLETED**.
4. Worker log should include `ai_note` / MockAI when `AI_NOTE_ENABLED=true`.
5. Click **Download (.docx)** — file under `worker/output/{quotation_id}.docx`.
6. Optional: force a failure via API, then **Retry** on the UI until **COMPLETED**.
7. Optional: **Deactivate** customer → **Tạo báo giá** is blocked (UI + API `400`).

**Note:** MockAI-normalized wording is applied when filling the DOCX. The API still stores the original note entered by the user.

---

## 9. API overview

| Method | Path | Notes |
|--------|------|-------|
| GET | `/health` | Liveness |
| GET/POST | `/api/customers` | List / create |
| GET/PUT | `/api/customers/{id}` | Detail / update |
| POST | `/api/customers/{id}/deactivate` | Soft-deactivate |
| GET/POST | `/api/quotations` | List / create (`Idempotency-Key` optional but used by FE) |
| GET/PUT | `/api/quotations/{id}` | Detail / update (`PENDING`\|`FAILED` only) |
| GET | `/api/quotations/{id}/history` | Status events |
| GET | `/api/quotations/{id}/attempts` | Processing attempts |
| GET | `/api/quotations/{id}/download` | DOCX (COMPLETED only; path allowlisted) |
| POST | `/api/quotations/{id}/retry` | FAILED → PENDING |
| GET | `/api/internal/jobs/next` | Worker claim (`204` if empty) |
| POST | `/api/internal/jobs/{id}/complete` | Worker success |
| POST | `/api/internal/jobs/{id}/fail` | Worker failure |
| GET | `/api/audit` | Audit log |

Full interactive docs: `/docs`.

---

## 10. AI / MockAI / Codex role

| Question | Answer in this prototype |
|----------|--------------------------|
| Where does AI run? | Worker, after claim, **before** TemplateService |
| What may AI change? | **Only** free-text `note` |
| What stays deterministic? | Items, qty, prices, payment/delivery terms, DOCX fill, validation, status machine |
| What is MockAI? | Rule-based note cleanup + simple tags — **no LLM call** |
| What is CodexRunner? | **Integration boundary** for real Codex CLI on Mac mini production |
| Default config? | `USE_CODEX_CLI=false`, `AI_NOTE_ENABLED=true`, `AI_FAIL_JOB_ON_ERROR=false` |

**Prototype today uses MockAI.**  
**Codex CLI is the production integration point** on Mac mini: set `USE_CODEX_CLI=true`, install/authenticate Codex, and finish wiring `codex exec` (or equivalent) inside `worker/codex/codex_runner.py`. Backend and TemplateService stay unchanged.

If AI fails / Codex is unavailable → fallback keeps the original note (unless `AI_FAIL_JOB_ON_ERROR=true`).

---

## 11. Completed features

- Customer list / search / create / edit / soft-deactivate
- Quotation create / update (PENDING|FAILED) / list / status detail
- Idempotency-Key on create; anti-dup for active PENDING/PROCESSING per customer
- Worker poll → claim → optional AI note → template → validate → complete/fail
- Status badges, error message on FAILED, Retry / Download gating
- Processing history, processing attempts, audit log
- Path-allowlisted DOCX download (`worker/output/{id}.docx` only)
- Backend + worker tests; frontend production build

---

## 12. Mocked / unimplemented parts

| Item | Status |
|------|--------|
| Mac mini hardware / agent | **Mocked** by local `worker/` process |
| Real Codex CLI note invoke | **Boundary only** — probe/stub; MockAI used for demo |
| JWT / RBAC / multi-tenant | **Unimplemented** (out of assessment scope) |
| Postgres / Redis / queue broker | **Unimplemented** (SQLite + HTTP poll) |
| Production dashboard / analytics | **Unimplemented** |
| Stuck-PROCESSING auto-recovery / lease timeout | **Unimplemented** |

---

## 13. Known limitations

- Local prototype: internal job endpoints are **unauthenticated** (anyone who can reach `:8000` can claim jobs).
- If the worker dies mid-job, a quotation can remain **PROCESSING** until manual DB cleanup or a fresh demo DB.
- Shared SQLite file; not for concurrent multi-writer production load.
- Concurrent creates with the same new Idempotency-Key may race (unique index) — rare in single-user demo.
- `npm run build` output needs a reverse proxy for `/api` (dev server already proxies).
- Normalized note appears in the **DOCX**; UI shows the stored original note.

---

## 14. Production improvements

1. Deploy `worker/` on Mac mini; enable real Codex CLI (`USE_CODEX_CLI=true` + full `codex exec`).
2. Add auth (JWT/mTLS) for UI and **especially** internal job APIs.
3. Replace SQLite with Postgres; add job lease / heartbeat for stuck PROCESSING.
4. Persist idempotency key + payload hash with TTL; distributed lock if multi-instance API.
5. Object storage for DOCX; signed download URLs.
6. Structured observability (correlation id across FE → API → worker).
7. Queue (Redis/SQS) instead of HTTP poll if throughput grows.

---

## 15. AI tools used during development

- **Cursor** (AI-assisted coding and documentation drafting)
- Candidate remains responsible for architecture decisions, review, and demo explanation

---

## Sample quotation file

`docs/samples/QT-2026-SAMPLE.docx` — see [`docs/samples/README.md`](docs/samples/README.md).
