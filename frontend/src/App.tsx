import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { CustomerCreatePage } from './pages/CustomerCreatePage'
import { CustomerDetailPage } from './pages/CustomerDetailPage'
import { CustomerListPage } from './pages/CustomerListPage'
import { QuotationFormPage } from './pages/QuotationFormPage'
import { QuotationListPage } from './pages/QuotationListPage'
import { QuotationStatusPage } from './pages/QuotationStatusPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<CustomerListPage />} />
          <Route path="customers/new" element={<CustomerCreatePage />} />
          <Route path="customers/:customerId" element={<CustomerDetailPage />} />
          <Route path="customers/:customerId/quotations/new" element={<QuotationFormPage />} />
          <Route path="quotations" element={<QuotationListPage />} />
          <Route path="quotations/:quotationId" element={<QuotationStatusPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
