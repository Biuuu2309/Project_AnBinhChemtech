# Tech stack (as built)

Stack actually used in this prototype. Items marked *out of scope* are **not** implemented.

## Frontend

- React 19
- TypeScript
- Vite
- Tailwind CSS 4
- React Router

## Backend

- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite

## Automation Worker (Mock Mac mini)

- Python + httpx
- python-docx (template fill)
- MockAI (default note normalization)
- CodexRunner (Codex CLI integration boundary for Mac mini production)

## Testing / tooling

- pytest (backend, worker)
- logging
- Git
- `.env` / `.env.example`

## Explicitly out of scope (not in this prototype)

- JWT / RBAC
- Postgres / Redis / message queue
- Docker (optional later)
- LibreOffice PDF export
- Physical Mac mini + live Codex `exec` session
