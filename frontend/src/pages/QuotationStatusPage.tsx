import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { Quotation, QuotationStatus } from '../types/quotation'

const STATUS_STYLE: Record<QuotationStatus, string> = {
  PENDING: 'bg-amber-100 text-amber-800',
  PROCESSING: 'bg-sky-100 text-sky-800',
  COMPLETED: 'bg-emerald-100 text-emerald-800',
  FAILED: 'bg-red-100 text-red-800',
}

export function QuotationStatusPage() {
  const { quotationId } = useParams()
  const [quotation, setQuotation] = useState<Quotation | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [retrying, setRetrying] = useState(false)
  const [pollKey, setPollKey] = useState(0)

  useEffect(() => {
    if (!quotationId) return
    let cancelled = false
    let timer: number | undefined

    const load = async () => {
      try {
        const data = await api.getQuotation(quotationId)
        if (cancelled) return
        setQuotation(data)
        setError(null)
        if (data.status === 'PENDING' || data.status === 'PROCESSING') {
          timer = window.setTimeout(load, 2000)
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Load failed')
      }
    }

    load()
    return () => {
      cancelled = true
      if (timer) window.clearTimeout(timer)
    }
  }, [quotationId, pollKey])

  async function onRetry() {
    if (!quotationId) return
    setRetrying(true)
    try {
      const data = await api.retryQuotation(quotationId)
      setQuotation(data)
      setPollKey((k) => k + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Retry failed')
    } finally {
      setRetrying(false)
    }
  }

  if (error && !quotation) return <p className="text-red-600">Lỗi: {error}</p>
  if (!quotation) return <p className="text-slate-500">Đang tải trạng thái...</p>

  return (
    <section>
      <Link to={`/customers/${quotation.customer_id}`} className="text-sm text-teal-700 hover:underline">
        ← Về khách hàng
      </Link>
      <h1 className="mt-3 text-2xl font-semibold text-slate-900">Trạng thái báo giá</h1>
      <p className="mt-1 text-sm text-slate-600">{quotation.id}</p>

      <div className="mt-6 rounded-lg border border-slate-200 bg-white p-4">
        <p className="text-sm text-slate-500">Status</p>
        <span
          className={`mt-1 inline-block rounded px-2 py-1 text-sm font-medium ${STATUS_STYLE[quotation.status]}`}
        >
          {quotation.status}
        </span>

        {(quotation.status === 'PENDING' || quotation.status === 'PROCESSING') && (
          <p className="mt-3 text-sm text-slate-600">
            Đang chờ worker (Mock Mac Mini) xử lý... tự làm mới mỗi 2 giây.
          </p>
        )}

        {quotation.status === 'FAILED' && (
          <div className="mt-3 space-y-3">
            <p className="text-sm text-red-600">{quotation.error_message || 'Xử lý thất bại'}</p>
            <button
              type="button"
              disabled={retrying}
              onClick={onRetry}
              className="rounded bg-slate-800 px-3 py-1.5 text-sm text-white hover:bg-slate-900 disabled:opacity-60"
            >
              {retrying ? 'Đang retry...' : 'Retry'}
            </button>
          </div>
        )}

        {quotation.status === 'COMPLETED' && (
          <div className="mt-4">
            <a
              href={api.downloadUrl(quotation.id)}
              className="inline-block rounded bg-teal-700 px-4 py-2 text-sm font-medium text-white hover:bg-teal-800"
            >
              Tải báo giá (.docx)
            </a>
          </div>
        )}
      </div>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
    </section>
  )
}
