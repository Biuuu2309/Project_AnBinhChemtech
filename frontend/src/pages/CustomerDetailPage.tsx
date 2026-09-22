import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { Customer } from '../types/quotation'

export function CustomerDetailPage() {
  const { customerId } = useParams()
  const navigate = useNavigate()
  const [customer, setCustomer] = useState<Customer | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!customerId) return
    api
      .getCustomer(customerId)
      .then(setCustomer)
      .catch((err: Error) => setError(err.message))
  }, [customerId])

  if (error) return <p className="text-red-600">Lỗi: {error}</p>
  if (!customer) return <p className="text-slate-500">Đang tải...</p>

  return (
    <section>
      <Link to="/" className="text-sm text-teal-700 hover:underline">
        ← Danh sách
      </Link>
      <h1 className="mt-3 text-2xl font-semibold text-slate-900">{customer.company}</h1>
      <dl className="mt-4 grid gap-2 rounded-lg border border-slate-200 bg-white p-4 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-slate-500">Mã KH</dt>
          <dd className="font-medium">{customer.id}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Người liên hệ</dt>
          <dd className="font-medium">{customer.name}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Email</dt>
          <dd className="font-medium">{customer.email}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Điện thoại</dt>
          <dd className="font-medium">{customer.phone}</dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="text-slate-500">Địa chỉ</dt>
          <dd className="font-medium">{customer.address}</dd>
        </div>
      </dl>
      <button
        type="button"
        className="mt-6 rounded bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800"
        onClick={() => navigate(`/customers/${customer.id}/quotations/new`)}
      >
        Tạo báo giá
      </button>
    </section>
  )
}
