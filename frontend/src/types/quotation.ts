export type Customer = {
  id: string
  name: string
  company: string
  email: string
  phone: string
  address: string
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
  items: QuotationItem[]
}

export type QuotationCreate = {
  customer_id: string
  items: Omit<QuotationItem, 'id'>[]
  payment_terms: string
  delivery_terms: string
  note?: string
}
