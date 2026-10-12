export interface Buyer {
  id: string
  tenant_id: string
  name: string
  code: string
  country?: string | null
  contact_email?: string | null
  payment_terms?: string | null
}

export interface Style {
  id: string
  tenant_id: string
  buyer_id: string
  style_number: string
  style_name: string
  garment_type: string
  sam: string | number
  target_efficiency: string | number
}

export interface OrderLine {
  id: string
  tenant_id: string
  order_id: string
  color: string
  size: string
  quantity: number
}

export interface OrderMilestone {
  id: string
  tenant_id: string
  order_id: string
  name: string
  planned_date: string
  actual_date?: string | null
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'BLOCKED'
  notes?: string | null
}

export interface Order {
  id: string
  tenant_id: string
  buyer_id: string
  style_id: string
  order_number: string
  total_quantity: number
  unit_price: string | number
  currency: string
  ex_factory_date: string
  planned_sewing_start?: string | null
  status: 'DRAFT' | 'CONFIRMED' | 'IN_PRODUCTION' | 'SHIPPED' | 'CANCELLED'
  buyer?: Buyer
  style?: Style
  lines: OrderLine[]
  milestones: OrderMilestone[]
  created_at?: string
}

export interface CsvImportSummary {
  rows_read: number
  orders_created: number
  lines_created: number
  milestones_created: number
  errors: string[]
}

export interface UserSession {
  id: string
  email: string
  full_name: string
  role: string
  tenant_id: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const DEMO_USERS = [
  {
    role: 'merchandiser',
    label: 'Priya (Lead Merchandiser)',
    email: 'merchandiser@tirupur-demo.com',
    password: 'MerchDemo123!',
  },
  {
    role: 'owner',
    label: 'Senthil (Managing Director)',
    email: 'owner@tirupur-demo.com',
    password: 'OwnerDemo123!',
  },
  {
    role: 'production_manager',
    label: 'Karthik (Production Manager)',
    email: 'production@tirupur-demo.com',
    password: 'ProdDemo123!',
  },
  {
    role: 'store_keeper',
    label: 'Ramesh (Store Keeper)',
    email: 'store@tirupur-demo.com',
    password: 'StoreDemo123!',
  },
  {
    role: 'supervisor',
    label: 'Anand (Floor Supervisor)',
    email: 'supervisor@tirupur-demo.com',
    password: 'SuperDemo123!',
  },
  {
    role: 'viewer',
    label: 'Auditor (Viewer)',
    email: 'viewer@tirupur-demo.com',
    password: 'ViewerDemo123!',
  },
]

export function getStoredToken(): string | null {
  return localStorage.getItem('overclock_token')
}

export function getStoredUser(): UserSession | null {
  const raw = localStorage.getItem('overclock_user')
  if (!raw) return null
  try {
    return JSON.parse(raw) as UserSession
  } catch {
    return null
  }
}

export function setStoredSession(token: string, user: UserSession): void {
  localStorage.setItem('overclock_token', token)
  localStorage.setItem('overclock_user', JSON.stringify(user))
}

export function clearStoredSession(): void {
  localStorage.removeItem('overclock_token')
  localStorage.removeItem('overclock_user')
}

export async function loginWithCredentials(
  email: string, 
  password: string, 
  tenantId: string = 'tirupur-demo'
): Promise<string> {
  const res = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      tenant_id: tenantId,
      email: email,
      password: password,
    }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Authentication failed' }))
    const msg = typeof err.detail === 'string' ? err.detail : 'Login failed'
    throw new Error(msg)
  }

  const data = await res.json()
  setStoredSession(data.access_token, {
    id: data.user_id,
    email: data.email,
    full_name: data.full_name,
    role: data.role,
    tenant_id: data.tenant_id,
  })
  return data.access_token
}

export async function ensureAuthenticated(): Promise<string> {
  const existing = getStoredToken()
  if (existing) return existing

  // Default to merchandiser demo user
  const defaultDemo = DEMO_USERS[0]
  return loginWithCredentials(defaultDemo.email, defaultDemo.password)
}

async function authenticatedFetch(path: string, options: RequestInit = {}): Promise<Response> {
  let token = await ensureAuthenticated()
  const headers = new Headers(options.headers || {})
  headers.set('Authorization', `Bearer ${token}`)

  let res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (res.status === 401) {
    // Attempt re-auth once with current or default demo user
    const user = getStoredUser()
    const demo = DEMO_USERS.find(u => u.email === user?.email) || DEMO_USERS[0]
    token = await loginWithCredentials(demo.email, demo.password)
    headers.set('Authorization', `Bearer ${token}`)
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    })
  }

  return res
}

export async function fetchOrders(): Promise<Order[]> {
  const res = await authenticatedFetch('/api/v1/orders')
  if (!res.ok) {
    throw new Error(`Failed to load orders: ${res.statusText}`)
  }
  return res.json()
}

export async function fetchBuyers(): Promise<Buyer[]> {
  const res = await authenticatedFetch('/api/v1/buyers')
  if (!res.ok) {
    throw new Error(`Failed to load buyers: ${res.statusText}`)
  }
  return res.json()
}

export async function fetchStyles(): Promise<Style[]> {
  const res = await authenticatedFetch('/api/v1/styles')
  if (!res.ok) {
    throw new Error(`Failed to load styles: ${res.statusText}`)
  }
  return res.json()
}

export async function createOrder(data: {
  buyer_id: string
  style_id: string
  order_number: string
  total_quantity: number
  unit_price: number
  currency: string
  ex_factory_date: string
  planned_sewing_start?: string
  lines?: { color: string; size: string; quantity: number }[]
}): Promise<Order> {
  const res = await authenticatedFetch('/api/v1/orders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create order' }))
    throw new Error(err.detail || 'Failed to create order')
  }
  return res.json()
}

export async function updateMilestone(
  orderId: string,
  milestoneId: string,
  update: { status?: string; actual_date?: string | null; notes?: string | null }
): Promise<OrderMilestone> {
  const res = await authenticatedFetch(`/api/v1/orders/${orderId}/milestones/${milestoneId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(update),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to update milestone' }))
    throw new Error(err.detail || 'Failed to update milestone')
  }
  return res.json()
}

export async function uploadOrdersCsv(file: File): Promise<CsvImportSummary> {
  const token = await ensureAuthenticated()
  const formData = new FormData()
  formData.append('file', file)

  const res = await fetch(`${API_BASE_URL}/api/v1/orders/import/csv`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'CSV import request failed' }))
    throw new Error(err.detail || 'CSV import failed')
  }
  return res.json()
}

export async function downloadOrdersCsv(): Promise<Blob> {
  const res = await authenticatedFetch('/api/v1/orders/export/csv')
  if (!res.ok) {
    throw new Error('Failed to export CSV')
  }
  return res.blob()
}

// ==========================================
// PHASE 4: MATERIALS, BOM, STOCK LEDGER & RISK
// ==========================================

export interface Material {
  id: string
  tenant_id: string
  code: string
  name: string
  category: 'FABRIC' | 'TRIM' | 'PACKAGING' | 'CHEMICAL'
  unit_of_measure: string
  minimum_stock_level: number
  unit_cost: number
  currency: string
  current_stock: number
  created_at?: string
  updated_at?: string
}

export interface StyleBomRequirement {
  component_name: string
  material_id: string
  material_code: string
  material_name: string
  unit_of_measure: string
  consumption_per_piece: number
  wastage_percentage: number
  gross_requirement: number
  available_stock: number
  deficit: number
}

export interface Supplier {
  id: string
  tenant_id: string
  name: string
  code: string
  category: string
  contact_email?: string
  contact_phone?: string
  lead_time_days: number
}

export interface SupplierPo {
  id: string
  tenant_id: string
  po_number: string
  supplier_id: string
  material_id: string
  order_id?: string | null
  quantity_ordered: number
  quantity_received: number
  unit_price: number
  expected_delivery_date: string
  status: 'DRAFT' | 'PLACED' | 'PARTIAL_RECEIVED' | 'COMPLETED' | 'CANCELLED'
  supplier_name?: string
  material_name?: string
  created_at?: string
}

export interface StockLedgerEntry {
  id: string
  tenant_id: string
  material_id: string
  movement_type: 'OPENING_BALANCE' | 'GRN_RECEIPT' | 'ISSUE_TO_CUTTING' | 'RETURN_TO_STORE' | 'ADJUSTMENT'
  quantity: number
  unit_cost: number
  reference_type: string
  reference_id?: string | null
  notes?: string | null
  created_at: string
}

export interface RiskAssessment {
  rule: string
  rule_name: string
  order_id: string
  order_number?: string
  buyer_name?: string
  triggered: boolean
  severity: 'NORMAL' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  deficit_qty: number
  days_delayed: number
  headline: string
  explanation: string
  evidence: Record<string, unknown>
}

export interface OrderRiskSummary {
  order_id: string
  order_number: string
  buyer_name?: string
  max_severity: 'NORMAL' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  risks: RiskAssessment[]
}

export async function fetchMaterials(category?: string): Promise<Material[]> {
  const query = category && category !== 'ALL' ? `?category=${category}` : ''
  const res = await authenticatedFetch(`/api/v1/materials${query}`)
  if (!res.ok) {
    throw new Error('Failed to fetch materials')
  }
  return res.json()
}

export async function createMaterial(payload: Partial<Material>): Promise<Material> {
  const res = await authenticatedFetch('/api/v1/materials', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create material' }))
    throw new Error(err.detail || 'Failed to create material')
  }
  return res.json()
}

export async function fetchSuppliers(): Promise<Supplier[]> {
  const res = await authenticatedFetch('/api/v1/suppliers')
  if (!res.ok) {
    throw new Error('Failed to fetch suppliers')
  }
  return res.json()
}

export async function fetchSupplierPos(): Promise<SupplierPo[]> {
  const res = await authenticatedFetch('/api/v1/supplier-pos')
  if (!res.ok) {
    throw new Error('Failed to fetch supplier purchase orders')
  }
  return res.json()
}

export async function fetchStockLedger(materialId?: string): Promise<StockLedgerEntry[]> {
  const query = materialId ? `?material_id=${materialId}` : ''
  const res = await authenticatedFetch(`/api/v1/stock/ledger${query}`)
  if (!res.ok) {
    throw new Error('Failed to fetch stock ledger')
  }
  return res.json()
}

export async function receiveStockGrn(data: {
  material_id: string
  supplier_po_id?: string
  quantity: number
  unit_cost?: number
  notes?: string
}): Promise<StockLedgerEntry> {
  const res = await authenticatedFetch('/api/v1/stock/receive', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to record GRN receipt' }))
    throw new Error(err.detail || 'Failed to record GRN receipt')
  }
  return res.json()
}

export async function issueStockCutting(data: {
  material_id: string
  order_id?: string
  quantity: number
  notes?: string
}): Promise<StockLedgerEntry> {
  const res = await authenticatedFetch('/api/v1/stock/issue', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to issue material' }))
    throw new Error(err.detail || 'Failed to issue material')
  }
  return res.json()
}

export async function fetchStyleBomRequirements(
  styleId: string,
  orderQty: number
): Promise<StyleBomRequirement[]> {
  const res = await authenticatedFetch(
    `/api/v1/styles/${styleId}/bom/calculate?order_qty=${orderQty}`
  )
  if (!res.ok) {
    throw new Error('Failed to calculate BOM requirements')
  }
  return res.json()
}

export async function fetchMaterialRisks(): Promise<OrderRiskSummary[]> {
  const res = await authenticatedFetch('/api/v1/risk/materials')
  if (!res.ok) {
    throw new Error('Failed to evaluate material risks')
  }
  return res.json()
}

// --- Phase 5: Production & Floor Logging ---
export interface ProductionLine {
  id: string
  tenant_id: string
  line_number: string
  name: string
  operator_count: number
  helper_count: number
  daily_working_hours: number | string
  is_active: boolean
  created_at: string
}

export interface DailyProductionLog {
  id: string
  tenant_id: string
  date: string
  order_id: string
  line_id?: string | null
  stage: 'CUTTING' | 'SEWING' | 'FINISHING' | 'PACKING'
  planned_output: number
  actual_output: number
  rejected_qty: number
  operator_count: number
  working_hours: number | string
  notes?: string | null
  created_by_user_id?: string | null
  created_at: string
  produced_minutes: number | string
  available_minutes: number | string
  efficiency_pct: number | string
  rejection_rate_pct: number | string
}

export interface DailyProductionLogCreate {
  date: string
  order_id: string
  line_id?: string
  stage: 'CUTTING' | 'SEWING' | 'FINISHING' | 'PACKING'
  planned_output?: number
  actual_output: number
  rejected_qty?: number
  operator_count?: number
  working_hours?: number
  notes?: string
}

export interface OrderProductionSummary {
  order_id: string
  order_number: string
  total_quantity: number
  ex_factory_date: string
  cumulative_cutting: number
  cumulative_sewing: number
  cumulative_finishing: number
  cumulative_rejected: number
  remaining_sewing_qty: number
  rolling_daily_rate: number | string
  avg_efficiency_pct: number | string
  projected_finish_date?: string | null
  is_on_track: boolean
}

export async function fetchProductionLines(): Promise<ProductionLine[]> {
  const res = await authenticatedFetch('/api/v1/production/lines')
  if (!res.ok) {
    throw new Error('Failed to fetch production lines')
  }
  return res.json()
}

export async function createProductionLine(data: {
  line_number: string
  name: string
  operator_count: number
  helper_count: number
  daily_working_hours: number
  is_active?: boolean
}): Promise<ProductionLine> {
  const res = await authenticatedFetch('/api/v1/production/lines', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create production line' }))
    throw new Error(err.detail || 'Failed to create production line')
  }
  return res.json()
}

export async function fetchDailyProductionLogs(params?: {
  order_id?: string
  line_id?: string
  stage?: string
  limit?: number
}): Promise<DailyProductionLog[]> {
  const query = new URLSearchParams()
  if (params?.order_id) query.append('order_id', params.order_id)
  if (params?.line_id) query.append('line_id', params.line_id)
  if (params?.stage) query.append('stage', params.stage)
  if (params?.limit) query.append('limit', String(params.limit))

  const res = await authenticatedFetch(`/api/v1/production/logs?${query.toString()}`)
  if (!res.ok) {
    throw new Error('Failed to fetch daily production logs')
  }
  return res.json()
}

export async function createDailyProductionLog(
  data: DailyProductionLogCreate
): Promise<DailyProductionLog> {
  const res = await authenticatedFetch('/api/v1/production/logs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to log daily production' }))
    throw new Error(err.detail || 'Failed to log daily production')
  }
  return res.json()
}

export async function fetchOrderProductionSummary(
  orderId: string
): Promise<OrderProductionSummary> {
  const res = await authenticatedFetch(`/api/v1/production/orders/${orderId}/summary`)
  if (!res.ok) {
    throw new Error('Failed to fetch order production summary')
  }
  return res.json()
}

export async function fetchProductionRisks(): Promise<RiskAssessment[]> {
  const res = await authenticatedFetch('/api/v1/risk/production')
  if (!res.ok) {
    throw new Error('Failed to evaluate production risks')
  }
  return res.json()
}

// --- Milestone 1 & 2: Job-Work Hub & Unified Risk Types & APIs ---
export interface JobworkProcessor {
  id: string
  tenant_id: string
  name: string
  process_type: 'DYEING' | 'PRINTING' | 'EMBROIDERY' | 'WASHING' | 'COMPACTING'
  contact_person?: string | null
  phone?: string | null
  address?: string | null
  is_active: boolean
  created_at: string
}

export interface JobworkProcessorCreate {
  name: string
  process_type: string
  contact_person?: string
  phone?: string
  address?: string
  is_active?: boolean
}

export interface JobworkChallan {
  id: string
  tenant_id: string
  challan_number: string
  challan_type: 'OUTWARD_ISSUE' | 'INWARD_RECEIPT'
  processor_id: string
  processor_name: string
  order_id?: string | null
  process_name: string
  material_description: string
  issued_qty: number
  issued_weight_kg: number
  expected_return_date: string
  actual_return_date?: string | null
  received_qty: number
  received_weight_kg: number
  status: 'ISSUED' | 'PARTIAL_RECEIVED' | 'COMPLETED' | 'CANCELLED'
  notes?: string | null
  created_at: string
  weight_loss_kg: number
  weight_loss_pct: number
  is_loss_anomaly: boolean
}

export interface JobworkChallanCreate {
  challan_number: string
  challan_type?: string
  processor_id: string
  order_id?: string
  process_name: string
  material_description: string
  issued_qty: number
  issued_weight_kg: number
  expected_return_date: string
  notes?: string
}

export interface JobworkChallanReceive {
  received_qty: number
  received_weight_kg: number
  actual_return_date?: string
  notes?: string
}

export async function fetchJobworkProcessors(): Promise<JobworkProcessor[]> {
  const res = await authenticatedFetch('/api/v1/jobwork/processors')
  if (!res.ok) {
    throw new Error('Failed to fetch job-work processors')
  }
  return res.json()
}

export async function createJobworkProcessor(data: JobworkProcessorCreate): Promise<JobworkProcessor> {
  const res = await authenticatedFetch('/api/v1/jobwork/processors', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create processor' }))
    throw new Error(err.detail || 'Failed to create processor')
  }
  return res.json()
}

export async function fetchJobworkChallans(params?: {
  order_id?: string
  processor_id?: string
  challan_status?: string
  limit?: number
}): Promise<JobworkChallan[]> {
  const query = new URLSearchParams()
  if (params?.order_id) query.append('order_id', params.order_id)
  if (params?.processor_id) query.append('processor_id', params.processor_id)
  if (params?.challan_status) query.append('challan_status', params.challan_status)
  if (params?.limit) query.append('limit', String(params.limit))

  const res = await authenticatedFetch(`/api/v1/jobwork/challans?${query.toString()}`)
  if (!res.ok) {
    throw new Error('Failed to fetch job-work challans')
  }
  return res.json()
}

export async function issueJobworkChallan(data: JobworkChallanCreate): Promise<JobworkChallan> {
  const res = await authenticatedFetch('/api/v1/jobwork/challans', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to issue challan' }))
    throw new Error(err.detail || 'Failed to issue challan')
  }
  return res.json()
}

export async function receiveJobworkChallan(
  challanId: string,
  data: JobworkChallanReceive
): Promise<JobworkChallan> {
  const res = await authenticatedFetch(`/api/v1/jobwork/challans/${challanId}/receive`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to record inward challan' }))
    throw new Error(err.detail || 'Failed to record inward challan')
  }
  return res.json()
}

export async function fetchJobworkRisks(): Promise<RiskAssessment[]> {
  const res = await authenticatedFetch('/api/v1/risk/jobwork')
  if (!res.ok) {
    throw new Error('Failed to evaluate job-work risks')
  }
  return res.json()
}

export async function fetchUnifiedRiskMatrix(): Promise<OrderRiskSummary[]> {
  const res = await authenticatedFetch('/api/v1/risk/evaluate')
  if (!res.ok) {
    throw new Error('Failed to evaluate unified risk matrix')
  }
  return res.json()
}

export async function fetchOrderRiskMatrix(orderId: string): Promise<OrderRiskSummary> {
  const res = await authenticatedFetch(`/api/v1/risk/orders/${orderId}`)
  if (!res.ok) {
    throw new Error('Failed to evaluate order risks')
  }
  return res.json()
}

// --- AI / Layout PO Extraction ---
export interface ExtractedField<T = any> {
  value: T
  confidence: number
  source: string
}

export interface ExtractedLineItem {
  color: string
  size: string
  quantity: number
  confidence: number
}

export interface PoExtractionResult {
  order_number: ExtractedField<string>
  buyer_name: ExtractedField<string>
  buyer_id?: string
  buyer_code?: string
  style_number: ExtractedField<string>
  style_name?: string
  style_id?: string
  total_quantity: ExtractedField<number>
  unit_price: ExtractedField<number>
  currency: ExtractedField<string>
  ex_factory_date: ExtractedField<string>
  planned_sewing_start: ExtractedField<string>
  lines: ExtractedLineItem[]
  raw_preview_text: string
  warnings: string[]
  extraction_source: string
}

export async function extractPurchaseOrder(options: {
  file?: File
  sampleId?: string
}): Promise<PoExtractionResult> {
  let path = '/api/v1/orders/extract-po'
  if (options.sampleId) {
    path += `?sample_id=${encodeURIComponent(options.sampleId)}`
  }

  let body: FormData | undefined = undefined
  if (options.file) {
    body = new FormData()
    body.append('file', options.file)
  }

  const res = await authenticatedFetch(path, {
    method: 'POST',
    body,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to extract purchase order' }))
    throw new Error(err.detail || 'Extraction failed')
  }

  return res.json()
}


