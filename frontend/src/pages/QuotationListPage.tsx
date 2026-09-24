import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Quotation, QuotationStatus } from '../types/quotation'

const STATUSES: Array<QuotationStatus | ''> = ['', 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED']

export function QuotationListPage() {
  const [rows, setRows] = useState<Quotation[]>([])
  const [q, setQ] = useState('')
  const [status, setStatus] = useState<QuotationStatus | ''>('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    try {
      const data = await api.listQuotations({
        q: q || undefined,
        status: status || undefined,
      })
      setRows(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Load failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function onFilter(e: FormEvent) {
    e.preventDefault()
    load()
  }

  return (
    <section>
      <h1 className="text-2xl font-semibold text-slate-900">Báo giá</h1>
      <p className="mt-1 text-sm text-slate-600">List / search / filter theo status.</p>

      <form onSubmit={onFilter} className="mt-4 flex flex-wrap gap-2">
        <input
          className="min-w-[200px] flex-1 rounded border border-slate-300 px-2 py-1.5 text-sm"
          placeholder="Tìm mã / note..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select
          className="rounded border border-slate-300 px-2 py-1.5 text-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value as QuotationStatus | '')}
        >
          {STATUSES.map((s) => (
            <option key={s || 'all'} value={s}>
              {s || 'All statuses'}
            </option>
          ))}
        </select>
        <button
          type="submit"
          disabled={loading}
          className="rounded bg-slate-800 px-3 py-1.5 text-sm text-white disabled:opacity-60"
        >
          {loading ? 'Đang lọc...' : 'Lọc'}
        </button>
      </form>

      {loading && <p className="mt-4 text-slate-500">Đang tải...</p>}
      {error && <p className="mt-4 text-red-600">{error}</p>}

      {!loading && !error && (
        <ul className="mt-4 divide-y rounded-lg border border-slate-200 bg-white">
          {rows.map((row) => (
            <li key={row.id}>
              <Link
                to={`/quotations/${row.id}`}
                className="flex items-center justify-between px-4 py-3 hover:bg-slate-50"
              >
                <div>
                  <p className="font-medium">{row.id}</p>
                  <p className="text-sm text-slate-600">
                    {row.customer_id} · attempts={row.attempt_count}
                  </p>
                </div>
                <span className="text-sm font-medium text-teal-700">{row.status}</span>
              </Link>
            </li>
          ))}
          {rows.length === 0 && <li className="px-4 py-6 text-sm text-slate-500">Không có báo giá.</li>}
        </ul>
      )}
    </section>
  )
}
