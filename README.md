# An Binh Chemtech — Quote Automation Prototype

Prototype tạo báo giá end-to-end: **Web nội bộ → FastAPI → Mock Mac Mini worker → file DOCX từ template**.

Deadline bài đánh giá: **25/09/2026**. Tài liệu: `doc/Describle.txt`, `doc/solution-plan-vi.md`, `doc/roadmap.md`.

## Kiến trúc nhanh

```text
React (Vite)  --REST-->  FastAPI + SQLite
                              ↑ poll
                     Python Worker (Mock Mac mini)
                              ↓
              quotation_template.docx → QT-*.docx
```

- Điền template: **deterministic** (`python-docx`)
- Codex CLI: **stub**, không dùng trong happy path
- Job status (source of truth): `PENDING → PROCESSING → COMPLETED | FAILED`

## Setup & chạy local (demo)

Yêu cầu: Python 3.11+, Node 20+.

```powershell
# Một lần
copy .env.example .env
cd backend; python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt
cd ..\worker; python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt
cd ..\frontend; npm install
```

**3 terminal:**

```powershell
# Terminal 1 — API
cd backend
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000

# Terminal 2 — Worker
cd worker
.\.venv\Scripts\python.exe main.py

# Terminal 3 — UI
cd frontend
npm run dev
```

| URL | Việc |
|-----|------|
| http://localhost:5173 | Demo UI |
| http://127.0.0.1:8000/docs | Swagger |
| http://127.0.0.1:8000/health | Health |

### Kịch bản demo (3–5 phút)

1. Mở UI → chọn khách hàng (`CUS-001` / `CUS-002`)
2. **Tạo báo giá** → điền form → **Gửi**
3. Theo dõi `PENDING` → `PROCESSING` → `COMPLETED`
4. **Tải báo giá (.docx)**

Test API: `cd backend; .\.venv\Scripts\python.exe -m pytest tests -q`

## File báo giá mẫu (nộp kèm)

`doc/samples/QT-2026-SAMPLE.docx` — sinh từ cùng pipeline template fill của prototype.

## Nội dung nộp (checklist Describle §6)

| Hạng mục | Vị trí |
|----------|--------|
| Solution Plan + sơ đồ | `doc/solution-plan-vi.md` (EN: `doc/solution-plan.md`) |
| Source code | Repository này |
| README setup/chạy | File này |
| Demo local | Mục “Setup & chạy local” ở trên |
| Sample output | `doc/samples/QT-2026-SAMPLE.docx` |
| Roadmap | `doc/roadmap.md` |

## Completed / Mocked / Unimplemented

| Hạng mục | Trạng thái |
|----------|------------|
| E2E: Customer → Form → Status → Download DOCX | **Completed** |
| Worker poll (Mock Mac mini) + validate output | **Completed** |
| Validation 422, retry, anti-duplicate, logging | **Completed** |
| Mac mini thật | **Mocked** — `worker/` poll Backend |
| Codex CLI | **Mocked/stub** — `worker/codex/codex_runner.py`; không điền template bằng AI |
| JWT / login / RBAC | **Unimplemented** — prototype nội bộ không auth |
| PostgreSQL, Redis queue, object storage, PDF | **Unimplemented** — hướng production trong solution plan |

## Giả định

- Dữ liệu KH/SP giả lập (seed).
- Một worker process đủ cho demo.
- Output DOCX (PDF optional chưa bật).

## AI tools đã dùng

Cursor (AI-assisted development) để triển khai theo roadmap/solution plan. Ứng viên chịu trách nhiệm giải thích kiến trúc và code.

## Hướng production (tóm tắt)

PostgreSQL, persistent job queue, Mac mini agent thật, JWT + RBAC, idempotency key, object storage, monitoring/heartbeat — chi tiết trong `doc/solution-plan-vi.md` §11.
