import React from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight, Home, ArrowLeft } from 'lucide-react'

interface ToolLayoutProps {
  toolName: string
  toolTag: string
  description: string
  actions?: React.ReactNode
  children: React.ReactNode
}

export const ToolLayout: React.FC<ToolLayoutProps> = ({
  toolName,
  toolTag,
  description,
  actions,
  children,
}) => {
  return (
    <div className="space-y-6 pb-20 max-w-6xl mx-auto w-full max-w-full">
      {/* Breadcrumb & Navigation Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-3 border-b border-white/[0.06]">
        <nav className="flex items-center gap-1.5 text-xs text-zinc-500 overflow-x-auto">
          <Link 
            to="/" 
            className="flex items-center gap-1 hover:text-white transition-colors shrink-0"
          >
            <Home className="w-3.5 h-3.5" />
            <span>Overview</span>
          </Link>
          <ChevronRight className="w-3 h-3 text-zinc-600 shrink-0" />
          <span className="font-medium text-zinc-300 truncate">{toolName}</span>
        </nav>

        <Link
          to="/"
          className="inline-flex items-center gap-1 text-xs text-zinc-400 hover:text-teal-300 transition-colors w-fit shrink-0"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Workspaces</span>
        </Link>
      </div>

      {/* Tool Header Box */}
      <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-4 sm:p-6 w-full max-w-full">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-1.5 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider bg-teal-500/10 text-teal-400 border border-teal-500/20 shrink-0">
                {toolTag}
              </span>
              <h1 className="text-lg sm:text-2xl font-bold text-white tracking-tight break-words">
                {toolName}
              </h1>
            </div>
            <p className="text-xs text-zinc-400 leading-relaxed max-w-3xl">
              {description}
            </p>
          </div>

          {actions && (
            <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
              {actions}
            </div>
          )}
        </div>
      </div>

      {/* Main Tool Content */}
      <div className="w-full max-w-full">
        {children}
      </div>
    </div>
  )
}
