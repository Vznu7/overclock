import React from 'react'
import { ToolLayout } from '../components/layout/ToolLayout'
import { Settings, Save, ShieldCheck } from 'lucide-react'

export const CompanySettingsPage: React.FC = () => {
  return (
    <ToolLayout
      toolName="Mill Settings & Risk Rules"
      toolTag="Administration"
      description="Configure factory shift timings, sewing line daily capacities, working days calendar, risk threshold sensitivities, and monthly AI cost caps."
      actions={
        <button className="px-3.5 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-[#090a0f] text-xs font-semibold inline-flex items-center gap-1.5 transition-colors shadow-sm">
          <Save className="w-3.5 h-3.5" />
          <span>Save Settings</span>
        </button>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Risk Thresholds Box */}
        <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-5 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-white/[0.05]">
            <Settings className="w-4 h-4 text-teal-400" />
            <h3 className="text-sm font-semibold text-white">Deterministic Risk Engine Tolerances</h3>
          </div>

          <div className="space-y-3.5 text-xs">
            <div className="space-y-1">
              <label className="font-medium text-zinc-300">R1 Material Shortage Horizon (Days)</label>
              <input type="number" defaultValue={7} className="w-full p-2 rounded-lg border border-white/[0.08] bg-[#090a0f] text-white focus:outline-none focus:border-teal-500/50" />
              <p className="text-[11px] text-zinc-500">Trigger alert when material need-by is within this many days.</p>
            </div>

            <div className="space-y-1">
              <label className="font-medium text-zinc-300">R3 Production Buffer (Days)</label>
              <input type="number" defaultValue={2} className="w-full p-2 rounded-lg border border-white/[0.08] bg-[#090a0f] text-white focus:outline-none focus:border-teal-500/50" />
              <p className="text-[11px] text-zinc-500">Finishing/packing safety buffer subtracted from working days.</p>
            </div>

            <div className="space-y-1">
              <label className="font-medium text-zinc-300">R4 Job-Work Scrap Tolerance (%)</label>
              <input type="number" defaultValue={2.0} step="0.1" className="w-full p-2 rounded-lg border border-white/[0.08] bg-[#090a0f] text-white focus:outline-none focus:border-teal-500/50" />
              <p className="text-[11px] text-zinc-500">Alert raised when external loss exceeds this percentage.</p>
            </div>
          </div>
        </div>

        {/* AI Guardrails & Budget Box */}
        <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-5 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-white/[0.05]">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-white">AI Budget & Execution Guardrails</h3>
          </div>

          <div className="space-y-3.5 text-xs">
            <div className="space-y-1">
              <label className="font-medium text-zinc-300">Monthly AI Budget Cap (INR ₹)</label>
              <input type="number" defaultValue={500} className="w-full p-2 rounded-lg border border-white/[0.08] bg-[#090a0f] text-white focus:outline-none focus:border-teal-500/50" />
              <p className="text-[11px] text-zinc-500">Hard stop enforced before any remote API call is executed.</p>
            </div>

            <div className="space-y-1">
              <label className="font-medium text-zinc-300">Active AI Provider Mode</label>
              <select className="w-full p-2 rounded-lg border border-white/[0.08] bg-[#090a0f] text-white font-mono focus:outline-none focus:border-teal-500/50">
                <option value="mock" className="bg-[#090a0f] text-white">mock (Deterministic fixtures, ₹0 cost)</option>
                <option value="openai" className="bg-[#090a0f] text-white">openai (OpenAI cascade with structured outputs)</option>
              </select>
            </div>

            <div className="p-3 bg-white/[0.02] border border-white/[0.04] rounded-lg text-[11px] text-zinc-400 space-y-1">
              <span className="font-semibold text-zinc-300 block">Strict Budget Guarantee:</span>
              <span>All deterministic operations (orders, balances, stock movements, risk alerts) continue running even if the AI budget cap is reached.</span>
            </div>
          </div>
        </div>
      </div>
    </ToolLayout>
  )
}
