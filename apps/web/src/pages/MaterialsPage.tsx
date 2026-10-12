import React, { useEffect, useState } from 'react'
import { ToolLayout } from '../components/layout/ToolLayout'
import {
  Plus,
  History,
  AlertTriangle,
  CheckCircle2,
  Package,
  Truck,
  Calculator,
  Search,
  ArrowDownLeft,
  RefreshCw,
  ShieldCheck,
  X,
} from 'lucide-react'
import {
  fetchMaterials,
  createMaterial,
  fetchSuppliers,
  fetchSupplierPos,
  fetchStockLedger,
  receiveStockGrn,
  fetchStyleBomRequirements,
  fetchMaterialRisks,
  fetchStyles,
  Material,
  Supplier,
  SupplierPo,
  StockLedgerEntry,
  StyleBomRequirement,
  OrderRiskSummary,
  Style,
} from '../lib/api'

type ActiveTab = 'catalog' | 'bom' | 'pos' | 'risks' | 'ledger'

export const MaterialsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('catalog')
  const [materials, setMaterials] = useState<Material[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [supplierPos, setSupplierPos] = useState<SupplierPo[]>([])
  const [ledgerEntries, setLedgerEntries] = useState<StockLedgerEntry[]>([])
  const [riskSummaries, setRiskSummaries] = useState<OrderRiskSummary[]>([])
  const [styles, setStyles] = useState<Style[]>([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters & Search
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL')
  const [searchQuery, setSearchQuery] = useState('')

  // BOM Calculator state
  const [selectedStyleId, setSelectedStyleId] = useState<string>('')
  const [calculatorOrderQty, setCalculatorOrderQty] = useState<number>(2500)
  const [bomRequirements, setBomRequirements] = useState<StyleBomRequirement[]>([])
  const [calcLoading, setCalcLoading] = useState(false)

  // Modals
  const [showGrnModal, setShowGrnModal] = useState(false)
  const [showAddMaterialModal, setShowAddMaterialModal] = useState(false)
  const [grnMaterialId, setGrnMaterialId] = useState('')
  const [grnSupplierPoId, setGrnSupplierPoId] = useState('')
  const [grnQty, setGrnQty] = useState<number>(500)
  const [grnCost, setGrnCost] = useState<number>(340)
  const [grnNotes, setGrnNotes] = useState('')
  const [submittingGrn, setSubmittingGrn] = useState(false)

  // New Material form state
  const [newMatCode, setNewMatCode] = useState('')
  const [newMatName, setNewMatName] = useState('')
  const [newMatCategory, setNewMatCategory] = useState<'FABRIC' | 'TRIM' | 'PACKAGING'>('FABRIC')
  const [newMatUom, setNewMatUom] = useState('KG')
  const [newMatMinStock, setNewMatMinStock] = useState<number>(100)
  const [newMatCost, setNewMatCost] = useState<number>(320)
  const [submittingMat, setSubmittingMat] = useState(false)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [mats, sups, pos, ledger, risks, stList] = await Promise.all([
        fetchMaterials(),
        fetchSuppliers(),
        fetchSupplierPos(),
        fetchStockLedger(),
        fetchMaterialRisks().catch(() => []),
        fetchStyles().catch(() => []),
      ])
      setMaterials(mats)
      setSuppliers(sups)
      setSupplierPos(pos)
      setLedgerEntries(ledger)
      setRiskSummaries(risks)
      setStyles(stList)

      if (stList.length > 0 && !selectedStyleId) {
        setSelectedStyleId(stList[0].id)
      }
      if (mats.length > 0 && !grnMaterialId) {
        setGrnMaterialId(mats[0].id)
      }
    } catch (err: unknown) {
      console.error(err)
      setError(err instanceof Error ? err.message : 'Failed to load materials and inventory')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Calculate BOM requirements when style or order qty changes
  useEffect(() => {
    if (!selectedStyleId || calculatorOrderQty <= 0) return
    let isCurrent = true
    setCalcLoading(true)
    fetchStyleBomRequirements(selectedStyleId, calculatorOrderQty)
      .then((reqs) => {
        if (isCurrent) setBomRequirements(reqs)
      })
      .catch((e) => console.error(e))
      .finally(() => {
        if (isCurrent) setCalcLoading(false)
      })
    return () => {
      isCurrent = false
    }
  }, [selectedStyleId, calculatorOrderQty])

  // Valuation calculation
  const totalValuationInr = materials.reduce(
    (acc, m) => acc + (m.current_stock || 0) * (m.unit_cost || 0),
    0
  )
  const valuationLakhs = (totalValuationInr / 100000).toFixed(2)

  // Risk count
  const criticalRiskCount = riskSummaries.reduce(
    (acc, s) => acc + s.risks.filter((r) => r.triggered).length,
    0
  )

  const filteredMaterials = materials.filter((m) => {
    const matchesCat = categoryFilter === 'ALL' || m.category === categoryFilter
    const matchesSearch =
      m.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.name.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesCat && matchesSearch
  })

  const handleReceiveGrn = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!grnMaterialId || grnQty <= 0) return
    setSubmittingGrn(true)
    try {
      await receiveStockGrn({
        material_id: grnMaterialId,
        supplier_po_id: grnSupplierPoId || undefined,
        quantity: grnQty,
        unit_cost: grnCost,
        notes: grnNotes || 'Store inward GRN',
      })
      setShowGrnModal(false)
      setGrnNotes('')
      await loadData()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to post GRN')
    } finally {
      setSubmittingGrn(false)
    }
  }

  const handleCreateMaterial = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMatCode || !newMatName) return
    setSubmittingMat(true)
    try {
      await createMaterial({
        code: newMatCode.toUpperCase(),
        name: newMatName,
        category: newMatCategory,
        unit_of_measure: newMatUom,
        minimum_stock_level: newMatMinStock,
        unit_cost: newMatCost,
        currency: 'INR',
      })
      setShowAddMaterialModal(false)
      setNewMatCode('')
      setNewMatName('')
      await loadData()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to create material')
    } finally {
      setSubmittingMat(false)
    }
  }

  return (
    <ToolLayout
      toolName="Materials, BOM & Stock Ledger"
      toolTag="Store & Inventory"
      description="Material specifications, style consumption formulas, double-entry immutable stock ledger, and deterministic risk rules (R1 Fabric Deficit & R2 Trim Shortage)."
      actions={
        <div className="flex items-center gap-2">
          <button
            onClick={() => loadData()}
            className="p-1.5 rounded-lg border border-white/[0.08] bg-white/[0.03] hover:bg-white/[0.06] text-zinc-300 transition-colors"
            title="Refresh inventory"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowGrnModal(true)}
            className="px-3 py-1.5 rounded-lg border border-teal-500/30 bg-teal-500/10 hover:bg-teal-500/20 text-teal-400 text-xs font-semibold inline-flex items-center gap-1.5 transition-colors"
          >
            <ArrowDownLeft className="w-3.5 h-3.5" />
            <span>Receive Goods (GRN)</span>
          </button>
          <button
            onClick={() => setShowAddMaterialModal(true)}
            className="px-3 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-[#090a0f] font-semibold text-xs inline-flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Material</span>
          </button>
        </div>
      }
    >
      <div className="space-y-4">
        {error && (
          <div className="rounded-xl bg-rose-500/10 border border-rose-500/20 p-3 text-xs text-rose-400 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-zinc-400 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
        {/* Metric Cards Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-4 space-y-1">
            <div className="flex items-center justify-between text-zinc-500 text-[10px] font-mono uppercase tracking-wider">
              <span>Catalog Master Items</span>
              <Package className="w-3.5 h-3.5 text-zinc-400" />
            </div>
            <div className="text-2xl font-bold text-white tabular-nums">{materials.length}</div>
            <div className="text-[11px] text-zinc-400">
              {materials.filter((m) => m.category === 'FABRIC').length} Fabrics ·{' '}
              {materials.filter((m) => m.category === 'TRIM').length} Trims
            </div>
          </div>

          <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-4 space-y-1">
            <div className="flex items-center justify-between text-zinc-500 text-[10px] font-mono uppercase tracking-wider">
              <span>On-Hand Valuation</span>
              <ShieldCheck className="w-3.5 h-3.5 text-teal-400" />
            </div>
            <div className="text-2xl font-bold text-white tabular-nums">
              ₹ {valuationLakhs} <span className="text-xs font-normal text-zinc-400">Lakhs</span>
            </div>
            <div className="text-[11px] text-zinc-400">Derived from ledger ledger transactions</div>
          </div>

          <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-4 space-y-1">
            <div className="flex items-center justify-between text-zinc-500 text-[10px] font-mono uppercase tracking-wider">
              <span>Inbound Supplier POs</span>
              <Truck className="w-3.5 h-3.5 text-zinc-400" />
            </div>
            <div className="text-2xl font-bold text-white tabular-nums">
              {supplierPos.filter((p) => p.status === 'PLACED' || p.status === 'PARTIAL_RECEIVED').length}
            </div>
            <div className="text-[11px] text-zinc-400">
              Across {suppliers.length} registered mills & vendors
            </div>
          </div>

          <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-4 space-y-1">
            <div className="flex items-center justify-between text-zinc-500 text-[10px] font-mono uppercase tracking-wider">
              <span>Active Risk Flags (R1/R2)</span>
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
              {criticalRiskCount > 0 ? 'Action required on critical delays' : 'All materials on schedule'}
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-white/[0.06] flex items-center justify-between">
          <div className="flex items-center gap-1">
            <button
              onClick={() => setActiveTab('catalog')}
              className={`px-3.5 py-2.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === 'catalog'
                  ? 'border-teal-500 text-teal-400 font-semibold'
                  : 'border-transparent text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Package className="w-3.5 h-3.5" />
              <span>Stock Catalog ({materials.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('bom')}
              className={`px-3.5 py-2.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === 'bom'
                  ? 'border-teal-500 text-teal-400 font-semibold'
                  : 'border-transparent text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Calculator className="w-3.5 h-3.5" />
              <span>Style BOM Calculator</span>
            </button>
            <button
              onClick={() => setActiveTab('pos')}
              className={`px-3.5 py-2.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === 'pos'
                  ? 'border-teal-500 text-teal-400 font-semibold'
                  : 'border-transparent text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Truck className="w-3.5 h-3.5" />
              <span>Supplier POs ({supplierPos.length})</span>
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
              onClick={() => setActiveTab('ledger')}
              className={`px-3.5 py-2.5 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === 'ledger'
                  ? 'border-teal-500 text-teal-400 font-semibold'
                  : 'border-transparent text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <History className="w-3.5 h-3.5" />
              <span>Immutable Ledger ({ledgerEntries.length})</span>
            </button>
          </div>
        </div>

        {/* Tab 1: Catalog & Stock */}
        {activeTab === 'catalog' && (
          <div className="space-y-3">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <div className="relative flex-1 sm:w-64">
                  <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search material code or name..."
                    className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-[#0d0e14] border border-white/[0.08] text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-teal-500"
                  />
                </div>
                <div className="flex items-center gap-1 bg-[#0d0e14] p-1 rounded-lg border border-white/[0.08]">
                  {['ALL', 'FABRIC', 'TRIM', 'PACKAGING'].map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setCategoryFilter(cat)}
                      className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${
                        categoryFilter === cat
                          ? 'bg-teal-500/20 text-teal-300'
                          : 'text-zinc-400 hover:text-white'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-white/[0.06] text-zinc-400 font-mono text-[11px]">
                    <th className="py-3 px-4">CODE</th>
                    <th className="py-3 px-4">DESCRIPTION</th>
                    <th className="py-3 px-4">CATEGORY</th>
                    <th className="py-3 px-4">UOM</th>
                    <th className="py-3 px-4 text-right">UNIT COST (₹)</th>
                    <th className="py-3 px-4 text-right">MIN LEVEL</th>
                    <th className="py-3 px-4 text-right">ON-HAND STOCK</th>
                    <th className="py-3 px-4 text-center">STATUS</th>
                    <th className="py-3 px-4 text-right">ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {filteredMaterials.map((mat) => {
                    const isLow = (mat.current_stock || 0) < (mat.minimum_stock_level || 0)
                    return (
                      <tr key={mat.id} className="hover:bg-white/[0.02] transition-colors">
                        <td className="py-3 px-4 font-mono font-medium text-white">{mat.code}</td>
                        <td className="py-3 px-4 text-zinc-200">{mat.name}</td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase ${
                              mat.category === 'FABRIC'
                                ? 'bg-indigo-500/10 text-indigo-300 border border-indigo-500/20'
                                : mat.category === 'TRIM'
                                ? 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
                                : 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                            }`}
                          >
                            {mat.category}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono text-zinc-400">{mat.unit_of_measure}</td>
                        <td className="py-3 px-4 text-right font-mono text-zinc-300">
                          ₹{Number(mat.unit_cost).toFixed(2)}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-zinc-400">
                          {Number(mat.minimum_stock_level).toFixed(1)}
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-bold text-white">
                          {Number(mat.current_stock || 0).toFixed(1)}
                        </td>
                        <td className="py-3 px-4 text-center">
                          {isLow ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                              Low Stock
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                              Optimal
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => {
                              setGrnMaterialId(mat.id)
                              setGrnCost(Number(mat.unit_cost))
                              setShowGrnModal(true)
                            }}
                            className="px-2 py-1 rounded bg-white/[0.04] hover:bg-teal-500/20 hover:text-teal-300 text-zinc-300 text-[11px] font-medium transition-colors"
                          >
                            + Inward
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                  {filteredMaterials.length === 0 && (
                    <tr>
                      <td colSpan={9} className="py-8 text-center text-zinc-500 text-xs">
                        No materials found matching criteria.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 2: Style BOM Calculator */}
        {activeTab === 'bom' && (
          <div className="space-y-4">
            <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-4 flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="flex flex-col sm:flex-row items-center gap-3 w-full md:w-auto">
                <div className="w-full sm:w-72">
                  <label className="text-[10px] font-mono text-zinc-400 uppercase block mb-1">
                    Select Garment Style
                  </label>
                  <select
                    value={selectedStyleId}
                    onChange={(e) => setSelectedStyleId(e.target.value)}
                    className="w-full px-3 py-1.5 rounded-lg bg-black border border-white/[0.08] text-xs text-white focus:outline-none focus:border-teal-500"
                  >
                    {styles.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.style_number} — {s.style_name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="w-full sm:w-44">
                  <label className="text-[10px] font-mono text-zinc-400 uppercase block mb-1">
                    Order Quantity (Pcs)
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={calculatorOrderQty}
                    onChange={(e) => setCalculatorOrderQty(Number(e.target.value))}
                    className="w-full px-3 py-1.5 rounded-lg bg-black border border-white/[0.08] text-xs text-white font-mono focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <div className="text-right text-xs text-zinc-400">
                Formula: <span className="font-mono text-teal-400">gross_req = Qty × Cons × (1 + Waste%)</span>
              </div>
            </div>

            <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-white/[0.06] text-zinc-400 font-mono text-[11px]">
                    <th className="py-3 px-4">COMPONENT</th>
                    <th className="py-3 px-4">MATERIAL SPEC</th>
                    <th className="py-3 px-4 text-right">CONSUMPTION/PC</th>
                    <th className="py-3 px-4 text-right">WASTAGE %</th>
                    <th className="py-3 px-4 text-right">GROSS REQUIREMENT</th>
                    <th className="py-3 px-4 text-right">ON-HAND STOCK</th>
                    <th className="py-3 px-4 text-right">DEFICIT / SHORTAGE</th>
                    <th className="py-3 px-4 text-center">STATUS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {bomRequirements.map((req, idx) => {
                    const isShort = Number(req.deficit) > 0
                    return (
                      <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                        <td className="py-3 px-4 font-medium text-white">{req.component_name}</td>
                        <td className="py-3 px-4">
                          <span className="font-mono text-zinc-300 font-semibold">{req.material_code}</span>
                          <span className="text-zinc-500 text-[11px] block">{req.material_name}</span>
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-zinc-300">
                          {Number(req.consumption_per_piece).toFixed(4)} {req.unit_of_measure}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-zinc-400">
                          {Number(req.wastage_percentage).toFixed(1)}%
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-bold text-white">
                          {Number(req.gross_requirement).toFixed(2)} {req.unit_of_measure}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-zinc-300">
                          {Number(req.available_stock).toFixed(2)} {req.unit_of_measure}
                        </td>
                        <td
                          className={`py-3 px-4 text-right font-mono font-bold ${
                            isShort ? 'text-amber-400' : 'text-emerald-400'
                          }`}
                        >
                          {isShort
                            ? `-${Number(req.deficit).toFixed(2)} ${req.unit_of_measure}`
                            : 'Fulfilled'}
                        </td>
                        <td className="py-3 px-4 text-center">
                          {isShort ? (
                            <span className="px-2 py-0.5 rounded-full text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                              Need Procurement
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-full text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                              Ready
                            </span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                  {bomRequirements.length === 0 && (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-zinc-500 text-xs">
                        {calcLoading ? 'Calculating mathematical requirement...' : 'No BOM lines recorded for this style.'}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: Supplier POs & Inward */}
        {activeTab === 'pos' && (
          <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-white/[0.06] text-zinc-400 font-mono text-[11px]">
                  <th className="py-3 px-4">PO NUMBER</th>
                  <th className="py-3 px-4">SUPPLIER</th>
                  <th className="py-3 px-4">MATERIAL ORDERED</th>
                  <th className="py-3 px-4 text-right">ORDERED</th>
                  <th className="py-3 px-4 text-right">RECEIVED</th>
                  <th className="py-3 px-4">FULFILLMENT</th>
                  <th className="py-3 px-4">EXPECTED ARRIVAL</th>
                  <th className="py-3 px-4 text-center">STATUS</th>
                  <th className="py-3 px-4 text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {supplierPos.map((po) => {
                  const pct = Math.min(
                    100,
                    Math.round(((po.quantity_received || 0) / po.quantity_ordered) * 100)
                  )
                  return (
                    <tr key={po.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3 px-4 font-mono font-medium text-white">{po.po_number}</td>
                      <td className="py-3 px-4 text-zinc-200">{po.supplier_name || 'Vendor'}</td>
                      <td className="py-3 px-4 text-zinc-300">{po.material_name || 'Material'}</td>
                      <td className="py-3 px-4 text-right font-mono text-zinc-300">
                        {Number(po.quantity_ordered).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-white font-bold">
                        {Number(po.quantity_received || 0).toLocaleString()}
                      </td>
                      <td className="py-3 px-4">
                        <div className="w-24 bg-white/[0.08] h-1.5 rounded-full overflow-hidden">
                          <div className="bg-teal-500 h-full" style={{ width: `${pct}%` }} />
                        </div>
                        <span className="text-[10px] font-mono text-zinc-400">{pct}%</span>
                      </td>
                      <td className="py-3 px-4 font-mono text-zinc-400">{po.expected_delivery_date}</td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-mono uppercase ${
                            po.status === 'COMPLETED'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : po.status === 'PARTIAL_RECEIVED'
                              ? 'bg-teal-500/10 text-teal-300 border border-teal-500/20'
                              : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          }`}
                        >
                          {po.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        {po.status !== 'COMPLETED' && (
                          <button
                            onClick={() => {
                              setGrnMaterialId(po.material_id)
                              setGrnSupplierPoId(po.id)
                              setGrnQty(Number(po.quantity_ordered) - Number(po.quantity_received || 0))
                              setGrnCost(Number(po.unit_price))
                              setShowGrnModal(true)
                            }}
                            className="px-2 py-1 rounded bg-teal-500/10 hover:bg-teal-500/20 text-teal-400 text-[11px] font-medium transition-colors"
                          >
                            Receive GRN
                          </button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 4: Deterministic Risk Rules (R1 & R2) */}
        {activeTab === 'risks' && (
          <div className="space-y-4">
            <div className="rounded-xl bg-amber-500/5 border border-amber-500/20 p-4 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-semibold text-white">
                  Deterministic Risk Engine Rules (R1 & R2 Active)
                </h4>
                <p className="text-xs text-zinc-400 mt-1">
                  100% mathematical calculations with zero hallucinated LLM values. Rule R1 computes
                  fabric deficit against the order TNA Fabric In-House milestone. Rule R2 checks for trim
                  shortages 7 days before sewing start.
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {riskSummaries.map((summary) => {
                const activeRisks = summary.risks.filter((r) => r.triggered)
                if (activeRisks.length === 0) return null
                return (
                  <div
                    key={summary.order_id}
                    className="rounded-xl bg-[#0d0e14] border border-white/[0.08] overflow-hidden"
                  >
                    <div className="p-4 border-b border-white/[0.04] flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm font-bold text-white">
                          {summary.order_number}
                        </span>
                        <span className="text-zinc-400 text-xs">· {summary.buyer_name}</span>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          summary.max_severity === 'CRITICAL'
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                            : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        }`}
                      >
                        {summary.max_severity} RISK
                      </span>
                    </div>

                    <div className="p-4 space-y-3">
                      {activeRisks.map((risk, i) => (
                        <div
                          key={i}
                          className="rounded-lg bg-black/40 border border-white/[0.04] p-3 space-y-2"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-xs font-semibold text-teal-400">
                              [{risk.rule}] {risk.rule_name}
                            </span>
                            <span className="text-xs text-amber-400 font-mono font-medium">
                              Deficit: {Number(risk.deficit_qty).toFixed(1)} Units
                            </span>
                          </div>
                          <p className="text-xs text-zinc-300 font-medium">{risk.headline}</p>
                          <p className="text-xs text-zinc-400 leading-relaxed">{risk.explanation}</p>

                          {/* Evidence Accordion / Box */}
                          <div className="mt-2 pt-2 border-t border-white/[0.04] text-[11px] font-mono text-zinc-400 grid grid-cols-2 sm:grid-cols-4 gap-2">
                            {Object.entries(risk.evidence)
                              .filter(([k]) => k !== 'shortages')
                              .map(([k, v]) => (
                                <div key={k} className="bg-white/[0.02] p-1.5 rounded">
                                  <span className="text-zinc-500 block text-[9px] uppercase">{k}</span>
                                  <span className="text-white font-medium">{String(v)}</span>
                                </div>
                              ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}

              {riskSummaries.every((s) => s.risks.filter((r) => r.triggered).length === 0) && (
                <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] p-10 text-center space-y-2">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
                  <h4 className="text-xs font-semibold text-white">All Orders Material Ready</h4>
                  <p className="text-xs text-zinc-400 max-w-sm mx-auto">
                    All fabric requirements and trims are verified on-hand or arriving prior to TNA milestone dates.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 5: Immutable Ledger */}
        {activeTab === 'ledger' && (
          <div className="rounded-xl bg-[#0d0e14] border border-white/[0.06] overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-white/[0.06] text-zinc-400 font-mono text-[11px]">
                  <th className="py-3 px-4">TIMESTAMP</th>
                  <th className="py-3 px-4">MOVEMENT TYPE</th>
                  <th className="py-3 px-4 text-right">QUANTITY</th>
                  <th className="py-3 px-4 text-right">UNIT COST (₹)</th>
                  <th className="py-3 px-4">REFERENCE</th>
                  <th className="py-3 px-4">NOTES</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {ledgerEntries.map((entry) => {
                  const isPositive = Number(entry.quantity) >= 0
                  return (
                    <tr key={entry.id} className="hover:bg-white/[0.02] transition-colors font-mono">
                      <td className="py-3 px-4 text-zinc-400">{new Date(entry.created_at).toLocaleString()}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            isPositive
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}
                        >
                          {entry.movement_type}
                        </span>
                      </td>
                      <td
                        className={`py-3 px-4 text-right font-bold ${
                          isPositive ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                      >
                        {isPositive ? `+${Number(entry.quantity).toFixed(2)}` : Number(entry.quantity).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right text-zinc-300">
                        ₹{Number(entry.unit_cost).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-zinc-400">
                        {entry.reference_type}
                        {entry.reference_id && ` (${entry.reference_id})`}
                      </td>
                      <td className="py-3 px-4 text-zinc-400 font-sans">{entry.notes || '—'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Receive GRN Modal */}
      {showGrnModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0f1118] border border-white/[0.08] rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <ArrowDownLeft className="w-4 h-4 text-teal-400" />
                Goods Receipt Note (GRN Inward)
              </h3>
              <button
                onClick={() => setShowGrnModal(false)}
                className="text-zinc-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleReceiveGrn} className="space-y-3.5 text-xs">
              <div>
                <label className="text-zinc-400 font-mono text-[10px] uppercase block mb-1">
                  Material
                </label>
                <select
                  value={grnMaterialId}
                  onChange={(e) => setGrnMaterialId(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-black border border-white/[0.08] text-white focus:outline-none focus:border-teal-500"
                >
                  {materials.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.code} — {m.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-zinc-400 font-mono text-[10px] uppercase block mb-1">
                  Linked Supplier PO (Optional)
                </label>
                <select
                  value={grnSupplierPoId}
                  onChange={(e) => setGrnSupplierPoId(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-black border border-white/[0.08] text-white focus:outline-none focus:border-teal-500"
                >
                  <option value="">Direct Store Inward (No PO link)</option>
                  {supplierPos.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.po_number} ({p.supplier_name} - {p.quantity_ordered} pcs)
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-zinc-400 font-mono text-[10px] uppercase block mb-1">
                    Inward Quantity
                  </label>
                  <input
                    type="number"
                    step="any"
                    min="0.001"
                    required
                    value={grnQty}
                    onChange={(e) => setGrnQty(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg bg-black border border-white/[0.08] text-white font-mono focus:outline-none focus:border-teal-500"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 font-mono text-[10px] uppercase block mb-1">
                    Unit Cost (₹)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={grnCost}
                    onChange={(e) => setGrnCost(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg bg-black border border-white/[0.08] text-white font-mono focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-zinc-400 font-mono text-[10px] uppercase block mb-1">
                  Receiving Inspection Notes
                </label>
                <input
                  type="text"
                  value={grnNotes}
                  onChange={(e) => setGrnNotes(e.target.value)}
                  placeholder="e.g. Lot 402, 10 rolls checked, 0 shade variation"
                  className="w-full px-3 py-2 rounded-lg bg-black border border-white/[0.08] text-white focus:outline-none focus:border-teal-500"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowGrnModal(false)}
                  className="px-3.5 py-1.5 rounded-lg border border-white/[0.08] text-zinc-300 hover:bg-white/[0.04]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingGrn}
                  className="px-4 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-black font-semibold"
                >
                  {submittingGrn ? 'Posting...' : 'Post Inward GRN'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Material Modal */}
      {showAddMaterialModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0f1118] border border-white/[0.08] rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Plus className="w-4 h-4 text-teal-400" />
                Add New Material Specification
              </h3>
              <button
                onClick={() => setShowAddMaterialModal(false)}
                className="text-zinc-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateMaterial} className="space-y-3.5 text-xs">
              <div>
                <label className="text-zinc-400 font-mono text-[10px] uppercase block mb-1">
                  Material Code
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. FAB-SJ-200"
                  value={newMatCode}
                  onChange={(e) => setNewMatCode(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-black border border-white/[0.08] text-white font-mono focus:outline-none focus:border-teal-500"
                />
              </div>

              <div>
                <label className="text-zinc-400 font-mono text-[10px] uppercase block mb-1">
                  Material Name / Specification
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 100% Combed Cotton Single Jersey 200 GSM"
                  value={newMatName}
                  onChange={(e) => setNewMatName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-black border border-white/[0.08] text-white focus:outline-none focus:border-teal-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-zinc-400 font-mono text-[10px] uppercase block mb-1">
                    Category
                  </label>
                  <select
                    value={newMatCategory}
                    onChange={(e) => setNewMatCategory(e.target.value as 'FABRIC' | 'TRIM' | 'PACKAGING')}
                    className="w-full px-3 py-2 rounded-lg bg-black border border-white/[0.08] text-white focus:outline-none focus:border-teal-500"
                  >
                    <option value="FABRIC">FABRIC</option>
                    <option value="TRIM">TRIM</option>
                    <option value="PACKAGING">PACKAGING</option>
                  </select>
                </div>
                <div>
                  <label className="text-zinc-400 font-mono text-[10px] uppercase block mb-1">
                    Unit of Measure
                  </label>
                  <select
                    value={newMatUom}
                    onChange={(e) => setNewMatUom(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-black border border-white/[0.08] text-white font-mono focus:outline-none focus:border-teal-500"
                  >
                    <option value="KG">KG</option>
                    <option value="METER">METER</option>
                    <option value="PIECE">PIECE</option>
                    <option value="CONE">CONE</option>
                    <option value="ROLL">ROLL</option>
                    <option value="BOX">BOX</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-zinc-400 font-mono text-[10px] uppercase block mb-1">
                    Unit Cost (₹)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={newMatCost}
                    onChange={(e) => setNewMatCost(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg bg-black border border-white/[0.08] text-white font-mono focus:outline-none focus:border-teal-500"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 font-mono text-[10px] uppercase block mb-1">
                    Min Stock Alert
                  </label>
                  <input
                    type="number"
                    step="any"
                    min="0"
                    value={newMatMinStock}
                    onChange={(e) => setNewMatMinStock(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg bg-black border border-white/[0.08] text-white font-mono focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddMaterialModal(false)}
                  className="px-3.5 py-1.5 rounded-lg border border-white/[0.08] text-zinc-300 hover:bg-white/[0.04]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingMat}
                  className="px-4 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-black font-semibold"
                >
                  {submittingMat ? 'Saving...' : 'Save Material'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </ToolLayout>
  )
}
