import React, { useState, useRef } from 'react'
import { ToolLayout } from '../components/layout/ToolLayout'
import { 
  UploadCloud, 
  FileSpreadsheet, 
  Download, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw, 
  ArrowRight,
  FileCheck
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { uploadOrdersCsv, CsvImportSummary } from '../lib/api'

export const ImportsPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState<boolean>(false)
  const [importSummary, setImportSummary] = useState<CsvImportSummary | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDownloadTemplate = () => {
    const csvContent = 
`buyer_name,buyer_code,style_number,style_name,garment_type,order_number,total_quantity,unit_price,ex_factory_date
Decathlon Sports,DECATH,DEC-TEE-01,QuickDry Performance Tee,Crew Neck Tee,PO-DEC-8899,10000,310.00,2026-12-15
Next Sourcing UK,NEXT,NXT-POLO-01,Classic Pique Mercerized Polo,Polo,PO-NXT-9055,4500,550.00,2026-12-20
H&M Global,HMG,HM-TEE-01,Bio-Wash Single Jersey Tee,Crew Neck Tee,PO-HM-4155,12000,285.00,2027-01-10`

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'overclock_orders_template.csv'
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
      setImportSummary(null)
      setErrorMessage(null)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return
    setIsUploading(true)
    setErrorMessage(null)

    try {
      const summary = await uploadOrdersCsv(selectedFile)
      setImportSummary(summary)
      setSelectedFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <ToolLayout
      toolName="Data Import & Migration Wizard"
      toolTag="Data Management"
      description="Migrate historical spreadsheets into OVERCLOCK. Upload buyers, styles, orders, materials, and stock balances with pre-flight validation and downloadable error reports."
      actions={
        <div className="flex items-center gap-2">
          <button 
            onClick={handleDownloadTemplate}
            className="px-3 py-1.5 rounded-lg border border-white/[0.08] bg-white/[0.03] hover:bg-white/[0.06] text-zinc-300 text-xs font-medium inline-flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download CSV Template</span>
          </button>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Active Upload Card for Orders */}
        <div className="rounded-xl bg-[#0d0e14] border border-white/[0.08] p-6 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-white/[0.05]">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-teal-500/10 text-teal-400 border border-teal-500/20 flex items-center justify-center">
                <FileSpreadsheet className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">
                  Bulk Orders & Buyer Styles Importer
                </h3>
                <p className="text-xs text-zinc-400">
                  Dialect-aware CSV parser with UTF-8 BOM, date standardization, and automatic TNA milestone synthesis.
                </p>
              </div>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 w-fit">
              Phase 3 Ready
            </span>
          </div>

          {/* Drag & Drop Upload Zone */}
          <div className="p-8 border-2 border-dashed border-white/[0.08] hover:border-teal-500/40 rounded-xl bg-white/[0.01] transition-all text-center space-y-3">
            <input 
              type="file" 
              ref={fileInputRef}
              accept=".csv"
              onChange={handleFileChange}
              className="hidden" 
              id="csv-file-input"
            />
            <label 
              htmlFor="csv-file-input"
              className="cursor-pointer block space-y-2"
            >
              <div className="w-10 h-10 rounded-full bg-white/[0.04] text-zinc-300 flex items-center justify-center mx-auto hover:bg-teal-500/10 hover:text-teal-400 transition-colors">
                <UploadCloud className="w-5 h-5" />
              </div>
              <div className="text-xs font-medium text-zinc-200">
                {selectedFile ? (
                  <span className="text-teal-400 font-mono">{selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)</span>
                ) : (
                  <span>Click to browse or drop an Orders CSV file here</span>
                )}
              </div>
              <p className="text-[11px] text-zinc-500">
                Accepts comma-delimited or semicolon-delimited CSV files up to 15 MB
              </p>
            </label>

            {selectedFile && (
              <div className="pt-2 flex items-center justify-center gap-2">
                <button
                  onClick={handleUpload}
                  disabled={isUploading}
                  className="px-4 py-2 rounded-lg bg-teal-500 hover:bg-teal-400 text-zinc-950 font-semibold text-xs inline-flex items-center gap-2 transition-colors disabled:opacity-50"
                >
                  {isUploading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Validating & Importing...</span>
                    </>
                  ) : (
                    <>
                      <FileCheck className="w-3.5 h-3.5" />
                      <span>Process & Commit to Supabase</span>
                    </>
                  )}
                </button>
                <button
                  onClick={() => {
                    setSelectedFile(null)
                    if (fileInputRef.current) fileInputRef.current.value = ''
                  }}
                  className="px-3 py-2 rounded-lg border border-white/[0.08] text-zinc-400 hover:text-white text-xs transition-colors"
                >
                  Clear
                </button>
              </div>
            )}
          </div>

          {/* Upload Error Banner */}
          {errorMessage && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Import Summary Results */}
          {importSummary && (
            <div className="p-4 rounded-xl bg-[#090a0f] border border-teal-500/30 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <h4 className="text-xs font-semibold text-white">Import Execution Completed</h4>
                </div>
                <Link
                  to="/orders"
                  className="text-xs text-teal-400 hover:text-teal-300 inline-flex items-center gap-1 font-medium"
                >
                  <span>View in Orders Registry</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>

              <div className="grid grid-cols-4 gap-2 pt-1 text-center">
                <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                  <div className="text-[10px] text-zinc-500 font-mono uppercase">Rows Processed</div>
                  <div className="text-sm font-semibold text-white mt-0.5">{importSummary.rows_read}</div>
                </div>
                <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                  <div className="text-[10px] text-zinc-500 font-mono uppercase">Orders Created</div>
                  <div className="text-sm font-semibold text-teal-400 mt-0.5">{importSummary.orders_created}</div>
                </div>
                <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                  <div className="text-[10px] text-zinc-500 font-mono uppercase">Color/Size Lines</div>
                  <div className="text-sm font-semibold text-white mt-0.5">{importSummary.lines_created}</div>
                </div>
                <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                  <div className="text-[10px] text-zinc-500 font-mono uppercase">TNA Milestones</div>
                  <div className="text-sm font-semibold text-emerald-400 mt-0.5">{importSummary.milestones_created}</div>
                </div>
              </div>

              {importSummary.errors.length > 0 && (
                <div className="mt-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs space-y-1">
                  <div className="font-semibold">Skipped Rows / Line Warnings ({importSummary.errors.length}):</div>
                  <ul className="list-disc pl-4 space-y-0.5 font-mono text-[11px] text-amber-200/90 max-h-32 overflow-y-auto">
                    {importSummary.errors.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Other Migration Modules Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-5 space-y-3">
            <div className="w-8 h-8 rounded-lg bg-white/[0.03] text-zinc-300 border border-white/[0.06] flex items-center justify-center">
              <FileSpreadsheet className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-semibold text-white">Materials & BOM Formulas</h4>
              <p className="text-xs text-zinc-400 mt-1">
                Scheduled for Phase 4: Import yarn/fabric codes, trim catalogs, and garment consumption formulas.
              </p>
            </div>
            <div className="pt-2">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-500/10 text-zinc-400 border border-zinc-500/20">
                Phase 4 Milestone
              </span>
            </div>
          </div>

          <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-5 space-y-3">
            <div className="w-8 h-8 rounded-lg bg-white/[0.03] text-zinc-300 border border-white/[0.06] flex items-center justify-center">
              <FileSpreadsheet className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-semibold text-white">Starting Stock Balances</h4>
              <p className="text-xs text-zinc-400 mt-1">
                Scheduled for Phase 5: Import verified physical stock counts to initialize the immutable inventory ledger.
              </p>
            </div>
            <div className="pt-2">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-500/10 text-zinc-400 border border-zinc-500/20">
                Phase 5 Milestone
              </span>
            </div>
          </div>
        </div>

        <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-4 text-xs text-zinc-400 flex items-center gap-3">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>PostgreSQL Row-Level Security ensures imported buyer and style records are strictly isolated to your tenant domain.</span>
        </div>
      </div>
    </ToolLayout>
  )
}
