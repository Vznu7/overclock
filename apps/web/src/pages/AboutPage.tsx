import React from 'react'
import { ToolLayout } from '../components/layout/ToolLayout'
import { 
  Cpu, 
  Users, 
  Sparkles, 
  MapPin, 
  ArrowRight
} from 'lucide-react'
import { Link } from 'react-router-dom'

export const AboutPage: React.FC = () => {
  return (
    <ToolLayout
      toolName="About OVERCLOCK"
      toolTag="Product & Mission"
      description="The AI-assisted Order-to-Production Operating System built specifically for Indian garment manufacturers and apparel export networks."
      actions={
        <Link
          to="/"
          className="px-3.5 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-[#090a0f] font-semibold text-xs inline-flex items-center gap-1.5 transition-colors shadow-sm"
        >
          <span>Explore Workspaces</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      }
    >
      <div className="space-y-10 max-w-4xl">
        {/* Hero Mission */}
        <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-6 sm:p-8 space-y-4">
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded text-[11px] font-mono text-teal-400 bg-teal-500/10 border border-teal-500/20">
            <Sparkles className="w-3.5 h-3.5" />
            <span>The Core Promise</span>
          </div>

          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-snug">
            "Know which orders will miss their ship date, and why, before it is too late."
          </h2>

          <div className="space-y-3 text-xs sm:text-sm text-zinc-400 leading-relaxed">
            <p>
              In apparel export hubs like Tiruppur and Coimbatore, factories juggle commercial purchase orders, yarn and dyeing lead times, fabric readiness, sewing run-rates, and unforgiving shipment cutoffs. Today, this vital knowledge is scattered across Excel spreadsheets, WhatsApp chats, paper challans, and memory.
            </p>
            <p>
              OVERCLOCK unites commercial orders, raw material stock, shop-floor output, and external processing into a single deterministic delivery radar with cost-first AI document extraction.
            </p>
          </div>
        </div>

        {/* Operating Philosophy: AI vs Deterministic Code */}
        <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-6 sm:p-8 space-y-5">
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-teal-400">
            <Cpu className="w-4 h-4" />
            <span>Core Engineering Principle</span>
          </div>
          <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            AI Proposes. Deterministic Code Calculates. Humans Approve.
          </h3>
          <p className="text-xs sm:text-sm text-zinc-400 leading-relaxed">
            We never let language models compute quantities, calculate stock balances, trigger risks, or mutate production records. All calculations—from consumption formulas to 5-day actual run-rates and loss tolerance thresholds—are executed by 100% pure deterministic Python functions with 100% branch test coverage.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
            <div className="bg-white/[0.02] border border-white/[0.05] rounded-lg p-4 space-y-1">
              <div className="text-teal-400 font-mono text-[11px] font-semibold uppercase">01 / AI Role</div>
              <div className="text-xs font-semibold text-white">Extract & Draft</div>
              <p className="text-[11px] text-zinc-400 mt-1 leading-relaxed">Extracts raw PDF fields, translates Tamil voice/text, and drafts supplier follow-up messages.</p>
            </div>
            <div className="bg-white/[0.02] border border-white/[0.05] rounded-lg p-4 space-y-1">
              <div className="text-teal-400 font-mono text-[11px] font-semibold uppercase">02 / Code Role</div>
              <div className="text-xs font-semibold text-white">Calculate & Guard</div>
              <p className="text-[11px] text-zinc-400 mt-1 leading-relaxed">Computes stock movements, checks delivery dates, evaluates R1-R6 rules, and enforces RLS.</p>
            </div>
            <div className="bg-white/[0.02] border border-white/[0.05] rounded-lg p-4 space-y-1">
              <div className="text-teal-400 font-mono text-[11px] font-semibold uppercase">03 / Human Role</div>
              <div className="text-xs font-semibold text-white">Review & Commit</div>
              <p className="text-[11px] text-zinc-400 mt-1 leading-relaxed">Every AI proposal requires explicit confirmation by authorized merchandisers or owners.</p>
            </div>
          </div>
        </div>

        {/* Built for 5 Factory Personas */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-teal-400" />
            <h3 className="text-base font-bold text-white">Built for Key Factory Personas</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {[
              { role: 'Factory Owners', desc: 'Real-time high-level visibility on at-risk orders, overdue outside processing, and delivery bottlenecks.' },
              { role: 'Merchandisers', desc: 'Zero manual data entry: convert buyer PO PDFs into structured orders and track milestone TNA approval gates.' },
              { role: 'Production Managers', desc: 'Monitor 4 sewing lines with 5-day rolling run-rate pacing and instant deficit alerts.' },
              { role: 'Store Keepers', desc: 'Immutable fabric and trims ledger; prevent sewing start until required lots are physically verified.' },
              { role: 'Line Supervisors', desc: 'Sub-30-second mobile entry form designed for Tamil and English with offline-tolerant retries.' },
            ].map((persona, i) => (
              <div key={i} className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-4 space-y-1.5">
                <div className="text-teal-400 font-mono font-bold text-xs">
                  0{i+1}
                </div>
                <h4 className="text-xs font-semibold text-white">{persona.role}</h4>
                <p className="text-[11px] text-zinc-400 leading-relaxed">{persona.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Setting: Cluster Context */}
        <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-6 space-y-3">
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-teal-400">
            <MapPin className="w-4 h-4" />
            <span>Industrial Cluster Focus</span>
          </div>
          <h3 className="text-base font-bold text-white">
            Engineered for Tiruppur & Coimbatore Apparel Networks
          </h3>
          <p className="text-xs text-zinc-400 leading-relaxed">
            Indian apparel exporters operate in dynamic job-work networks: fabric knitting, yarn dyeing, rotary printing, embroidery, compacting, and bio-washing are often distributed across external specialist vendors. OVERCLOCK handles these external challans, inward reconciliations, and shrinkage losses seamlessly.
          </p>
          <div className="flex flex-wrap gap-1.5 pt-2 text-[11px] font-mono text-zinc-400">
            <span className="px-2.5 py-1 rounded bg-white/[0.03] border border-white/[0.06]">Tiruppur Knitwear</span>
            <span className="px-2.5 py-1 rounded bg-white/[0.03] border border-white/[0.06]">Coimbatore Weaving</span>
            <span className="px-2.5 py-1 rounded bg-white/[0.03] border border-white/[0.06]">Bilingual (English & தமிழ்)</span>
            <span className="px-2.5 py-1 rounded bg-white/[0.03] border border-white/[0.06]">PostgreSQL Row-Level Security</span>
          </div>
        </div>
      </div>
    </ToolLayout>
  )
}
