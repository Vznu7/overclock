import React, { useState, useEffect } from 'react'
import { ToolLayout } from '../components/layout/ToolLayout'
import { 
  Truck, 
  Plus, 
  AlertTriangle, 
  ArrowDownLeft, 
  ArrowUpRight, 
  Scale, 
  RefreshCw,
  Building2,
  X
} from 'lucide-react'
import { 
  fetchJobworkProcessors, 
  fetchJobworkChallans, 
  fetchJobworkRisks, 
  issueJobworkChallan, 
  receiveJobworkChallan,
  JobworkProcessor, 
  JobworkChallan, 
  RiskAssessment,
  JobworkChallanCreate,
  JobworkChallanReceive,
  fetchOrders,
  Order
} from '../lib/api'

export const JobworkPage: React.FC = () => {
  const [processors, setProcessors] = useState<JobworkProcessor[]>([])
  const [challans, setChallans] = useState<JobworkChallan[]>([])
  const [jwRisks, setJwRisks] = useState<RiskAssessment[]>([])
  const [orders, setOrders] = useState<Order[]>([])

  // Modals
  const [isIssueModalOpen, setIsIssueModalOpen] = useState<boolean>(false)
  const [isReceiveModalOpen, setIsReceiveModalOpen] = useState<boolean>(false)
  const [selectedChallanForReceive, setSelectedChallanForReceive] = useState<JobworkChallan | null>(null)

  // Form states
  const [issueForm, setIssueForm] = useState<JobworkChallanCreate>({
    challan_number: `DC-OUT-${Math.floor(1000 + Math.random() * 9000)}`,
    processor_id: '',
    order_id: '',
    process_name: 'Dyeing & Bio-Wash',
    material_description: 'Combed Cotton Single Jersey 160 GSM',
    issued_qty: 1000,
    issued_weight_kg: 200,
    expected_return_date: new Date(Date.now() + 3 * 86400000).toISOString().split('T')[0],
    notes: '',
  })

  const [receiveForm, setReceiveForm] = useState<JobworkChallanReceive>({
    received_qty: 1000,
    received_weight_kg: 195,
    actual_return_date: new Date().toISOString().split('T')[0],
    notes: '',
  })

  const loadData = async () => {
    try {
      const [procsData, challansData, risksData, ordersData] = await Promise.all([
        fetchJobworkProcessors().catch(() => []),
        fetchJobworkChallans().catch(() => []),
        fetchJobworkRisks().catch(() => []),
        fetchOrders().catch(() => []),
      ])
      setProcessors(procsData)
      setChallans(challansData)
      setJwRisks(risksData)
      setOrders(ordersData)
      if (procsData.length > 0 && !issueForm.processor_id) {
        setIssueForm(prev => ({ ...prev, processor_id: procsData[0].id }))
      }
      if (ordersData.length > 0 && !issueForm.order_id) {
        setIssueForm(prev => ({ ...prev, order_id: ordersData[0].id }))
      }
    } catch (err) {
      console.error('Failed to load Job-Work hub telemetry:', err)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleIssueSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await issueJobworkChallan(issueForm)
      setIsIssueModalOpen(false)
      loadData()
    } catch (err: any) {
      alert(err.message || 'Failed to issue challan')
    }
  }

  const handleReceiveSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedChallanForReceive) return
    try {
      await receiveJobworkChallan(selectedChallanForReceive.id, receiveForm)
      setIsReceiveModalOpen(false)
      setSelectedChallanForReceive(null)
      loadData()
    } catch (err: any) {
      alert(err.message || 'Failed to record receipt')
    }
  }

  const openReceiveModal = (challan: JobworkChallan) => {
    setSelectedChallanForReceive(challan)
    setReceiveForm({
      received_qty: challan.issued_qty,
      received_weight_kg: Number(challan.issued_weight_kg) * 0.96, // default ~4% loss test
      actual_return_date: new Date().toISOString().split('T')[0],
      notes: '',
    })
    setIsReceiveModalOpen(true)
  }

  // Computed metrics
  const activeVendorsCount = processors.length
  const openChallans = challans.filter(c => c.status === 'ISSUED' || c.status === 'PARTIAL_RECEIVED')
  const openWeightKg = openChallans.reduce((sum, c) => sum + Number(c.issued_weight_kg), 0)
  const lossAnomaliesCount = challans.filter(c => c.is_loss_anomaly).length
  const triggeredRisksCount = jwRisks.filter(r => r.triggered).length

  return (
    <ToolLayout
      toolName="Outside Job-Work Processor Hub"
      toolTag="Finishing Network & Rule R4"
      description="Track outward fabric lots to external dyers and rotary screen printers, inward garment receipts, and automatically calculate process shrinkage loss % with Rule R4 anomaly detection."
      actions={
        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            className="px-3 py-1.5 rounded-full border border-white/[0.08] bg-white/[0.03] hover:bg-white/[0.06] text-zinc-300 text-xs font-medium inline-flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Sync Hub</span>
          </button>
          <button
            onClick={() => setIsIssueModalOpen(true)}
            className="px-4 py-1.5 rounded-full bg-emerald-500 hover:bg-emerald-400 text-[#090a0f] font-bold text-xs inline-flex items-center gap-1.5 transition-all shadow-sm shadow-emerald-500/20"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Issue Outward Challan</span>
          </button>
        </div>
      }
    >
      <div className="space-y-6">

        {/* 1. TOP METRICS STRIP */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          <div className="rounded-2xl bg-[#0c0d15] border border-white/[0.06] p-4.5 space-y-1">
            <div className="text-[10px] font-mono text-zinc-500 uppercase flex items-center justify-between">
              <span>Partner Finishing Units</span>
              <Building2 className="w-3.5 h-3.5 text-zinc-400" />
            </div>
            <div className="text-2xl font-bold text-white tabular-nums">
              {activeVendorsCount} Vendors
            </div>
            <div className="text-[11px] text-zinc-400">Dyeing, Screen Print, Bio-Wash</div>
          </div>

          <div className="rounded-2xl bg-[#0c0d15] border border-white/[0.06] p-4.5 space-y-1">
            <div className="text-[10px] font-mono text-zinc-500 uppercase flex items-center justify-between">
              <span>Open Outward Lots</span>
              <ArrowUpRight className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold text-cyan-300 tabular-nums">
              {openChallans.length} Challans
            </div>
            <div className="text-[11px] text-zinc-400">{openWeightKg.toFixed(1)} kg material in transit</div>
          </div>

          <div className="rounded-2xl bg-[#0c0d15] border border-white/[0.06] p-4.5 space-y-1">
            <div className="text-[10px] font-mono text-zinc-500 uppercase flex items-center justify-between">
              <span>Process Loss Tolerance</span>
              <Scale className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-amber-400 tabular-nums">
              3.5% Cap
            </div>
            <div className="text-[11px] text-zinc-400">Tiruppur cluster standard tolerance</div>
          </div>

          <div className="rounded-2xl bg-[#0c0d15] border border-white/[0.06] p-4.5 space-y-1">
            <div className="text-[10px] font-mono text-zinc-500 uppercase flex items-center justify-between">
              <span>Rule R4 Breaches</span>
              <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
            </div>
            <div className="text-2xl font-bold text-red-400 tabular-nums">
              {triggeredRisksCount} Orders Flagged
            </div>
            <div className="text-[11px] text-red-300/80">{lossAnomaliesCount} lot(s) exceeding shrinkage limit</div>
          </div>
        </div>

        {/* 2. RULE R4 RISK RADAR CARD */}
        {triggeredRisksCount > 0 && (
          <div className="rounded-2xl bg-red-950/20 border border-red-500/30 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="p-1 rounded-lg bg-red-500/20 text-red-400">
                  <AlertTriangle className="w-4 h-4" />
                </span>
                <div>
                  <h4 className="text-xs font-bold text-red-200">
                    Rule R4 Active Trigger: Outside Job-Work Discrepancy & Anomaly Detected
                  </h4>
                  <p className="text-[11px] text-zinc-400">
                    Deterministic calculation flagged outside processing delay or weight loss higher than 3.50%.
                  </p>
                </div>
              </div>
              <span className="px-2.5 py-0.5 rounded-full bg-red-500/20 text-red-300 text-[10px] font-mono uppercase tracking-wider">
                CRITICAL INTERVENTION
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 pt-1">
              {jwRisks.filter(r => r.triggered).map((risk, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-black/40 border border-red-500/20 text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white">{risk.order_number}</span>
                    <span className="text-[10px] font-mono text-red-400">{risk.buyer_name}</span>
                  </div>
                  <p className="text-zinc-300 text-[11px] leading-relaxed">
                    {risk.headline}
                  </p>
                  <p className="text-[10px] text-zinc-400">
                    {risk.explanation}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 3. DELIVERY CHALLANS LEDGER TABLE */}
        <div className="rounded-2xl bg-[#0c0d15] border border-white/[0.06] overflow-hidden space-y-3 p-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Truck className="w-4 h-4 text-emerald-400" />
                <span>Job-Work Delivery Challans & Weight Loss Ledger</span>
              </h3>
              <p className="text-xs text-zinc-400">
                Track material sent for external processes (inward weight vs outward weight reconciliation)
              </p>
            </div>
            <span className="text-xs font-mono text-zinc-500">
              {challans.length} Total Records
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-white/[0.08] text-[10px] font-mono text-zinc-400 uppercase tracking-wider">
                  <th className="py-2.5 px-3">Challan No</th>
                  <th className="py-2.5 px-3">Processor / Unit</th>
                  <th className="py-2.5 px-3">Process Name</th>
                  <th className="py-2.5 px-3">Issued (kg)</th>
                  <th className="py-2.5 px-3">Expected Return</th>
                  <th className="py-2.5 px-3">Received (kg)</th>
                  <th className="py-2.5 px-3">Weight Loss %</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {challans.map((c) => {
                  const isIssued = c.status === 'ISSUED'
                  return (
                    <tr key={c.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3 px-3 font-mono font-medium text-white">
                        {c.challan_number}
                      </td>
                      <td className="py-3 px-3 text-zinc-300">
                        {c.processor_name}
                      </td>
                      <td className="py-3 px-3 text-zinc-400">
                        {c.process_name}
                      </td>
                      <td className="py-3 px-3 font-mono text-zinc-200">
                        {Number(c.issued_weight_kg).toFixed(1)} kg
                      </td>
                      <td className="py-3 px-3 text-zinc-400">
                        {c.expected_return_date}
                      </td>
                      <td className="py-3 px-3 font-mono text-zinc-200">
                        {Number(c.received_weight_kg) > 0 ? `${Number(c.received_weight_kg).toFixed(1)} kg` : '—'}
                      </td>
                      <td className="py-3 px-3">
                        {Number(c.received_weight_kg) > 0 ? (
                          <span className={`inline-flex items-center gap-1 font-mono font-semibold ${
                            c.is_loss_anomaly ? 'text-red-400' : 'text-emerald-400'
                          }`}>
                            {Number(c.weight_loss_pct).toFixed(2)}%
                            {c.is_loss_anomaly && (
                              <span className="text-[9px] px-1 py-0.2 rounded bg-red-500/20 border border-red-500/30 uppercase">
                                Anomaly
                              </span>
                            )}
                          </span>
                        ) : (
                          <span className="text-zinc-600 font-mono">Pending</span>
                        )}
                      </td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono uppercase tracking-wider ${
                          c.status === 'COMPLETED'
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                            : c.status === 'ISSUED'
                            ? 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
                            : 'bg-zinc-500/10 text-zinc-400'
                        }`}>
                          {c.status}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right">
                        {isIssued ? (
                          <button
                            onClick={() => openReceiveModal(c)}
                            className="px-2.5 py-1 rounded-lg bg-teal-500/15 hover:bg-teal-500/25 text-teal-300 border border-teal-500/30 font-medium transition-colors text-xs"
                          >
                            Receive Inward
                          </button>
                        ) : (
                          <span className="text-[11px] text-zinc-500">Reconciled</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* 4. PROCESSORS DIRECTORY */}
        <div className="rounded-2xl bg-[#0c0d15] border border-white/[0.06] p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Building2 className="w-4 h-4 text-cyan-400" />
                <span>Registered Outside Finishing Units</span>
              </h3>
              <p className="text-xs text-zinc-400">
                Authorized job-work vendors with standard Tiruppur operating agreements
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {processors.map((p) => (
              <div key={p.id} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] space-y-2">
                <div className="flex items-start justify-between">
                  <h4 className="text-xs font-bold text-white leading-tight">
                    {p.name}
                  </h4>
                  <span className="px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 text-[9px] font-mono">
                    {p.process_type}
                  </span>
                </div>
                <div className="text-[11px] text-zinc-400 space-y-0.5">
                  <div>Contact: {p.contact_person || 'N/A'}</div>
                  <div>Phone: {p.phone || 'N/A'}</div>
                  <div className="text-[10px] text-zinc-500 truncate">{p.address || 'Tirupur Cluster'}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* ISSUE MODAL */}
      {isIssueModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-100">
          <div className="w-full max-w-lg bg-[#0e0f18] border border-white/[0.12] rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400">
                  <Truck className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-white">Issue Outward Delivery Challan</h3>
              </div>
              <button onClick={() => setIsIssueModalOpen(false)} className="text-zinc-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleIssueSubmit} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-zinc-400 block mb-1">Challan Number</label>
                  <input
                    type="text"
                    required
                    value={issueForm.challan_number}
                    onChange={(e) => setIssueForm({ ...issueForm, challan_number: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 block mb-1">Finishing Vendor</label>
                  <select
                    value={issueForm.processor_id}
                    onChange={(e) => setIssueForm({ ...issueForm, processor_id: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg bg-zinc-900 border border-white/[0.08] text-white"
                  >
                    {processors.map(p => (
                      <option key={p.id} value={p.id}>{p.name} ({p.process_type})</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-zinc-400 block mb-1">Linked Export Order</label>
                <select
                  value={issueForm.order_id || ''}
                  onChange={(e) => setIssueForm({ ...issueForm, order_id: e.target.value })}
                  className="w-full px-3 py-1.5 rounded-lg bg-zinc-900 border border-white/[0.08] text-white"
                >
                  {orders.map(o => (
                    <option key={o.id} value={o.id}>{o.order_number} ({o.total_quantity} pcs)</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-zinc-400 block mb-1">Process Name</label>
                  <input
                    type="text"
                    required
                    value={issueForm.process_name}
                    onChange={(e) => setIssueForm({ ...issueForm, process_name: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 block mb-1">Expected Return Date</label>
                  <input
                    type="date"
                    required
                    value={issueForm.expected_return_date}
                    onChange={(e) => setIssueForm({ ...issueForm, expected_return_date: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-zinc-400 block mb-1">Issued Quantity (Pieces/Meters)</label>
                  <input
                    type="number"
                    step="0.001"
                    required
                    value={issueForm.issued_qty}
                    onChange={(e) => setIssueForm({ ...issueForm, issued_qty: Number(e.target.value) })}
                    className="w-full px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white font-mono"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 block mb-1">Issued Net Weight (kg)</label>
                  <input
                    type="number"
                    step="0.001"
                    required
                    value={issueForm.issued_weight_kg}
                    onChange={(e) => setIssueForm({ ...issueForm, issued_weight_kg: Number(e.target.value) })}
                    className="w-full px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="text-zinc-400 block mb-1">Material Description</label>
                <input
                  type="text"
                  required
                  value={issueForm.material_description}
                  onChange={(e) => setIssueForm({ ...issueForm, material_description: e.target.value })}
                  className="w-full px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsIssueModalOpen(false)}
                  className="px-3.5 py-1.5 rounded-lg bg-white/[0.05] text-zinc-300 hover:bg-white/[0.1]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black font-bold"
                >
                  Issue Challan
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* RECEIVE MODAL */}
      {isReceiveModalOpen && selectedChallanForReceive && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-100">
          <div className="w-full max-w-md bg-[#0e0f18] border border-white/[0.12] rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-teal-500/10 text-teal-400">
                  <ArrowDownLeft className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-white">Record Inward Receipt</h3>
              </div>
              <button onClick={() => setIsReceiveModalOpen(false)} className="text-zinc-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] text-xs space-y-1">
              <div className="font-semibold text-white">Challan: {selectedChallanForReceive.challan_number}</div>
              <div className="text-zinc-400">Processor: {selectedChallanForReceive.processor_name}</div>
              <div className="text-zinc-400 font-mono">Issued Weight: {Number(selectedChallanForReceive.issued_weight_kg).toFixed(1)} kg</div>
            </div>

            <form onSubmit={handleReceiveSubmit} className="space-y-3.5 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-zinc-400 block mb-1">Received Qty</label>
                  <input
                    type="number"
                    step="0.001"
                    required
                    value={receiveForm.received_qty}
                    onChange={(e) => setReceiveForm({ ...receiveForm, received_qty: Number(e.target.value) })}
                    className="w-full px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white font-mono"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 block mb-1">Received Weight (kg)</label>
                  <input
                    type="number"
                    step="0.001"
                    required
                    value={receiveForm.received_weight_kg}
                    onChange={(e) => setReceiveForm({ ...receiveForm, received_weight_kg: Number(e.target.value) })}
                    className="w-full px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white font-mono"
                  />
                </div>
              </div>

              {/* Instantaneous weight loss calculation preview */}
              {(() => {
                const issuedW = Number(selectedChallanForReceive.issued_weight_kg)
                const recW = Number(receiveForm.received_weight_kg)
                const lossKg = Math.max(0, issuedW - recW)
                const lossPct = issuedW > 0 ? (lossKg / issuedW) * 100 : 0
                const isAnomaly = lossPct > 3.50

                return (
                  <div className={`p-3 rounded-xl border ${
                    isAnomaly ? 'bg-red-500/10 border-red-500/30' : 'bg-emerald-500/10 border-emerald-500/20'
                  }`}>
                    <div className="flex items-center justify-between font-mono font-semibold">
                      <span className={isAnomaly ? 'text-red-300' : 'text-emerald-300'}>
                        Calculated Process Loss: {lossPct.toFixed(2)}% ({lossKg.toFixed(1)} kg)
                      </span>
                      {isAnomaly && (
                        <span className="text-[10px] text-red-400 px-1.5 py-0.5 rounded bg-red-500/20">
                          Above 3.5% Cap
                        </span>
                      )}
                    </div>
                    {isAnomaly && (
                      <p className="text-[11px] text-red-300/80 mt-1">
                        Warning: This will trigger a Rule R4 anomaly alert on the Executive Control Tower!
                      </p>
                    )}
                  </div>
                )
              })()}

              <div>
                <label className="text-zinc-400 block mb-1">Receipt Notes / Shrinkage Reason</label>
                <textarea
                  rows={2}
                  value={receiveForm.notes || ''}
                  onChange={(e) => setReceiveForm({ ...receiveForm, notes: e.target.value })}
                  placeholder="e.g. Normal 2.5% relaxation shrinkage in bio-wash"
                  className="w-full px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-white resize-none"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsReceiveModalOpen(false)}
                  className="px-3.5 py-1.5 rounded-lg bg-white/[0.05] text-zinc-300 hover:bg-white/[0.1]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-black font-bold"
                >
                  Confirm Receipt
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </ToolLayout>
  )
}
