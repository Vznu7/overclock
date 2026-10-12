import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

interface PageMeta {
  title: string
  description: string
}

const ROUTE_META: Record<string, PageMeta> = {
  '/': {
    title: 'OVERCLOCK — Predictive Garment Shipment & Factory Operations AI SaaS',
    description: 'Predict garment shipment delays before they breach. Multi-tenant AI SaaS for apparel manufacturers uniting buyer POs, fabric readiness, daily sewing SAM pacing, and outside job-work.'
  },
  '/dashboard': {
    title: 'Executive Control Tower — OVERCLOCK',
    description: 'Unified R1-R6 delivery risk engine, real-time floor telemetry, and active delay blockers for apparel export factories.'
  },
  '/orders': {
    title: 'Orders & TNA Tracking — OVERCLOCK',
    description: 'Buyer PO line items, color-size breakup, delivery gates, and real-time shipment pacing for garment merchandisers.'
  },
  '/po-review': {
    title: 'AI PO Ingestion & Split-Screen Review — OVERCLOCK',
    description: 'Side-by-side commercial buyer PDF preview, table extraction, and 1-click confirmation with zero LLM math errors.'
  },
  '/materials': {
    title: 'Materials, BOM & Stock Ledger — OVERCLOCK',
    description: 'Double-entry fabric and trims inventory ledger with BOM consumption, receipts, and shortfall risk alerts.'
  },
  '/production': {
    title: 'Floor Production Lines & SAM Telemetry — OVERCLOCK',
    description: 'Daily sewing line output pacing, SAM efficiency, 30-second mobile entry, and bottleneck detection.'
  },
  '/jobwork': {
    title: 'Outside Job-Work Processor Hub — OVERCLOCK',
    description: 'Delivery challans for dyeing and printing, processor turnaround pacing, and weight loss shrinkage tracking.'
  },
  '/risk-evidence': {
    title: 'Risk Evidence Matrix & R1-R6 Proof — OVERCLOCK',
    description: 'Pure mathematical proof behind flagged delivery rules R1-R6 with deterministic timeline reconstruction.'
  },
  '/imports': {
    title: 'CSV & Excel Data Migration — OVERCLOCK',
    description: 'Bulk import buyers, styles, purchase orders, materials, stock ledger, and production telemetry in seconds.'
  },
  '/company': {
    title: 'Company Portal & TNA Governance — OVERCLOCK',
    description: 'Organizational factory settings, TNA milestone approval gates, and multi-tenant operational security.'
  },
  '/about': {
    title: 'About OVERCLOCK — Factory OS for Garment Manufacturers',
    description: 'Built for garment and textile manufacturers in Tiruppur, India. 100% deterministic operating system with bilingual Tamil and English UI.'
  }
}

export const RouteSeo = () => {
  const location = useLocation()

  useEffect(() => {
    const meta = ROUTE_META[location.pathname] || ROUTE_META['/']

    // Update document title
    document.title = meta.title

    // Update meta description
    let metaDesc = document.querySelector('meta[name="description"]')
    if (!metaDesc) {
      metaDesc = document.createElement('meta')
      metaDesc.setAttribute('name', 'description')
      document.head.appendChild(metaDesc)
    }
    metaDesc.setAttribute('content', meta.description)

    // Update Open Graph tags
    const ogTitle = document.querySelector('meta[property="og:title"]')
    if (ogTitle) ogTitle.setAttribute('content', meta.title)

    const ogDesc = document.querySelector('meta[property="og:description"]')
    if (ogDesc) ogDesc.setAttribute('content', meta.description)

    const ogUrl = document.querySelector('meta[property="og:url"]')
    if (ogUrl) ogUrl.setAttribute('content', `https://www.theoverclock.tech${location.pathname === '/' ? '' : location.pathname}`)

    // Update Canonical URL
    let canonical = document.querySelector('link[rel="canonical"]')
    if (!canonical) {
      canonical = document.createElement('link')
      canonical.setAttribute('rel', 'canonical')
      document.head.appendChild(canonical)
    }
    canonical.setAttribute('href', `https://www.theoverclock.tech${location.pathname === '/' ? '' : location.pathname}`)
  }, [location.pathname])

  return null
}
