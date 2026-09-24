import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { Customer } from '../types/quotation'

export function CustomerDetailPage() {
  const { customerId } = useParams()
  const navigate = useNavigate()
  const [customer, setCustomer] = useState<Customer | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [deactivating, setDeactivating] = useState(false)
  const [form, setForm] = useState({ name: '', company: '', email: '', phone: '', address: '' })

  useEffect(() => {
    if (!customerId) return
    setLoading(true)
    api
      .getCustomer(customerId)
      .then((c) => {
        setCustomer(c)
        setForm({
          name: c.name,
          company: c.company,
          email: c.email,
          phone: c.phone,
          address: c.address,
        })
        setError(null)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [customerId])

  async function onSave(e: FormEvent) {
    e.preventDefault()
    if (!customerId) return
    setSaving(true)
    try {
      const updated = await api.updateCustomer(customerId, form)
      setCustomer(updated)
      setEditing(false)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed')
    } finally {
      setSaving(false)
    }
  }

  async function onDeactivate() {
    if (!customerId || !confirm('Deactivate khách hàng này?')) return
    setDeactivating(true)
    try {
      const updated = await api.deactivateCustomer(customerId)
      setCustomer(updated)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Deactivate failed')
    } finally {
      setDeactivating(false)
    }
  }

  if (loading) return <p className="text-slate-500">Đang tải...</p>
  if (error && !customer) return <p className="text-red-600">Lỗi: {error}</p>
  if (!customer) return <p className="text-slate-500">Không tìm thấy khách hàng.</p>

  return (
    <section>
      <Link to="/" className="text-sm text-teal-700 hover:underline">
        ← Danh sách
      </Link>
      <h1 className="mt-3 text-2xl font-semibold text-slate-900">
        {customer.company}{' '}
        {!customer.is_active && <span className="text-base text-red-600">(inactive)</span>}
      </h1>

      {!customer.is_active && (
        <p className="mt-2 text-sm text-amber-700">
          Khách hàng inactive — không thể tạo báo giá mới. Quotation cũ vẫn xem được.
        </p>
      )}

      {!editing ? (
        <>
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
          <div className="mt-4 flex flex-wrap gap-2">
            {customer.is_active ? (
              <button
                type="button"
                className="rounded bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800"
                onClick={() => navigate(`/customers/${customer.id}/quotations/new`)}
              >
                Tạo báo giá
              </button>
            ) : (
              <button
                type="button"
                disabled
                className="cursor-not-allowed rounded bg-slate-300 px-4 py-2 text-sm text-slate-600"
              >
                Tạo báo giá (blocked)
              </button>
            )}
            <button
              type="button"
              className="rounded border border-slate-300 px-3 py-2 text-sm"
              onClick={() => setEditing(true)}
            >
              Sửa
            </button>
            {customer.is_active && (
              <button
                type="button"
                disabled={deactivating}
                className="rounded border border-red-300 px-3 py-2 text-sm text-red-700 disabled:opacity-60"
                onClick={onDeactivate}
              >
                {deactivating ? 'Đang deactivate...' : 'Deactivate'}
              </button>
            )}
          </div>
        </>
      ) : (
        <form onSubmit={onSave} className="mt-4 grid max-w-xl gap-3 rounded border bg-white p-4">
          {(['name', 'company', 'email', 'phone', 'address'] as const).map((field) => (
            <label key={field} className="text-sm capitalize">
              {field}
              <input
                className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
                value={form[field]}
                onChange={(e) => setForm((f) => ({ ...f, [field]: e.target.value }))}
                required
                disabled={saving}
              />
            </label>
          ))}
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={saving}
              className="rounded bg-teal-700 px-3 py-2 text-sm text-white disabled:opacity-60"
            >
              {saving ? 'Đang lưu...' : 'Lưu'}
            </button>
            <button
              type="button"
              className="rounded border px-3 py-2 text-sm"
              disabled={saving}
              onClick={() => setEditing(false)}
            >
              Hủy
            </button>
          </div>
        </form>
      )}

      {error && !editing && <p className="mt-3 text-sm text-red-600">{error}</p>}
    </section>
  )
}
