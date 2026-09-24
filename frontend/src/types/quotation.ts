export type Customer = {
  id: string
  name: string
  company: string
  email: string
  phone: string
  address: string
  is_active: boolean
}

export type QuotationItem = {
  id?: number
  product_name: string
  specification: string
  quantity: number
  unit_price: number
}

export type QuotationStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'

export type Quotation = {
  id: string
  customer_id: string
  status: QuotationStatus
  payment_terms: string
  delivery_terms: string
  note: string | null
  output_path: string | null
  error_message: string | null
  attempt_count: number
  items: QuotationItem[]
}

export type QuotationCreate = {
  customer_id: string
  items: Omit<QuotationItem, 'id'>[]
  payment_terms: string
  delivery_terms: string
  note?: string
}

export type QuotationEvent = {
  id: number
  quotation_id: string
  from_status: string | null
  to_status: string
  message: string
  error_message: string | null
  created_at: string | null
}

export type ProcessingAttempt = {
  id: number
  quotation_id: string
  attempt_no: number
  status: string
  error_message: string | null
  output_path: string | null
  started_at: string | null
  finished_at: string | null
}

export type AuditLog = {
  id: number
  action: string
  entity_type: string
  entity_id: string
  detail: string | null
  created_at: string | null
}
