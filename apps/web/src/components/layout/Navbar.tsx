import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
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
  ChevronDown,
  UserCheck,
  Sparkles,
  Globe,
  Database
} from 'lucide-react'
import { DEMO_USERS, getStoredUser, loginWithCredentials, UserSession } from '../../lib/api'

export const Navbar: React.FC = () => {
  const { i18n } = useTranslation()
  const location = useLocation()
  const [suiteMenuOpen, setSuiteMenuOpen] = useState<boolean>(false)
  const [currentUser, setCurrentUser] = useState<UserSession | null>(getStoredUser())
  const [userMenuOpen, setUserMenuOpen] = useState<boolean>(false)

  const handleSwitchUser = async (demo: typeof DEMO_USERS[0]) => {
    try {
      await loginWithCredentials(demo.email, demo.password)
      setCurrentUser(getStoredUser())
      setUserMenuOpen(false)
      window.location.reload()
    } catch (err) {
      console.error('Failed to switch user:', err)
    }
  }

  useEffect(() => {
    setSuiteMenuOpen(false)
    setUserMenuOpen(false)
  }, [location.pathname])

  const toggleLanguage = () => {
    const nextLang = i18n.language === 'en' ? 'ta' : 'en'
    i18n.changeLanguage(nextLang)
  }

  // CampusLoom categorized suites with custom color accents
  const toolCategories = [
    {
      label: i18n.language === 'ta' ? 'ஆர்டர் & மர்ச்சென்டைசிங்' : 'Merchandising Hub',
      badgeColor: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
      items: [
        {
          name: i18n.language === 'ta' ? 'ஆர்டர்கள் & TNA மைல்கற்கள்' : 'Orders & TNA Tracking',
          desc: 'Buyer PO line items, color-size breakup, delivery gates',
          path: '/orders',
          icon: Package,
          accent: 'text-cyan-400',
        },
        {
          name: i18n.language === 'ta' ? 'AI PO பிரித்தெடுத்தல்' : 'AI Purchase Order Ingestion',
          desc: 'Side-by-side PDF preview, confidence scoring, 1-click draft',
          path: '/po-review',
          icon: FileText,
          accent: 'text-violet-400',
        },
      ],
    },
    {
      label: i18n.language === 'ta' ? 'ஸ்டோர் & மூலப்பொருட்கள்' : 'Store & Materials',
      badgeColor: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      items: [
        {
          name: i18n.language === 'ta' ? 'துணி & ட்ரிம்ஸ் இருப்பு லெட்ஜர்' : 'Materials, BOM & Stock Ledger',
          desc: 'Double-entry inventory ledger, BOM consumption & receipts',
          path: '/materials',
          icon: Layers,
          accent: 'text-amber-400',
        },
      ],
    },
    {
      label: i18n.language === 'ta' ? 'தொழிற்சாலை தளம் & வேலைப்பாடுகள்' : 'Floor Operations & Job-Work',
      badgeColor: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
      items: [
        {
          name: i18n.language === 'ta' ? 'தையல் வேக அளவீடு & தளம்' : 'Floor Production Lines',
          desc: '30-second mobile entry, line output pacing & SAM efficiency',
          path: '/production',
          icon: Scissors,
          accent: 'text-rose-400',
        },
        {
          name: i18n.language === 'ta' ? 'வெளி வேலைப்பாடு (சலான் & எடை இழப்பு)' : 'Outside Job-Work Hub',
          desc: 'Delivery challans, process weight shrinkage loss anomaly tracking',
          path: '/jobwork',
          icon: Truck,
          accent: 'text-emerald-400',
        },
      ],
    },
    {
      label: i18n.language === 'ta' ? 'ஆபத்து கட்டுப்பாடு & நுண்ணறிவு' : 'Risk Engine & Radar',
      badgeColor: 'bg-red-500/10 text-red-400 border-red-500/20',
      items: [
        {
          name: i18n.language === 'ta' ? 'நிர்வாக கட்டுப்பாட்டு அறை' : 'Executive Control Tower',
          desc: 'Unified R1-R6 risk ranking, floor telemetry & active blockers',
          path: '/dashboard',
          icon: Activity,
          accent: 'text-red-400',
        },
        {
          name: i18n.language === 'ta' ? 'ஆபத்து காரண சான்றுகள்' : 'Risk Evidence Matrix',
          desc: 'Pure mathematical proof behind each flagged rule R1-R6',
          path: '/risk-evidence',
          icon: ShieldAlert,
          accent: 'text-orange-400',
        },
      ],
    },
  ]

  return (
    <header className="sticky top-0 z-50 pt-2 pb-2 px-3 sm:px-6">
      {/* CampusLoom Frosted Floating Pill Header */}
      <div className="max-w-6xl mx-auto bg-[#0a0b12]/80 backdrop-blur-xl border border-white/[0.08] shadow-2xl shadow-black/80 rounded-full px-3.5 py-2 flex items-center justify-between gap-3 transition-all duration-300">
        
        {/* Brand & Home */}
        <div className="flex items-center gap-3">
          <Link to="/" className="flex items-center gap-2.5 group pl-1">
            <div className="w-7 h-7 rounded-lg overflow-hidden border border-white/[0.15] bg-[#0c0d15] flex items-center justify-center group-hover:scale-105 group-hover:border-teal-400/60 transition-all shadow-md shadow-black/50 shrink-0">
              <img src="/logo.png" alt="OVERCLOCK" className="w-full h-full object-cover" />
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="font-extrabold text-white text-sm tracking-tight group-hover:text-teal-300 transition-colors">
                OVERCLOCK
              </span>
              <span className="text-[9px] uppercase tracking-widest text-teal-400/80 font-mono hidden sm:inline px-1 py-0.2 rounded bg-teal-500/10 border border-teal-500/20">
                v2.0
              </span>
            </div>
          </Link>

          {/* Quick Nav Links */}
          <div className="hidden md:flex items-center gap-1 pl-2 border-l border-white/[0.08]">
            <Link
              to="/"
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                location.pathname === '/'
                  ? 'bg-white/[0.1] text-white shadow-inner'
                  : 'text-zinc-400 hover:text-white hover:bg-white/[0.05]'
              }`}
            >
              {i18n.language === 'ta' ? 'முகப்பு' : 'Portal'}
            </Link>
            <Link
              to="/dashboard"
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                location.pathname === '/dashboard'
                  ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                  : 'text-zinc-400 hover:text-white hover:bg-white/[0.05]'
              }`}
            >
              {i18n.language === 'ta' ? 'கட்டுப்பாட்டு அறை' : 'Control Tower'}
            </Link>
          </div>
        </div>

        {/* Center: CampusLoom Tools Dropdown Trigger */}
        <div className="relative">
          <button
            onClick={() => setSuiteMenuOpen(!suiteMenuOpen)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all border ${
              suiteMenuOpen 
                ? 'bg-white/[0.12] text-white border-white/20 shadow-md' 
                : 'bg-white/[0.03] text-zinc-300 border-white/[0.08] hover:bg-white/[0.07] hover:text-white'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-teal-400" />
            <span>{i18n.language === 'ta' ? 'தொழிற்சாலை கருவிகள்' : 'Factory Tools Suite'}</span>
            <ChevronDown className={`w-3 h-3 transition-transform ${suiteMenuOpen ? 'rotate-180' : ''}`} />
          </button>

          {/* CampusLoom Style Mega Dropdown Menu */}
          {suiteMenuOpen && (
            <div className="absolute left-1/2 -translate-x-1/2 top-full mt-3 w-[580px] max-w-[92vw] bg-[#0c0d16]/95 backdrop-blur-2xl border border-white/[0.12] rounded-2xl p-4 shadow-2xl shadow-black/90 z-50 animate-in fade-in zoom-in-95 duration-150">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {toolCategories.map((cat, idx) => (
                  <div key={idx} className="space-y-2">
                    <div className="flex items-center justify-between pb-1 border-b border-white/[0.06]">
                      <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
                        {cat.label}
                      </span>
                    </div>
                    <div className="space-y-1">
                      {cat.items.map((item, i) => {
                        const Icon = item.icon
                        const isActive = location.pathname === item.path
                        return (
                          <Link
                            key={i}
                            to={item.path}
                            onClick={() => setSuiteMenuOpen(false)}
                            className={`group flex items-start gap-2.5 p-2 rounded-xl transition-all ${
                              isActive 
                                ? 'bg-white/[0.08] border border-white/[0.12]' 
                                : 'hover:bg-white/[0.04] border border-transparent'
                            }`}
                          >
                            <div className={`p-1.5 rounded-lg bg-white/[0.03] border border-white/[0.08] group-hover:border-white/20 transition-colors ${item.accent}`}>
                              <Icon className="w-4 h-4" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="text-xs font-semibold text-zinc-200 group-hover:text-white transition-colors truncate">
                                {item.name}
                              </div>
                              <div className="text-[10px] text-zinc-400 line-clamp-1">
                                {item.desc}
                              </div>
                            </div>
                          </Link>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-3 pt-3 border-t border-white/[0.06] flex items-center justify-between text-[11px] text-zinc-400 px-1">
                <span className="flex items-center gap-1.5 font-mono text-[10px]">
                  <Database className="w-3 h-3 text-emerald-400" />
                  Supabase Cloud DB • Tiruppur Cluster
                </span>
                <Link
                  to="/imports"
                  onClick={() => setSuiteMenuOpen(false)}
                  className="text-zinc-400 hover:text-teal-300 transition-colors flex items-center gap-1 text-[11px]"
                >
                  <UploadCloud className="w-3 h-3" />
                  <span>CSV/Excel Data Import</span>
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Right: Language Pill & Persona Switcher */}
        <div className="flex items-center gap-2">
          {/* Live Cloud Status Dot */}
          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-mono text-emerald-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>Cloud Active</span>
          </div>

          {/* Language Toggle Pill */}
          <button
            onClick={toggleLanguage}
            data-testid="lang-toggle"
            title="Toggle English / தமிழ்"
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-[11px] font-medium text-zinc-300 transition-colors"
          >
            <Globe className="w-3 h-3 text-teal-400" />
            <span className="font-semibold">{i18n.language === 'en' ? 'EN / தமிழ்' : 'தமிழ் / EN'}</span>
          </button>

          {/* User Persona Switcher */}
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-2 pl-2 pr-2.5 py-1 rounded-full bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-xs transition-colors"
            >
              <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-cyan-600 to-teal-400 flex items-center justify-center text-[10px] font-bold text-white uppercase shadow-sm">
                {currentUser?.full_name?.charAt(0) || 'U'}
              </div>
              <span className="hidden sm:inline text-zinc-300 text-[11px] font-medium max-w-[85px] truncate">
                {currentUser?.role?.replace('_', ' ') || 'Demo'}
              </span>
              <ChevronDown className="w-3 h-3 text-zinc-400" />
            </button>

            {userMenuOpen && (
              <div className="absolute right-0 top-full mt-2 w-64 bg-[#0d0e16]/95 backdrop-blur-xl border border-white/[0.12] rounded-2xl p-2 shadow-2xl z-50 animate-in fade-in duration-100">
                <div className="px-3 py-2 border-b border-white/[0.06] mb-1">
                  <div className="text-xs font-semibold text-white">{currentUser?.full_name || 'Demo User'}</div>
                  <div className="text-[10px] text-zinc-400 font-mono capitalize">
                    {currentUser?.role?.replace('_', ' ') || 'Owner'}
                  </div>
                </div>

                <div className="text-[10px] uppercase font-mono tracking-wider text-zinc-400 px-3 py-1">
                  Fast Persona Switcher
                </div>

                <div className="space-y-0.5">
                  {DEMO_USERS.map((demo) => {
                    const isSelected = currentUser?.email === demo.email
                    return (
                      <button
                        key={demo.email}
                        onClick={() => handleSwitchUser(demo)}
                        className={`w-full text-left px-3 py-1.5 rounded-xl text-xs flex items-center justify-between transition-colors ${
                          isSelected
                            ? 'bg-teal-500/15 text-teal-300 font-semibold'
                            : 'text-zinc-300 hover:bg-white/[0.04] hover:text-white'
                        }`}
                      >
                        <div className="truncate">
                          <div>{demo.label}</div>
                          <div className="text-[10px] text-zinc-400 capitalize">{demo.role.replace('_', ' ')}</div>
                        </div>
                        {isSelected && <UserCheck className="w-3.5 h-3.5 text-teal-400 shrink-0 ml-1" />}
                      </button>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

      </div>
    </header>
  )
}
