import React, { useEffect, useState, useCallback } from 'react'
import { ToolLayout } from '../components/layout/ToolLayout'
import { 
  Plus, 
  Search, 
  Filter, 
  Download, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  X,
  ChevronRight,
  Package,
  Calendar,
  Layers
} from 'lucide-react'
import { 
  fetchOrders, 
  fetchBuyers, 
  fetchStyles, 
  createOrder, 
  updateMilestone, 
  downloadOrdersCsv,
  Order, 
  Buyer, 
  Style, 
  OrderMilestone 
} from '../lib/api'

export const OrdersPage: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([])
  const [buyers, setBuyers] = useState<Buyer[]>([])
  const [styles, setStyles] = useState<Style[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [refreshing, setRefreshing] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  // Filters & search
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('ALL')

  // Selected Order for TNA / Line matrix drawer
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)

  // Create Order Modal State
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false)
  const [newOrderForm, setNewOrderForm] = useState({
    buyer_id: '',
    style_id: '',
    order_number: '',
    total_quantity: 5000,
    unit_price: 350.00,
    currency: 'INR',
    ex_factory_date: new Date(Date.now() + 45 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    planned_sewing_start: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  })
  const [creating, setCreating] = useState<boolean>(false)
  const [exporting, setExporting] = useState<boolean>(false)

  const loadData = useCallback(async (isManualRefresh = false) => {
    if (isManualRefresh) setRefreshing(true)
    else setLoading(true)
    setError(null)

    try {
      const [ordersData, buyersData, stylesData] = await Promise.all([
        fetchOrders(),
        fetchBuyers().catch(() => []),
        fetchStyles().catch(() => []),
      ])
      setOrders(ordersData)
      setBuyers(buyersData)
      setStyles(stylesData)

      // Keep drawer in sync if open
      setSelectedOrder(prev => {
        if (!prev) return null
        return ordersData.find(o => o.id === prev.id) || prev
      })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unable to connect to database'
      setError(message)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleMilestoneStatusToggle = async (milestone: OrderMilestone) => {
    if (!selectedOrder) return
    const nextStatus = milestone.status === 'COMPLETED' ? 'PENDING' : 'COMPLETED'
    const today = new Date().toISOString().split('T')[0]

    try {
      const updated = await updateMilestone(selectedOrder.id, milestone.id, {
        status: nextStatus,
        actual_date: nextStatus === 'COMPLETED' ? today : null,
      })

      // Update state locally
      setSelectedOrder(prev => {
        if (!prev) return null
        return {
          ...prev,
          milestones: prev.milestones.map(m => m.id === updated.id ? updated : m),
        }
      })
      setOrders(prev => prev.map(o => {
        if (o.id !== selectedOrder.id) return o
        return {
          ...o,
          milestones: o.milestones.map(m => m.id === updated.id ? updated : m),
        }
      }))
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to update milestone')
    }
  }

  const handleExportCsv = async () => {
    try {
      setExporting(true)
      const blob = await downloadOrdersCsv()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `orders_export_${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Export failed')
    } finally {
      setExporting(false)
    }
  }

  const handleCreateOrderSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newOrderForm.buyer_id || !newOrderForm.style_id || !newOrderForm.order_number) {
      alert('Please fill out all required fields')
      return
    }

    try {
      setCreating(true)
      await createOrder({
        buyer_id: newOrderForm.buyer_id,
        style_id: newOrderForm.style_id,
        order_number: newOrderForm.order_number,
        total_quantity: Number(newOrderForm.total_quantity),
        unit_price: Number(newOrderForm.unit_price),
        currency: newOrderForm.currency,
        ex_factory_date: newOrderForm.ex_factory_date,
        planned_sewing_start: newOrderForm.planned_sewing_start,
      })
      setIsCreateOpen(false)
      await loadData()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Error creating order')
    } finally {
      setCreating(false)
    }
  }

  const filteredOrders = orders.filter(order => {
    const q = searchQuery.toLowerCase()
    const matchesSearch = 
      order.order_number.toLowerCase().includes(q) ||
      (order.buyer?.name && order.buyer.name.toLowerCase().includes(q)) ||
      (order.style?.style_number && order.style.style_number.toLowerCase().includes(q)) ||
      (order.style?.style_name && order.style.style_name.toLowerCase().includes(q))

    const matchesStatus = statusFilter === 'ALL' || order.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const totalPieces = orders.reduce((sum, o) => sum + (o.total_quantity || 0), 0)
  const totalValue = orders.reduce((sum, o) => sum + (Number(o.total_quantity || 0) * Number(o.unit_price || 0)), 0)

  return (
    <ToolLayout
      toolName="Orders & TNA Tracking Suite"
      toolTag="Merchandising Suite"
      description="Manage buyer purchase orders, style master specifications, color/size quantity matrices, and delivery milestone approval gates (TNA)."
      actions={
        <div className="flex items-center gap-2">
          <button 
            onClick={() => loadData(true)}
            disabled={refreshing}
            className="p-1.5 rounded-lg border border-white/[0.08] bg-white/[0.03] hover:bg-white/[0.06] text-zinc-300 transition-colors"
            title="Refresh Orders"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-teal-400' : ''}`} />
          </button>

          <button 
            onClick={handleExportCsv}
            disabled={exporting}
            className="px-3 py-1.5 rounded-lg border border-white/[0.08] bg-white/[0.03] hover:bg-white/[0.06] text-zinc-300 text-xs font-medium inline-flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{exporting ? 'Exporting...' : 'Export CSV'}</span>
          </button>

          <button 
            onClick={() => setIsCreateOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-[#090a0f] font-semibold text-xs inline-flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Order</span>
          </button>
        </div>
      }
    >
      <div className="space-y-4">
        {/* Metric summary strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3 rounded-xl bg-[#0d0e14] border border-white/[0.06]">
            <div className="text-[10px] font-mono text-zinc-500 uppercase">Total Orders</div>
            <div className="text-base font-semibold text-white mt-0.5">{orders.length}</div>
            <div className="text-[11px] text-zinc-400">In PostgreSQL Supabase</div>
          </div>
          <div className="p-3 rounded-xl bg-[#0d0e14] border border-white/[0.06]">
            <div className="text-[10px] font-mono text-zinc-500 uppercase">Total Volume</div>
            <div className="text-base font-semibold text-teal-400 mt-0.5">{totalPieces.toLocaleString()} pcs</div>
            <div className="text-[11px] text-zinc-400">Contracted Units</div>
          </div>
          <div className="p-3 rounded-xl bg-[#0d0e14] border border-white/[0.06]">
            <div className="text-[10px] font-mono text-zinc-500 uppercase">Total Value</div>
            <div className="text-base font-semibold text-white mt-0.5">₹{(totalValue / 100000).toFixed(2)} Lakhs</div>
            <div className="text-[11px] text-zinc-400">Order Booking</div>
          </div>
          <div className="p-3 rounded-xl bg-[#0d0e14] border border-white/[0.06]">
            <div className="text-[10px] font-mono text-zinc-500 uppercase">Active Buyers</div>
            <div className="text-base font-semibold text-emerald-400 mt-0.5">{buyers.length || 3} Accounts</div>
            <div className="text-[11px] text-zinc-400">EU & UK Brands</div>
          </div>
        </div>

        {/* Search & Filter Bar */}
        <div className="p-3 rounded-xl bg-[#0d0e14] border border-white/[0.06] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
            <input 
              type="text" 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search Buyer PO #, Style Code, or Buyer Name..."
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-white/[0.08] bg-[#090a0f] text-white focus:outline-none focus:border-teal-500/50 transition-colors placeholder:text-zinc-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-zinc-400" />
            <div className="flex items-center gap-1 bg-[#090a0f] p-1 rounded-lg border border-white/[0.08]">
              {['ALL', 'CONFIRMED', 'IN_PRODUCTION', 'DRAFT'].map((s) => (
                <button
                  key={s}
                  onClick={() => setStatusFilter(s)}
                  className={`px-2 py-1 text-[11px] rounded-md font-medium transition-colors ${
                    statusFilter === s
                      ? 'bg-white/[0.1] text-white'
                      : 'text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
            <button 
              onClick={() => loadData(true)} 
              className="px-2.5 py-1 rounded bg-rose-500/20 hover:bg-rose-500/30 font-medium text-rose-200 transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading ? (
          <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-12 text-center text-xs text-zinc-400 space-y-2">
            <RefreshCw className="w-5 h-5 animate-spin mx-auto text-teal-400" />
            <p>Fetching orders from Supabase cloud database...</p>
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-12 text-center space-y-2.5">
            <div className="w-10 h-10 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20 flex items-center justify-center mx-auto text-sm">
              📋
            </div>
            <h4 className="text-xs font-semibold text-white">No Matching Orders Found</h4>
            <p className="text-xs text-zinc-400 max-w-sm mx-auto">
              Create an order using the <strong className="text-teal-400">New Order</strong> button or upload spreadsheets in <strong className="text-teal-400">Data Import</strong>.
            </p>
          </div>
        ) : (
          /* Orders Table */
          <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-white/[0.06] bg-white/[0.02] text-zinc-400 font-medium">
                    <th className="py-3 px-4">PO Number</th>
                    <th className="py-3 px-4">Buyer Account</th>
                    <th className="py-3 px-4">Style & Product</th>
                    <th className="py-3 px-4 text-right">Order Quantity</th>
                    <th className="py-3 px-4 text-right">Price</th>
                    <th className="py-3 px-4">Ex-Factory Date</th>
                    <th className="py-3 px-4">TNA Milestone Gates</th>
                    <th className="py-3 px-4 text-center">Status</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {filteredOrders.map((order) => {
                    const completedMilestones = (order.milestones || []).filter(m => m.status === 'COMPLETED').length
                    const totalMilestones = (order.milestones || []).length

                    return (
                      <tr 
                        key={order.id} 
                        className="hover:bg-white/[0.02] transition-colors group cursor-pointer"
                        onClick={() => setSelectedOrder(order)}
                      >
                        <td className="py-3 px-4 font-mono font-medium text-teal-300">
                          {order.order_number}
                        </td>
                        <td className="py-3 px-4 text-zinc-200">
                          <div className="font-medium">{order.buyer?.name || 'Buyer'}</div>
                          <div className="text-[11px] font-mono text-zinc-500">{order.buyer?.country || 'Export'}</div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-medium text-zinc-200">{order.style?.style_number || 'Style'}</div>
                          <div className="text-[11px] text-zinc-400">{order.style?.style_name || order.style?.garment_type}</div>
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-zinc-100 font-medium">
                          {order.total_quantity?.toLocaleString()} <span className="text-zinc-500 font-sans text-[11px]">pcs</span>
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-zinc-300">
                          ₹{Number(order.unit_price).toFixed(2)}
                        </td>
                        <td className="py-3 px-4 text-zinc-300 font-mono text-[11px]">
                          {order.ex_factory_date}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <div className="w-20 bg-white/[0.06] rounded-full h-1.5 overflow-hidden">
                              <div 
                                className="bg-teal-400 h-full rounded-full transition-all"
                                style={{ width: `${totalMilestones > 0 ? (completedMilestones / totalMilestones) * 100 : 0}%` }}
                              />
                            </div>
                            <span className="text-[11px] font-mono text-zinc-400">
                              {completedMilestones}/{totalMilestones}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wide border ${
                            order.status === 'CONFIRMED'
                              ? 'bg-teal-500/10 text-teal-400 border-teal-500/20'
                              : order.status === 'IN_PRODUCTION'
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                              : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
                          }`}>
                            {order.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button 
                            onClick={(e) => {
                              e.stopPropagation()
                              setSelectedOrder(order)
                            }}
                            className="p-1 rounded-md bg-white/[0.03] hover:bg-white/[0.08] text-zinc-300 group-hover:text-teal-400 transition-colors inline-flex items-center gap-1 text-xs"
                          >
                            <span>Inspect</span>
                            <ChevronRight className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* ORDER DETAILS & TNA DRAWER */}
      {selectedOrder && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="w-full max-w-xl bg-[#0c0d13] border-l border-white/[0.08] h-full flex flex-col shadow-2xl">
            {/* Drawer Header */}
            <div className="p-5 border-b border-white/[0.08] flex items-center justify-between bg-white/[0.01]">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-teal-500/10 text-teal-400 border border-teal-500/20">
                    {selectedOrder.status}
                  </span>
                  <span className="text-sm font-semibold font-mono text-white">
                    {selectedOrder.order_number}
                  </span>
                </div>
                <p className="text-xs text-zinc-400">
                  {selectedOrder.buyer?.name} • {selectedOrder.style?.style_number} ({selectedOrder.style?.style_name})
                </p>
              </div>
              <button 
                onClick={() => setSelectedOrder(null)}
                className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.06] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Drawer Content */}
            <div className="flex-1 overflow-y-auto p-5 space-y-6">
              {/* Order Metadata Cards */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
                  <div className="text-[10px] font-mono text-zinc-500 uppercase">Quantity</div>
                  <div className="text-sm font-semibold text-white mt-0.5">{selectedOrder.total_quantity?.toLocaleString()} pcs</div>
                </div>
                <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
                  <div className="text-[10px] font-mono text-zinc-500 uppercase">Unit Price</div>
                  <div className="text-sm font-semibold text-white mt-0.5">₹{Number(selectedOrder.unit_price).toFixed(2)}</div>
                </div>
                <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
                  <div className="text-[10px] font-mono text-zinc-500 uppercase">Ex-Factory</div>
                  <div className="text-xs font-semibold text-teal-400 mt-1 font-mono">{selectedOrder.ex_factory_date}</div>
                </div>
              </div>

              {/* Color & Size Breakdown */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-teal-400" />
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-200">
                    Color & Size Matrix
                  </h4>
                </div>

                {selectedOrder.lines && selectedOrder.lines.length > 0 ? (
                  <div className="rounded-lg bg-white/[0.02] border border-white/[0.05] overflow-hidden">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-white/[0.05] bg-white/[0.02] text-zinc-400 text-[11px]">
                          <th className="py-2 px-3">Colorway</th>
                          <th className="py-2 px-3">Size</th>
                          <th className="py-2 px-3 text-right">Quantity</th>
                          <th className="py-2 px-3 text-right">Share</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/[0.03]">
                        {selectedOrder.lines.map((line) => {
                          const pct = selectedOrder.total_quantity ? ((line.quantity / selectedOrder.total_quantity) * 100).toFixed(1) : 0
                          return (
                            <tr key={line.id}>
                              <td className="py-2 px-3 font-medium text-zinc-300">{line.color}</td>
                              <td className="py-2 px-3 font-mono text-zinc-400">{line.size}</td>
                              <td className="py-2 px-3 text-right font-mono text-zinc-200">{line.quantity.toLocaleString()}</td>
                              <td className="py-2 px-3 text-right font-mono text-zinc-500">{pct}%</td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="p-4 rounded-lg bg-white/[0.02] border border-white/[0.05] text-xs text-zinc-500 text-center">
                    No breakdown lines entered yet.
                  </div>
                )}
              </div>

              {/* TNA Milestone Checklist */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-teal-400" />
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-200">
                      TNA Delivery Gates
                    </h4>
                  </div>
                  <span className="text-[10px] text-zinc-400">Click to toggle gate status</span>
                </div>

                <div className="space-y-2">
                  {selectedOrder.milestones && selectedOrder.milestones.map((m) => {
                    const isDone = m.status === 'COMPLETED'
                    return (
                      <div 
                        key={m.id}
                        onClick={() => handleMilestoneStatusToggle(m)}
                        className={`p-3 rounded-lg border transition-all cursor-pointer flex items-center justify-between ${
                          isDone 
                            ? 'bg-emerald-500/[0.04] border-emerald-500/20 hover:border-emerald-500/40' 
                            : 'bg-white/[0.02] border-white/[0.05] hover:border-teal-500/30'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <button 
                            className={`w-5 h-5 rounded-md flex items-center justify-center transition-colors ${
                              isDone ? 'bg-emerald-500 text-zinc-950 font-bold' : 'border border-zinc-600 text-transparent hover:border-zinc-400'
                            }`}
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                          </button>
                          <div>
                            <div className={`text-xs font-medium ${isDone ? 'text-zinc-300 line-through' : 'text-zinc-100'}`}>
                              {m.name}
                            </div>
                            <div className="text-[10px] font-mono text-zinc-500 flex items-center gap-2 mt-0.5">
                              <span>Planned: {m.planned_date}</span>
                              {m.actual_date && <span className="text-emerald-400">Done: {m.actual_date}</span>}
                            </div>
                          </div>
                        </div>

                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase ${
                          isDone 
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                            : 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                        }`}>
                          {m.status}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* Drawer Footer */}
            <div className="p-4 border-t border-white/[0.08] bg-white/[0.01] flex items-center justify-between text-xs text-zinc-400">
              <span className="font-mono text-[11px]">Tenant: tirupur-demo</span>
              <button 
                onClick={() => setSelectedOrder(null)}
                className="px-3 py-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] text-zinc-200 transition-colors"
              >
                Close Drawer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CREATE ORDER MODAL */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-150">
          <div className="w-full max-w-lg bg-[#0d0e14] border border-white/[0.08] rounded-2xl shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-white/[0.06] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Package className="w-4 h-4 text-teal-400" />
                <h3 className="text-sm font-semibold text-white">Create Purchase Order</h3>
              </div>
              <button 
                onClick={() => setIsCreateOpen(false)}
                className="p-1 rounded text-zinc-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateOrderSubmit} className="p-5 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-zinc-400 font-medium">Buyer Account *</label>
                  <select 
                    value={newOrderForm.buyer_id} 
                    onChange={e => setNewOrderForm({ ...newOrderForm, buyer_id: e.target.value })}
                    required
                    className="w-full px-3 py-2 rounded-lg bg-[#090a0f] border border-white/[0.08] text-white focus:outline-none focus:border-teal-500"
                  >
                    <option value="">Select Buyer...</option>
                    {buyers.map(b => (
                      <option key={b.id} value={b.id}>{b.name} ({b.code})</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-zinc-400 font-medium">Style Master *</label>
                  <select 
                    value={newOrderForm.style_id} 
                    onChange={e => setNewOrderForm({ ...newOrderForm, style_id: e.target.value })}
                    required
                    className="w-full px-3 py-2 rounded-lg bg-[#090a0f] border border-white/[0.08] text-white focus:outline-none focus:border-teal-500"
                  >
                    <option value="">Select Style...</option>
                    {styles.map(s => (
                      <option key={s.id} value={s.id}>{s.style_number} - {s.style_name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <label className="text-zinc-400 font-medium">Buyer PO # *</label>
                  <input 
                    type="text" 
                    placeholder="e.g. PO-DEC-9941"
                    value={newOrderForm.order_number}
                    onChange={e => setNewOrderForm({ ...newOrderForm, order_number: e.target.value })}
                    required
                    className="w-full px-3 py-2 rounded-lg bg-[#090a0f] border border-white/[0.08] text-white font-mono focus:outline-none focus:border-teal-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-zinc-400 font-medium">Order Quantity *</label>
                  <input 
                    type="number" 
                    value={newOrderForm.total_quantity}
                    onChange={e => setNewOrderForm({ ...newOrderForm, total_quantity: parseInt(e.target.value) || 0 })}
                    required
                    className="w-full px-3 py-2 rounded-lg bg-[#090a0f] border border-white/[0.08] text-white font-mono focus:outline-none focus:border-teal-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-zinc-400 font-medium">Unit Price (INR) *</label>
                  <input 
                    type="number" 
                    step="0.01"
                    value={newOrderForm.unit_price}
                    onChange={e => setNewOrderForm({ ...newOrderForm, unit_price: parseFloat(e.target.value) || 0 })}
                    required
                    className="w-full px-3 py-2 rounded-lg bg-[#090a0f] border border-white/[0.08] text-white font-mono focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-zinc-400 font-medium">Planned Sewing Start</label>
                  <input 
                    type="date" 
                    value={newOrderForm.planned_sewing_start}
                    onChange={e => setNewOrderForm({ ...newOrderForm, planned_sewing_start: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-[#090a0f] border border-white/[0.08] text-white focus:outline-none focus:border-teal-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-zinc-400 font-medium">Ex-Factory Date *</label>
                  <input 
                    type="date" 
                    value={newOrderForm.ex_factory_date}
                    onChange={e => setNewOrderForm({ ...newOrderForm, ex_factory_date: e.target.value })}
                    required
                    className="w-full px-3 py-2 rounded-lg bg-[#090a0f] border border-white/[0.08] text-white focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-white/[0.06] flex items-center justify-end gap-2">
                <button 
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-3 py-2 rounded-lg border border-white/[0.08] text-zinc-300 hover:bg-white/[0.04] transition-colors"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 rounded-lg bg-teal-500 hover:bg-teal-400 text-zinc-950 font-semibold transition-colors disabled:opacity-50"
                >
                  {creating ? 'Saving...' : 'Create Order & Init TNA'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </ToolLayout>
  )
}
