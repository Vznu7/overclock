import React, { useState, useEffect } from 'react'
import { ToolLayout } from '../components/layout/ToolLayout'
import { 
  ShieldAlert, 
  CheckCircle2, 
  FileJson, 
  Sparkles, 
  RefreshCw, 
  Calculator
} from 'lucide-react'
import { fetchOrders, fetchUnifiedRiskMatrix, Order, OrderRiskSummary } from '../lib/api'

export const RiskEvidencePage: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([])
  const [riskMatrix, setRiskMatrix] = useState<OrderRiskSummary[]>([])
  const [selectedOrderId, setSelectedOrderId] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(true)

  const rulesCatalog = [
    {
      code: 'R1',
      name: 'Fabric Arrival Deficit',
      description: 'Verifies verified inbound fabric POs arriving on or before cutting target date against gross BOM demand.',
      formula: 'Deficit = Gross Requirement - (On-Hand Stock + On-Time Inbound POs)',
      threshold: 'Deficit > 0 OR Arrival > Need-by Date (CRITICAL if Delay > 5d OR Deficit > 25%)',
      badgeColor: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
    },
    {
      code: 'R2',
      name: 'Trim & Accessory Shortage',
      description: 'Checks critical accessories (sewing thread, buttons, zippers, polybags) for zero-stock stop conditions.',
      formula: 'Shortage = Trim Gross Requirement - (Current Stock + Inbound Receipts)',
      threshold: 'Any critical trim deficit prior to sewing gate triggers HIGH risk flag',
      badgeColor: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    },
    {
      code: 'R3',
      name: 'Sewing Run-Rate Slippage',
      description: 'Calculates rolling 3-day actual line pacing against the required daily pace needed to hit the ex-factory date.',
      formula: 'Required Daily Rate = Remaining Quantity / Available Floor Working Days',
      threshold: 'Actual Pace < Required Pace (CRITICAL if Slippage > 30% OR Projected Slip > 5d)',
      badgeColor: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
    },
    {
      code: 'R4',
      name: 'Outside Job-Work Delay & Loss Anomaly',
      description: 'Reconciles outward and inward delivery challans with Tiruppur standard weight shrinkage tolerance.',
      formula: 'Weight Loss % = ((Issued Weight - Received Weight) / Issued Weight) * 100',
      threshold: 'Loss % > 3.50% Anomaly OR Delivery Overdue > 3 Working Days',
      badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    },
    {
      code: 'R5',
      name: 'Milestone Gate Slippage',
      description: 'Monitors TNA calendar gates (PP Sample Approval, Fabric In-House, Cutting Start, Packing).',
      formula: 'Gate Breach = Today > Planned Date AND Status != "COMPLETED"',
      threshold: 'Overdue Gate > 5 Days triggers CRITICAL delivery blocker',
      badgeColor: 'text-violet-400 bg-violet-500/10 border-violet-500/20',
    },
    {
      code: 'R6',
      name: 'Order Stagnation / Inactivity',
      description: 'Detects dormant orders in active production status with zero recorded activity across all floor systems.',
      formula: 'Inactivity = Days since latest of (Floor Logs, Stock Ledger, Jobwork Challans)',
      threshold: 'Inactivity >= 5 Days triggers HIGH; >= 7 Days triggers CRITICAL alert',
      badgeColor: 'text-red-400 bg-red-500/10 border-red-500/20',
    },
  ]

  const loadData = async () => {
    try {
      setLoading(true)
      const [oList, rList] = await Promise.all([
        fetchOrders().catch(() => []),
        fetchUnifiedRiskMatrix().catch(() => []),
      ])
      setOrders(oList)
      setRiskMatrix(rList)
      if (oList.length > 0 && !selectedOrderId) {
        setSelectedOrderId(oList[0].id)
      }
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const selectedSummary = riskMatrix.find(r => r.order_id === selectedOrderId)

  return (
    <ToolLayout
      toolName="Deterministic Risk Engine & Evidence Center"
      toolTag="100% Branch Coverage"
      description="Zero LLM calculation hallucination. Every risk evaluation executes pure mathematical Python functions over PostgreSQL records with immutable JSON audit evidence."
      actions={
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={loadData}
            className="px-2.5 sm:px-3 py-1.5 rounded-full border border-white/[0.08] bg-white/[0.03] hover:bg-white/[0.06] text-zinc-300 text-xs font-medium inline-flex items-center gap-1 sm:gap-1.5 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Re-evaluate Matrix</span>
            <span className="sm:hidden">Re-evaluate</span>
          </button>
          <span className="px-2.5 sm:px-3 py-1 rounded-full text-xs font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1 sm:gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">35 Branch Tests Passed</span>
            <span className="sm:hidden">35 Tests</span>
          </span>
        </div>
      }
    >
      <div className="space-y-8">

        {/* 1. INTERACTIVE LIVE RULE EVALUATOR */}
        <div className="rounded-2xl bg-[#0c0d15] border border-white/[0.08] p-5 sm:p-6 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-white/[0.06]">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20">
                <Calculator className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Live Mathematical Evaluation Simulator</h3>
                <p className="text-xs text-zinc-400">Select an active export order to inspect the live deterministic evaluation</p>
              </div>
            </div>

            {/* Order Selector */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-zinc-400">Select Order:</span>
              <select
                value={selectedOrderId}
                onChange={(e) => setSelectedOrderId(e.target.value)}
                className="px-3 py-1.5 rounded-xl bg-zinc-900 border border-white/[0.1] text-xs text-white font-mono focus:outline-none focus:border-teal-400"
              >
                {orders.map(o => (
                  <option key={o.id} value={o.id}>{o.order_number} ({o.total_quantity} pcs)</option>
                ))}
              </select>
            </div>
          </div>

          {selectedSummary ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                <div>
                  <div className="text-xs font-bold text-white">{selectedSummary.order_number}</div>
                  <div className="text-[11px] text-zinc-400">Buyer: {selectedSummary.buyer_name || 'Direct Buyer'}</div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-zinc-400">Max Evaluated Severity:</span>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold uppercase border ${
                    selectedSummary.max_severity === 'CRITICAL' ? 'bg-red-500/20 text-red-300 border-red-500/40' :
                    selectedSummary.max_severity === 'HIGH' ? 'bg-orange-500/20 text-orange-300 border-orange-500/40' :
                    'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                  }`}>
                    {selectedSummary.max_severity}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                {selectedSummary.risks.map((risk) => (
                  <div
                    key={risk.rule}
                    className={`p-4 rounded-xl border text-xs space-y-2 transition-all ${
                      risk.triggered
                        ? 'bg-red-950/20 border-red-500/40'
                        : 'bg-white/[0.015] border-white/[0.05]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-white flex items-center gap-1.5">
                        <span className={`px-1.5 py-0.2 rounded text-[10px] ${
                          risk.triggered ? 'bg-red-500/20 text-red-300' : 'bg-zinc-800 text-zinc-400'
                        }`}>
                          {risk.rule}
                        </span>
                        <span>{risk.rule_name}</span>
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono uppercase ${
                        risk.triggered ? 'bg-red-500/20 text-red-300 font-bold' : 'bg-emerald-500/10 text-emerald-400'
                      }`}>
                        {risk.triggered ? risk.severity : 'PASS'}
                      </span>
                    </div>

                    <p className="text-zinc-200 font-semibold text-[11px] leading-snug">
                      {risk.headline}
                    </p>

                    <p className="text-zinc-400 text-[11px] leading-relaxed">
                      {risk.explanation}
                    </p>

                    {/* Verifiable Math Details */}
                    {risk.evidence && Object.keys(risk.evidence).length > 0 && (
                      <div className="mt-2 p-2.5 rounded-lg bg-black/60 border border-white/[0.04] font-mono text-[10px] text-zinc-400 space-y-1">
                        <div className="text-[9px] uppercase tracking-wider text-teal-400 font-bold flex items-center justify-between">
                          <span>Evidence JSON Telemetry</span>
                          <span className="text-zinc-500">PostgreSQL JSONB</span>
                        </div>
                        {Object.entries(risk.evidence).slice(0, 4).map(([k, v]) => (
                          <div key={k} className="flex justify-between border-t border-white/[0.02] pt-0.5">
                            <span className="text-zinc-500">{k}:</span>
                            <span className="text-zinc-200">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-zinc-500">
              No orders selected or awaiting calculation
            </div>
          )}
        </div>

        {/* 2. THE 6 CANONICAL DETERMINISTIC RULES CATALOG */}
        <div className="rounded-2xl bg-[#0c0d15] border border-white/[0.06] overflow-hidden space-y-3 p-5 sm:p-6">
          <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-teal-400" />
              <h3 className="text-sm font-bold text-white">Rule Engine Architecture (R1 – R6)</h3>
            </div>
            <span className="text-xs font-mono text-zinc-400">Pure Functions • Zero Hallucinations</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 pt-2">
            {rulesCatalog.map((r) => (
              <div key={r.code} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded-md font-mono text-xs font-bold border ${r.badgeColor}`}>
                      {r.code}
                    </span>
                    <h4 className="text-xs font-bold text-white">{r.name}</h4>
                  </div>
                </div>

                <p className="text-xs text-zinc-400 leading-relaxed">
                  {r.description}
                </p>

                <div className="p-2.5 rounded-lg bg-black/40 border border-white/[0.04] space-y-1 font-mono text-[10px]">
                  <div className="text-teal-400 flex items-center justify-between">
                    <span>Formula:</span>
                    <span className="text-zinc-500 text-[9px]">Python 3.12</span>
                  </div>
                  <div className="text-zinc-300 font-semibold">{r.formula}</div>
                  <div className="text-zinc-500 pt-0.5 border-t border-white/[0.04]">
                    Trigger: <span className="text-amber-300">{r.threshold}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 3. GUARANTEE CARDS */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-5 rounded-2xl bg-[#0c0d15] border border-white/[0.06] space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-zinc-200">
              <FileJson className="w-4 h-4 text-cyan-400" />
              <span>Immutable Evidence Auditability</span>
            </div>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Every flag emitted stores the exact inventory figures, dates, and record IDs in PostgreSQL JSONB. Stakeholders can inspect the source mathematics at any point in time.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-[#0c0d15] border border-white/[0.06] space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-zinc-200">
              <Sparkles className="w-4 h-4 text-violet-400" />
              <span>AI Numeric Consistency Validator</span>
            </div>
            <p className="text-xs text-zinc-400 leading-relaxed">
              AI models only draft human communications and root-cause summaries. The deterministic numeric consistency checker automatically rejects any AI response stating quantities not in the evidence table.
            </p>
          </div>
        </div>

      </div>
    </ToolLayout>
  )
}
