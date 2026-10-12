import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { 
  Activity, 
  Package, 
  FileText, 
  Layers, 
  Scissors, 
  Truck, 
  ShieldAlert, 
  UploadCloud, 
  Settings,
  Building2,
  ArrowRight,
  Sparkles,
  Search,
  Cpu,
  Database
} from 'lucide-react'

export const CompanyPortal: React.FC = () => {
  const { i18n } = useTranslation()
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState<string>('')

  const tools = [
    {
      id: 'dashboard',
      path: '/dashboard',
      title: i18n.language === 'ta' ? 'தொழிற்சாலை கட்டுப்பாட்டு அறை' : 'Executive Control Tower',
      category: 'intelligence',
      icon: Activity,
      tag: 'Core Intelligence',
      badgeColor: 'bg-red-500/10 text-red-400 border-red-500/20',
      description: i18n.language === 'ta' 
        ? 'ஆபத்தில் உள்ள ஆர்டர்கள், நிலுவை சலான்கள் மற்றும் தினசரி வேகத்தைக் கண்காணிக்கும் முக்கிய திரை.'
        : 'R1–R6 unified delivery risk ranking, floor telemetry pacing, and real-time shipment blocker alerts.',
      status: 'Live Active',
      accent: 'text-red-400 group-hover:text-red-300',
    },
    {
      id: 'orders',
      path: '/orders',
      title: i18n.language === 'ta' ? 'ஆர்டர்கள் & TNA மேலாண்மை' : 'Orders & TNA Tracking',
      category: 'merchandising',
      icon: Package,
      tag: 'Merchandising',
      badgeColor: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
      description: i18n.language === 'ta'
        ? 'வாங்குபவர் ஆர்டர்கள், ஸ்டைல் விவரங்கள், அளவு/வண்ண பட்டியல் மற்றும் ஒப்புதல் மைல்கற்கள்.'
        : 'Buyer purchase orders, multi-line color/size matrix, ex-factory delivery dates, and TNA gate approvals.',
      status: 'Ready',
      accent: 'text-cyan-400 group-hover:text-cyan-300',
    },
    {
      id: 'po-review',
      path: '/po-review',
      title: i18n.language === 'ta' ? 'AI PO தரவுப் பிரிப்பு' : 'AI Purchase Order Ingestion',
      category: 'merchandising',
      icon: FileText,
      tag: 'AI Assisted',
      badgeColor: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
      description: i18n.language === 'ta'
        ? 'வாங்குபவர் PDF ஆர்டர்களை நேரடியாக பிரித்து சரிபார்க்கக்கூடிய வரைவு ஆர்டராக மாற்றும் AI கருவி.'
        : 'Zero-data-entry PDF parsing into reviewable draft orders with split-screen visual validation.',
      status: 'Human-in-Loop',
      accent: 'text-violet-400 group-hover:text-violet-300',
    },
    {
      id: 'materials',
      path: '/materials',
      title: i18n.language === 'ta' ? 'மூலப்பொருட்கள் & இருப்பு லெட்ஜர்' : 'Materials, BOM & Stock Ledger',
      category: 'materials',
      icon: Layers,
      tag: 'Store & Inventory',
      badgeColor: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      description: i18n.language === 'ta'
        ? 'துணி மற்றும் துணைப்பொருட்கள் பட்டியல், BOM விவரங்கள் மற்றும் மாறாத இருப்பு வரவு-செலவு கணக்கு.'
        : 'Double-entry stock ledger, deterministic BOM gross calculators, supplier PO deliveries, and deficit math.',
      status: 'Ledger Verified',
      accent: 'text-amber-400 group-hover:text-amber-300',
    },
    {
      id: 'production',
      path: '/production',
      title: i18n.language === 'ta' ? 'ஷாப்-ஃப்ளோர் உற்பத்திப் பதிவு' : 'Shop-Floor Production Logger',
      category: 'floor',
      icon: Scissors,
      tag: 'Shop Floor (Mobile)',
      badgeColor: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
      description: i18n.language === 'ta'
        ? 'தையல் மற்றும் கட்டிங் லைன்களில் மேற்பார்வையாளர்கள் 30 நொடிகளில் பதிவு செய்யும் மொபைல் வடிவம்.'
        : 'Sub-30-second mobile floor entry: sewing output, operator counts, SAM efficiency %, and Rule R3 pacing radar.',
      status: 'Mobile Ready',
      accent: 'text-rose-400 group-hover:text-rose-300',
    },
    {
      id: 'jobwork',
      path: '/jobwork',
      title: i18n.language === 'ta' ? 'வெளிப்பணி (ஜாப்-ஒர்க்) மையம்' : 'Outside Job-Work Processor Hub',
      category: 'floor',
      icon: Truck,
      tag: 'Finishing Vendors',
      badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      description: i18n.language === 'ta'
        ? 'டையிங், பிரிண்டிங், எம்பிராய்டரி சலான்கள், சேத இழப்பு சதவீதம் மற்றும் தாமத எச்சரிக்கைகள்.'
        : 'Outward/inward delivery challans, automatic process weight loss calculation, and Rule R4 shrinkage anomalies (>3.5%).',
      status: 'Weight Reconciled',
      accent: 'text-emerald-400 group-hover:text-emerald-300',
    },
    {
      id: 'risk-evidence',
      path: '/risk-evidence',
      title: i18n.language === 'ta' ? 'ஆபத்து பகுப்பாய்வு & சான்றுகள்' : 'Risk Evidence Matrix (R1-R6)',
      category: 'intelligence',
      icon: ShieldAlert,
      tag: 'Pure Math Rules',
      badgeColor: 'bg-red-500/10 text-red-400 border-red-500/20',
      description: i18n.language === 'ta'
        ? 'துல்லியமான கணித விதிகளின் அடிப்படையில் வெளிப்படையான காரணங்களுடன் ஆபத்து எச்சரிக்கைகள்.'
        : '100% deterministic branch-tested risk engine covering fabric deficit, trim shortage, sewing pacing, job-work, and gates.',
      status: '100% Branch Tested',
      accent: 'text-orange-400 group-hover:text-orange-300',
    },
    {
      id: 'imports',
      path: '/imports',
      title: i18n.language === 'ta' ? 'தரவு இறக்குமதி & ஏற்றுமதி' : 'Data Import & Migration Wizard',
      category: 'data',
      icon: UploadCloud,
      tag: 'ETL Tools',
      badgeColor: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      description: i18n.language === 'ta'
        ? 'எக்செல் மற்றும் CSV கோப்புகளிலிருந்து வாங்குபவர், மூலப்பொருள், இருப்பு விவரங்களை இறக்குமதி செய்யும் கருவி.'
        : 'High-speed CSV/Excel data ingestion for legacy factory records with row-level validation and error reporting.',
      status: 'CSV / Excel',
      accent: 'text-blue-400 group-hover:text-blue-300',
    },
    {
      id: 'company',
      path: '/company',
      title: i18n.language === 'ta' ? 'நிறுவன அமைப்புகள் & தொழிற்சாலை' : 'Mill Settings & Risk Parameters',
      category: 'data',
      icon: Settings,
      tag: 'Administration',
      badgeColor: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
      description: i18n.language === 'ta'
        ? 'தொழிற்சாலை லைன் திறன்கள், விடுமுறை நாட்கள், ஆபத்து வரம்புகள் மற்றும் AI மாதாந்திர செலவு வரம்பு.'
        : 'Daily sewing factory capacity, weekly off-days, risk trigger thresholds, and strict ₹500 AI monthly budget caps.',
      status: 'Configured',
      accent: 'text-slate-400 group-hover:text-slate-300',
    },
  ]

  const filteredTools = tools.filter((tool) => {
    const matchesCategory = selectedCategory === 'all' || tool.category === selectedCategory
    const matchesSearch = searchQuery === '' || 
      tool.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.tag.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesCategory && matchesSearch
  })

  return (
    <div className="space-y-16 pb-28 max-w-6xl mx-auto px-4 sm:px-6">
      
      {/* 1. OPENAI-STYLE OBSIDIAN EDITORIAL HERO */}
      <section className="relative pt-12 pb-8 text-center max-w-4xl mx-auto space-y-6">
        {/* Subtle Background Glow */}
        <div className="absolute inset-0 -top-10 -z-10 bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,rgba(45,212,191,0.12),transparent)] pointer-events-none" />

        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-medium text-teal-300 bg-teal-500/[0.08] border border-teal-500/25 shadow-sm shadow-teal-500/10">
          <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
          <span>{i18n.language === 'ta' ? 'திருப்பூர் ஏற்றுமதி கிளஸ்டர் • தொழிற்சாலை OS v2.0' : 'Tiruppur Cluster Pilot • Factory OS v2.0'}</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-white leading-[1.08]">
          {i18n.language === 'ta' ? 'ஏற்றுமதி சரக்கு அனுப்புவதில் தாமதம் ' : 'Predict garment shipment delay '}
          <span className="bg-gradient-to-r from-teal-300 via-cyan-400 to-sky-400 bg-clip-text text-transparent">
            {i18n.language === 'ta' ? 'ஏற்படுவதற்கு முன்பே கண்டறியுங்கள்.' : 'before it breaches.'}
          </span>
        </h1>

        <p className="text-sm sm:text-base text-zinc-400 leading-relaxed max-w-2xl mx-auto font-normal">
          {i18n.language === 'ta'
            ? 'வாங்குபவர் ஆணை, மூலப்பொருள் இருப்பு, தினசரி தையல் வேகம் மற்றும் வெளிப்பணிகளை ஒன்றிணைக்கும் துல்லியமான ரேடார் பலகை.'
            : 'A multi-tenant precision operating radar uniting commercial buyer POs, fabric inward readiness, daily sewing SAM pacing, and outside job-work processors with zero LLM calculation errors.'}
        </p>

        {/* Minimalist Action Pill Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-gradient-to-r from-teal-400 to-cyan-500 hover:from-teal-300 hover:to-cyan-400 text-[#07080d] text-xs font-bold transition-all shadow-lg shadow-teal-500/20 hover:scale-[1.02]"
          >
            <Activity className="w-4 h-4" />
            <span>{i18n.language === 'ta' ? 'கட்டுப்பாட்டு அறையைத் திற' : 'Launch Control Tower'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
          <a
            href="#tools-grid"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-full bg-white/[0.04] hover:bg-white/[0.08] text-zinc-200 text-xs font-medium border border-white/[0.1] transition-colors"
          >
            <span>{i18n.language === 'ta' ? 'அனைத்து 9 பணித்தளங்கள்' : 'Explore 9 Workspaces'}</span>
          </a>
          <Link
            to="/about"
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-zinc-400 hover:text-teal-300 transition-colors"
          >
            <span>{i18n.language === 'ta' ? 'பொறியியல் கட்டமைப்பு →' : 'Engineering Architecture →'}</span>
          </Link>
        </div>

        {/* OpenAI Editorial Telemetry Strip */}
        <div className="pt-6 grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-left">
          <div className="p-3 rounded-2xl bg-white/[0.02] border border-white/[0.05]">
            <div className="text-[10px] text-zinc-500 font-mono uppercase tracking-wider flex items-center gap-1">
              <Database className="w-3 h-3 text-cyan-400" />
              <span>{i18n.language === 'ta' ? 'தரவு தனிமை' : 'Data Isolation'}</span>
            </div>
            <div className="text-xs font-semibold text-zinc-200 mt-1">PostgreSQL RLS</div>
            <div className="text-[10px] text-emerald-400">{i18n.language === 'ta' ? 'பூஜ்ஜிய தரவுக் கசிவு' : 'Zero cross-tenant leakage'}</div>
          </div>
          <div className="p-3 rounded-2xl bg-white/[0.02] border border-white/[0.05]">
            <div className="text-[10px] text-zinc-500 font-mono uppercase tracking-wider flex items-center gap-1">
              <Cpu className="w-3 h-3 text-amber-400" />
              <span>{i18n.language === 'ta' ? 'ஆபத்து கணிதம்' : 'Risk Calculations'}</span>
            </div>
            <div className="text-xs font-semibold text-zinc-200 mt-1">100% Deterministic</div>
            <div className="text-[10px] text-zinc-400">Rules R1–R6 pure Python</div>
          </div>
          <div className="p-3 rounded-2xl bg-white/[0.02] border border-white/[0.05]">
            <div className="text-[10px] text-zinc-500 font-mono uppercase tracking-wider flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-violet-400" />
              <span>{i18n.language === 'ta' ? 'AI நிர்வாகம்' : 'AI Governance'}</span>
            </div>
            <div className="text-xs font-semibold text-zinc-200 mt-1">Human-in-Loop</div>
            <div className="text-[10px] text-violet-300">{i18n.language === 'ta' ? 'மனித ஒப்புதல் அவசியம்' : 'Draft reviews, no auto-commits'}</div>
          </div>
          <div className="p-3 rounded-2xl bg-white/[0.02] border border-white/[0.05]">
            <div className="text-[10px] text-zinc-500 font-mono uppercase tracking-wider flex items-center gap-1">
              <Building2 className="w-3 h-3 text-teal-400" />
              <span>{i18n.language === 'ta' ? 'கிளவுட் சுபாபேஸ்' : 'Cloud Database'}</span>
            </div>
            <div className="text-xs font-semibold text-zinc-200 mt-1">Supabase Cloud</div>
            <div className="text-[10px] text-teal-300">100% Free Tier</div>
          </div>
        </div>
      </section>

      {/* 2. CAMPUSLOOM CATEGORIZED TOOLS SUITE */}
      <section id="tools-grid" className="space-y-6 pt-4">
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 pb-2 border-b border-white/[0.08]">
          <div>
            <div className="text-xs font-mono uppercase tracking-widest text-teal-400 flex items-center gap-1.5">
              <span>01 / Specialized Utilities</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white mt-1">
              Interactive Mill Workspaces
            </h2>
          </div>

          {/* Search & Category Filter Pills */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
            {/* Quick Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search tools & rules..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 rounded-full bg-white/[0.03] border border-white/[0.08] text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-teal-500/50 w-full sm:w-44"
              />
            </div>

            {/* Category Filter Pills */}
            <div className="flex items-center gap-1 p-1 bg-white/[0.02] rounded-full border border-white/[0.06] overflow-x-auto">
              {[
                { id: 'all', label: 'All (9)' },
                { id: 'intelligence', label: 'Risk' },
                { id: 'merchandising', label: 'Orders' },
                { id: 'materials', label: 'Store' },
                { id: 'floor', label: 'Floor' },
                { id: 'data', label: 'Settings' },
              ].map(cat => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`px-3 py-1 text-xs font-medium rounded-full transition-all shrink-0 ${
                    selectedCategory === cat.id
                      ? 'bg-white/[0.1] text-white shadow-sm font-semibold'
                      : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* CampusLoom Badge Tiles Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTools.map((tool) => {
            const Icon = tool.icon
            return (
              <Link
                key={tool.id}
                to={tool.path}
                className="group relative p-5 rounded-2xl bg-[#0c0d15] border border-white/[0.06] hover:border-white/[0.18] hover:bg-[#11131e] transition-all duration-200 flex flex-col justify-between shadow-sm hover:shadow-xl hover:shadow-black/50"
              >
                <div className="space-y-3.5">
                  <div className="flex items-center justify-between">
                    <div className={`p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.08] group-hover:border-white/20 transition-all ${tool.accent}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    {/* CampusLoom Color Coded Badge */}
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${tool.badgeColor}`}>
                      {tool.tag}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-sm font-bold text-zinc-100 group-hover:text-white transition-colors">
                      {tool.title}
                    </h3>
                    <p className="text-xs text-zinc-400 mt-1.5 leading-relaxed line-clamp-2">
                      {tool.description}
                    </p>
                  </div>
                </div>

                <div className="pt-4 mt-4 border-t border-white/[0.04] flex items-center justify-between text-xs">
                  <span className="text-[11px] font-mono text-zinc-500 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    <span>{tool.status}</span>
                  </span>
                  <span className="text-zinc-400 group-hover:text-teal-300 font-semibold inline-flex items-center gap-1 transition-colors">
                    <span>Enter</span>
                    <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                  </span>
                </div>
              </Link>
            )
          })}
        </div>
      </section>

      {/* 3. ACTIVE FACILITY PROFILE & PILOT METRICS */}
      <section className="rounded-3xl bg-[#0b0c14] border border-white/[0.08] p-6 sm:p-8 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-5 border-b border-white/[0.06]">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-teal-500/20 to-cyan-500/20 border border-teal-500/30 flex items-center justify-center text-teal-300 shrink-0 shadow-inner">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white tracking-tight">
                  Tirupur Tex Fab (Pilot Facility)
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                  Online
                </span>
              </div>
              <p className="text-xs text-zinc-400 mt-0.5">
                Tiruppur Export Processing Zone • GSTIN: 33AAACD1234F1Z5
              </p>
            </div>
          </div>

          <div className="text-xs font-mono text-zinc-400 bg-white/[0.02] px-3 py-1.5 rounded-full border border-white/[0.06] w-fit">
            tenant_id: tirupur-demo
          </div>
        </div>

        <p className="text-xs text-zinc-400 leading-relaxed max-w-3xl">
          High-volume circular knit manufacturer operating 4 dedicated sewing lines (1,500 pcs/day), computer-aided marker spreading, laser cutting, and linked outside processors for reactive yarn dyeing, rotary screen printing, and bio-enzyme soft washing.
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
          <div className="p-3.5 rounded-2xl bg-white/[0.015] border border-white/[0.05]">
            <div className="text-[10px] font-mono text-zinc-500 uppercase">Lines Allocated</div>
            <div className="text-sm font-bold text-white mt-1">4 Active Lines</div>
            <div className="text-[11px] text-zinc-400">120 Total Operators</div>
          </div>
          <div className="p-3.5 rounded-2xl bg-white/[0.015] border border-white/[0.05]">
            <div className="text-[10px] font-mono text-zinc-500 uppercase">Compliance</div>
            <div className="text-sm font-bold text-white mt-1">OEKO-TEX Class 1</div>
            <div className="text-[11px] text-emerald-400">SEDEX SMETA 4-Pillar</div>
          </div>
          <div className="p-3.5 rounded-2xl bg-white/[0.015] border border-white/[0.05]">
            <div className="text-[10px] font-mono text-zinc-500 uppercase">Active Export POs</div>
            <div className="text-sm font-bold text-white mt-1">PO-DEC-8821 & 9014</div>
            <div className="text-[11px] text-zinc-400">Decathlon & Next UK</div>
          </div>
          <div className="p-3.5 rounded-2xl bg-white/[0.015] border border-white/[0.05]">
            <div className="text-[10px] font-mono text-zinc-500 uppercase">Outside Processors</div>
            <div className="text-sm font-bold text-white mt-1">3 Finishing Units</div>
            <div className="text-[11px] text-zinc-400">Dyeing, Wash, Print</div>
          </div>
        </div>
      </section>

      {/* 4. SEO FAQ & KNOWLEDGE BASE SECTION */}
      <section id="faq" className="space-y-6 pt-4">
        <div className="pb-2 border-b border-white/[0.08]">
          <div className="text-xs font-mono uppercase tracking-widest text-teal-400 flex items-center gap-1.5">
            <span>02 / Platform Knowledge Base & FAQ</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-white mt-1">
            {i18n.language === 'ta' ? 'அடிக்கடி கேட்கப்படும் கேள்விகள் (FAQ)' : 'Frequently Asked Questions about OVERCLOCK'}
          </h2>
          <p className="text-xs text-zinc-400 mt-1 max-w-2xl">
            Everything you need to know about OVERCLOCK's predictive delivery radar, deterministic risk engine, and bilingual apparel manufacturing operating system.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-5 rounded-2xl bg-[#0c0d16] border border-white/[0.08] space-y-2.5">
            <h3 className="text-sm font-bold text-teal-300 flex items-center gap-2">
              <span className="text-teal-400 font-mono text-xs">Q1:</span>
              <span>What is OVERCLOCK and how does it predict garment shipment delays?</span>
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              OVERCLOCK is an AI-powered SaaS operating system built specifically for garment and apparel manufacturers. Unlike traditional static ERPs, OVERCLOCK uses a 100% deterministic mathematical risk engine (Rules R1 through R6) that correlates commercial buyer POs, fabric inward dates, double-entry stock ledgers, sewing SAM efficiency, and outside job-work processors to flag delivery risks days before an ex-factory breach occurs.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-[#0c0d16] border border-white/[0.08] space-y-2.5">
            <h3 className="text-sm font-bold text-teal-300 flex items-center gap-2">
              <span className="text-teal-400 font-mono text-xs">Q2:</span>
              <span>Why does OVERCLOCK guarantee zero LLM math errors?</span>
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Large language models are notoriously prone to arithmetic hallucinations. OVERCLOCK enforces a strict architectural division: LLMs are utilized solely for optical document parsing and natural-language draft explanations, while all calculations—BOM fabric consumption, stock balances, sewing SAM pacing, and shrinkage percentage loss—are computed by pure, branch-tested Python and TypeScript rules.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-[#0c0d16] border border-white/[0.08] space-y-2.5">
            <h3 className="text-sm font-bold text-teal-300 flex items-center gap-2">
              <span className="text-teal-400 font-mono text-xs">Q3:</span>
              <span>How does OVERCLOCK support apparel export hubs like Tiruppur?</span>
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              OVERCLOCK is engineered for the fast-paced realities of Indian apparel clusters. It features out-of-the-box support for outside job-work delivery challans (dyeing, printing, embroidery, washing), automated weight loss reconciliation against Tiruppur industry thresholds (3.5%), and a 30-second mobile floor entry interface for floor supervisors.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-[#0c0d16] border border-white/[0.08] space-y-2.5">
            <h3 className="text-sm font-bold text-teal-300 flex items-center gap-2">
              <span className="text-teal-400 font-mono text-xs">Q4:</span>
              <span>Is OVERCLOCK available in regional languages like Tamil (தமிழ்)?</span>
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Yes! OVERCLOCK features native bilingual support with instant one-click switching between English and Tamil across all navigation menus, operational dashboards, telemetry badges, and modal dialogs. Floor supervisors and storekeepers can interact in Tamil while merchandisers review buyer specifications in English.
            </p>
          </div>
        </div>
      </section>

      {/* 5. SEO SITEMAP & RICH FOOTER */}
      <footer className="pt-10 border-t border-white/[0.08] space-y-8">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-xs text-zinc-400">
          <div className="space-y-2.5">
            <div className="font-mono text-[11px] uppercase tracking-wider text-white font-semibold">
              Core Intelligence
            </div>
            <ul className="space-y-1.5">
              <li><Link to="/dashboard" className="hover:text-teal-300 transition-colors">Executive Control Tower</Link></li>
              <li><Link to="/risk-evidence" className="hover:text-teal-300 transition-colors">Risk Evidence Matrix (R1-R6)</Link></li>
              <li><Link to="/about" className="hover:text-teal-300 transition-colors">Architecture Specification</Link></li>
            </ul>
          </div>

          <div className="space-y-2.5">
            <div className="font-mono text-[11px] uppercase tracking-wider text-white font-semibold">
              Merchandising
            </div>
            <ul className="space-y-1.5">
              <li><Link to="/orders" className="hover:text-teal-300 transition-colors">Orders & TNA Milestones</Link></li>
              <li><Link to="/po-review" className="hover:text-teal-300 transition-colors">AI PO Ingestion & Split-Screen</Link></li>
              <li><Link to="/imports" className="hover:text-teal-300 transition-colors">CSV/Excel Data Migration</Link></li>
            </ul>
          </div>

          <div className="space-y-2.5">
            <div className="font-mono text-[11px] uppercase tracking-wider text-white font-semibold">
              Store & Operations
            </div>
            <ul className="space-y-1.5">
              <li><Link to="/materials" className="hover:text-teal-300 transition-colors">Fabric & Trims Stock Ledger</Link></li>
              <li><Link to="/production" className="hover:text-teal-300 transition-colors">Floor Production Pacing</Link></li>
              <li><Link to="/jobwork" className="hover:text-teal-300 transition-colors">Outside Job-Work Processor Hub</Link></li>
            </ul>
          </div>

          <div className="space-y-2.5">
            <div className="font-mono text-[11px] uppercase tracking-wider text-white font-semibold">
              About OVERCLOCK
            </div>
            <p className="text-[11px] text-zinc-500 leading-relaxed">
              OVERCLOCK is the leading multi-tenant AI SaaS for apparel exporters, knitwear manufacturers, and textile sourcing houses across Tiruppur, Surat, Ludhiana, and Bengaluru.
            </p>
          </div>
        </div>

        <div className="pt-6 border-t border-white/[0.06] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 text-xs text-zinc-500">
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-white tracking-wider">OVERCLOCK</span>
            <span>•</span>
            <span>Factory Operating System v2.0</span>
            <span>•</span>
            <span className="text-teal-400 font-mono text-[11px]">#1 Predictive Garment Operations AI</span>
          </div>
          <div className="flex items-center gap-4 text-zinc-400">
            <span>Tiruppur Cluster Pilot</span>
            <span>•</span>
            <span>PostgreSQL RLS Secured</span>
            <span>•</span>
            <span>Zero LLM Hallucinations</span>
          </div>
        </div>
      </footer>

    </div>
  )
}
