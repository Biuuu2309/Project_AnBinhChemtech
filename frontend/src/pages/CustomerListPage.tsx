import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Customer } from '../types/quotation'

export function CustomerListPage() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .listCustomers()
      .then(setCustomers)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-slate-500">Đang tải...</p>
  if (error) return <p className="text-red-600">Lỗi: {error}</p>

  return (
    <section>
      <h1 className="text-2xl font-semibold text-slate-900">Danh sách khách hàng</h1>
      <p className="mt-1 text-sm text-slate-600">Chọn khách hàng để tạo báo giá.</p>
      <ul className="mt-6 divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
        {customers.map((c) => (
          <li key={c.id}>
            <Link
              to={`/customers/${c.id}`}
              className="flex items-center justify-between px-4 py-3 hover:bg-slate-50"
            >
              <div>
                <p className="font-medium text-slate-900">{c.company}</p>
                <p className="text-sm text-slate-600">
                  {c.name} · {c.id}
                </p>
              </div>
              <span className="text-sm text-teal-700">Chi tiết →</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  )
}
