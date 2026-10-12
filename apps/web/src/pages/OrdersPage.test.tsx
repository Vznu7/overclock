import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { OrdersPage } from './OrdersPage'
import * as api from '../lib/api'

vi.mock('../lib/api', () => ({
  fetchOrders: vi.fn(),
  fetchBuyers: vi.fn(),
  fetchStyles: vi.fn(),
  createOrder: vi.fn(),
  updateMilestone: vi.fn(),
  downloadOrdersCsv: vi.fn(),
}))

const mockOrders: api.Order[] = [
  {
    id: 'ord-123',
    tenant_id: 'tirupur-demo',
    buyer_id: 'buy-1',
    style_id: 'sty-1',
    order_number: 'PO-DEC-8821',
    total_quantity: 12000,
    unit_price: 320.00,
    currency: 'INR',
    ex_factory_date: '2026-11-28',
    status: 'CONFIRMED',
    buyer: {
      id: 'buy-1',
      tenant_id: 'tirupur-demo',
      name: 'Decathlon Sports',
      code: 'DECATH',
      country: 'France',
    },
    style: {
      id: 'sty-1',
      tenant_id: 'tirupur-demo',
      buyer_id: 'buy-1',
      style_number: 'DEC-TEE-01',
      style_name: 'QuickDry Performance Tee',
      garment_type: 'Crew Neck Tee',
      sam: 12.5,
      target_efficiency: 68.0,
    },
    lines: [
      { id: 'line-1', tenant_id: 'tirupur-demo', order_id: 'ord-123', color: 'Navy Blue', size: 'M', quantity: 6000 },
      { id: 'line-2', tenant_id: 'tirupur-demo', order_id: 'ord-123', color: 'Navy Blue', size: 'L', quantity: 6000 },
    ],
    milestones: [
      { id: 'm-1', tenant_id: 'tirupur-demo', order_id: 'ord-123', name: 'Fabric In-House', planned_date: '2026-11-07', status: 'COMPLETED' },
      { id: 'm-2', tenant_id: 'tirupur-demo', order_id: 'ord-123', name: 'PP Sample Approved', planned_date: '2026-11-10', status: 'PENDING' },
    ],
  },
]

describe('OrdersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.fetchOrders).mockResolvedValue(mockOrders)
    vi.mocked(api.fetchBuyers).mockResolvedValue([])
    vi.mocked(api.fetchStyles).mockResolvedValue([])
  })

  it('renders orders suite header and orders table with real data', async () => {
    render(
      <BrowserRouter>
        <OrdersPage />
      </BrowserRouter>
    )

    expect(screen.getAllByText('Orders & TNA Tracking Suite').length).toBeGreaterThan(0)

    await waitFor(() => {
      expect(screen.getByText('PO-DEC-8821')).toBeInTheDocument()
      expect(screen.getByText('Decathlon Sports')).toBeInTheDocument()
      expect(screen.getByText('DEC-TEE-01')).toBeInTheDocument()
      expect(screen.getByText('12,000 pcs')).toBeInTheDocument()
    })
  })

  it('renders metric strip summaries correctly', async () => {
    render(
      <BrowserRouter>
        <OrdersPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('12,000 pcs')).toBeInTheDocument()
      expect(screen.getByText('Total Orders')).toBeInTheDocument()
      expect(screen.getByText('Total Volume')).toBeInTheDocument()
    })
  })
})
