import React, { useState, useEffect } from 'react'
import { ToolLayout } from '../components/layout/ToolLayout'
import { 
  AlertTriangle, 
  Clock, 
  Scissors, 
  Truck, 
  ArrowUpRight, 
  RefreshCw, 
  ShieldAlert, 
  CheckCircle2, 
  ExternalLink,
  ChevronRight,
  X
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { 
  fetchUnifiedRiskMatrix, 
  fetchOrders, 
  OrderRiskSummary, 
  Order
} from '../lib/api'

export const DashboardPage: React.FC = () => {
  const { i18n } = useTranslation()
  const isTa = i18n.language === 'ta'
  const [riskMatrix, setRiskMatrix] = useState<OrderRiskSummary[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [selectedOrderSummary, setSelectedOrderSummary] = useState<OrderRiskSummary | null>(null)

  const loadData = async () => {
    try {
      setLoading(true)
      const [matrixData, ordersData] = await Promise.all([
        fetchUnifiedRiskMatrix().catch(() => []),
        fetchOrders().catch(() => []),
      ])
      setRiskMatrix(matrixData)
      setOrders(ordersData)
    } catch (err) {
      console.error('Failed to load Executive Control Tower data:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // KPI calculations
  const totalOrdersCount = orders.length
  const criticalOrders = riskMatrix.filter(s => s.max_severity === 'CRITICAL' || s.max_severity === 'HIGH')
  const r3TriggeredCount = riskMatrix.reduce(
    (acc, s) => acc + s.risks.filter(r => r.rule === 'R3' && r.triggered).length, 0
  )
  const r4TriggeredCount = riskMatrix.reduce(
    (acc, s) => acc + s.risks.filter(r => r.rule === 'R4' && r.triggered).length, 0
  )
  const r5TriggeredCount = riskMatrix.reduce(
    (acc, s) => acc + s.risks.filter(r => r.rule === 'R5' && r.triggered).length, 0
  )

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-500/15 text-red-400 border-red-500/30'
      case 'HIGH':
        return 'bg-orange-500/15 text-orange-400 border-orange-500/30'
      case 'MEDIUM':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30'
      case 'LOW':
        return 'bg-blue-500/15 text-blue-400 border-blue-500/30'
      default:
        return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
    }
  }

  return (
    <ToolLayout
      toolName={isTa ? 'நிர்வாக கட்டுப்பாட்டு அறை' : 'Executive Control Tower'}
      toolTag={isTa ? 'துல்லியமான விநியோக ரேடார்' : 'Deterministic Delivery Radar'}
      description={
        isTa
          ? 'வாங்குபவர் ஆர்டர்கள், மூலப்பொருள் பற்றாக்குறை, தையல் வேகம் மற்றும் நிலுவை சலான்கள் குறித்த நேரடி ஒருங்கிணைந்த பார்வை.'
          : 'Live unified visibility across all active buyer purchase orders, material shortages, sewing lines run-rates, and overdue outside challans.'
      }
      actions={
        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            className="px-3 py-1.5 rounded-full border border-white/[0.08] bg-white/[0.03] hover:bg-white/[0.06] text-zinc-300 text-xs font-medium inline-flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{isTa ? 'புதுப்பி' : 'Sync Control Tower'}</span>
          </button>
          <Link
            to="/orders"
            className="px-4 py-1.5 rounded-full bg-teal-500 hover:bg-teal-400 text-[#090a0f] font-bold text-xs inline-flex items-center gap-1.5 transition-all shadow-sm shadow-teal-500/20"
          >
            <span>{isTa ? 'ஆர்டர்கள் (TNA)' : 'View Orders (TNA)'}</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      }
    >
      <div className="space-y-6">

        {/* 1. EXECUTIVE KPI BAND */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          <div className="p-4.5 rounded-2xl bg-[#0c0d15] border border-white/[0.06] space-y-1">
            <div className="flex items-center justify-between text-zinc-400 text-xs font-medium">
              <span className="font-mono text-[10px] uppercase tracking-wider text-zinc-500">
                {isTa ? 'ஆபத்தில் உள்ள ஆர்டர்கள்' : 'Orders At Risk'}
              </span>
              <AlertTriangle className="w-4 h-4 text-red-400" />
            </div>
            <div className="text-2xl font-bold text-white tabular-nums">
              {criticalOrders.length} / {riskMatrix.length || totalOrdersCount}
            </div>
            <div className="text-[11px] text-red-300/80 font-medium">
              {isTa ? 'அதிக / தீவிர ஏற்றுமதி அச்சுறுத்தல்கள்' : 'High / Critical shipment threats'}
            </div>
          </div>

          <div className="p-4.5 rounded-2xl bg-[#0c0d15] border border-white/[0.06] space-y-1">
            <div className="flex items-center justify-between text-zinc-400 text-xs font-medium">
              <span className="font-mono text-[10px] uppercase tracking-wider text-zinc-500">
                {isTa ? 'தையல் வேகப் பின்னடைவு' : 'Sewing Pace Slippage'}
              </span>
              <Scissors className="w-4 h-4 text-orange-400" />
            </div>
            <div className="text-2xl font-bold text-orange-400 tabular-nums">
              {r3TriggeredCount} {isTa ? 'ஆர்டர்கள்' : 'Orders'}
            </div>
            <div className="text-[11px] text-zinc-400">
              {isTa ? 'விதி R3: தினசரி இலக்கை விடக் குறைவான தையல்' : 'Rule R3: Rolling output below daily target'}
            </div>
          </div>

          <div className="p-4.5 rounded-2xl bg-[#0c0d15] border border-white/[0.06] space-y-1">
            <div className="flex items-center justify-between text-zinc-400 text-xs font-medium">
              <span className="font-mono text-[10px] uppercase tracking-wider text-zinc-500">
                {isTa ? 'வெளிப்பணி இழப்பு / தாமதம்' : 'Job-Work Anomaly / Delay'}
              </span>
              <Truck className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-amber-400 tabular-nums">
              {r4TriggeredCount} {isTa ? 'ஆர்டர்கள்' : 'Orders'}
            </div>
            <div className="text-[11px] text-zinc-400">
              {isTa ? 'விதி R4: எடை இழப்பு > 3.5% அல்லது தாமதம்' : 'Rule R4: Shrinkage > 3.5% or overdue'}
            </div>
          </div>

          <div className="p-4.5 rounded-2xl bg-[#0c0d15] border border-white/[0.06] space-y-1">
            <div className="flex items-center justify-between text-zinc-400 text-xs font-medium">
              <span className="font-mono text-[10px] uppercase tracking-wider text-zinc-500">
                {isTa ? 'மைல்கல் தாமதங்கள்' : 'Milestone Gate Breaches'}
              </span>
              <Clock className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-bold text-cyan-300 tabular-nums">
              {r5TriggeredCount} {isTa ? 'வாயில்கள்' : 'Gates'}
            </div>
            <div className="text-[11px] text-zinc-400">
              {isTa ? 'விதி R5: முக்கியமான பாதையில் தாமதமான ஒப்புதல்கள்' : 'Rule R5: Approvals overdue on critical path'}
            </div>
          </div>
        </div>

        {/* 2. UNIFIED RISK CONTROL MATRIX TABLE */}
        <div className="rounded-2xl bg-[#0c0d15] border border-white/[0.06] p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-red-400" />
                <span>{isTa ? 'நடப்பு ஆர்டர்கள் விநியோக ஆபத்து வரிசை' : 'Active Orders Delivery Risk Matrix'}</span>
              </h3>
              <p className="text-xs text-zinc-400">
                {isTa
                  ? 'அதிக ஆபத்து வரிசையில் வகைப்படுத்தப்பட்டுள்ளது. கணித ஆதாரங்களைப் பார்க்க ஏதேனும் ஆர்டரைக் கிளிக் செய்யவும்.'
                  : 'Sorted by highest risk severity. Click any order row to inspect mathematical evidence.'}
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono text-zinc-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>{isTa ? 'நிகழ்நேர கணித இயந்திரம்' : 'Real-Time Engine'}</span>
            </div>
          </div>

          <div className="space-y-3">
            {riskMatrix.map((summary) => {
              const triggeredRules = summary.risks.filter(r => r.triggered)
              const isSelected = selectedOrderSummary?.order_id === summary.order_id

              return (
                <div
                  key={summary.order_id}
                  onClick={() => setSelectedOrderSummary(summary)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-white/[0.05] border-teal-500/40 shadow-lg'
                      : 'bg-white/[0.02] border-white/[0.05] hover:bg-white/[0.04] hover:border-white/[0.12]'
                  }`}
                >
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-sm">
                          {summary.order_number}
                        </span>
                        <span className="text-xs text-zinc-400">
                          ({summary.buyer_name || 'Buyer'})
                        </span>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono border uppercase tracking-wider ${getSeverityBadge(summary.max_severity)}`}>
                          {summary.max_severity} RISK
                        </span>
                      </div>
                      <div className="text-xs text-zinc-400">
                        {triggeredRules.length === 0 ? (
                          <span className="text-emerald-400 flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            All 6 deterministic rules satisfied. On track for delivery.
                          </span>
                        ) : (
                          <span className="text-zinc-300">
                            {triggeredRules.length} active flag(s): {triggeredRules.map(r => `${r.rule} (${r.rule_name})`).join(', ')}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-3 self-end md:self-center">
                      <div className="flex items-center gap-1.5">
                        {['R1', 'R2', 'R3', 'R4', 'R5', 'R6'].map(rCode => {
                          const assessment = summary.risks.find(r => r.rule === rCode)
                          const isTrig = assessment?.triggered
                          return (
                            <span
                              key={rCode}
                              title={assessment ? `${assessment.rule_name}: ${assessment.headline}` : rCode}
                              className={`w-6 h-6 rounded-md flex items-center justify-center font-mono text-[10px] font-bold border transition-all ${
                                isTrig
                                  ? 'bg-red-500/20 text-red-300 border-red-500/40 shadow-sm shadow-red-500/20'
                                  : 'bg-white/[0.02] text-zinc-500 border-white/[0.04]'
                              }`}
                            >
                              {rCode}
                            </span>
                          )
                        })}
                      </div>

                      <button className="text-zinc-400 hover:text-white p-1">
                        <ChevronRight className={`w-4 h-4 transition-transform ${isSelected ? 'rotate-90 text-teal-400' : ''}`} />
                      </button>
                    </div>
                  </div>

                  {/* Inline Quick Evidence Preview if Triggered */}
                  {triggeredRules.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-white/[0.04] grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {triggeredRules.slice(0, 2).map((r, i) => (
                        <div key={i} className="text-[11px] p-2 rounded-lg bg-black/40 border border-white/[0.04] text-zinc-300">
                          <span className="font-mono text-red-400 font-semibold mr-1.5">[{r.rule}]</span>
                          <span>{r.headline}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* 3. MATHEMATICAL EVIDENCE DRAWER / MODAL */}
        {selectedOrderSummary && (
          <div className="rounded-2xl bg-[#0c0d15] border border-teal-500/30 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-white">
                    Mathematical Audit Proof: {selectedOrderSummary.order_number}
                  </h3>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono border ${getSeverityBadge(selectedOrderSummary.max_severity)}`}>
                    {selectedOrderSummary.max_severity}
                  </span>
                </div>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Buyer: {selectedOrderSummary.buyer_name} • Deterministic rule evaluation breakdown (Zero LLM Hallucinations)
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Link
                  to={`/orders?search=${selectedOrderSummary.order_number}`}
                  className="px-3 py-1 rounded-full bg-white/[0.05] hover:bg-white/[0.1] text-xs text-zinc-300 transition-colors inline-flex items-center gap-1"
                >
                  <span>Open PO</span>
                  <ExternalLink className="w-3 h-3" />
                </Link>
                <button
                  onClick={() => setSelectedOrderSummary(null)}
                  className="p-1 rounded-full text-zinc-500 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 pt-1">
              {selectedOrderSummary.risks.map((risk) => (
                <div
                  key={risk.rule}
                  className={`p-4 rounded-xl border text-xs space-y-2 ${
                    risk.triggered
                      ? 'bg-red-950/15 border-red-500/30 shadow-sm'
                      : 'bg-white/[0.02] border-white/[0.05]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-white">
                      {risk.rule} — {risk.rule_name}
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono uppercase ${
                      risk.triggered ? 'bg-red-500/20 text-red-300' : 'bg-emerald-500/10 text-emerald-300'
                    }`}>
                      {risk.triggered ? risk.severity : 'NORMAL'}
                    </span>
                  </div>

                  <p className="text-zinc-200 font-medium text-[11px] leading-relaxed">
                    {risk.headline}
                  </p>

                  <p className="text-zinc-400 text-[11px] leading-relaxed">
                    {risk.explanation}
                  </p>

                  {/* Math Evidence Details */}
                  {risk.evidence && Object.keys(risk.evidence).length > 0 && (
                    <div className="p-2 rounded bg-black/50 border border-white/[0.04] font-mono text-[10px] text-zinc-400 space-y-0.5">
                      <div className="text-zinc-500 uppercase tracking-wider text-[9px]">Verified Parameters</div>
                      {Object.entries(risk.evidence).slice(0, 4).map(([k, v]) => (
                        <div key={k} className="flex justify-between">
                          <span className="text-zinc-500">{k}:</span>
                          <span className="text-zinc-300">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </ToolLayout>
  )
}
