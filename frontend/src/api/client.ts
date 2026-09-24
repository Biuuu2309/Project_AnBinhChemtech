import type {
  AuditLog,
  Customer,
  ProcessingAttempt,
  Quotation,
  QuotationCreate,
  QuotationEvent,
} from '../types/quotation'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ? JSON.stringify(body.detail) : detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  if (res.status === 204) {
    return undefined as T
  }
  return res.json() as Promise<T>
}

export const api = {
  listCustomers: (q?: string, activeOnly = true) => {
    const params = new URLSearchParams()
    if (q) params.set('q', q)
    params.set('active_only', String(activeOnly))
    return request<Customer[]>(`/api/customers?${params}`)
  },
  getCustomer: (id: string) => request<Customer>(`/api/customers/${id}`),
  createCustomer: (payload: Omit<Customer, 'id' | 'is_active'>) =>
    request<Customer>('/api/customers', { method: 'POST', body: JSON.stringify(payload) }),
  updateCustomer: (id: string, payload: Partial<Omit<Customer, 'id' | 'is_active'>>) =>
    request<Customer>(`/api/customers/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deactivateCustomer: (id: string) =>
    request<Customer>(`/api/customers/${id}/deactivate`, { method: 'POST' }),

  listQuotations: (opts?: { q?: string; status?: string; customer_id?: string }) => {
    const params = new URLSearchParams()
    if (opts?.q) params.set('q', opts.q)
    if (opts?.status) params.set('status', opts.status)
    if (opts?.customer_id) params.set('customer_id', opts.customer_id)
    const qs = params.toString()
    return request<Quotation[]>(`/api/quotations${qs ? `?${qs}` : ''}`)
  },
  createQuotation: (payload: QuotationCreate, idempotencyKey: string) =>
    request<Quotation>('/api/quotations', {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: { 'Idempotency-Key': idempotencyKey },
    }),
  getQuotation: (id: string) => request<Quotation>(`/api/quotations/${id}`),
  updateQuotation: (
    id: string,
    payload: {
      items?: QuotationCreate['items']
      payment_terms?: string
      delivery_terms?: string
      note?: string | null
    },
  ) =>
    request<Quotation>(`/api/quotations/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  retryQuotation: (id: string) =>
    request<Quotation>(`/api/quotations/${id}/retry`, { method: 'POST' }),
  downloadUrl: (id: string) => `/api/quotations/${id}/download`,
  getHistory: (id: string) => request<QuotationEvent[]>(`/api/quotations/${id}/history`),
  getAttempts: (id: string) => request<ProcessingAttempt[]>(`/api/quotations/${id}/attempts`),
  listAudit: (entityType?: string, entityId?: string) => {
    const params = new URLSearchParams()
    if (entityType) params.set('entity_type', entityType)
    if (entityId) params.set('entity_id', entityId)
    const qs = params.toString()
    return request<AuditLog[]>(`/api/audit${qs ? `?${qs}` : ''}`)
  },
}
