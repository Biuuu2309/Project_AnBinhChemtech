import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'

type ItemForm = {
  product_name: string
  specification: string
  quantity: string
  unit_price: string
}

const emptyItem = (): ItemForm => ({
  product_name: 'Chemical Product A',
  specification: '99.5%',
  quantity: '100',
  unit_price: '250000',
})

export function QuotationFormPage() {
  const { customerId } = useParams()
  const navigate = useNavigate()
  const [items, setItems] = useState<ItemForm[]>([emptyItem()])
  const [paymentTerms, setPaymentTerms] = useState('30 days')
  const [deliveryTerms, setDeliveryTerms] = useState('Within 7 days')
  const [note, setNote] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  function updateItem(index: number, field: keyof ItemForm, value: string) {
    setItems((prev) => prev.map((item, i) => (i === index ? { ...item, [field]: value } : item)))
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!customerId) return
    setError(null)
    setSubmitting(true)
    try {
      const quotation = await api.createQuotation({
        customer_id: customerId,
        payment_terms: paymentTerms,
        delivery_terms: deliveryTerms,
        note: note || undefined,
        items: items.map((item) => ({
          product_name: item.product_name.trim(),
          specification: item.specification.trim(),
          quantity: Number(item.quantity),
          unit_price: Number(item.unit_price),
        })),
      })
      navigate(`/quotations/${quotation.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submit failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section>
      <Link to={`/customers/${customerId}`} className="text-sm text-teal-700 hover:underline">
        ← Chi tiết khách hàng
      </Link>
      <h1 className="mt-3 text-2xl font-semibold text-slate-900">Form báo giá</h1>
      <p className="mt-1 text-sm text-slate-600">Khách hàng: {customerId}</p>

      <form onSubmit={onSubmit} className="mt-6 space-y-6 rounded-lg border border-slate-200 bg-white p-4">
        {items.map((item, index) => (
          <fieldset key={index} className="grid gap-3 sm:grid-cols-2">
            <legend className="mb-1 text-sm font-medium text-slate-700">Sản phẩm #{index + 1}</legend>
            <label className="text-sm">
              Tên sản phẩm
              <input
                className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
                value={item.product_name}
                onChange={(e) => updateItem(index, 'product_name', e.target.value)}
                required
              />
            </label>
            <label className="text-sm">
              Quy cách
              <input
                className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
                value={item.specification}
                onChange={(e) => updateItem(index, 'specification', e.target.value)}
                required
              />
            </label>
            <label className="text-sm">
              Số lượng
              <input
                type="number"
                min="0.01"
                step="any"
                className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
                value={item.quantity}
                onChange={(e) => updateItem(index, 'quantity', e.target.value)}
                required
              />
            </label>
            <label className="text-sm">
              Đơn giá (VND)
              <input
                type="number"
                min="0"
                step="any"
                className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
                value={item.unit_price}
                onChange={(e) => updateItem(index, 'unit_price', e.target.value)}
                required
              />
            </label>
          </fieldset>
        ))}

        <button
          type="button"
          className="text-sm text-teal-700 hover:underline"
          onClick={() => setItems((prev) => [...prev, emptyItem()])}
        >
          + Thêm dòng sản phẩm
        </button>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-sm">
            Điều kiện thanh toán
            <input
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
              value={paymentTerms}
              onChange={(e) => setPaymentTerms(e.target.value)}
              required
            />
          </label>
          <label className="text-sm">
            Điều kiện giao hàng
            <input
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
              value={deliveryTerms}
              onChange={(e) => setDeliveryTerms(e.target.value)}
              required
            />
          </label>
        </div>

        <label className="block text-sm">
          Ghi chú
          <textarea
            className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
            rows={3}
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800 disabled:opacity-60"
        >
          {submitting ? 'Đang gửi...' : 'Gửi'}
        </button>
      </form>
    </section>
  )
}
