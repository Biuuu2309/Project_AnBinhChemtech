# Solution Plan — Quotation Automation System

## 1. Objective

Build a prototype that allows an employee to create a quotation from customer and product information through the Internal Management System.

The main objectives are:

- Reduce manual work when creating quotations.
- Standardize the quotation generation workflow.
- Separate business logic from document generation and automation.
- Track quotation processing status.
- Handle common failures and support retry.
- Validate data before sending it to the automation layer.

The prototype focuses on the main end-to-end workflow and does not attempt to implement a full CRM or production-grade enterprise system.

---

## 2. System Architecture

```text
┌───────────────────────────────────────────────────────────┐
│                Internal Management System                 │
│                                                           │
│  React + TypeScript                                       │
│                                                           │
│  Customer Detail                                          │
│        │                                                  │
│        ▼                                                  │
│  Create Quotation                                         │
│        │                                                  │
│        ▼                                                  │
│  Quotation Form                                           │
└──────────────────────┬────────────────────────────────────┘
                       │
                       │ REST API
                       ▼
┌───────────────────────────────────────────────────────────┐
│                    Backend API                            │
│                                                           │
│  FastAPI + Python                                         │
│                                                           │
│  ┌────────────────┐    ┌───────────────────────────────┐ │
│  │ Validation     │    │ Quotation Service             │ │
│  │                │    │                               │ │
│  │ Input /        │    │ Create quotation              │ │
│  │ Business rules │    │ Update status / Retry         │ │
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
│              Automation Layer / Mac mini                  │
│                                                           │
│  Python Worker                                            │
│                                                           │
│  ┌──────────────────┐                                    │
│  │ Template Service │                                    │
│  │ Fill DOCX        │                                    │
│  └────────┬─────────┘                                    │
│           │                                               │
│           ▼                                               │
│  ┌──────────────────┐    ┌────────────────────────────┐  │
│  │ Codex CLI        │    │ Output Validator           │  │
│  │                  │    │                            │  │
│  │ AI-assisted      │    │ Check generated file       │  │
│  │ processing only  │    │ exists / is valid          │  │
│  │ when necessary   │    │                            │  │
│  └──────────────────┘    └────────────────────────────┘  │
│                                                           │
│              Quotation Template (.docx)                   │
│                         │                                 │
│                         ▼                                 │
│                 Generated Quotation                       │
└───────────────────────────────────────────────────────────┘
```

### Components

| Component | Responsibility |
|---|---|
| React Frontend | Customer detail, quotation form, submission, job status |
| FastAPI Backend | API, validation, business logic, job lifecycle |
| SQLite | Store quotation data and processing status |
| Automation Worker | Receive job and generate quotation file |
| Template Service | Fill quotation template deterministically |
| Codex CLI | AI-assisted processing only where appropriate |
| Output Validator | Verify the generated file before completion |

---

## 3. Data Flow

The main workflow is:

```text
1. Customer Detail
        │
        ▼
2. User clicks "Tạo báo giá"
        │
        ▼
3. Quotation Form
        │
        │ Product
        │ Specification
        │ Quantity
        │ Unit Price
        │ Payment Terms
        │ Delivery Terms
        │ Related Content
        ▼
4. POST /api/quotations
        │
        ▼
5. Backend Validation
        │
        ├── Invalid → 400 / validation error
        │
        ▼
6. Create Quotation
   status = PENDING
        │
        ▼
7. Send Automation Job
        │
        ▼
8. Mac mini / Mock Worker
   status = PROCESSING
        │
        ▼
9. Generate quotation
        │
        ├── Load template
        ├── Fill customer information
        ├── Fill product information
        ├── Fill pricing
        └── Fill terms
        │
        ▼
10. Validate generated file
        │
        ├── Invalid / missing → FAILED
        │
        ▼
11. Store output file
        │
        ▼
12. status = COMPLETED
        │
        ▼
13. Frontend displays
    "Quotation completed"
        │
        ▼
14. User downloads quotation
```

---

## 4. API Design

### Create quotation

```http
POST /api/quotations
```

Example request:

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

Example response:

```json
{
  "quotation_id": "QT-2026-001",
  "status": "PENDING"
}
```

### Get quotation status

```http
GET /api/quotations/{quotation_id}
```

Example:

```json
{
  "quotation_id": "QT-2026-001",
  "status": "PROCESSING"
}
```

### Retry failed quotation

```http
POST /api/quotations/{quotation_id}/retry
```

### Download quotation

```http
GET /api/quotations/{quotation_id}/download
```

---

## 5. Job State Management

The Backend is the source of truth for the quotation job state.

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

### State definitions

| State | Meaning |
|---|---|
| `DRAFT` | User is entering or editing quotation data |
| `PENDING` | Request has been created and is waiting for automation |
| `PROCESSING` | Automation worker is processing the quotation |
| `COMPLETED` | File has been generated and validated successfully |
| `FAILED` | Processing failed |

The frontend reads the status from the Backend instead of determining the job state by itself.

---

## 6. Automation and Codex CLI

The system separates deterministic processing from AI-assisted processing.

### Deterministic tasks

The following tasks should normally be handled by regular code because they are structured, testable, and reproducible:

```text
Validate input
      ↓
Load quotation template
      ↓
Map quotation fields
      ↓
Fill customer/product/price data
      ↓
Generate DOCX
      ↓
Validate output
```

### Codex CLI

Codex CLI is isolated behind a dedicated integration boundary such as:

```text
automation/codex_runner.py
```

It is invoked only for tasks where AI/CLI automation is actually appropriate.

The system does not make the LLM responsible for the entire quotation-generation workflow.

---

## 7. Error Handling and Retry

### Invalid input

```text
Frontend
   ↓
Backend validation
   ↓
400 Bad Request
```

No automation job is created when the request is invalid.

### Mac mini unavailable

```text
Backend
   ↓
Automation request
   ↓
Connection failed
   ↓
FAILED
   ↓
Retry
```

### File generation failure

```text
Worker
  ↓
Generate file
  ↓
Exception
  ↓
FAILED
```

### Missing or invalid output

```text
Worker
  ↓
Generate file
  ↓
Output validation
  ↓
File missing / invalid
  ↓
FAILED
```

### Duplicate request

The Backend should avoid creating multiple jobs for the same submission. A production implementation can use an idempotency key or request identifier.

For the prototype, an existing `PENDING` or `PROCESSING` quotation can be returned instead of creating a duplicate job.

---

## 8. Automation Boundary and Mac mini

If a real Mac mini is not available during development, the prototype uses a `MockAutomationService`.

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

The Backend does not depend on the concrete implementation.

This allows the prototype to run locally while keeping a clear integration boundary for the real Mac mini deployment.

---

## 9. Security

Prototype-level security includes:

- Request validation.
- Authentication/authorization boundary.
- Logging of important processing events.
- No hard-coded credentials or API keys.
- Configuration and secrets stored in environment variables.
- Controlled access to generated quotation files.

Example:

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

For production, the system can be extended with JWT/OAuth2, RBAC, audit logs, encrypted storage, secret management, HTTPS, and stronger file access control.

---

## 10. Technology Choice

| Layer | Technology | Reason |
|---|---|---|
| Frontend | React + TypeScript + Vite | Fast development and clear structure |
| UI | Tailwind CSS | Simple and fast UI implementation |
| HTTP | Axios | API communication |
| Backend | Python + FastAPI | Lightweight REST API and easy integration |
| Validation | Pydantic | Structured request validation |
| Database | SQLite | Sufficient for the prototype |
| Automation | Python Worker | Simple file-processing integration |
| Template | DOCX | Suitable for quotation document generation |
| AI/CLI | Codex CLI | Isolated AI-assisted processing |
| Logging | Python logging | Sufficient observability for prototype |

The architecture intentionally avoids unnecessary infrastructure because the assessment values a simple, runnable, understandable, and appropriately scoped solution.

---

## 11. Prototype vs Production

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
Generated Quotation
```

### Production direction

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
Quotation
```

Potential production improvements:

- PostgreSQL
- Redis or another persistent job queue
- Retry with backoff
- Idempotency
- Object storage
- RBAC
- Audit logging
- Monitoring and alerting
- Health checks / Mac mini heartbeat
- Backup and recovery

These components are intentionally outside the prototype scope unless required to demonstrate the main workflow.

---

## 12. Main Design Principle

> **Keep business logic deterministic, isolate automation and AI behind clear interfaces, and make job status the source of truth for the quotation workflow.**

In short:

> **Tách business logic khỏi automation/AI, ưu tiên xử lý deterministic cho các tác vụ có cấu trúc và sử dụng trạng thái job làm nguồn thông tin chính để theo dõi toàn bộ quy trình tạo báo giá.**
