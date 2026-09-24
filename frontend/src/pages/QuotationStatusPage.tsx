import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type {
  Customer,
  ProcessingAttempt,
  Quotation,
  QuotationEvent,
  QuotationStatus,
} from '../types/quotation'

const STATUS_STYLE: Record<QuotationStatus, string> = {
  PENDING: 'bg-amber-100 text-amber-800',
  PROCESSING: 'bg-sky-100 text-sky-800',
  COMPLETED: 'bg-emerald-100 text-emerald-800',
  FAILED: 'bg-red-100 text-red-800',
}

type ItemForm = {
  product_name: string
  specification: string
  quantity: string
  unit_price: string
}

export function QuotationStatusPage() {
  const { quotationId } = useParams()
  const [quotation, setQuotation] = useState<Quotation | null>(null)
  const [customer, setCustomer] = useState<Customer | null>(null)
  const [history, setHistory] = useState<QuotationEvent[]>([])
  const [attempts, setAttempts] = useState<ProcessingAttempt[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [retrying, setRetrying] = useState(false)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [pollKey, setPollKey] = useState(0)

  const [paymentTerms, setPaymentTerms] = useState('')
  const [deliveryTerms, setDeliveryTerms] = useState('')
  const [note, setNote] = useState('')
  const [items, setItems] = useState<ItemForm[]>([])

  useEffect(() => {
    if (!quotationId) return
    let cancelled = false
    let timer: number | undefined

    const load = async () => {
      try {
        const data = await api.getQuotation(quotationId)
        if (cancelled) return
        setQuotation(data)
        setPaymentTerms(data.payment_terms)
        setDeliveryTerms(data.delivery_terms)
        setNote(data.note || '')
        setItems(
          data.items.map((i) => ({
            product_name: i.product_name,
            specification: i.specification,
            quantity: String(i.quantity),
            unit_price: String(i.unit_price),
          })),
        )

        const [events, tries, cust] = await Promise.all([
          api.getHistory(quotationId),
          api.getAttempts(quotationId),
          api.getCustomer(data.customer_id).catch(() => null),
        ])
        if (cancelled) return
        setHistory(events)
        setAttempts(tries)
        setCustomer(cust)
        setError(null)
        setLoading(false)

        // Poll only while in-flight — stop on COMPLETED / FAILED
        if (data.status === 'PENDING' || data.status === 'PROCESSING') {
          timer = window.setTimeout(load, 2000)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Load failed')
          setLoading(false)
        }
      }
    }

    setLoading(true)
    load()
    return () => {
      cancelled = true
      if (timer) window.clearTimeout(timer)
    }
  }, [quotationId, pollKey])

  async function onRetry() {
    if (!quotationId || quotation?.status !== 'FAILED') return
    setRetrying(true)
    setError(null)
    try {
      await api.retryQuotation(quotationId)
      setEditing(false)
      setPollKey((k) => k + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Retry failed')
    } finally {
      setRetrying(false)
    }
  }

  async function onSave(e: FormEvent) {
    e.preventDefault()
    if (!quotationId || !quotation) return
    if (quotation.status !== 'PENDING' && quotation.status !== 'FAILED') return
    setSaving(true)
    setError(null)
    try {
      const updated = await api.updateQuotation(quotationId, {
        payment_terms: paymentTerms,
        delivery_terms: deliveryTerms,
        note: note || null,
        items: items.map((item) => ({
          product_name: item.product_name.trim(),
          specification: item.specification.trim(),
          quantity: Number(item.quantity),
          unit_price: Number(item.unit_price),
        })),
      })
      setQuotation(updated)
      setEditing(false)
      setPollKey((k) => k + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed')
    } finally {
      setSaving(false)
    }
  }

  function updateItem(index: number, field: keyof ItemForm, value: string) {
    setItems((prev) => prev.map((item, i) => (i === index ? { ...item, [field]: value } : item)))
  }

  if (loading && !quotation) return <p className="text-slate-500">Đang tải...</p>
  if (error && !quotation) return <p className="text-red-600">Lỗi: {error}</p>
  if (!quotation) return <p className="text-slate-500">Không tìm thấy báo giá.</p>

  const canEdit = quotation.status === 'PENDING' || quotation.status === 'FAILED'

  return (
    <section>
      <Link to="/quotations" className="text-sm text-teal-700 hover:underline">
        ← Danh sách báo giá
      </Link>
      <h1 className="mt-3 text-2xl font-semibold text-slate-900">Chi tiết báo giá</h1>
      <p className="mt-1 text-sm text-slate-600">{quotation.id}</p>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <span className={`rounded px-2 py-1 text-sm font-medium ${STATUS_STYLE[quotation.status]}`}>
          {quotation.status}
        </span>
        <span className="text-sm text-slate-500">attempts={quotation.attempt_count}</span>
      </div>

      {(quotation.status === 'PENDING' || quotation.status === 'PROCESSING') && (
        <p className="mt-3 text-sm text-slate-600">
          Đang chờ worker... (tự làm mới mỗi 2s, dừng khi COMPLETED/FAILED). Chạy{' '}
          <code>worker/main.py</code>.
        </p>
      )}

      {quotation.status === 'FAILED' && (
        <div className="mt-3 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {quotation.error_message || 'Xử lý thất bại'}
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        {canEdit && !editing && (
          <button
            type="button"
            className="rounded border border-slate-300 px-3 py-2 text-sm"
            onClick={() => setEditing(true)}
          >
            Sửa báo giá
          </button>
        )}
        {quotation.status === 'FAILED' && (
          <button
            type="button"
            disabled={retrying}
            onClick={onRetry}
            className="rounded bg-slate-800 px-3 py-2 text-sm text-white disabled:opacity-60"
          >
            {retrying ? 'Đang retry...' : 'Retry'}
          </button>
        )}
        {quotation.status === 'COMPLETED' && (
          <a
            href={api.downloadUrl(quotation.id)}
            className="rounded bg-teal-700 px-3 py-2 text-sm font-medium text-white hover:bg-teal-800"
          >
            Download (.docx)
          </a>
        )}
      </div>

      {editing && canEdit && (
        <form onSubmit={onSave} className="mt-4 space-y-4 rounded border bg-white p-4">
          <h2 className="font-medium">Cập nhật (PENDING / FAILED)</h2>
          {items.map((item, index) => (
            <fieldset key={index} className="grid gap-2 sm:grid-cols-2">
              <legend className="text-sm font-medium">SP #{index + 1}</legend>
              {(
                [
                  ['product_name', 'Tên SP'],
                  ['specification', 'Quy cách'],
                  ['quantity', 'SL'],
                  ['unit_price', 'Đơn giá'],
                ] as const
              ).map(([field, label]) => (
                <label key={field} className="text-sm">
                  {label}
                  <input
                    className="mt-1 w-full rounded border px-2 py-1.5"
                    type={field === 'quantity' || field === 'unit_price' ? 'number' : 'text'}
                    value={item[field]}
                    onChange={(e) => updateItem(index, field, e.target.value)}
                    required
                    disabled={saving}
                  />
                </label>
              ))}
            </fieldset>
          ))}
          <div className="grid gap-2 sm:grid-cols-2">
            <label className="text-sm">
              Thanh toán
              <input
                className="mt-1 w-full rounded border px-2 py-1.5"
                value={paymentTerms}
                onChange={(e) => setPaymentTerms(e.target.value)}
                required
                disabled={saving}
              />
            </label>
            <label className="text-sm">
              Giao hàng
              <input
                className="mt-1 w-full rounded border px-2 py-1.5"
                value={deliveryTerms}
                onChange={(e) => setDeliveryTerms(e.target.value)}
                required
                disabled={saving}
              />
            </label>
          </div>
          <label className="block text-sm">
            Ghi chú
            <textarea
              className="mt-1 w-full rounded border px-2 py-1.5"
              rows={2}
              maxLength={2000}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              disabled={saving}
            />
          </label>
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

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="rounded border bg-white p-4 text-sm">
          <h2 className="font-medium">Khách hàng</h2>
          {customer ? (
            <dl className="mt-2 space-y-1">
              <div>
                <dt className="text-slate-500">Công ty</dt>
                <dd>
                  <Link className="text-teal-700 hover:underline" to={`/customers/${customer.id}`}>
                    {customer.company}
                  </Link>{' '}
                  {!customer.is_active && <span className="text-red-600">(inactive)</span>}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Liên hệ</dt>
                <dd>
                  {customer.name} · {customer.email} · {customer.phone}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Địa chỉ</dt>
                <dd>{customer.address}</dd>
              </div>
            </dl>
          ) : (
            <p className="mt-2 text-slate-500">{quotation.customer_id}</p>
          )}
        </div>

        <div className="rounded border bg-white p-4 text-sm">
          <h2 className="font-medium">Thông tin báo giá</h2>
          <dl className="mt-2 space-y-1">
            <div>
              <dt className="text-slate-500">Thanh toán / Giao hàng</dt>
              <dd>
                {quotation.payment_terms} · {quotation.delivery_terms}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Ghi chú</dt>
              <dd>{quotation.note || '—'}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Sản phẩm</dt>
              <dd>
                <ul className="list-disc pl-4">
                  {quotation.items.map((i) => (
                    <li key={i.id ?? `${i.product_name}-${i.quantity}`}>
                      {i.product_name} ({i.specification}) — SL {i.quantity} × {i.unit_price}
                    </li>
                  ))}
                </ul>
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">File</dt>
              <dd>
                {quotation.status === 'COMPLETED' && quotation.output_path ? (
                  <span className="break-all text-xs">{quotation.output_path}</span>
                ) : (
                  'Chưa có file'
                )}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="rounded border bg-white p-4">
          <h2 className="font-medium">Processing history</h2>
          <ul className="mt-2 space-y-2 text-sm">
            {history.map((e) => (
              <li key={e.id} className="border-b border-slate-100 pb-2">
                <p className="font-medium">
                  {e.from_status || '—'} → {e.to_status}
                </p>
                <p className="text-slate-600">{e.message}</p>
                {e.error_message && <p className="text-red-600">{e.error_message}</p>}
                <p className="text-xs text-slate-400">{e.created_at}</p>
              </li>
            ))}
            {history.length === 0 && <li className="text-slate-500">Chưa có sự kiện.</li>}
          </ul>
        </div>

        <div className="rounded border bg-white p-4">
          <h2 className="font-medium">Processing attempts</h2>
          <ul className="mt-2 space-y-2 text-sm">
            {attempts.map((a) => (
              <li key={a.id} className="border-b border-slate-100 pb-2">
                <p className="font-medium">
                  #{a.attempt_no} · {a.status}
                </p>
                {a.error_message && <p className="text-red-600">{a.error_message}</p>}
                {a.output_path && <p className="break-all text-xs text-slate-500">{a.output_path}</p>}
                <p className="text-xs text-slate-400">
                  {a.started_at} → {a.finished_at || '...'}
                </p>
              </li>
            ))}
            {attempts.length === 0 && <li className="text-slate-500">Chưa có attempt.</li>}
          </ul>
        </div>
      </div>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
    </section>
  )
}
