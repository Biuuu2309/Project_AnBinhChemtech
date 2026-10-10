# Tech stack (as built)

Stack **thực tế trong prototype**. Mục Laravel/Postgres trong đề bài công ty là hướng production — **chưa dùng** ở đây.

## Frontend

- React, TypeScript, Vite, Tailwind CSS, React Router

## Backend

- Python 3.11+, FastAPI, Pydantic, SQLAlchemy, **SQLite**

## Automation Worker

- Python, httpx
- **python-pptx** (fill template V2 theo shape id)
- python-docx (legacy DOCX helper — không còn happy path)
- MockAI / CodexRunner stub (note only)

## Testing / config

- pytest, logging, Git, `.env` / `.env.example`
- **Không** Docker trong prototype này

## Out of scope

- JWT/RBAC, PostgreSQL, Redis, Laravel, Tailscale/Mac mini thật, Codex `exec` đầy đủ
