# Frontend — Internal Management UI

React + TypeScript + Vite app for the An Bình Chemtech quotation prototype.

**Project docs / runbook:** [`../README.md`](../README.md) · [`../docs/README.md`](../docs/README.md).

```powershell
npm install
npm run dev    # http://localhost:5173 (proxies /api → :8000)
npm run build
```

Vite proxies `/api` and `/health` to the FastAPI backend — run backend + worker together for a full demo.
