# Solution Plan — Quotation Automation (As Built)

This document describes the **implemented prototype**, not a future wishlist. Items that are mocked or out of scope are labeled explicitly.

| | |
|-|-|
| Vietnamese | [`solution-plan-vi.md`](solution-plan-vi.md) |
| Diagrams | [`architecture-diagrams.md`](architecture-diagrams.md) |
| Tech stack | [`tech-stack.md`](tech-stack.md) |
| Runbook | [`../README.md`](../README.md) |
| Assessment brief | [`Describle.txt`](Describle.txt) |

---

## 1. Problem

An Bình Chemtech creates customer quotations manually. Employees need:

- A form on the customer detail page
- Validated, structured data hand-off to an automation agent (Mac mini)
- A company-standard DOCX output
- Visible status, failure messages, and retry
- Clear boundaries so AI does not invent commercial figures

The assessment asks for a **demoable prototype**, not a full CRM or production platform.

---

## 2. Proposed architecture (implemented)

Three processes, one responsibility each:

| Component | Role in prototype |
|-----------|-------------------|
| **Internal Management System** | React SPA: customers, quotation form, status UI |
| **Backend API** | FastAPI: validation, persistence, job state, download |
| **Automation Worker** | Local Python process that **stands in for the Mac mini agent** |

```text
┌──────────────────────────┐
│ Internal Management      │
│ System (React)           │
└────────────┬─────────────┘
             │ REST
             ▼
┌──────────────────────────┐
│ Backend API (FastAPI)    │
│ Validation · SQLite      │
│ Quotation Job + History  │
└────────────┬─────────────┘
             │ claim / complete / fail
             ▼
┌──────────────────────────┐
│ Automation Worker        │
│ (Mock Mac mini process)  │
│                          │
│  AI/Codex (optional)     │
│       │ note only        │
│       ▼                  │
│  Template Service        │
│       │                  │
│       ▼                  │
│  Validator → DOCX        │
└──────────────────────────┘
```

**Why this split:** the API stays the source of truth for business state; document generation and optional AI run off the request path so UI submit stays fast and failures can be retried cleanly.

---

## 3. Data flow

```text
Internal Management System
        │
        │  POST /api/quotations (+ Idempotency-Key)
        ▼
Backend API  ──validate──►  Quotation Job (PENDING)
        ▲                         │
        │                         │  GET /api/internal/jobs/next
        │                         ▼
        │                 Automation Worker / Mac mini (mocked locally)
        │                         │
        │                         ├─► AI / Codex (optional, note only)
        │                         │         │
        │                         │         ▼
        │                         ├─► Deterministic Template Service
        │                         │         │
        │                         │         ▼
        │                         ├─► Validator
        │                         │         │
        │                         │         ▼
        │                         └─► Generated DOCX
        │                                   │
        │  POST .../complete | .../fail     │
        │◄──────────────────────────────────┘
        │
        ▼
Status / History / Attempts / Download
```

Persisted entities (SQLite):

- `Customer` (`is_active` soft-deactivate)
- `Quotation` + `QuotationItem`
- `QuotationEvent` (processing history)
- `ProcessingAttempt`
- `AuditLog`

---

## 4. Mac mini integration

| Environment | What runs |
|-------------|-----------|
| **This prototype** | `worker/main.py` on the same machine as the API — **Mock Mac mini** |
| **Production intent** | Same worker package on a Mac mini host, polling the Backend |

The Backend does **not** embed Codex or DOCX generation. It only exposes internal job endpoints the agent calls.

Production cut-over:

1. Deploy `worker/` to Mac mini
2. Point `BACKEND_URL` at the API
3. Set `USE_CODEX_CLI=true` and finish Codex CLI wiring
4. Keep TemplateService + Validator deterministic

---

## 5. Automation workflow

1. Backend creates quotation → `PENDING`, writes history + audit
2. Worker polls `GET /api/internal/jobs/next` → atomic claim → `PROCESSING` + new attempt row
3. Load customer; optionally normalize note via AI layer
4. Build field mapping; fill DOCX template; validate file exists / opens / non-empty
5. `POST .../complete` with allowlisted `output_path` → `COMPLETED`
6. On any pipeline error → `POST .../fail` → `FAILED` (UI may Retry → `PENDING`)

Worker entry: `worker/main.py`. Template: `worker/jobs/template_service.py`. Validator: `worker/jobs/validator.py`.

---

## 6. AI vs deterministic processing

### Deterministic (always)

- Schema validation (quantity > 0, note ≤ 2000, required fields)
- Anti-duplicate / idempotency rules
- Status transitions
- Field mapping for products, quantities, unit prices, payment/delivery terms
- DOCX template fill
- Output validation
- Download path allowlist

### AI (optional, note only)

| Mode | When | Behavior |
|------|------|----------|
| **MockAI** | `USE_CODEX_CLI=false` (default) | Rule-based cleanup + tags — **no LLM** |
| **CodexRunner** | `USE_CODEX_CLI=true` | Integration boundary for Codex CLI on Mac mini; prototype probes/`CodexUnavailableError` → fallback |

Guards:

- `apply_note_only` / `assert_protected_fields_unchanged`
- Note result validation (length, forbidden commercial keys in AI output)

**Important for demos:** MockAI output is used when writing the DOCX. The database/UI keep the original user note.

---

## 7. State management

```text
                  create
                    │
                    ▼
                 PENDING ◄──────────────┐
                    │                   │
                 claim                  │ retry
                    ▼                   │
               PROCESSING               │
               /        \               │
              /          \              │
     complete/            \fail         │
            ▼              ▼            │
       COMPLETED         FAILED ────────┘
```

| Status | UI | Allowed actions |
|--------|----|-----------------|
| PENDING | Poll | Update form; wait for worker |
| PROCESSING | Poll | No update / no retry |
| COMPLETED | Stop poll | Download only |
| FAILED | Stop poll | Update; Retry |

Frontend polling stops only on **COMPLETED** or **FAILED**.

---

## 8. Error / retry strategy

| Failure | Handling |
|---------|----------|
| Invalid payload | HTTP 422 (Pydantic) |
| Inactive customer | HTTP 400; UI blocks create |
| Worker template/validate error | Job → FAILED + error_message; attempt recorded |
| AI / Codex unavailable | Fallback to original note (unless `AI_FAIL_JOB_ON_ERROR=true`) |
| User Retry | FAILED → PENDING; new attempt on next claim |
| Duplicate submit | Same `Idempotency-Key` → existing row (`200`); active PENDING/PROCESSING per customer → existing row |

**Not implemented:** automatic recovery if a job stays **PROCESSING** after worker crash (documented limitation).

---

## 9. Security (prototype level)

Implemented:

- Input validation on create/update
- Download / complete only under allowlisted output roots and filename `{quotation_id}.docx`
- Soft-deactivate blocks new quotations
- AI cannot rewrite commercial fields in the worker pipeline

Explicitly **not** in scope for this prototype:

- JWT / RBAC
- Authentication on `/api/internal/jobs/*`
- Encrypted secrets management beyond `.env`

Production must lock down internal job APIs (mTLS or service token) and replace SQLite assumptions.

---

## 10. Prototype vs production

| Topic | Prototype (this repo) | Production |
|-------|------------------------|------------|
| Automation host | Local `worker/` process | Mac mini agent |
| AI note | **MockAI** | Codex CLI via `CodexRunner` |
| Database | SQLite file | Managed Postgres (typical) |
| Job transport | HTTP poll | Poll or queue + lease/heartbeat |
| Auth | None | JWT/RBAC + internal service auth |
| Files | Local `worker/output` | Object storage + signed URLs |
| Idempotency | Key column + anti-dup | Key + payload hash + TTL |

---

## 11. Architecture / workflow diagram (summary)

```text
Internal Management System
        │
        ▼
Backend API
        │
        ▼
Quotation Job (PENDING → PROCESSING → COMPLETED | FAILED)
        │
        ▼
Automation Worker / Mac mini
        │
        ├──────────────────┐
        ▼                  ▼
AI / Codex (optional)   Deterministic Template Service
   note only                    │
        │                       ▼
        └─────────────────► Validator
                                │
                                ▼
                         Generated DOCX
                                │
                                ▼
              Status / History / Attempts / Download
```

---

## 12. What this plan deliberately does **not** claim as done

- Real Codex CLI session completing note normalization
- Physical Mac mini deployment
- JWT, roles, multi-tenancy
- Dashboard / analytics / full CRM
- Automatic PROCESSING lease recovery

Those belong in production follow-up, not in the submitted demo.
