# Architecture & workflow diagrams

Companion to [`solution-plan.md`](solution-plan.md). ASCII only — no extra tooling required.

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
[AI/Codex] Normalize free-text note (optional)
        │   protected commercial fields unchanged
        ▼
[Template Service] Fill DOCX from mapping
        │
        ▼
[Validator] File exists, opens, non-empty
        │
        ▼
[API] COMPLETED + path allowlist
        │
        ▼
[UI] Status / History / Attempts / Download
```

## AI boundary

```text
                 ┌── USE_CODEX_CLI=false ──► MockAI (demo default)
Quotation.note ──┤
                 └── USE_CODEX_CLI=true  ──► CodexRunner (Mac mini boundary)
                                                    │
                                                    ▼
                                          note summary only
                                                    │
                                                    ▼
                                          Template Service (deterministic)
```
