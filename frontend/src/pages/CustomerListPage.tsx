import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Customer } from '../types/quotation'

export function CustomerListPage() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [q, setQ] = useState('')
  const [showInactive, setShowInactive] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function load(search = q, inactive = showInactive) {
    setLoading(true)
    try {
      const rows = await api.listCustomers(search || undefined, !inactive)
      setCustomers(rows)
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

  function onSearch(e: FormEvent) {
    e.preventDefault()
    load()
  }

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Khách hàng</h1>
          <p className="mt-1 text-sm text-slate-600">Tìm kiếm / tạo / quản lý khách hàng.</p>
        </div>
        <Link
          to="/customers/new"
          className="rounded bg-teal-700 px-3 py-2 text-sm font-medium text-white hover:bg-teal-800"
        >
          + Tạo khách hàng
        </Link>
      </div>

      <form onSubmit={onSearch} className="mt-4 flex flex-wrap items-center gap-2">
        <input
          className="min-w-[220px] flex-1 rounded border border-slate-300 px-2 py-1.5 text-sm"
          placeholder="Tìm theo tên, công ty, email, mã..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <label className="flex items-center gap-1 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={showInactive}
            onChange={(e) => {
              setShowInactive(e.target.checked)
              load(q, e.target.checked)
            }}
          />
          Hiện inactive
        </label>
        <button
          type="submit"
          disabled={loading}
          className="rounded bg-slate-800 px-3 py-1.5 text-sm text-white disabled:opacity-60"
        >
          {loading ? 'Đang tìm...' : 'Tìm'}
        </button>
      </form>

      {loading && <p className="mt-4 text-slate-500">Đang tải...</p>}
      {error && <p className="mt-4 text-red-600">Lỗi: {error}</p>}

      {!loading && !error && (
        <ul className="mt-4 divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
          {customers.map((c) => (
            <li key={c.id}>
              <Link
                to={`/customers/${c.id}`}
                className="flex items-center justify-between px-4 py-3 hover:bg-slate-50"
              >
                <div>
                  <p className="font-medium text-slate-900">
                    {c.company}{' '}
                    {!c.is_active && (
                      <span className="text-xs font-normal text-red-600">(inactive)</span>
                    )}
                  </p>
                  <p className="text-sm text-slate-600">
                    {c.name} · {c.id}
                  </p>
                </div>
                <span className="text-sm text-teal-700">Chi tiết →</span>
              </Link>
            </li>
          ))}
          {customers.length === 0 && (
            <li className="px-4 py-6 text-sm text-slate-500">Không có khách hàng.</li>
          )}
        </ul>
      )}
    </section>
  )
}
