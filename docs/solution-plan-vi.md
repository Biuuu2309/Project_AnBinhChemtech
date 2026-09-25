# Kế hoạch giải pháp — Tự động tạo báo giá (As Built)

Tài liệu mô tả **prototype đã triển khai**, không liệt kê ý tưởng tương lai như đã hoàn thành.  
Bản tiếng Anh: [`solution-plan.md`](solution-plan.md).  
Chạy demo: [`../README.md`](../README.md). Brief đề bài: [`Describle.txt`](Describle.txt).

---

## 1. Vấn đề

An Bình Chemtech cần giảm thao tác thủ công khi lập báo giá:

- Form trên trang chi tiết khách hàng
- Đẩy dữ liệu đã validate sang agent tự động hóa (Mac mini)
- Xuất DOCX theo mẫu công ty
- Theo dõi trạng thái, lỗi, retry
- AI không được tự bịa số lượng / đơn giá / điều khoản thương mại

Bài đánh giá yêu cầu **prototype demo được**, không phải CRM production.

---

## 2. Kiến trúc (đã implement)

Ba process, mỗi process một trách nhiệm:

| Thành phần | Vai trò trong prototype |
|------------|-------------------------|
| **Hệ thống quản lý nội bộ** | React SPA: khách hàng, form báo giá, status |
| **Backend API** | FastAPI: validate, lưu job, trạng thái, download |
| **Automation Worker** | Process Python local **thay cho agent trên Mac mini** |

```text
Internal Management (React)
        │ REST
        ▼
Backend API (FastAPI + SQLite)
        │ claim / complete / fail
        ▼
Automation Worker (Mock Mac mini)
  · AI/Codex (optional, chỉ note)
  · Template Service → Validator → DOCX
```

API là nguồn sự thật cho trạng thái nghiệp vụ; tạo file và AI chạy ngoài hot path của HTTP request.

---

## 3. Luồng dữ liệu

```text
UI → POST /api/quotations (+ Idempotency-Key)
   → Quotation Job (PENDING)
   → Worker poll GET /api/internal/jobs/next (PROCESSING)
   → AI/Codex (optional, note)
   → Template Service → Validator → DOCX
   → POST complete | fail
   → Status / History / Attempts / Download
```

Entity SQLite: `Customer`, `Quotation` + `QuotationItem`, `QuotationEvent`, `ProcessingAttempt`, `AuditLog`.

---

## 4. Tích hợp Mac mini

| Môi trường | Chạy gì |
|------------|---------|
| **Prototype này** | `worker/main.py` cùng máy với API — **Mock Mac mini** |
| **Production** | Cùng package `worker/` trên Mac mini, poll Backend |

Backend **không** nhúng Codex hay python-docx. Chỉ expose internal job API.

Cut-over production: deploy worker → `BACKEND_URL` → `USE_CODEX_CLI=true` + hoàn thiện `codex exec` → giữ TemplateService deterministic.

---

## 5. Automation workflow

1. Tạo báo giá → `PENDING` (+ history, audit)
2. Worker claim → `PROCESSING` (+ attempt)
3. (Optional) chuẩn hóa note bằng AI
4. Fill template + validate file
5. `complete` → `COMPLETED` hoặc `fail` → `FAILED`
6. UI Retry: `FAILED` → `PENDING`

---

## 6. AI vs xử lý deterministic

**Luôn deterministic:** validate schema, idempotency/anti-dup, state machine, mapping qty/giá/điều khoản, fill DOCX, validator, allowlist download.

**AI (optional, chỉ note):**

| Mode | Khi nào | Hành vi |
|------|---------|---------|
| **MockAI** | `USE_CODEX_CLI=false` (mặc định) | Rule-based — **không gọi LLM** |
| **CodexRunner** | `USE_CODEX_CLI=true` | Boundary Codex CLI trên Mac mini; prototype stub → fallback |

Guard: `apply_note_only`, `assert_protected_fields_unchanged`, validate kết quả note.

Demo: note đã chuẩn hóa nằm trong **DOCX**; API/UI giữ note gốc người dùng nhập.

---

## 7. Quản lý trạng thái

```text
PENDING → PROCESSING → COMPLETED
                    ↘ FAILED → (retry) → PENDING → …
```

| Status | UI | Hành động |
|--------|-----|-----------|
| PENDING | Poll | Sửa form; chờ worker |
| PROCESSING | Poll | Không sửa / không retry |
| COMPLETED | Dừng poll | Download |
| FAILED | Dừng poll | Sửa; Retry |

---

## 8. Lỗi / retry

| Tình huống | Xử lý |
|------------|--------|
| Payload sai | 422 |
| KH inactive | 400 + UI block |
| Lỗi template/validate | FAILED + message |
| AI/Codex lỗi | Fallback note gốc (trừ `AI_FAIL_JOB_ON_ERROR=true`) |
| Retry | FAILED → PENDING |
| Trùng submit | Cùng Idempotency-Key → 200 + bản cũ; anti-dup PENDING/PROCESSING theo customer |

**Chưa có:** tự phục hồi job kẹt `PROCESSING` khi worker chết giữa chừng.

---

## 9. Bảo mật (mức prototype)

Có: validate input, allowlist path download/`complete`, soft-deactivate KH, AI không sửa field thương mại.

Không có (ngoài scope): JWT/RBAC, auth cho `/api/internal/jobs/*`.

---

## 10. Prototype vs production

| Chủ đề | Prototype | Production |
|--------|-----------|------------|
| Host automation | `worker/` local | Mac mini |
| AI note | **MockAI** | Codex CLI qua CodexRunner |
| DB | SQLite | Postgres (điển hình) |
| Job | HTTP poll | Poll/queue + lease |
| Auth | Không | JWT/RBAC + service auth |
| File | `worker/output` | Object storage + signed URL |

---

## 11. Cố ý không claim là đã làm

- Codex CLI thật hoàn tất normalize note
- Deploy Mac mini vật lý
- JWT, multi-tenant, dashboard CRM
- Lease recovery cho PROCESSING

Chi tiết sơ đồ: [`architecture-diagrams.md`](architecture-diagrams.md).
