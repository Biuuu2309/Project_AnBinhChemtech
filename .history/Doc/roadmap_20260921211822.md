# Lộ trình triển khai — Quotation Automation Prototype

**Phiên bản hợp nhất** từ `roadmap.md` + `roadmap-quotation-automation.docx`.  
Tham chiếu: `Describle.txt`, `solution-plan-vi.md`.  
Phạm vi: prototype E2E trong ~2–4 giờ. Deadline: **25/09/2026**.

---

## Quyết định kỹ thuật (chốt trước khi code)

| Quyết định | Lựa chọn | Lý do |
|---|---|---|
| Folder automation | `worker/` (giữ repo hiện tại) | Không đổi tên giữa chừng |
| Cách Mac mini nhận job | **Worker poll** Backend | Giống hệ thống riêng; mock dễ; backend không phụ thuộc process worker |
| Tạo file báo giá | `python-docx` deterministic | Testable, tái lập |
| Codex CLI | Stub interface `worker/codex/codex_runner.py` | Không dùng trong happy path prototype |
| DB | SQLite | Đủ cho prototype |
| Auth | JWT tối thiểu **hoặc** ghi “mock” trong README | Không over-engineer |

### Luồng kỹ thuật chốt

```text
React → FastAPI (validate) → SQLite (PENDING)
                                    ↑ poll
                              Python Worker (Mock Mac mini)
                                    ↓
                         TemplateService → DOCX → Validator
                                    ↓
                         COMPLETED / FAILED (+ download)
```

```text
AutomationService (interface)
  ├── MockWorkerPoll          ← Prototype (worker process)
  └── MacMiniAgent            ← Production (thay sau)
```

---

## Tổng quan phase

```text
Phase 0  Foundation + Plan          ✅ Done
Phase 1  Setup chạy được            Must   (~15–20’)
Phase 2  DB + Backend API + state   Must   (~40–50’)
Phase 3  Template + DOCX + Worker   Must   (~45–60’)
Phase 4  Frontend E2E               Must   (~40–50’)
Phase 5  Error / Retry / Logging    Should (~20–25’)
Phase 6  README + Demo + Nộp        Must   (~20–30’)
```

| Phase | Mục tiêu | Ước lượng | Ưu tiên |
|-------|----------|-----------|---------|
| 0 | Plan + cấu trúc repo | — | ✅ Done |
| 1 | FE/BE/Worker chạy skeleton | 15–20’ | **Must** |
| 2 | Models, seed, API, job status | 40–50’ | **Must** |
| 3 | DOCX template + worker poll | 45–60’ | **Must** |
| 4 | Customer → Form → Status → Download | 40–50’ | **Must** |
| 5 | Retry, anti-dup, validation edge, logs | 20–25’ | Should |
| 6 | README, sample file, demo | 20–30’ | **Must** |

> **Must** = cần để demo đạt yêu cầu bài.  
> **Should** = làm nếu còn giờ; không kịp thì mô tả hướng xử lý trong README.

---

## Phase 0 — Foundation *(Done)*

- [x] Cấu trúc `frontend/`, `backend/`, `worker/`
- [x] Solution Plan + sơ đồ
- [x] `.env.example`, requirements skeleton
- [x] Roadmap hợp nhất (file này)

---

## Phase 1 — Setup chạy được *(Must)*

**Mục tiêu:** 3 process chạy local trước khi viết nghiệp vụ.

1. Backend: venv + `pip install -r requirements.txt` + `uvicorn app.main:app --reload` → `/health` OK, Swagger mở được
2. Frontend: Tailwind (theo TechStack) + `npm run dev`
3. Worker: `pip install -r requirements.txt` + `python main.py` in được “ready”
4. Copy `.env.example` → `.env`

**Done when:** mở được Swagger + Vite + worker process (dù chưa có job thật).

---

## Phase 2 — Database + Backend API + Job state *(Must)*

**Mục tiêu:** Backend là **source of truth** cho quotation và status.

### Models / seed
- `Customer`, `Quotation`, `QuotationItem`
- Status: `PENDING` → `PROCESSING` → `COMPLETED` | `FAILED`  
  (`DRAFT` chỉ trên FE form, không bắt buộc persist)
- Seed 1–2 khách hàng giả

### API công khai
| Method | Path | Việc |
|--------|------|------|
| GET | `/api/customers` | Danh sách |
| GET | `/api/customers/{id}` | Chi tiết |
| POST | `/api/quotations` | Tạo job → `PENDING` |
| GET | `/api/quotations/{id}` | Status + metadata |
| GET | `/api/quotations/{id}/download` | Tải file (sau Phase 3) |
| POST | `/api/quotations/{id}/retry` | Stub → hoàn thiện Phase 5 |

### API nội bộ (worker poll)
| Method | Path | Việc |
|--------|------|------|
| GET | `/api/internal/jobs/next` | Claim 1 job `PENDING` → `PROCESSING` |
| POST | `/api/internal/jobs/{id}/complete` | Lưu `output_path` → `COMPLETED` |
| POST | `/api/internal/jobs/{id}/fail` | `FAILED` + `error_message` |

### Validation (Pydantic, làm ngay ở đây)
- `items` không rỗng, `quantity > 0`, `unit_price >= 0`, required fields

**Done when:** Swagger tạo quotation `PENDING`, GET status đúng.

---

## Phase 3 — Template DOCX + Worker *(Must)*

**Mục tiêu:** Chứng minh automation tạo file từ mẫu (deterministic).

1. `worker/templates/quotation_template.docx`  
   Placeholder: `quotation_number`, `customer_name`, `product_*`, `quantity`, `unit_price`, `payment_terms`, `delivery_terms`, …
2. `worker/jobs/template_service.py` — load → map → save
3. `worker/jobs/validator.py` — tồn tại, size > 0, mở được DOCX
4. Worker loop: poll `/jobs/next` → generate → validate → complete/fail
5. `worker/codex/codex_runner.py` — stub + docstring: *không gọi trong happy path*
6. Output: `worker/output/QT-….docx`; Backend lưu path cho download

**Done when:** POST quotation + chạy worker → có file DOCX tải được qua API.

---

## Phase 4 — Frontend E2E *(Must)*

**Mục tiêu:** Demo đúng workflow nghiệp vụ (UI đơn giản).

1. Customer List / Customer Detail + nút **Tạo báo giá**
2. Quotation Form (SP, quy cách, SL, đơn giá, TT, giao hàng, ghi chú)
3. Submit → poll status (`PENDING` / `PROCESSING` / `COMPLETED` / `FAILED`)
4. `COMPLETED` → nút **Tải báo giá**
5. Axios (hoặc fetch) + React Router nếu cần

**Done when:** trên browser: xem KH → form → gửi → nhận file.

---

## Phase 5 — Reliability *(Should)*

Làm theo thứ tự nếu còn thời gian:

1. Retry: chỉ khi `FAILED` → về `PENDING` (không tạo job mới)
2. Anti-duplicate: cùng customer đang `PENDING`/`PROCESSING` → trả quotation hiện có
3. Logging: `quotation_created`, `automation_started`, `completed`, `failed` (+ id, timestamp, error)
4. Auth tối thiểu (JWT 1 user seed) **hoặc** ghi rõ mock trong README
5. Test nhanh: invalid input (400), worker exception → `FAILED`, missing output → `FAILED`

**Done when:** retry + 400 validation chạy; phần chưa làm ghi trong README.

---

## Phase 6 — README + Demo + Nộp *(Must)*

Theo mục 6 Describle:

| Hạng mục | Nội dung |
|----------|----------|
| Solution Plan | `solution-plan-vi.md` (+ EN nếu cần) |
| Source | Repo chạy được |
| README | Setup 3 process; Completed / Mocked / Unimplemented; Assumptions; AI tools; Production next |
| Demo | Video 3–5’ **hoặc** hướng dẫn local |
| Sample | ≥ 1 file `.docx` sinh từ prototype |

**Demo script:** Customer → Tạo báo giá → Form → Submit → Status → Download.

---

## Lịch gợi ý 4 giờ

| Thời gian | Việc |
|-----------|------|
| 0:00–0:20 | Phase 1 — setup chạy được |
| 0:20–1:10 | Phase 2 — DB + API + status |
| 1:10–2:10 | Phase 3 — template + worker DOCX |
| 2:10–3:00 | Phase 4 — Frontend E2E |
| 3:00–3:25 | Phase 5 — retry / lỗi / log (nếu còn giờ) |
| 3:25–4:00 | Phase 6 — README + sample + demo |

---

## Nếu thiếu thời gian — cắt theo thứ tự

```text
1. Giữ Phase 2+3+download     → chứng minh tạo file
2. Phase 4 tối thiểu          → chứng minh UX workflow
3. Phase 6 README + sample    → nộp được
4. Phase 5 retry/anti-dup     → điểm cộng
5. JWT đầy đủ / PDF / Docker / Mac mini thật / Codex thật  → bỏ, chỉ mô tả
```

**Không làm trong prototype:** CRM đầy đủ, PostgreSQL, Redis queue, RBAC phức tạp.

---

## Ranh giới AI / Codex CLI

```text
Không bắt đầu bằng Codex.
Xây pipeline deterministic trước.
Codex chỉ sau interface rõ ràng (codex_runner.py).
Template mapping + validation + state machine = code thường.
```

---

## Checklist Definition of Done (toàn dự án)

- [ ] Mở chi tiết khách hàng giả lập
- [ ] Tạo báo giá qua form và gửi
- [ ] Theo dõi được `PENDING` / `PROCESSING` / `COMPLETED` / `FAILED`
- [ ] Worker (mock Mac mini) tạo DOCX từ template
- [ ] Download file hoàn chỉnh
- [ ] README nêu rõ phần mock (Mac mini / Codex)
- [ ] Giải thích được: gửi data, nhận job (poll), chạy task, lưu kết quả, status

---

## Cấu trúc repo mục tiêu (khớp hiện tại)

```text
Project_AnBinhChemtech/
├── frontend/src/{pages,components,api,types,hooks}/
├── backend/app/{api,models,schemas,services,core}/
├── worker/{jobs,templates,output,codex}/
├── doc/{Describle,TechStack,solution-plan*,roadmap.md}
├── .env.example
└── README.md
```

---

## Bước tiếp theo

**Bắt đầu Phase 1** (setup: venv backend, Tailwind frontend, worker chạy skeleton), rồi vào Phase 2 API.
