# Kế hoạch giải pháp — Hệ thống tự động tạo báo giá

## 1. Mục tiêu

Xây dựng một prototype cho phép nhân viên tạo báo giá từ thông tin khách hàng và sản phẩm thông qua Hệ thống Quản lý Nội bộ.

Các mục tiêu chính:

- Giảm thao tác thủ công khi tạo báo giá.
- Chuẩn hóa quy trình tạo báo giá.
- Tách biệt business logic khỏi quá trình tạo tài liệu và automation.
- Theo dõi trạng thái xử lý của báo giá.
- Xử lý các lỗi phổ biến và hỗ trợ retry.
- Kiểm tra dữ liệu trước khi gửi sang tầng automation.

Prototype tập trung vào luồng end-to-end chính và không nhằm xây dựng một hệ thống CRM hoặc hệ thống enterprise production hoàn chỉnh.

---

## 2. Kiến trúc hệ thống

```text
┌───────────────────────────────────────────────────────────┐
│                 Hệ thống Quản lý Nội bộ                  │
│                                                           │
│  React + TypeScript                                       │
│                                                           │
│  Thông tin khách hàng                                     │
│        │                                                  │
│        ▼                                                  │
│  Tạo báo giá                                              │
│        │                                                  │
│        ▼                                                  │
│  Form báo giá                                             │
└──────────────────────┬────────────────────────────────────┘
                       │
                       │ REST API
                       ▼
┌───────────────────────────────────────────────────────────┐
│                     Backend API                           │
│                                                           │
│  FastAPI + Python                                         │
│                                                           │
│  ┌────────────────┐    ┌───────────────────────────────┐ │
│  │ Validation     │    │ Quotation Service             │ │
│  │                │    │                               │ │
│  │ Dữ liệu đầu vào│    │ Tạo báo giá                   │ │
│  │ Quy tắc nghiệp │    │ Cập nhật trạng thái / Retry   │ │
│  │ vụ             │    │                               │ │
│  └────────────────┘    └───────────────┬───────────────┘ │
│                                        │                 │
│                                        ▼                 │
│                              ┌────────────────┐           │
│                              │ SQLite         │           │
│                              │                │           │
│                              │ Customer       │           │
│                              │ Quotation      │           │
│                              │ Quotation Item │           │
│                              └────────────────┘           │
└──────────────────────┬────────────────────────────────────┘
                       │
                       │ Automation Request
                       ▼
┌───────────────────────────────────────────────────────────┐
│                 Tầng Automation / Mac mini                │
│                                                           │
│  Python Worker                                            │
│                                                           │
│  ┌──────────────────┐                                    │
│  │ Template Service │                                    │
│  │ Điền dữ liệu DOCX│                                    │
│  └────────┬─────────┘                                    │
│           │                                               │
│           ▼                                               │
│  ┌──────────────────┐    ┌────────────────────────────┐  │
│  │ Codex CLI        │    │ Output Validator           │  │
│  │                  │    │                            │  │
│  │ AI hỗ trợ xử lý  │    │ Kiểm tra file được tạo     │  │
│  │ khi thực sự cần  │    │ có tồn tại / hợp lệ        │  │
│  └──────────────────┘    └────────────────────────────┘  │
│                                                           │
│              Template báo giá (.docx)                     │
│                         │                                 │
│                         ▼                                 │
│                 File báo giá hoàn chỉnh                   │
└───────────────────────────────────────────────────────────┘
```

### Các thành phần

| Thành phần | Trách nhiệm |
|---|---|
| React Frontend | Thông tin khách hàng, form báo giá, gửi request, hiển thị trạng thái job |
| FastAPI Backend | API, validation, business logic, vòng đời job |
| SQLite | Lưu dữ liệu báo giá và trạng thái xử lý |
| Automation Worker | Nhận job và tạo file báo giá |
| Template Service | Điền dữ liệu vào template theo cách deterministic |
| Codex CLI | Hỗ trợ AI tại những bước thực sự phù hợp |
| Output Validator | Kiểm tra file đầu ra trước khi đánh dấu hoàn thành |

---

## 3. Luồng dữ liệu

Luồng chính:

```text
1. Thông tin khách hàng
        │
        ▼
2. Nhân viên chọn "Tạo báo giá"
        │
        ▼
3. Form báo giá
        │
        │ Sản phẩm
        │ Quy cách
        │ Số lượng
        │ Đơn giá
        │ Điều khoản thanh toán
        │ Điều khoản giao hàng
        │ Nội dung liên quan
        ▼
4. POST /api/quotations
        │
        ▼
5. Backend Validation
        │
        ├── Không hợp lệ → 400 / lỗi validation
        │
        ▼
6. Tạo quotation
   status = PENDING
        │
        ▼
7. Gửi Automation Job
        │
        ▼
8. Mac mini / Mock Worker
   status = PROCESSING
        │
        ▼
9. Tạo file báo giá
        │
        ├── Load template
        ├── Điền thông tin khách hàng
        ├── Điền thông tin sản phẩm
        ├── Điền giá
        └── Điền các điều khoản
        │
        ▼
10. Kiểm tra file đầu ra
        │
        ├── Không hợp lệ / thiếu file → FAILED
        │
        ▼
11. Lưu file đầu ra
        │
        ▼
12. status = COMPLETED
        │
        ▼
13. Frontend hiển thị
    "Tạo báo giá thành công"
        │
        ▼
14. Nhân viên tải file báo giá
```

---

## 4. Thiết kế API

### Tạo báo giá

```http
POST /api/quotations
```

Ví dụ request:

```json
{
  "customer_id": "CUS-001",
  "items": [
    {
      "product_name": "Chemical Product A",
      "specification": "99.5%",
      "quantity": 100,
      "unit_price": 250000
    }
  ],
  "payment_terms": "30 days",
  "delivery_terms": "Within 7 days",
  "note": "Sample quotation"
}
```

Ví dụ response:

```json
{
  "quotation_id": "QT-2026-001",
  "status": "PENDING"
}
```

### Lấy trạng thái báo giá

```http
GET /api/quotations/{quotation_id}
```

Ví dụ:

```json
{
  "quotation_id": "QT-2026-001",
  "status": "PROCESSING"
}
```

### Retry báo giá thất bại

```http
POST /api/quotations/{quotation_id}/retry
```

### Tải file báo giá

```http
GET /api/quotations/{quotation_id}/download
```

---

## 5. Quản lý trạng thái Job

Backend là nguồn thông tin chính (source of truth) cho trạng thái của quotation job.

```text
DRAFT
  │
  ▼
PENDING
  │
  ▼
PROCESSING
  │
  ├──────────────► COMPLETED
  │
  └──────────────► FAILED
                       │
                       │ Retry
                       ▼
                   PROCESSING
```

### Ý nghĩa các trạng thái

| Trạng thái | Ý nghĩa |
|---|---|
| `DRAFT` | Nhân viên đang nhập hoặc chỉnh sửa dữ liệu báo giá |
| `PENDING` | Request đã được tạo và đang chờ automation xử lý |
| `PROCESSING` | Automation Worker đang xử lý báo giá |
| `COMPLETED` | File đã được tạo và kiểm tra thành công |
| `FAILED` | Quá trình xử lý thất bại |

Frontend đọc trạng thái từ Backend thay vì tự suy đoán trạng thái của job.

---

## 6. Automation và Codex CLI

Hệ thống tách biệt phần xử lý deterministic khỏi phần có AI hỗ trợ.

### Các tác vụ deterministic

Các tác vụ sau nên được xử lý bằng code thông thường vì chúng có cấu trúc rõ ràng, có thể kiểm thử và tái lập:

```text
Kiểm tra dữ liệu đầu vào
      ↓
Load template báo giá
      ↓
Mapping các trường dữ liệu
      ↓
Điền thông tin khách hàng / sản phẩm / giá
      ↓
Tạo file DOCX
      ↓
Kiểm tra file đầu ra
```

### Codex CLI

Codex CLI được cô lập phía sau một integration boundary riêng, ví dụ:

```text
automation/codex_runner.py
```

Codex CLI chỉ được gọi đối với những tác vụ mà AI/CLI automation thực sự phù hợp.

Hệ thống không giao toàn bộ quy trình tạo báo giá cho LLM.

---

## 7. Xử lý lỗi và Retry

### Dữ liệu đầu vào không hợp lệ

```text
Frontend
   ↓
Backend validation
   ↓
400 Bad Request
```

Không tạo automation job nếu request không hợp lệ.

### Mac mini không khả dụng

```text
Backend
   ↓
Automation request
   ↓
Kết nối thất bại
   ↓
FAILED
   ↓
Retry
```

### Lỗi khi tạo file

```text
Worker
  ↓
Tạo file
  ↓
Exception
  ↓
FAILED
```

### File đầu ra thiếu hoặc không hợp lệ

```text
Worker
  ↓
Tạo file
  ↓
Kiểm tra output
  ↓
File thiếu / không hợp lệ
  ↓
FAILED
```

### Request trùng lặp

Backend cần tránh tạo nhiều job cho cùng một lần submit. Trong production có thể sử dụng `idempotency key` hoặc request identifier.

Trong prototype, nếu quotation đang ở trạng thái `PENDING` hoặc `PROCESSING`, hệ thống có thể trả về quotation hiện tại thay vì tạo job trùng lặp.

---

## 8. Ranh giới Automation và Mac mini

Nếu không có Mac mini thật trong quá trình phát triển, prototype sử dụng:

```text
MockAutomationService
```

thay cho:

```text
MacMiniAutomationService
```

Kiến trúc:

```text
Backend
   │
   ▼
AutomationService
   │
   ├── MockAutomationService       ← Prototype
   │
   └── MacMiniAutomationService    ← Production
```

Backend không phụ thuộc trực tiếp vào implementation cụ thể.

Cách này cho phép prototype chạy hoàn toàn trên máy local nhưng vẫn giữ rõ integration boundary để triển khai Mac mini thật sau này.

---

## 9. Bảo mật

Ở mức prototype, hệ thống bao gồm:

- Validation request.
- Authentication/authorization ở mức phù hợp.
- Logging các sự kiện xử lý quan trọng.
- Không hard-code credentials hoặc API keys.
- Configuration và secret được lưu qua environment variables.
- Kiểm soát quyền truy cập file báo giá.

Ví dụ:

```text
Frontend
    │
    │ HTTPS / API
    ▼
Backend
    │
    ├── Input validation
    ├── Authentication
    ├── Authorization
    └── Logging
```

Khi triển khai production có thể mở rộng với JWT/OAuth2, RBAC, audit log, encrypted storage, secret management, HTTPS và cơ chế kiểm soát quyền truy cập file chặt chẽ hơn.

---

## 10. Lựa chọn công nghệ

| Tầng | Công nghệ | Lý do |
|---|---|---|
| Frontend | React + TypeScript + Vite | Phát triển nhanh, cấu trúc rõ ràng |
| UI | Tailwind CSS | Xây dựng giao diện nhanh |
| HTTP | Axios | Giao tiếp với API |
| Backend | Python + FastAPI | REST API nhẹ, dễ tích hợp |
| Validation | Pydantic | Validation request có cấu trúc |
| Database | SQLite | Đủ cho prototype |
| Automation | Python Worker | Dễ tích hợp xử lý file |
| Template | DOCX | Phù hợp để tạo tài liệu báo giá |
| AI/CLI | Codex CLI | Hỗ trợ AI và CLI được cô lập |
| Logging | Python logging | Đủ cho mức observability của prototype |

Kiến trúc cố ý không sử dụng quá nhiều infrastructure vì mục tiêu của bài đánh giá là một giải pháp đơn giản, có thể chạy, dễ hiểu và phù hợp phạm vi.

---

## 11. Prototype và Production

### Prototype

```text
React
   ↓
FastAPI
   ↓
SQLite
   ↓
Mock Automation Worker
   ↓
DOCX Template
   ↓
File báo giá
```

### Định hướng Production

```text
React
   ↓
Backend API
   ↓
PostgreSQL
   ↓
Job Queue
   ↓
Automation Worker
   ↓
Mac mini Agent
   ↓
Template / Codex CLI
   ↓
Object Storage
   ↓
File báo giá
```

Các cải tiến có thể bổ sung khi triển khai production:

- PostgreSQL
- Redis hoặc persistent job queue
- Retry với backoff
- Idempotency
- Object storage
- RBAC
- Audit logging
- Monitoring và alerting
- Health check / Mac mini heartbeat
- Backup và recovery

Các thành phần trên được giữ ngoài phạm vi prototype trừ khi cần thiết để chứng minh main workflow.

---

## 12. Nguyên tắc thiết kế chính

> **Giữ business logic ở dạng deterministic, cô lập automation và AI phía sau các interface rõ ràng, đồng thời sử dụng trạng thái job làm nguồn thông tin chính cho toàn bộ quy trình tạo báo giá.**

Tóm lại:

> **Tách business logic khỏi automation/AI, ưu tiên xử lý deterministic cho các tác vụ có cấu trúc và sử dụng trạng thái job làm nguồn thông tin chính để theo dõi toàn bộ quy trình tạo báo giá.**
