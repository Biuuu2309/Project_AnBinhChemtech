import type { Customer, Quotation, QuotationCreate } from '../types/quotation'

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
  listCustomers: () => request<Customer[]>('/api/customers'),
  getCustomer: (id: string) => request<Customer>(`/api/customers/${id}`),
  createQuotation: (payload: QuotationCreate) =>
    request<Quotation>('/api/quotations', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getQuotation: (id: string) => request<Quotation>(`/api/quotations/${id}`),
  retryQuotation: (id: string) =>
    request<Quotation>(`/api/quotations/${id}/retry`, { method: 'POST' }),
  downloadUrl: (id: string) => `/api/quotations/${id}/download`,
}
