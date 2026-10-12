# Kịch bản demo 3–5 phút

Dữ liệu giả — không dùng khách hàng / giá thật của công ty.

## Chuẩn bị (trước khi quay/trình bày)

Ba process đang chạy: backend `:8000`, worker, frontend `:5173` (xem `README.md`).

## Script

| Phút | Nội dung |
|------|----------|
| 0:00–0:40 | **Mục tiêu:** từ form nội bộ → agent điền mẫu PowerPoint V2 → file `.pptx`. **Kiến trúc:** React (mock IMS) → FastAPI/SQLite → Worker (mock thiết bị thực thi) → PPTX theo shape ID. Nêu rõ: **không** Laravel/Tailscale/Mac mini thật trong demo. |
| 0:40–1:10 | UI → tạo khách hàng demo (`Cong Ty Demo An Binh`) hoặc chọn KH active. |
| 1:10–2:00 | **Tạo báo giá:** 1–2 sản phẩm (≤3), đơn giá chưa VAT, quy cách `25 kg/bao`, gửi. Chỉ ra Idempotency-Key (không tạo trùng khi double-submit). |
| 2:00–2:40 | Trang chi tiết: `PENDING` → `PROCESSING` → `COMPLETED`. Mở log worker nếu cần (`pptx_filled`). |
| 2:40–3:20 | **Download (.pptx)** → mở file: tên KH, tên SP, giá chưa/gồm VAT, ngày; mã `ABC-[]/QT/[yymm]-[seq]`; header/điều khoản cố định còn. |
| 3:20–4:20 | *(Nếu còn giờ)* Tạo job fail (vd. >3 SP hoặc fail giả) → xem lỗi/attempts → sửa/retry → COMPLETED. |
| 4:20–5:00 | Tóm tắt: đã làm thật / mock / chưa (VAT, mã BG, Laravel). Trỏ `README.md` + `pptx-v2-integration-plan.md`. |

## Checklist nói rõ khi demo

- **Thật:** API, SQLite job state, worker fill PPTX, download allowlist, retry/history.
- **Mock:** UI thay Laravel; worker local thay Mac mini/Tailscale; MockAI (note không lên slide).
- **Chưa:** mã KH trong `ABC-[]`, auth JWT, Codex CLI thật.
