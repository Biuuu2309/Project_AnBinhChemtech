# Architecture & workflow diagrams

Companion to [`solution-plan.md`](solution-plan.md) / [`solution-plan-vi.md`](solution-plan-vi.md).  
Index: [`README.md`](README.md). ASCII only — no extra tooling required.

## System context

```text
┌─────────────────────────────┐       ┌─────────────────────────────┐
│ Internal Management System  │       │ Automation (Mac mini)       │
│                             │       │                             │
│  React SPA                  │       │  Worker process (prototype) │
│  · Customer pages           │       │  · Optional AI / Codex      │
│  · Quotation form/status    │◄─────►│  · Template + Validator     │
└──────────────┬──────────────┘  API  └─────────────────────────────┘
               │
               ▼
┌─────────────────────────────┐
│ Backend API + SQLite        │
│ Jobs · History · Downloads  │
└─────────────────────────────┘
```

## End-to-end processing pipeline

```text
[UI] Create quotation
        │
        ▼
[API] Validate + store Quotation Job (PENDING)
        │
        ▼
[Worker] Claim job (PROCESSING)
        │
        ▼
[AI/Codex] Normalize free-text note (optional; not written to PPTX V2 slide)
        │   protected commercial fields unchanged
        ▼
[PPTX fill] Shape-id mapping on template V2 (copy + mutate)
        │
        ▼
[Validator] PPTX ZIP / slides present
        │
        ▼
[API] COMPLETED + path allowlist ({id}.pptx)
        │
        ▼
[UI] Status / History / Attempts / Download (.pptx)
```

## AI boundary

```text
                 ┌── USE_CODEX_CLI=false ──► MockAI (demo default)
Quotation.note ──┤
                 └── USE_CODEX_CLI=true  ──► CodexRunner (stub boundary)
                                                    │
                                                    ▼
                                          note summary only (DB/UI; not on V2 slide)
                                                    │
                                                    ▼
                                          PPTX fill is deterministic (shape ids)
```
