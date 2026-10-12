import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Navbar } from './components/layout/Navbar'
import { CompanyPortal } from './pages/CompanyPortal'
import { DashboardPage } from './pages/DashboardPage'
import { OrdersPage } from './pages/OrdersPage'
import { PoReviewPage } from './pages/PoReviewPage'
import { MaterialsPage } from './pages/MaterialsPage'
import { ProductionPage } from './pages/ProductionPage'
import { JobworkPage } from './pages/JobworkPage'
import { RiskEvidencePage } from './pages/RiskEvidencePage'
import { ImportsPage } from './pages/ImportsPage'
import { CompanySettingsPage } from './pages/CompanySettingsPage'
import { AboutPage } from './pages/AboutPage'

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-[#08090e] text-zinc-100 font-sans selection:bg-teal-500/30 selection:text-teal-200">
        <Navbar />
        
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Routes>
            <Route path="/" element={<CompanyPortal />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/orders" element={<OrdersPage />} />
            <Route path="/po-review" element={<PoReviewPage />} />
            <Route path="/materials" element={<MaterialsPage />} />
            <Route path="/production" element={<ProductionPage />} />
            <Route path="/jobwork" element={<JobworkPage />} />
            <Route path="/risk-evidence" element={<RiskEvidencePage />} />
            <Route path="/imports" element={<ImportsPage />} />
            <Route path="/company" element={<CompanySettingsPage />} />
            <Route path="*" element={<CompanyPortal />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
