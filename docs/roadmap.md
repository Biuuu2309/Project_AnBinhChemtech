# Roadmap — trạng thái triển khai

Tham chiếu: [`Describle.txt`](Describle.txt), [`solution-plan-vi.md`](solution-plan-vi.md), runbook [`../README.md`](../README.md).  
Deadline bài đánh giá: **25/09/2026**.

## Quyết định kỹ thuật (đã chốt trong code)

| Quyết định | Lựa chọn |
|---|---|
| Automation folder | `worker/` |
| Mac mini nhận job | Worker HTTP poll Backend |
| Tạo DOCX | `python-docx` deterministic |
| AI note (demo) | **MockAI** (`USE_CODEX_CLI=false`) |
| AI note (prod boundary) | `CodexRunner` → Codex CLI trên Mac mini |
| DB | SQLite |
| Auth | **Không** JWT/RBAC (ghi rõ out of scope) |

## Phase status

| Phase | Nội dung | Status |
|-------|----------|--------|
| 1 | Scaffold FE / Backend / Worker, env, health | **Done** |
| 2 | Customer + Quotation API, SQLite, validation | **Done** |
| 3 | Worker poll → template → validator → DOCX | **Done** |
| 4 | FE E2E: form → status poll → download | **Done** |
| 5 | Retry, history/attempts/audit, idempotency, file allowlist | **Done** |
| 6 | MockAI + Codex boundary, docs submission | **Done** |

## Ngoài scope (cố ý chưa làm)

- JWT / RBAC / dashboard CRM
- Postgres / Redis / queue broker
- Mac mini vật lý + Codex `exec` thật
- Tự phục hồi job kẹt `PROCESSING`
