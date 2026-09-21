# An Binh Chemtech — Quote Automation Prototype

Prototype quy trình tạo báo giá: Web nội bộ → API → Mock Mac Mini worker → file báo giá từ template.

## Cấu trúc

```
frontend/   React + TypeScript + Vite + Tailwind
backend/    FastAPI + SQLAlchemy + SQLite
worker/     Mock Mac Mini (python-docx, Codex CLI interface)
Doc/        Mô tả bài toán & tech stack
```

## Setup nhanh (sẽ bổ sung sau khi implement)

```bash
# Backend
cd backend && python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Worker
cd worker && pip install -r requirements.txt && python main.py
```

Copy `.env.example` → `.env` trước khi chạy.
