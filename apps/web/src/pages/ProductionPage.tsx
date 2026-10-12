import React, { useEffect, useState } from 'react'
import { ToolLayout } from '../components/layout/ToolLayout'
import {
  Smartphone,
  Plus,
  RefreshCw,
  AlertTriangle,
  Activity,
  Layers,
  Clock,
  CheckCircle2,
  Calendar,
  X,
  TrendingDown,
  ArrowRight,
} from 'lucide-react'
import {
  fetchProductionLines,
  createProductionLine,
  fetchDailyProductionLogs,
  createDailyProductionLog,
  fetchOrders,
  fetchProductionRisks,
  ProductionLine,
  DailyProductionLog,
  Order,
  RiskAssessment,
} from '../lib/api'

export const ProductionPage: React.FC = () => {
  const [lines, setLines] = useState<ProductionLine[]>([])
  const [logs, setLogs] = useState<DailyProductionLog[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [risks, setRisks] = useState<RiskAssessment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [activeTab, setActiveTab] = useState<'lines' | 'orders' | 'risks' | 'logs'>('lines')

  // Modals
  const [isLogModalOpen, setIsLogModalOpen] = useState(false)
  const [isLineModalOpen, setIsLineModalOpen] = useState(false)

  // Log Form State
  const [logForm, setLogForm] = useState({
    date: new Date().toISOString().split('T')[0],
    order_id: '',
    line_id: '',
    stage: 'SEWING' as 'CUTTING' | 'SEWING' | 'FINISHING' | 'PACKING',
    planned_output: 500,
    actual_output: 480,
    rejected_qty: 12,
    operator_count: 24,
    working_hours: 8.0,
    notes: '',
  })

  // Line Form State
  const [lineForm, setLineForm] = useState({
    line_number: '',
    name: '',
    operator_count: 24,
    helper_count: 4,
    daily_working_hours: 8.0,
  })

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [linesData, logsData, ordersData, risksData] = await Promise.all([
        fetchProductionLines(),
        fetchDailyProductionLogs({ limit: 150 }),
        fetchOrders(),
        fetchProductionRisks(),
      ])
      setLines(linesData)
      setLogs(logsData)
      setOrders(ordersData)
      setRisks(risksData)

      if (ordersData.length > 0 && !logForm.order_id) {
        setLogForm((prev) => ({ ...prev, order_id: ordersData[0].id }))
      }
      if (linesData.length > 0 && !logForm.line_id) {
        setLogForm((prev) => ({ ...prev, line_id: linesData[0].id }))
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load production data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleCreateLog = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createDailyProductionLog({
        date: logForm.date,
        order_id: logForm.order_id,
        line_id: logForm.line_id || undefined,
        stage: logForm.stage,
        planned_output: Number(logForm.planned_output),
        actual_output: Number(logForm.actual_output),
        rejected_qty: Number(logForm.rejected_qty),
        operator_count: Number(logForm.operator_count),
        working_hours: Number(logForm.working_hours),
        notes: logForm.notes || undefined,
      })
      setIsLogModalOpen(false)
      loadData()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to submit production log')
    }
  }

  const handleCreateLine = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createProductionLine({
        line_number: lineForm.line_number,
        name: lineForm.name,
        operator_count: Number(lineForm.operator_count),
        helper_count: Number(lineForm.helper_count),
        daily_working_hours: Number(lineForm.daily_working_hours),
      })
      setIsLineModalOpen(false)
      setLineForm({
        line_number: '',
        name: '',
        operator_count: 24,
        helper_count: 4,
        daily_working_hours: 8.0,
      })
      loadData()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to create production line')
    }
  }

  // Aggregate Metrics
  const totalOperators = lines.reduce((sum, l) => sum + (l.is_active ? l.operator_count : 0), 0)
  const totalLogsCount = logs.length
  const totalActualOutput = logs.reduce((sum, l) => sum + l.actual_output, 0)
  const criticalRiskCount = risks.filter((r) => r.triggered && r.severity === 'CRITICAL').length
  const avgEfficiency =
    logs.length > 0
      ? (
          logs.reduce((sum, l) => sum + Number(l.efficiency_pct || 0), 0) /
          logs.filter((l) => Number(l.efficiency_pct) > 0).length || 1
        ).toFixed(1)
      : '0.0'

  // Selected Order for SAM Preview
  const selectedOrder = orders.find((o) => o.id === logForm.order_id)
  const styleSam = Number(selectedOrder?.style?.sam || 15.0)
  const previewProducedMin = Number(logForm.actual_output) * styleSam
  const previewAvailableMin = Number(logForm.operator_count) * Number(logForm.working_hours) * 60
  const previewEff =
    previewAvailableMin > 0 ? ((previewProducedMin / previewAvailableMin) * 100).toFixed(1) : '0.0'

  return (
    <ToolLayout
      toolName="Shop-Floor Production Logger"
      toolTag="Phase 5 · Floor Tracking & Risk Rule R3"
      description="Sub-30 second rapid mobile floor logging, Standard Allowed Minutes (SAM) efficiency math, and deterministic Rule R3 sewing pacing slippage evaluation."
      actions={
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => loadData()}
            className="p-1.5 sm:p-2 rounded-lg border border-white/[0.08] hover:bg-white/[0.04] text-zinc-400 hover:text-zinc-200 transition-colors"
            title="Refresh Data"
          >
            <RefreshCw className={`w-3.5 h-3.5 sm:w-4 sm:h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setIsLineModalOpen(true)}
            className="px-2.5 sm:px-3 py-1.5 rounded-lg border border-white/[0.12] text-xs font-medium text-zinc-200 hover:bg-white/[0.05] transition-colors flex items-center gap-1 sm:gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Line</span>
          </button>
          <button
            onClick={() => setIsLogModalOpen(true)}
            className="px-3 sm:px-3.5 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-sm shadow-teal-500/20"
          >
            <Smartphone className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">+ Quick Floor Log (30s)</span>
            <span className="sm:hidden">+ Quick Log</span>
          </button>
        </div>
      }
    >
      <div className="space-y-6">
        {/* KPI Top Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-4 space-y-1">
            <div className="flex items-center justify-between text-zinc-500 text-[10px] font-mono uppercase tracking-wider">
              <span>Active Lines & Capacity</span>
              <Activity className="w-3.5 h-3.5 text-zinc-400" />
            </div>
            <div className="text-2xl font-bold text-white tabular-nums">
              {lines.filter((l) => l.is_active).length} <span className="text-xs text-zinc-500 font-normal">Lines</span>
            </div>
            <div className="text-[11px] text-zinc-400">
              {totalOperators} registered floor operators
            </div>
          </div>

          <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-4 space-y-1">
            <div className="flex items-center justify-between text-zinc-500 text-[10px] font-mono uppercase tracking-wider">
              <span>Recorded Output</span>
              <Layers className="w-3.5 h-3.5 text-teal-400" />
            </div>
            <div className="text-2xl font-bold text-white tabular-nums">
              {totalActualOutput.toLocaleString()} <span className="text-xs text-zinc-500 font-normal">Pcs</span>
            </div>
            <div className="text-[11px] text-zinc-400">
              Across {totalLogsCount} logged floor shifts
            </div>
          </div>

          <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-4 space-y-1">
            <div className="flex items-center justify-between text-zinc-500 text-[10px] font-mono uppercase tracking-wider">
              <span>Average SAM Efficiency</span>
              <Clock className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-emerald-400 tabular-nums">
              {avgEfficiency}%
            </div>
            <div className="text-[11px] text-zinc-400">
              Calculated via Standard Allowed Minutes
            </div>
          </div>

          <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-4 space-y-1">
            <div className="flex items-center justify-between text-zinc-500 text-[10px] font-mono uppercase tracking-wider">
              <span>Active Pacing Flags (R3)</span>
              <AlertTriangle
                className={`w-3.5 h-3.5 ${criticalRiskCount > 0 ? 'text-amber-400' : 'text-emerald-400'}`}
              />
            </div>
            <div
              className={`text-2xl font-bold tabular-nums ${
                criticalRiskCount > 0 ? 'text-amber-400' : 'text-emerald-400'
              }`}
            >
              {criticalRiskCount}
            </div>
            <div className="text-[11px] text-zinc-400">
              {criticalRiskCount > 0
                ? 'Orders projected to miss Ex-Factory date'
                : 'All active orders pacing on schedule'}
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-white/[0.06] flex items-center justify-between">
          <div className="flex items-center gap-1">
            <button
              onClick={() => setActiveTab('lines')}
              className={`px-3.5 py-2.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === 'lines'
                  ? 'border-teal-500 text-teal-400 font-semibold'
                  : 'border-transparent text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Production Lines ({lines.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('orders')}
              className={`px-3.5 py-2.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === 'orders'
                  ? 'border-teal-500 text-teal-400 font-semibold'
                  : 'border-transparent text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Order Stage Progression ({orders.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('risks')}
              className={`px-3.5 py-2.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === 'risks'
                  ? 'border-amber-400 text-amber-400 font-semibold'
                  : 'border-transparent text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              <span>Deterministic Risk Rules</span>
              {criticalRiskCount > 0 && (
                <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-amber-500/20 text-amber-300 font-bold">
                  {criticalRiskCount}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('logs')}
              className={`px-3.5 py-2.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === 'logs'
                  ? 'border-teal-500 text-teal-400 font-semibold'
                  : 'border-transparent text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Calendar className="w-3.5 h-3.5" />
              <span>Daily Floor Logs ({logs.length})</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
            {error}
          </div>
        )}

        {/* Tab 1: Production Lines */}
        {activeTab === 'lines' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {lines.map((l) => (
              <div
                key={l.id}
                className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-4 space-y-3 hover:border-white/[0.12] transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-teal-500/10 text-teal-400 border border-teal-500/20">
                    {l.line_number}
                  </span>
                  <span
                    className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full ${
                      l.is_active
                        ? 'bg-emerald-500/10 text-emerald-400'
                        : 'bg-zinc-800 text-zinc-400'
                    }`}
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    {l.is_active ? 'Active' : 'Idle'}
                  </span>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">{l.name}</h4>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    {l.operator_count} Operators · {l.helper_count} Helpers
                  </p>
                </div>
                <div className="pt-2 border-t border-white/[0.05] flex items-center justify-between text-xs text-zinc-400">
                  <span>Shift Duration:</span>
                  <span className="text-white font-mono">{Number(l.daily_working_hours)} hrs/day</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tab 2: Order Progression Matrix */}
        {activeTab === 'orders' && (
          <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-white/[0.06] bg-white/[0.02] text-zinc-400 font-mono text-[11px] uppercase tracking-wider">
                    <th className="py-3 px-4">Order #</th>
                    <th className="py-3 px-4">Buyer & Style</th>
                    <th className="py-3 px-4">Total Qty</th>
                    <th className="py-3 px-4">Cutting</th>
                    <th className="py-3 px-4">Sewing (Main)</th>
                    <th className="py-3 px-4">Remaining</th>
                    <th className="py-3 px-4">Ex-Factory</th>
                    <th className="py-3 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {orders.map((ord) => {
                    const ordLogs = logs.filter((l) => l.order_id === ord.id)
                    const sewn = ordLogs
                      .filter((l) => l.stage === 'SEWING')
                      .reduce((sum, l) => sum + l.actual_output, 0)
                    const cut = ordLogs
                      .filter((l) => l.stage === 'CUTTING')
                      .reduce((sum, l) => sum + l.actual_output, 0)
                    const remaining = Math.max(0, ord.total_quantity - sewn)
                    const pct = Math.min(100, Math.round((sewn / ord.total_quantity) * 100))

                    return (
                      <tr key={ord.id} className="hover:bg-white/[0.02] transition-colors">
                        <td className="py-3.5 px-4 font-mono font-medium text-white">
                          {ord.order_number}
                        </td>
                        <td className="py-3.5 px-4 text-zinc-300">
                          <div className="font-medium text-white">{ord.buyer?.name || 'Direct Buyer'}</div>
                          <div className="text-[11px] text-zinc-500">
                            {ord.style?.style_name} (SAM: {ord.style?.sam || '15.0'})
                          </div>
                        </td>
                        <td className="py-3.5 px-4 font-mono font-bold text-white tabular-nums">
                          {ord.total_quantity.toLocaleString()} pcs
                        </td>
                        <td className="py-3.5 px-4 font-mono text-zinc-300 tabular-nums">
                          {cut.toLocaleString()} pcs
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-semibold text-teal-400 tabular-nums">
                              {sewn.toLocaleString()} pcs
                            </span>
                            <span className="text-[10px] text-zinc-500">({pct}%)</span>
                          </div>
                          <div className="w-28 h-1.5 rounded-full bg-white/[0.06] overflow-hidden mt-1">
                            <div
                              className="h-full bg-teal-500 rounded-full"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </td>
                        <td className="py-3.5 px-4 font-mono text-amber-400 tabular-nums">
                          {remaining.toLocaleString()} pcs
                        </td>
                        <td className="py-3.5 px-4 font-mono text-zinc-400">
                          {ord.ex_factory_date}
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-teal-500/10 text-teal-300 border border-teal-500/20">
                            {ord.status}
                          </span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: Risk Rules (R3 Pacing Slippage) */}
        {activeTab === 'risks' && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 text-xs text-amber-200/90 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <div className="font-semibold text-amber-300">
                  Deterministic Risk Rule Engine: Rule R3 (Sewing Run-Rate Slippage)
                </div>
                <p className="text-zinc-400 text-xs">
                  Pure mathematical evaluation with zero LLM math. Computes rolling 3-day sewing run
                  rate vs required daily output rate to meet target shipping dates.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {risks.map((r, i) => (
                <div
                  key={i}
                  className={`rounded-xl border p-5 space-y-4 ${
                    r.severity === 'CRITICAL'
                      ? 'bg-rose-950/20 border-rose-500/30'
                      : r.severity === 'HIGH'
                        ? 'bg-amber-950/20 border-amber-500/30'
                        : 'bg-[#0d0e14] border-white/[0.06]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-1 rounded text-xs font-mono font-bold bg-white/[0.05] text-white">
                        {r.order_number}
                      </span>
                      <span className="text-xs text-zinc-400">{r.buyer_name}</span>
                    </div>
                    <span
                      className={`px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider ${
                        r.severity === 'CRITICAL'
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : r.severity === 'HIGH'
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                            : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      }`}
                    >
                      {r.severity}
                    </span>
                  </div>

                  <div className="space-y-1.5">
                    <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                      {r.triggered ? (
                        <TrendingDown className="w-4 h-4 text-amber-400" />
                      ) : (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      )}
                      <span>{r.headline}</span>
                    </h4>
                    <p className="text-xs text-zinc-300 leading-relaxed">{r.explanation}</p>
                  </div>

                  {r.evidence && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-white/[0.05]">
                      <div className="p-2 rounded bg-black/30 border border-white/[0.04]">
                        <div className="text-[10px] text-zinc-500 uppercase font-mono">
                          Remaining Unsewn
                        </div>
                        <div className="text-xs font-bold text-white font-mono">
                          {Number(r.evidence.remaining_qty || 0).toLocaleString()} pcs
                        </div>
                      </div>
                      <div className="p-2 rounded bg-black/30 border border-white/[0.04]">
                        <div className="text-[10px] text-zinc-500 uppercase font-mono">
                          Current Daily Pace
                        </div>
                        <div className="text-xs font-bold text-teal-400 font-mono">
                          {String(r.evidence.actual_daily_rate ?? '0')} pcs/day
                        </div>
                      </div>
                      <div className="p-2 rounded bg-black/30 border border-white/[0.04]">
                        <div className="text-[10px] text-zinc-500 uppercase font-mono">
                          Required Daily Pace
                        </div>
                        <div className="text-xs font-bold text-amber-400 font-mono">
                          {String(r.evidence.required_daily_rate ?? '0')} pcs/day
                        </div>
                      </div>
                      <div className="p-2 rounded bg-black/30 border border-white/[0.04]">
                        <div className="text-[10px] text-zinc-500 uppercase font-mono">
                          Forecast Delay
                        </div>
                        <div className="text-xs font-bold text-rose-400 font-mono">
                          {r.days_delayed > 0 ? `+${r.days_delayed} days late` : 'On Schedule'}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 4: Daily Floor Logs Stream */}
        {activeTab === 'logs' && (
          <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-white/[0.06] bg-white/[0.02] text-zinc-400 font-mono text-[11px] uppercase tracking-wider">
                    <th className="py-3 px-4">Date</th>
                    <th className="py-3 px-4">Stage</th>
                    <th className="py-3 px-4">Planned Output</th>
                    <th className="py-3 px-4">Actual Output</th>
                    <th className="py-3 px-4">Defects</th>
                    <th className="py-3 px-4">Produced (SAM)</th>
                    <th className="py-3 px-4">Available Min</th>
                    <th className="py-3 px-4">Line Efficiency</th>
                    <th className="py-3 px-4">Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {logs.map((log) => {
                    const eff = Number(log.efficiency_pct || 0)
                    return (
                      <tr key={log.id} className="hover:bg-white/[0.02] transition-colors">
                        <td className="py-3 px-4 font-mono text-zinc-400 whitespace-nowrap">
                          {log.date}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                              log.stage === 'SEWING'
                                ? 'bg-teal-500/10 text-teal-400 border border-teal-500/20'
                                : log.stage === 'CUTTING'
                                  ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                                  : 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                            }`}
                          >
                            {log.stage}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono text-zinc-400 tabular-nums">
                          {log.planned_output.toLocaleString()}
                        </td>
                        <td className="py-3 px-4 font-mono font-bold text-white tabular-nums">
                          {log.actual_output.toLocaleString()}
                        </td>
                        <td className="py-3 px-4 font-mono text-rose-400 tabular-nums">
                          {log.rejected_qty} ({log.rejection_rate_pct}%)
                        </td>
                        <td className="py-3 px-4 font-mono text-zinc-300 tabular-nums">
                          {Number(log.produced_minutes).toLocaleString()}m
                        </td>
                        <td className="py-3 px-4 font-mono text-zinc-400 tabular-nums">
                          {Number(log.available_minutes).toLocaleString()}m
                        </td>
                        <td className="py-3 px-4 font-mono font-bold tabular-nums">
                          <span
                            className={
                              eff >= 65
                                ? 'text-emerald-400'
                                : eff >= 50
                                  ? 'text-teal-400'
                                  : 'text-amber-400'
                            }
                          >
                            {eff}%
                          </span>
                        </td>
                        <td className="py-3 px-4 text-zinc-400 max-w-xs truncate">
                          {log.notes || '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Modal: Record Daily Log (<30s Entry) */}
        {isLogModalOpen && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0e0f16] border border-white/[0.1] rounded-2xl w-full max-w-lg p-6 space-y-5 shadow-2xl">
              <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
                <div className="flex items-center gap-2">
                  <Smartphone className="w-5 h-5 text-teal-400" />
                  <div>
                    <h3 className="text-base font-semibold text-white">Quick Floor Log Entry</h3>
                    <p className="text-xs text-zinc-400">Rapid 30-second mobile entry for shift supervisors</p>
                  </div>
                </div>
                <button
                  onClick={() => setIsLogModalOpen(false)}
                  className="p-1 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.05]"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleCreateLog} className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-zinc-300">Production Date</label>
                    <input
                      type="date"
                      value={logForm.date}
                      onChange={(e) => setLogForm({ ...logForm, date: e.target.value })}
                      className="w-full text-xs rounded-lg border border-white/[0.08] p-2 bg-[#08090e] text-white focus:outline-none focus:border-teal-500/50"
                      required
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-zinc-300">Floor Stage</label>
                    <select
                      value={logForm.stage}
                      onChange={(e) =>
                        setLogForm({
                          ...logForm,
                          stage: e.target.value as 'CUTTING' | 'SEWING' | 'FINISHING' | 'PACKING',
                        })
                      }
                      className="w-full text-xs rounded-lg border border-white/[0.08] p-2 bg-[#08090e] text-white focus:outline-none focus:border-teal-500/50"
                    >
                      <option value="CUTTING">Cutting</option>
                      <option value="SEWING">Sewing (Assembly)</option>
                      <option value="FINISHING">Finishing</option>
                      <option value="PACKING">Packing & Cartoning</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-zinc-300">Order</label>
                  <select
                    value={logForm.order_id}
                    onChange={(e) => setLogForm({ ...logForm, order_id: e.target.value })}
                    className="w-full text-xs rounded-lg border border-white/[0.08] p-2 bg-[#08090e] text-white focus:outline-none focus:border-teal-500/50"
                    required
                  >
                    {orders.map((o) => (
                      <option key={o.id} value={o.id}>
                        {o.order_number} · {o.buyer?.name} · {o.style?.style_name} ({o.total_quantity} pcs)
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-zinc-300">Production Line</label>
                    <select
                      value={logForm.line_id}
                      onChange={(e) => setLogForm({ ...logForm, line_id: e.target.value })}
                      className="w-full text-xs rounded-lg border border-white/[0.08] p-2 bg-[#08090e] text-white focus:outline-none focus:border-teal-500/50"
                    >
                      <option value="">No line (Floor wide)</option>
                      {lines.map((l) => (
                        <option key={l.id} value={l.id}>
                          {l.line_number} · {l.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-zinc-300">Operators Count</label>
                    <input
                      type="number"
                      value={logForm.operator_count}
                      onChange={(e) => setLogForm({ ...logForm, operator_count: Number(e.target.value) })}
                      className="w-full text-xs rounded-lg border border-white/[0.08] p-2 bg-[#08090e] text-white focus:outline-none focus:border-teal-500/50"
                      min={1}
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-zinc-300">Actual Passed (Pcs)</label>
                    <input
                      type="number"
                      value={logForm.actual_output}
                      onChange={(e) => setLogForm({ ...logForm, actual_output: Number(e.target.value) })}
                      className="w-full text-xs rounded-lg border border-teal-500/40 p-2 bg-[#08090e] text-teal-300 font-mono font-bold focus:outline-none"
                      min={0}
                      required
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-zinc-300">Defects / Rejections</label>
                    <input
                      type="number"
                      value={logForm.rejected_qty}
                      onChange={(e) => setLogForm({ ...logForm, rejected_qty: Number(e.target.value) })}
                      className="w-full text-xs rounded-lg border border-white/[0.08] p-2 bg-[#08090e] text-rose-300 font-mono focus:outline-none"
                      min={0}
                      required
                    />
                  </div>
                </div>

                {/* Live SAM Math Preview Card */}
                <div className="p-3 rounded-lg bg-teal-500/5 border border-teal-500/20 text-xs space-y-1">
                  <div className="flex items-center justify-between text-zinc-400">
                    <span>Style SAM: {styleSam} min</span>
                    <span>Produced: {previewProducedMin.toLocaleString()}m</span>
                  </div>
                  <div className="flex items-center justify-between text-zinc-400">
                    <span>Available Capacity ({logForm.operator_count} ops × 8h):</span>
                    <span>{previewAvailableMin.toLocaleString()}m</span>
                  </div>
                  <div className="pt-1 border-t border-teal-500/20 flex items-center justify-between font-bold text-teal-300">
                    <span>Calculated Line Efficiency:</span>
                    <span className="text-sm font-mono">{previewEff}%</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-zinc-300">Supervisor Floor Notes</label>
                  <input
                    type="text"
                    value={logForm.notes}
                    onChange={(e) => setLogForm({ ...logForm, notes: e.target.value })}
                    placeholder="e.g. Neck rib attach bottleneck, machine 4 needle breakage"
                    className="w-full text-xs rounded-lg border border-white/[0.08] p-2 bg-[#08090e] text-white focus:outline-none focus:border-teal-500/50"
                  />
                </div>

                <div className="pt-3 flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setIsLogModalOpen(false)}
                    className="px-4 py-2 rounded-lg border border-white/[0.1] text-xs font-medium text-zinc-300 hover:bg-white/[0.05]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold text-xs flex items-center gap-1.5 shadow-md shadow-teal-500/20"
                  >
                    <span>Confirm & Commit Output</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Add Production Line */}
        {isLineModalOpen && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#0e0f16] border border-white/[0.1] rounded-2xl w-full max-w-md p-6 space-y-5 shadow-2xl">
              <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
                <h3 className="text-base font-semibold text-white">Add Factory Production Line</h3>
                <button
                  onClick={() => setIsLineModalOpen(false)}
                  className="p-1 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.05]"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleCreateLine} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-zinc-300">Line Number / Code</label>
                  <input
                    type="text"
                    value={lineForm.line_number}
                    onChange={(e) => setLineForm({ ...lineForm, line_number: e.target.value })}
                    placeholder="e.g. Line 5"
                    className="w-full text-xs rounded-lg border border-white/[0.08] p-2 bg-[#08090e] text-white focus:outline-none focus:border-teal-500/50"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-zinc-300">Line Name / Description</label>
                  <input
                    type="text"
                    value={lineForm.name}
                    onChange={(e) => setLineForm({ ...lineForm, name: e.target.value })}
                    placeholder="e.g. Sportswear Sewing Line 5"
                    className="w-full text-xs rounded-lg border border-white/[0.08] p-2 bg-[#08090e] text-white focus:outline-none focus:border-teal-500/50"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-zinc-300">Operators</label>
                    <input
                      type="number"
                      value={lineForm.operator_count}
                      onChange={(e) => setLineForm({ ...lineForm, operator_count: Number(e.target.value) })}
                      className="w-full text-xs rounded-lg border border-white/[0.08] p-2 bg-[#08090e] text-white focus:outline-none focus:border-teal-500/50"
                      min={1}
                      required
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-zinc-300">Helpers</label>
                    <input
                      type="number"
                      value={lineForm.helper_count}
                      onChange={(e) => setLineForm({ ...lineForm, helper_count: Number(e.target.value) })}
                      className="w-full text-xs rounded-lg border border-white/[0.08] p-2 bg-[#08090e] text-white focus:outline-none focus:border-teal-500/50"
                      min={0}
                      required
                    />
                  </div>
                </div>

                <div className="pt-3 flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setIsLineModalOpen(false)}
                    className="px-4 py-2 rounded-lg border border-white/[0.1] text-xs font-medium text-zinc-300 hover:bg-white/[0.05]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold text-xs flex items-center gap-1.5 shadow-md shadow-teal-500/20"
                  >
                    <span>Register Line</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </ToolLayout>
  )
}
