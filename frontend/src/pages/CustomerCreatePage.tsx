import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export function CustomerCreatePage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '',
    company: '',
    email: '',
    phone: '',
    address: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const created = await api.createCustomer(form)
      navigate(`/customers/${created.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Create failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section>
      <Link to="/" className="text-sm text-teal-700 hover:underline">
        ← Danh sách
      </Link>
      <h1 className="mt-3 text-2xl font-semibold">Tạo khách hàng</h1>
      <form onSubmit={onSubmit} className="mt-4 grid max-w-xl gap-3 rounded border border-slate-200 bg-white p-4">
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
        <button
          type="submit"
          disabled={saving}
          className="rounded bg-teal-700 px-3 py-2 text-sm text-white disabled:opacity-60"
        >
          {saving ? 'Đang lưu...' : 'Lưu'}
        </button>
      </form>
    </section>
  )
}
