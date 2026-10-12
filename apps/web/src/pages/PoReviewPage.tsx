import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ToolLayout } from '../components/layout/ToolLayout'
import { 
  Upload, 
  FileCheck, 
  AlertCircle, 
  FileText, 
  Sparkles, 
  CheckCircle2, 
  ArrowRight, 
  Plus, 
  Trash2, 
  Calendar, 
  Layers, 
  ShieldCheck, 
  Loader2 
} from 'lucide-react'
import { 
  extractPurchaseOrder, 
  fetchBuyers, 
  fetchStyles, 
  createOrder, 
  Buyer, 
  Style, 
  PoExtractionResult, 
  ExtractedLineItem 
} from '../lib/api'

export const PoReviewPage: React.FC = () => {
  const { i18n } = useTranslation()
  const isTa = i18n.language === 'ta'

  const [loading, setLoading] = useState<boolean>(false)
  const [buyers, setBuyers] = useState<Buyer[]>([])
  const [styles, setStyles] = useState<Style[]>([])
  const [extractionResult, setExtractionResult] = useState<PoExtractionResult | null>(null)
  const [selectedSample, setSelectedSample] = useState<string>('')
  
  // Editable Draft Form States
  const [buyerId, setBuyerId] = useState<string>('')
  const [styleId, setStyleId] = useState<string>('')
  const [orderNumber, setOrderNumber] = useState<string>('')
  const [totalQuantity, setTotalQuantity] = useState<number>(0)
  const [unitPrice, setUnitPrice] = useState<number>(0)
  const [currency, setCurrency] = useState<string>('USD')
  const [exFactoryDate, setExFactoryDate] = useState<string>('')
  const [plannedSewingStart, setPlannedSewingStart] = useState<string>('')
  const [lines, setLines] = useState<ExtractedLineItem[]>([])
  
  // Action Feedback
  const [creating, setCreating] = useState<boolean>(false)
  const [createdOrderNumber, setCreatedOrderNumber] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    async function loadMasterData() {
      try {
        const [bList, sList] = await Promise.all([fetchBuyers(), fetchStyles()])
        setBuyers(bList)
        setStyles(sList)
      } catch (err) {
        console.error('Failed to load buyers/styles:', err)
      }
    }
    loadMasterData()
    // Auto-load Decathlon sample as initial interactive preview
    handleLoadPreset('sample_decathlon')
  }, [])

  const handleLoadPreset = async (sampleKey: string) => {
    setLoading(true)
    setErrorMessage(null)
    setCreatedOrderNumber(null)
    setSelectedSample(sampleKey)
    try {
      const result = await extractPurchaseOrder({ sampleId: sampleKey })
      applyExtractionResult(result)
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to extract sample')
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setLoading(true)
    setErrorMessage(null)
    setCreatedOrderNumber(null)
    setSelectedSample('custom_upload')
    try {
      const result = await extractPurchaseOrder({ file })
      applyExtractionResult(result)
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to parse uploaded document')
    } finally {
      setLoading(false)
    }
  }

  const applyExtractionResult = (result: PoExtractionResult) => {
    setExtractionResult(result)
    setOrderNumber(result.order_number.value)
    setTotalQuantity(result.total_quantity.value)
    setUnitPrice(result.unit_price.value)
    setCurrency(result.currency.value)
    setExFactoryDate(result.ex_factory_date.value)
    setPlannedSewingStart(result.planned_sewing_start.value)
    setLines(result.lines || [])

    // Match buyer ID if found or select first matching code
    if (result.buyer_id) {
      setBuyerId(result.buyer_id)
    } else if (result.buyer_code) {
      const match = buyers.find(b => b.code.toLowerCase() === result.buyer_code?.toLowerCase())
      if (match) setBuyerId(match.id)
      else if (buyers.length > 0) setBuyerId(buyers[0].id)
    } else if (buyers.length > 0) {
      setBuyerId(buyers[0].id)
    }

    // Match style ID
    if (result.style_id) {
      setStyleId(result.style_id)
    } else {
      const match = styles.find(s => s.style_number.toLowerCase() === result.style_number.value.toLowerCase())
      if (match) setStyleId(match.id)
      else if (styles.length > 0) setStyleId(styles[0].id)
    }
  }

  // Line item manipulation
  const handleUpdateLine = (index: number, field: keyof ExtractedLineItem, value: any) => {
    const next = [...lines]
    next[index] = { ...next[index], [field]: value }
    setLines(next)
    // Recalculate total quantity
    const sum = next.reduce((acc, curr) => acc + (Number(curr.quantity) || 0), 0)
    setTotalQuantity(sum)
  }

  const handleAddLine = () => {
    setLines([...lines, { color: 'Navy', size: 'M', quantity: 1000, confidence: 1.0 }])
  }

  const handleRemoveLine = (index: number) => {
    const next = lines.filter((_, i) => i !== index)
    setLines(next)
    const sum = next.reduce((acc, curr) => acc + (Number(curr.quantity) || 0), 0)
    setTotalQuantity(sum)
  }

  const sumLineQuantities = lines.reduce((acc, curr) => acc + (Number(curr.quantity) || 0), 0)
  const isQuantityBalanced = sumLineQuantities === totalQuantity

  const handleConfirmAndCreate = async () => {
    if (!buyerId || !styleId || !orderNumber) {
      setErrorMessage('Please select a Buyer, Style, and verify Order Number')
      return
    }
    setCreating(true)
    setErrorMessage(null)
    try {
      const payload = {
        buyer_id: buyerId,
        style_id: styleId,
        order_number: orderNumber,
        total_quantity: totalQuantity,
        unit_price: unitPrice,
        currency,
        ex_factory_date: exFactoryDate,
        planned_sewing_start: plannedSewingStart || undefined,
        lines: lines.map(l => ({ color: l.color, size: l.size, quantity: Number(l.quantity) })),
      }
      const created = await createOrder(payload)
      setCreatedOrderNumber(created.order_number)
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save order to Supabase')
    } finally {
      setCreating(false)
    }
  }

  return (
    <ToolLayout
      toolName={isTa ? 'AI கொள்முதல் ஆணை பிரித்தெடுக்கும் கருவி' : 'AI Purchase Order Extraction Engine'}
      toolTag={isTa ? 'ஆவண பகுப்பாய்வு' : 'Document Intelligence'}
      description={
        isTa
          ? 'வாங்குபவர் பிடிஎஃப் ஆவணங்களை பதிவேற்றி, வடிவமைப்பு, அளவுகள், விலைகள் மற்றும் தேதிகளை சரிபார்த்து கிளவுட் தரவுத்தளத்தில் நேரடியாக ஆர்டர்களை உருவாக்கலாம்.'
          : 'Zero-hallucination layout cascade extracts buyer PO numbers, styles, quantities, and dates into a side-by-side reviewable draft with human approval.'
      }
      actions={
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-full text-[11px] font-mono bg-violet-500/10 text-violet-300 border border-violet-500/20 font-semibold flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-violet-400" />
            <span>{isTa ? 'அதிவேக ஆவணப் பிரிப்பு' : 'Fast Cost-First Cascade'}</span>
          </span>
        </div>
      }
    >
      {/* Preset Samples Selector Bar */}
      <div className="mb-6 p-4 rounded-xl bg-[#0c0d15] border border-white/[0.08] flex flex-wrap items-center justify-between gap-3 w-full max-w-full">
        <div className="flex flex-col sm:flex-row sm:items-center gap-2 w-full sm:w-auto">
          <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider font-mono">
            {isTa ? 'மாதிரி ஆவணங்கள்:' : 'Load Sample Presets:'}
          </span>
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => handleLoadPreset('sample_decathlon')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                selectedSample === 'sample_decathlon'
                  ? 'bg-teal-500/20 text-teal-300 border-teal-500/40 shadow-sm shadow-teal-500/20'
                  : 'bg-white/[0.03] text-zinc-300 border-white/[0.06] hover:bg-white/[0.06]'
              }`}
            >
              Decathlon (#DEC-9041, 12k pcs)
            </button>
            <button
              onClick={() => handleLoadPreset('sample_hm')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                selectedSample === 'sample_hm'
                  ? 'bg-teal-500/20 text-teal-300 border-teal-500/40 shadow-sm shadow-teal-500/20'
                  : 'bg-white/[0.03] text-zinc-300 border-white/[0.06] hover:bg-white/[0.06]'
              }`}
            >
              H&M Global (#HMG-4412, 8.5k pcs)
            </button>
            <button
              onClick={() => handleLoadPreset('sample_next')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                selectedSample === 'sample_next'
                  ? 'bg-teal-500/20 text-teal-300 border-teal-500/40 shadow-sm shadow-teal-500/20'
                  : 'bg-white/[0.03] text-zinc-300 border-white/[0.06] hover:bg-white/[0.06]'
              }`}
            >
              Next UK (#NEXT-1108, 6k pcs)
            </button>
          </div>
        </div>

        <label className="cursor-pointer inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.09] text-xs font-medium text-white border border-white/[0.1] transition-all">
          <Upload className="w-3.5 h-3.5 text-teal-400" />
          <span>{isTa ? 'சொந்த PDF பதிவேற்றவும்' : 'Upload Custom PDF'}</span>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            className="hidden"
          />
        </label>
      </div>

      {/* Success Notification */}
      {createdOrderNumber && (
        <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
            <div>
              <h4 className="text-sm font-semibold text-emerald-300">
                {isTa ? 'ஆர்டர் வெற்றிகரமாக உருவாக்கப்பட்டது!' : 'Order Successfully Created in Cloud Database!'}
              </h4>
              <p className="text-xs text-zinc-400">
                {isTa
                  ? `ஆர்டர் ${createdOrderNumber} கிளவுட் சுபாபேஸில் பதிவு செய்யப்பட்டு TNA மைல்கற்கள் தயாராக உள்ளன.`
                  : `Order ${createdOrderNumber} is committed to Supabase PostgreSQL with immutable audit logs.`}
              </p>
            </div>
          </div>
          <Link
            to="/orders"
            className="px-3.5 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-black text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md shadow-emerald-500/20"
          >
            <span>{isTa ? 'ஆர்டர்கள் பக்கத்திற்கு செல்' : 'View in Orders & TNA'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Error Notification */}
      {errorMessage && (
        <div className="mb-6 p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Split-Screen Main Container */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        
        {/* Left Column: Document Preview Pane */}
        <div className="lg:col-span-5 rounded-xl bg-[#0c0d15] border border-white/[0.08] p-5 flex flex-col justify-between min-h-[580px]">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-teal-400" />
                <span>{isTa ? 'வாங்குபவர் ஆவண முன்னோட்டம்' : 'Buyer Purchase Order Document'}</span>
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/[0.03] text-zinc-400 border border-white/[0.06]">
                {extractionResult?.extraction_source || 'Preset Cascade'}
              </span>
            </div>

            {/* Document Content View */}
            <div className="mt-4 p-4 rounded-xl bg-[#07080c] border border-white/[0.05] font-mono text-xs text-zinc-300 whitespace-pre-wrap leading-relaxed max-h-[440px] overflow-y-auto">
              {loading ? (
                <div className="py-20 flex flex-col items-center justify-center text-zinc-500 gap-2">
                  <Loader2 className="w-6 h-6 animate-spin text-teal-400" />
                  <span>{isTa ? 'ஆவணம் பகுப்பாய்வு செய்யப்படுகிறது...' : 'Analyzing document layout...'}</span>
                </div>
              ) : extractionResult ? (
                <div>
                  <div className="pb-3 mb-3 border-b border-white/[0.06] flex items-center justify-between">
                    <span className="text-teal-400 font-bold uppercase tracking-wider text-[11px]">
                      {extractionResult.buyer_name.value}
                    </span>
                    <span className="text-emerald-400 text-[10px] bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded">
                      Confidence: {Math.round(extractionResult.order_number.confidence * 100)}%
                    </span>
                  </div>
                  {extractionResult.raw_preview_text}
                </div>
              ) : (
                <div className="py-20 text-center text-zinc-500">
                  {isTa ? 'மாதிரியைத் தேர்ந்தெடுக்கவும் அல்லது PDF பதிவேற்றவும்' : 'Select a sample above or drop a buyer PDF'}
                </div>
              )}
            </div>

            {/* Document Visual Tags */}
            <div className="mt-4 flex flex-wrap gap-2 text-[10px] font-mono">
              <span className="px-2 py-1 rounded bg-teal-500/10 text-teal-300 border border-teal-500/20">
                PO: {orderNumber || '—'}
              </span>
              <span className="px-2 py-1 rounded bg-violet-500/10 text-violet-300 border border-violet-500/20">
                Qty: {totalQuantity.toLocaleString()} pcs
              </span>
              <span className="px-2 py-1 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                Ex-Factory: {exFactoryDate || '—'}
              </span>
            </div>
          </div>

          <div className="mt-4 p-3 bg-white/[0.02] rounded-lg border border-white/[0.04] text-[11px] text-zinc-400 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-teal-400 shrink-0" />
            <span>
              {isTa
                ? 'AI கணக்கீடு செய்யாது; மனிதர் ஒப்புதலுக்குப் பிறகே தரவு சேமிக்கப்படும்.'
                : 'Deterministic safeguard: Zero LLM math. Human verifies before cloud commit.'}
            </span>
          </div>
        </div>

        {/* Right Column: Editable Draft Form */}
        <div className="lg:col-span-7 rounded-xl bg-[#0c0d15] border border-white/[0.08] p-5 flex flex-col justify-between">
          <div className="space-y-4">
            
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
              <div>
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <FileCheck className="w-4 h-4 text-emerald-400" />
                  <span>{isTa ? 'பிரித்தெடுக்கப்பட்ட ஆர்டர் படிவம்' : 'Extracted Draft Order Fields'}</span>
                </h3>
                <p className="text-xs text-zinc-400 mt-0.5">
                  {isTa
                    ? 'மதிப்புகளை சரிபார்த்து திருத்திக் கொள்ளலாம்.'
                    : 'Values extracted from PO document. All fields are editable prior to commitment.'}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
                  isQuantityBalanced 
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                    : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                }`}>
                  {isQuantityBalanced ? '✓ Lines Balanced' : '⚠ Qty Mismatch'}
                </span>
              </div>
            </div>

            {/* Warnings list */}
            {extractionResult?.warnings && extractionResult.warnings.length > 0 && (
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 space-y-1">
                {extractionResult.warnings.map((w, i) => (
                  <div key={i} className="text-xs text-amber-300 flex items-center gap-2">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    <span>{w}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Form Fields Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              
              {/* Buyer Selector */}
              <div>
                <label className="block text-[11px] font-medium text-zinc-400 mb-1 flex items-center justify-between">
                  <span>{isTa ? 'வாங்குபவர் (Buyer)' : 'Buyer'}</span>
                  {extractionResult?.buyer_name.confidence && (
                    <span className="text-[10px] text-teal-400 font-mono">
                      {Math.round(extractionResult.buyer_name.confidence * 100)}% conf
                    </span>
                  )}
                </label>
                <select
                  value={buyerId}
                  onChange={(e) => setBuyerId(e.target.value)}
                  className="w-full bg-[#131520] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-400"
                >
                  <option value="">{isTa ? '-- வாங்குபவரைத் தேர்ந்தெடுக்கவும் --' : '-- Select Buyer --'}</option>
                  {buyers.map(b => (
                    <option key={b.id} value={b.id}>{b.name} ({b.code})</option>
                  ))}
                </select>
              </div>

              {/* Style Selector */}
              <div>
                <label className="block text-[11px] font-medium text-zinc-400 mb-1 flex items-center justify-between">
                  <span>{isTa ? 'ஆடை வடிவம் (Style)' : 'Garment Style'}</span>
                  {extractionResult?.style_number.confidence && (
                    <span className="text-[10px] text-teal-400 font-mono">
                      {Math.round(extractionResult.style_number.confidence * 100)}% conf
                    </span>
                  )}
                </label>
                <select
                  value={styleId}
                  onChange={(e) => setStyleId(e.target.value)}
                  className="w-full bg-[#131520] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-400"
                >
                  <option value="">{isTa ? '-- வடிவத்தைத் தேர்ந்தெடுக்கவும் --' : '-- Select Style --'}</option>
                  {styles.map(s => (
                    <option key={s.id} value={s.id}>{s.style_number} — {s.style_name}</option>
                  ))}
                </select>
              </div>

              {/* Order Number */}
              <div>
                <label className="block text-[11px] font-medium text-zinc-400 mb-1 flex items-center justify-between">
                  <span>{isTa ? 'ஆர்டர் எண் (PO Number)' : 'Buyer Order / PO Number'}</span>
                  {extractionResult?.order_number.confidence && (
                    <span className="text-[10px] text-teal-400 font-mono">
                      {Math.round(extractionResult.order_number.confidence * 100)}% conf
                    </span>
                  )}
                </label>
                <input
                  type="text"
                  value={orderNumber}
                  onChange={(e) => setOrderNumber(e.target.value)}
                  className="w-full bg-[#131520] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-400 font-mono"
                />
              </div>

              {/* Total Quantity */}
              <div>
                <label className="block text-[11px] font-medium text-zinc-400 mb-1 flex items-center justify-between">
                  <span>{isTa ? 'மொத்த எண்ணிக்கை (Total Qty)' : 'Total Quantity (pcs)'}</span>
                  <span className="text-[10px] text-teal-400 font-mono">Sum: {sumLineQuantities}</span>
                </label>
                <input
                  type="number"
                  value={totalQuantity}
                  onChange={(e) => setTotalQuantity(Number(e.target.value))}
                  className="w-full bg-[#131520] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-400 font-mono"
                />
              </div>

              {/* Unit Price & Currency */}
              <div>
                <label className="block text-[11px] font-medium text-zinc-400 mb-1">
                  {isTa ? 'விலை & நாணயம் (Unit Price)' : 'Unit Price & Currency'}
                </label>
                <div className="flex gap-2">
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="w-24 bg-[#131520] border border-white/[0.08] rounded-lg px-2.5 py-2 text-xs text-white focus:outline-none focus:border-teal-400 font-mono"
                  >
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="GBP">GBP</option>
                    <option value="INR">INR</option>
                  </select>
                  <input
                    type="number"
                    step="0.01"
                    value={unitPrice}
                    onChange={(e) => setUnitPrice(Number(e.target.value))}
                    className="flex-1 bg-[#131520] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-400 font-mono"
                  />
                </div>
              </div>

              {/* Planned Sewing Start */}
              <div>
                <label className="block text-[11px] font-medium text-zinc-400 mb-1 flex items-center justify-between">
                  <span>{isTa ? 'தையல் தொடக்க தேதி' : 'Planned Sewing Start'}</span>
                  <Calendar className="w-3 h-3 text-zinc-500" />
                </label>
                <input
                  type="date"
                  value={plannedSewingStart}
                  onChange={(e) => setPlannedSewingStart(e.target.value)}
                  className="w-full bg-[#131520] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-400 font-mono"
                />
              </div>

              {/* Ex-Factory Date */}
              <div className="sm:col-span-2">
                <label className="block text-[11px] font-medium text-zinc-400 mb-1 flex items-center justify-between">
                  <span>{isTa ? 'ஏற்றுமதி தேதி (Ex-Factory Date)' : 'Target Ex-Factory Date'}</span>
                  <Calendar className="w-3 h-3 text-zinc-500" />
                </label>
                <input
                  type="date"
                  value={exFactoryDate}
                  onChange={(e) => setExFactoryDate(e.target.value)}
                  className="w-full bg-[#131520] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-400 font-mono"
                />
              </div>
            </div>

            {/* Line Items Matrix Breakdown */}
            <div className="mt-4 pt-4 border-t border-white/[0.06]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-white flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-teal-400" />
                  <span>{isTa ? 'வண்ணம் & அளவு விபரம் (Color / Size Breakdown)' : 'Color & Size Breakdown'}</span>
                </span>
                <button
                  type="button"
                  onClick={handleAddLine}
                  className="px-2 py-1 rounded bg-white/[0.04] hover:bg-white/[0.08] text-teal-300 text-[11px] font-medium flex items-center gap-1 border border-white/[0.08] transition-all"
                >
                  <Plus className="w-3 h-3" />
                  <span>{isTa ? 'வரிசை சேர்' : 'Add Row'}</span>
                </button>
              </div>

              <div className="rounded-lg border border-white/[0.06] overflow-hidden bg-[#07080c]">
                <table className="w-full text-xs text-left">
                  <thead className="bg-white/[0.02] text-zinc-400 font-mono text-[10px] uppercase border-b border-white/[0.05]">
                    <tr>
                      <th className="px-3 py-2">{isTa ? 'வண்ணம்' : 'Color'}</th>
                      <th className="px-3 py-2 w-24">{isTa ? 'அளவு' : 'Size'}</th>
                      <th className="px-3 py-2 w-32">{isTa ? 'எண்ணிக்கை' : 'Quantity'}</th>
                      <th className="px-2 py-2 w-10 text-center"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.03] text-zinc-300">
                    {lines.map((line, idx) => (
                      <tr key={idx} className="hover:bg-white/[0.01]">
                        <td className="px-3 py-1.5">
                          <input
                            type="text"
                            value={line.color}
                            onChange={(e) => handleUpdateLine(idx, 'color', e.target.value)}
                            className="w-full bg-transparent border-0 text-xs text-white focus:outline-none"
                          />
                        </td>
                        <td className="px-3 py-1.5">
                          <input
                            type="text"
                            value={line.size}
                            onChange={(e) => handleUpdateLine(idx, 'size', e.target.value)}
                            className="w-full bg-transparent border-0 text-xs text-white focus:outline-none font-mono"
                          />
                        </td>
                        <td className="px-3 py-1.5">
                          <input
                            type="number"
                            value={line.quantity}
                            onChange={(e) => handleUpdateLine(idx, 'quantity', Number(e.target.value))}
                            className="w-full bg-transparent border-0 text-xs text-white focus:outline-none font-mono"
                          />
                        </td>
                        <td className="px-2 py-1.5 text-center">
                          <button
                            type="button"
                            onClick={() => handleRemoveLine(idx)}
                            className="text-zinc-500 hover:text-red-400 transition-colors p-1"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

          </div>

          {/* Bottom Confirmation Bar */}
          <div className="mt-6 pt-4 border-t border-white/[0.06] flex items-center justify-between gap-4">
            <div className="text-[11px] text-zinc-500">
              {isTa ? 'சரிபார்த்து ஆர்டரை இறுதி செய்க' : 'Human verification complete. Ready to store.'}
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => handleLoadPreset('sample_decathlon')}
                className="px-3 py-2 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-zinc-300 text-xs font-medium border border-white/[0.06] transition-all"
              >
                {isTa ? 'மீட்டமை' : 'Reset'}
              </button>

              <button
                type="button"
                disabled={creating || !orderNumber || !buyerId || !styleId}
                onClick={handleConfirmAndCreate}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 text-black text-xs font-semibold flex items-center gap-2 shadow-lg shadow-teal-500/20 disabled:opacity-50 transition-all cursor-pointer"
              >
                {creating ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>{isTa ? 'சேமிக்கப்படுகிறது...' : 'Committing to Supabase...'}</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>{isTa ? 'சுபாபேஸில் ஆர்டரை உறுதிசெய்' : 'Confirm & Create Order in Supabase'}</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

      </div>
    </ToolLayout>
  )
}
