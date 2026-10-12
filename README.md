# An Bình Chemtech — Quotation Automation Prototype

Prototype đánh giá Fresher/Junior: **Web nội bộ (mock) → FastAPI → Automation Worker → điền mẫu PowerPoint V2 → tải `.pptx`**.

Đề bài công ty: [`docs/README.md`](docs/README.md). Template: [`docs/01_Bao_Gia_An_Binh_Chemtech.V2.pptx`](docs/01_Bao_Gia_An_Binh_Chemtech.V2.pptx).  
Kế hoạch ánh xạ PPTX: [`docs/pptx-v2-integration-plan.md`](docs/pptx-v2-integration-plan.md). Demo 3–5’: [`docs/DEMO.md`](docs/DEMO.md).

> **Đây là prototype**, không phải production CRM. **Không** tích hợp Laravel/PostgreSQL/Tailscale/Mac mini thật trong repo này — các thành phần đó được **mô phỏng** bằng React UI + worker local.

---

## 1. Mục tiêu & phạm vi

| Có trong prototype | Không có / mock |
|--------------------|-----------------|
| Tạo KH + báo giá, trạng thái, retry, history/attempts/audit | Hệ thống nội bộ Laravel thật |
| Worker poll job, điền PPTX V2 theo shape ID | Mac mini / Tailscale thật |
| Download PPTX an toàn (allowlist thư mục) | JWT/RBAC, Postgres |
| MockAI chuẩn hóa **note** (optional; note không lên slide V2) | Codex CLI thật hoàn tất note |
| Idempotency-Key; `% VAT` → giá gồm VAT; mã `ABC-[]/QT/[yymm]-[seq]` | `[]` sau ABC (mã KH nội bộ) chưa map |

---

## 2. Kiến trúc & workflow

```text
React (Vite)  —mock Internal Management System—
      │ REST /api
      ▼
FastAPI + SQLite
  Validation · Quotation job · History/Attempts/Audit
      │ poll claim / complete / fail
      ▼
Automation Worker  —mock thiết bị thực thi / Mac mini—
  Optional MockAI (note only)
      ▼
  PPTX fill (shape id) + Validator
      ▼
  worker/output/{quotation_id}.pptx
      ▼
UI: status · Retry · Download (.pptx)
```

```text
PENDING → PROCESSING → COMPLETED
                    ↘ FAILED → (retry) → PENDING → …
```

---

## 3. Tech stack (thực tế trong repo)

| Lớp | Công nghệ |
|-----|-----------|
| Frontend | React, TypeScript, Vite, Tailwind CSS, React Router |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, **SQLite** |
| Worker | Python, httpx, **python-pptx**, python-docx (legacy) |
| AI (demo) | MockAI (rule-based); CodexRunner = boundary (stub) |
| Tests | pytest (backend, worker); `npm run build` |

Stack Laravel / Postgres trong [`docs/README.md`](docs/README.md) là **môi trường công ty sau này**, không phải stack của prototype này.

---

## 4. Cấu trúc thư mục

```text
frontend/                 # UI khách hàng + báo giá
backend/                  # API + SQLite
worker/
  ai/                     # MockAI + validate note
  codex/                  # Codex CLI boundary (stub)
  jobs/
    pptx_mapping.py       # Shape-id → dữ liệu (V2)
    pptx_template_service.py
    template_service.py   # DOCX legacy (không còn happy path)
    validator.py
  templates/
    01_Bao_Gia_An_Binh_Chemtech.V2.pptx   # template chính
    quotation_template.docx               # legacy
  output/                 # file sinh ra (.pptx)
docs/                     # đề bài, plan PPTX, demo, samples
.env.example
README.md
```

---

## 5. Cấu hình & chạy local

**Yêu cầu:** Python 3.11+, Node.js 20+.

```powershell
# Từ root repo
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

**Ba terminal (bắt buộc có Worker — nếu không job kẹt PENDING):**

```powershell
# 1) Backend
cd backend
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000

# 2) Worker
cd worker
.\.venv\Scripts\python.exe main.py

# 3) Frontend
cd frontend
npm run dev
```

| URL | Mục đích |
|-----|----------|
| http://localhost:5173 | UI demo |
| http://127.0.0.1:8000/docs | OpenAPI |
| http://127.0.0.1:8000/health | Health |

`.env.example` đã đủ cho local. **Không dùng Docker** trong prototype này (3 process đơn giản hơn cho bài đánh giá).

---

## 6. Demo: tạo báo giá → theo dõi → tải PPTX

1. Mở UI → tạo/chọn khách hàng **active**.
2. **Tạo báo giá** (tối đa **3** dòng SP — API trả **422** nếu nhiều hơn; worker vẫn fail-safe nếu >3).
3. Trang chi tiết poll `PENDING` → `PROCESSING` → `COMPLETED` / `FAILED`.
4. **Download (.pptx)** → file tải tên `BaoGia-{id}.pptx`.
5. (Tuỳ chọn) Khi `FAILED`: sửa (PENDING/FAILED) → **Retry**.
6. KH **inactive** → không tạo báo giá mới (UI + API 400).

Dữ liệu demo: dùng công ty giả (vd. `Cong Ty Demo An Binh`), không dùng KH/bí mật thật.

---

## 7. Chạy test

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -q

cd ..\worker
.\.venv\Scripts\python.exe -m pytest tests -q

cd ..\frontend
npm run build
```

---

## 8. Template PPTX & ánh xạ trường

- Nguồn: `docs/01_Bao_Gia_An_Binh_Chemtech.V2.pptx` (copy trong `worker/templates/`).
- File V2 **không có** tên shape `txt_*` (README công ty mô tả ideal); prototype map theo **shape ID** đã inventory.
- Chi tiết: [`docs/pptx-v2-integration-plan.md`](docs/pptx-v2-integration-plan.md).

| Shape ID | Nội dung điền |
|----------|----------------|
| 20 | `customer.company` |
| 28/32/36 | `product_name` (tối đa 3 dòng) |
| 29/33/37 | `unit_price` (chưa VAT) |
| 30/34/38 | `unit_price × (1 + vat_percent/100)` nếu có `% VAT`; không thì trống |
| 49/50/51 | Quy cách parse từ `specification`, mặc định `25` |
| 42 | Ngày/tháng từ `created_at`, giữ **năm 2026** |
| 46 | `ABC-[]/QT/[yymm]-[seq]` (`yymm` từ ngày tạo, `seq` từ đuôi `quotation.id`) |

Không đưa `payment_terms` / `delivery_terms` / `note` lên slide (giữ trong DB/UI).

---

## 9. Ví dụ đầu ra

- Mẫu sinh từ pipeline: [`docs/samples/QT-DEMO-SAMPLE.pptx`](docs/samples/QT-DEMO-SAMPLE.pptx)
- Template gốc: [`docs/01_Bao_Gia_An_Binh_Chemtech.V2.pptx`](docs/01_Bao_Gia_An_Binh_Chemtech.V2.pptx)
- Runtime: `worker/output/{quotation_id}.pptx`

---

## 10. Mock / chưa hoàn thành

| Thành phần | Trạng thái |
|------------|------------|
| Internal UI (React) | **Implemented** (mock Laravel IMS) |
| FastAPI + SQLite job API | **Implemented** |
| Worker fill PPTX V2 | **Implemented** |
| MockAI note | **Implemented** (note không lên slide) |
| Codex CLI | **Mock/stub** boundary |
| Laravel / Postgres / Tailscale / Mac mini | **Not integrated** — mô tả trong đề bài công ty |
| Mã `ABC-[]/QT/[yymm]-[seq]` | **Có** — điền shape 46; `[]` sau ABC để trống |
| VAT gồm thuế | **Có** — nhập `vat_percent` trên báo giá |
| JWT / RBAC | **Out of scope** |
| Auto-recovery job kẹt PROCESSING | **Chưa** |

---

## 11. Hạn chế & hướng tiếp theo

- Internal job API **không auth** (chỉ local demo).
- Worker chết giữa chừng → có thể kẹt `PROCESSING`.
- Cột giá gồm VAT: điền khi có `% VAT`; mã báo giá shape 46 theo `ABC-[]/QT/[yymm]-[seq]`.
- Production: deploy worker trên thiết bị thực thi (Tailscale), auth nội bộ, Postgres, rule VAT/mã, Codex thật nếu cần.

---

## 12. AI tools khi phát triển

Cursor (AI-assisted). Ứng viên chịu trách nhiệm giải thích kiến trúc và demo.
