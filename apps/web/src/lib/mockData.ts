import { 
  Order, 
  Buyer, 
  Style, 
  Material, 
  Supplier, 
  SupplierPo, 
  StockLedgerEntry, 
  ProductionLine, 
  DailyProductionLog, 
  JobworkProcessor, 
  JobworkChallan, 
  OrderRiskSummary
} from './api'

export const MOCK_BUYERS: Buyer[] = [
  {
    id: 'b1111111-1111-1111-1111-111111111111',
    tenant_id: 'tirupur-demo',
    name: 'H&M Global Sourcing',
    code: 'HMG',
    country: 'Sweden',
    contact_email: 'buyer@hm.com',
    payment_terms: 'Net 30 Days'
  },
  {
    id: 'b2222222-2222-2222-2222-222222222222',
    tenant_id: 'tirupur-demo',
    name: 'Next Sourcing UK',
    code: 'NEXT',
    country: 'United Kingdom',
    contact_email: 'orders@nextsourcing.com',
    payment_terms: 'LC 45 Days'
  },
  {
    id: 'b3333333-3333-3333-3333-333333333333',
    tenant_id: 'tirupur-demo',
    name: 'Decathlon Sports France',
    code: 'DECATH',
    country: 'France',
    contact_email: 'sourcing@decathlon.com',
    payment_terms: 'LC 60 Days'
  }
]

export const MOCK_STYLES: Style[] = [
  {
    id: 's1111111-1111-1111-1111-111111111111',
    tenant_id: 'tirupur-demo',
    buyer_id: 'b1111111-1111-1111-1111-111111111111',
    style_number: 'HM-TEE-01',
    style_name: 'Bio-Wash Single Jersey Crew Tee',
    garment_type: 'Crew Neck Tee',
    sam: 14.0,
    target_efficiency: 68.0
  },
  {
    id: 's2222222-2222-2222-2222-222222222222',
    tenant_id: 'tirupur-demo',
    buyer_id: 'b1111111-1111-1111-1111-111111111111',
    style_number: 'HM-VEST-02',
    style_name: '2x2 Ribbed Athletic Gym Vest',
    garment_type: 'Vest',
    sam: 9.5,
    target_efficiency: 72.0
  },
  {
    id: 's3333333-3333-3333-3333-333333333333',
    tenant_id: 'tirupur-demo',
    buyer_id: 'b2222222-2222-2222-2222-222222222222',
    style_number: 'NXT-POLO-01',
    style_name: 'Classic Pique Mercerized Polo',
    garment_type: 'Polo',
    sam: 18.0,
    target_efficiency: 65.0
  },
  {
    id: 's4444444-4444-4444-4444-444444444444',
    tenant_id: 'tirupur-demo',
    buyer_id: 'b2222222-2222-2222-2222-222222222222',
    style_number: 'NXT-HOOD-02',
    style_name: 'Brushed Fleece Heavy Zip Hoodie',
    garment_type: 'Hoodie',
    sam: 24.5,
    target_efficiency: 60.0
  },
  {
    id: 's5555555-5555-5555-5555-555555555555',
    tenant_id: 'tirupur-demo',
    buyer_id: 'b3333333-3333-3333-3333-333333333333',
    style_number: 'DEC-TEE-01',
    style_name: 'QuickDry Micro-Poly Running Tee',
    garment_type: 'Crew Neck Tee',
    sam: 12.5,
    target_efficiency: 70.0
  },
  {
    id: 's6666666-6666-6666-6666-666666666666',
    tenant_id: 'tirupur-demo',
    buyer_id: 'b3333333-3333-3333-3333-333333333333',
    style_number: 'DEC-SHORT-02',
    style_name: 'Running 4-Way Stretch Training Shorts',
    garment_type: 'Shorts',
    sam: 16.0,
    target_efficiency: 66.0
  }
]

export const MOCK_ORDERS: Order[] = [
  {
    id: 'ord-1',
    tenant_id: 'tirupur-demo',
    buyer_id: 'b3333333-3333-3333-3333-333333333333',
    style_id: 's5555555-5555-5555-5555-555555555555',
    order_number: 'PO-DEC-8821',
    total_quantity: 12000,
    unit_price: 320.00,
    currency: 'INR',
    ex_factory_date: '2026-11-28',
    planned_sewing_start: '2026-11-14',
    status: 'IN_PRODUCTION',
    buyer: MOCK_BUYERS[2],
    style: MOCK_STYLES[4],
    lines: [
      { id: 'l1', tenant_id: 'tirupur-demo', order_id: 'ord-1', color: 'Navy Blue', size: 'M', quantity: 4000 },
      { id: 'l2', tenant_id: 'tirupur-demo', order_id: 'ord-1', color: 'Navy Blue', size: 'L', quantity: 4000 },
      { id: 'l3', tenant_id: 'tirupur-demo', order_id: 'ord-1', color: 'Optic White', size: 'M', quantity: 2000 },
      { id: 'l4', tenant_id: 'tirupur-demo', order_id: 'ord-1', color: 'Optic White', size: 'L', quantity: 2000 },
    ],
    milestones: [
      { id: 'm1', tenant_id: 'tirupur-demo', order_id: 'ord-1', name: 'Yarn Inward', planned_date: '2026-10-20', actual_date: '2026-10-18', status: 'COMPLETED' },
      { id: 'm2', tenant_id: 'tirupur-demo', order_id: 'ord-1', name: 'Knitting & Dyeing', planned_date: '2026-10-30', actual_date: '2026-10-29', status: 'COMPLETED' },
      { id: 'm3', tenant_id: 'tirupur-demo', order_id: 'ord-1', name: 'PP Sample Approval', planned_date: '2026-11-05', actual_date: '2026-11-04', status: 'COMPLETED' },
      { id: 'm4', tenant_id: 'tirupur-demo', order_id: 'ord-1', name: 'Fabric Inward', planned_date: '2026-11-10', actual_date: null, status: 'IN_PROGRESS' },
      { id: 'm5', tenant_id: 'tirupur-demo', order_id: 'ord-1', name: 'Sewing Start', planned_date: '2026-11-14', actual_date: null, status: 'PENDING' },
      { id: 'm6', tenant_id: 'tirupur-demo', order_id: 'ord-1', name: 'Final Inspection', planned_date: '2026-11-25', actual_date: null, status: 'PENDING' },
      { id: 'm7', tenant_id: 'tirupur-demo', order_id: 'ord-1', name: 'Ex-Factory Dispatch', planned_date: '2026-11-28', actual_date: null, status: 'PENDING' },
    ]
  },
  {
    id: 'ord-2',
    tenant_id: 'tirupur-demo',
    buyer_id: 'b2222222-2222-2222-2222-222222222222',
    style_id: 's3333333-3333-3333-3333-333333333333',
    order_number: 'PO-NXT-9014',
    total_quantity: 6500,
    unit_price: 580.00,
    currency: 'INR',
    ex_factory_date: '2026-12-05',
    planned_sewing_start: '2026-11-18',
    status: 'CONFIRMED',
    buyer: MOCK_BUYERS[1],
    style: MOCK_STYLES[2],
    lines: [
      { id: 'l5', tenant_id: 'tirupur-demo', order_id: 'ord-2', color: 'Burgundy Red', size: 'S', quantity: 1500 },
      { id: 'l6', tenant_id: 'tirupur-demo', order_id: 'ord-2', color: 'Burgundy Red', size: 'M', quantity: 2500 },
      { id: 'l7', tenant_id: 'tirupur-demo', order_id: 'ord-2', color: 'Burgundy Red', size: 'L', quantity: 2500 },
    ],
    milestones: [
      { id: 'm8', tenant_id: 'tirupur-demo', order_id: 'ord-2', name: 'Yarn Inward', planned_date: '2026-10-25', actual_date: '2026-10-26', status: 'COMPLETED' },
      { id: 'm9', tenant_id: 'tirupur-demo', order_id: 'ord-2', name: 'Fabric Inward', planned_date: '2026-11-12', actual_date: null, status: 'PENDING' },
      { id: 'm10', tenant_id: 'tirupur-demo', order_id: 'ord-2', name: 'PP Sample Approval', planned_date: '2026-11-15', actual_date: null, status: 'BLOCKED', notes: 'Fit comment pending from UK buyer' },
      { id: 'm11', tenant_id: 'tirupur-demo', order_id: 'ord-2', name: 'Sewing Start', planned_date: '2026-11-18', actual_date: null, status: 'PENDING' },
      { id: 'm12', tenant_id: 'tirupur-demo', order_id: 'ord-2', name: 'Ex-Factory Dispatch', planned_date: '2026-12-05', actual_date: null, status: 'PENDING' },
    ]
  },
  {
    id: 'ord-3',
    tenant_id: 'tirupur-demo',
    buyer_id: 'b1111111-1111-1111-1111-111111111111',
    style_id: 's1111111-1111-1111-1111-111111111111',
    order_number: 'PO-HM-4102',
    total_quantity: 15000,
    unit_price: 290.00,
    currency: 'INR',
    ex_factory_date: '2026-12-12',
    planned_sewing_start: '2026-11-25',
    status: 'CONFIRMED',
    buyer: MOCK_BUYERS[0],
    style: MOCK_STYLES[0],
    lines: [
      { id: 'l8', tenant_id: 'tirupur-demo', order_id: 'ord-3', color: 'Jet Black', size: 'S', quantity: 3000 },
      { id: 'l9', tenant_id: 'tirupur-demo', order_id: 'ord-3', color: 'Jet Black', size: 'M', quantity: 6000 },
      { id: 'l10', tenant_id: 'tirupur-demo', order_id: 'ord-3', color: 'Jet Black', size: 'L', quantity: 6000 },
    ],
    milestones: [
      { id: 'm13', tenant_id: 'tirupur-demo', order_id: 'ord-3', name: 'Lab Dip Approval', planned_date: '2026-11-01', actual_date: '2026-10-31', status: 'COMPLETED' },
      { id: 'm14', tenant_id: 'tirupur-demo', order_id: 'ord-3', name: 'Fabric Inward', planned_date: '2026-11-20', actual_date: null, status: 'PENDING' },
      { id: 'm15', tenant_id: 'tirupur-demo', order_id: 'ord-3', name: 'Sewing Start', planned_date: '2026-11-25', actual_date: null, status: 'PENDING' },
      { id: 'm16', tenant_id: 'tirupur-demo', order_id: 'ord-3', name: 'Ex-Factory Dispatch', planned_date: '2026-12-12', actual_date: null, status: 'PENDING' },
    ]
  },
  {
    id: 'ord-4',
    tenant_id: 'tirupur-demo',
    buyer_id: 'b3333333-3333-3333-3333-333333333333',
    style_id: 's6666666-6666-6666-6666-666666666666',
    order_number: 'PO-DEC-8902',
    total_quantity: 8000,
    unit_price: 340.00,
    currency: 'INR',
    ex_factory_date: '2026-12-20',
    planned_sewing_start: '2026-12-02',
    status: 'CONFIRMED',
    buyer: MOCK_BUYERS[2],
    style: MOCK_STYLES[5],
    lines: [
      { id: 'l11', tenant_id: 'tirupur-demo', order_id: 'ord-4', color: 'Charcoal Grey', size: 'M', quantity: 4000 },
      { id: 'l12', tenant_id: 'tirupur-demo', order_id: 'ord-4', color: 'Charcoal Grey', size: 'L', quantity: 4000 },
    ],
    milestones: [
      { id: 'm17', tenant_id: 'tirupur-demo', order_id: 'ord-4', name: 'Fabric Inward', planned_date: '2026-11-28', actual_date: null, status: 'PENDING' },
      { id: 'm18', tenant_id: 'tirupur-demo', order_id: 'ord-4', name: 'Sewing Start', planned_date: '2026-12-02', actual_date: null, status: 'PENDING' },
      { id: 'm19', tenant_id: 'tirupur-demo', order_id: 'ord-4', name: 'Ex-Factory Dispatch', planned_date: '2026-12-20', actual_date: null, status: 'PENDING' },
    ]
  },
  {
    id: 'ord-5',
    tenant_id: 'tirupur-demo',
    buyer_id: 'b2222222-2222-2222-2222-222222222222',
    style_id: 's4444444-4444-4444-4444-444444444444',
    order_number: 'PO-NXT-9220',
    total_quantity: 4200,
    unit_price: 840.00,
    currency: 'INR',
    ex_factory_date: '2026-12-24',
    planned_sewing_start: '2026-12-08',
    status: 'DRAFT',
    buyer: MOCK_BUYERS[1],
    style: MOCK_STYLES[3],
    lines: [
      { id: 'l13', tenant_id: 'tirupur-demo', order_id: 'ord-5', color: 'Heather Grey', size: 'M', quantity: 2100 },
      { id: 'l14', tenant_id: 'tirupur-demo', order_id: 'ord-5', color: 'Heather Grey', size: 'L', quantity: 2100 },
    ],
    milestones: [
      { id: 'm20', tenant_id: 'tirupur-demo', order_id: 'ord-5', name: 'Fabric Inward', planned_date: '2026-12-01', actual_date: null, status: 'PENDING' },
      { id: 'm21', tenant_id: 'tirupur-demo', order_id: 'ord-5', name: 'Sewing Start', planned_date: '2026-12-08', actual_date: null, status: 'PENDING' },
      { id: 'm22', tenant_id: 'tirupur-demo', order_id: 'ord-5', name: 'Ex-Factory Dispatch', planned_date: '2026-12-24', actual_date: null, status: 'PENDING' },
    ]
  },
  {
    id: 'ord-6',
    tenant_id: 'tirupur-demo',
    buyer_id: 'b1111111-1111-1111-1111-111111111111',
    style_id: 's2222222-2222-2222-2222-222222222222',
    order_number: 'PO-HM-4250',
    total_quantity: 9800,
    unit_price: 260.00,
    currency: 'INR',
    ex_factory_date: '2027-01-05',
    planned_sewing_start: '2026-12-18',
    status: 'CONFIRMED',
    buyer: MOCK_BUYERS[0],
    style: MOCK_STYLES[1],
    lines: [
      { id: 'l15', tenant_id: 'tirupur-demo', order_id: 'ord-6', color: 'White Melange', size: 'M', quantity: 4900 },
      { id: 'l16', tenant_id: 'tirupur-demo', order_id: 'ord-6', color: 'White Melange', size: 'L', quantity: 4900 },
    ],
    milestones: [
      { id: 'm23', tenant_id: 'tirupur-demo', order_id: 'ord-6', name: 'Fabric Inward', planned_date: '2026-12-12', actual_date: null, status: 'PENDING' },
      { id: 'm24', tenant_id: 'tirupur-demo', order_id: 'ord-6', name: 'Sewing Start', planned_date: '2026-12-18', actual_date: null, status: 'PENDING' },
      { id: 'm25', tenant_id: 'tirupur-demo', order_id: 'ord-6', name: 'Ex-Factory Dispatch', planned_date: '2027-01-05', actual_date: null, status: 'PENDING' },
    ]
  }
]

export const MOCK_MATERIALS: Material[] = [
  {
    id: 'mat-1',
    tenant_id: 'tirupur-demo',
    code: 'FAB-SJ-160',
    name: '100% Combed Cotton Single Jersey 160 GSM',
    category: 'FABRIC',
    unit_of_measure: 'KGS',
    minimum_stock_level: 500,
    unit_cost: 380.00,
    currency: 'INR',
    current_stock: 3250.00
  },
  {
    id: 'mat-2',
    tenant_id: 'tirupur-demo',
    code: 'FAB-RIB-1X1',
    name: '95/5 Cotton Spandex 1x1 Rib 220 GSM',
    category: 'FABRIC',
    unit_of_measure: 'KGS',
    minimum_stock_level: 150,
    unit_cost: 440.00,
    currency: 'INR',
    current_stock: 420.00
  },
  {
    id: 'mat-3',
    tenant_id: 'tirupur-demo',
    code: 'TRIM-THRD-POLY',
    name: 'Spun Polyester Sewing Thread 40/2 (5000m)',
    category: 'TRIM',
    unit_of_measure: 'CONES',
    minimum_stock_level: 80,
    unit_cost: 85.00,
    currency: 'INR',
    current_stock: 240.00
  },
  {
    id: 'mat-4',
    tenant_id: 'tirupur-demo',
    code: 'TRIM-LBL-MAIN',
    name: 'Woven Satin Main Brand Neck Label',
    category: 'TRIM',
    unit_of_measure: 'PCS',
    minimum_stock_level: 5000,
    unit_cost: 1.25,
    currency: 'INR',
    current_stock: 18500.00
  },
  {
    id: 'mat-5',
    tenant_id: 'tirupur-demo',
    code: 'PKG-POLY-BAG',
    name: 'Self-Adhesive Recycled LDPE Polybag 12x15',
    category: 'PACKAGING',
    unit_of_measure: 'PCS',
    minimum_stock_level: 5000,
    unit_cost: 2.10,
    currency: 'INR',
    current_stock: 22000.00
  },
  {
    id: 'mat-6',
    tenant_id: 'tirupur-demo',
    code: 'TRIM-ELAS-20MM',
    name: 'Knitted Waistband Elastic 20mm',
    category: 'TRIM',
    unit_of_measure: 'MTRS',
    minimum_stock_level: 1000,
    unit_cost: 6.50,
    currency: 'INR',
    current_stock: 4800.00
  }
]

export const MOCK_SUPPLIERS: Supplier[] = [
  {
    id: 'sup-1',
    tenant_id: 'tirupur-demo',
    name: 'Lakshmi Cotton Mills Ltd',
    code: 'LAKSHMI-KNIT',
    category: 'Fabric Yarn',
    contact_email: 'sales@lakshmicotton.com',
    lead_time_days: 10
  },
  {
    id: 'sup-2',
    tenant_id: 'tirupur-demo',
    name: 'Vardhman Threads India',
    code: 'VARDHMAN-TRIM',
    category: 'Sewing Threads',
    contact_email: 'orders@vardhman.com',
    lead_time_days: 5
  },
  {
    id: 'sup-3',
    tenant_id: 'tirupur-demo',
    name: 'Sri Venkateswara Poly Products',
    code: 'SVP-PACK',
    category: 'Packaging',
    contact_email: 'contact@svppoly.in',
    lead_time_days: 3
  }
]

export const MOCK_SUPPLIER_POS: SupplierPo[] = [
  {
    id: 'spo-1',
    tenant_id: 'tirupur-demo',
    po_number: 'SPO-2026-081',
    supplier_id: 'sup-1',
    material_id: 'mat-1',
    order_id: 'ord-1',
    quantity_ordered: 2500,
    quantity_received: 2500,
    unit_price: 380.00,
    expected_delivery_date: '2026-11-05',
    status: 'COMPLETED',
    supplier_name: 'Lakshmi Cotton Mills Ltd',
    material_name: '100% Combed Cotton Single Jersey 160 GSM'
  },
  {
    id: 'spo-2',
    tenant_id: 'tirupur-demo',
    po_number: 'SPO-2026-094',
    supplier_id: 'sup-1',
    material_id: 'mat-1',
    order_id: 'ord-2',
    quantity_ordered: 1800,
    quantity_received: 750,
    unit_price: 380.00,
    expected_delivery_date: '2026-11-15',
    status: 'PARTIAL_RECEIVED',
    supplier_name: 'Lakshmi Cotton Mills Ltd',
    material_name: '100% Combed Cotton Single Jersey 160 GSM'
  }
]

export const MOCK_STOCK_LEDGER: StockLedgerEntry[] = [
  {
    id: 'led-1',
    tenant_id: 'tirupur-demo',
    material_id: 'mat-1',
    movement_type: 'OPENING_BALANCE',
    quantity: 1500,
    unit_cost: 380.00,
    reference_type: 'ANNUAL_AUDIT',
    notes: 'Initial audited physical count',
    created_at: '2026-10-01T08:00:00Z'
  },
  {
    id: 'led-2',
    tenant_id: 'tirupur-demo',
    material_id: 'mat-1',
    movement_type: 'GRN_RECEIPT',
    quantity: 2500,
    unit_cost: 380.00,
    reference_type: 'SUPPLIER_PO',
    reference_id: 'spo-1',
    notes: 'GRN-4491 from Lakshmi Mills',
    created_at: '2026-11-05T11:30:00Z'
  },
  {
    id: 'led-3',
    tenant_id: 'tirupur-demo',
    material_id: 'mat-1',
    movement_type: 'ISSUE_TO_CUTTING',
    quantity: -750,
    unit_cost: 380.00,
    reference_type: 'PRODUCTION_ORDER',
    reference_id: 'ord-1',
    notes: 'Spreading table lay #1 issue',
    created_at: '2026-11-10T14:15:00Z'
  }
]

export const MOCK_PRODUCTION_LINES: ProductionLine[] = [
  {
    id: 'line-1',
    tenant_id: 'tirupur-demo',
    line_number: 'L-01',
    name: 'Main Sewing Line 1 (Polo Specialists)',
    operator_count: 24,
    helper_count: 4,
    daily_working_hours: 8,
    is_active: true,
    created_at: '2026-10-01'
  },
  {
    id: 'line-2',
    tenant_id: 'tirupur-demo',
    line_number: 'L-02',
    name: 'Fast Track Tee Line 2',
    operator_count: 22,
    helper_count: 3,
    daily_working_hours: 8,
    is_active: true,
    created_at: '2026-10-01'
  },
  {
    id: 'line-3',
    tenant_id: 'tirupur-demo',
    line_number: 'L-03',
    name: 'Heavy Fleece & Sweatshirt Line 3',
    operator_count: 26,
    helper_count: 5,
    daily_working_hours: 8,
    is_active: true,
    created_at: '2026-10-01'
  }
]

export const MOCK_DAILY_LOGS: DailyProductionLog[] = [
  {
    id: 'log-1',
    tenant_id: 'tirupur-demo',
    date: '2026-11-15',
    order_id: 'ord-1',
    line_id: 'line-2',
    stage: 'SEWING',
    planned_output: 1200,
    actual_output: 1150,
    rejected_qty: 18,
    operator_count: 22,
    working_hours: 8,
    notes: 'Smooth line flow, needle change at 2 PM',
    created_at: '2026-11-15T18:00:00Z',
    produced_minutes: 14375,
    available_minutes: 10560,
    efficiency_pct: 68.2,
    rejection_rate_pct: 1.5
  },
  {
    id: 'log-2',
    tenant_id: 'tirupur-demo',
    date: '2026-11-16',
    order_id: 'ord-1',
    line_id: 'line-2',
    stage: 'SEWING',
    planned_output: 1200,
    actual_output: 1210,
    rejected_qty: 12,
    operator_count: 22,
    working_hours: 8,
    notes: 'Target achieved ahead of shift end',
    created_at: '2026-11-16T18:00:00Z',
    produced_minutes: 15125,
    available_minutes: 10560,
    efficiency_pct: 71.5,
    rejection_rate_pct: 0.98
  }
]

export const MOCK_JOBWORK_PROCESSORS: JobworkProcessor[] = [
  {
    id: 'proc-1',
    tenant_id: 'tirupur-demo',
    name: 'Sri Balaji Modern Dyeing Unit',
    process_type: 'DYEING',
    contact_person: 'M. Balasubramaniam',
    phone: '+91 98430 11223',
    address: 'SIPCOT Industrial Park, Perundurai',
    is_active: true,
    created_at: '2026-10-01'
  },
  {
    id: 'proc-2',
    tenant_id: 'tirupur-demo',
    name: 'Premier Rotary & Screen Printers',
    process_type: 'PRINTING',
    contact_person: 'K. Rajendran',
    phone: '+91 94432 44556',
    address: 'Kunnathur Road, Tiruppur',
    is_active: true,
    created_at: '2026-10-01'
  },
  {
    id: 'proc-3',
    tenant_id: 'tirupur-demo',
    name: 'Kongu Multi-Head Embroidery Works',
    process_type: 'EMBROIDERY',
    contact_person: 'S. Selvakumar',
    phone: '+91 97880 77889',
    address: 'Avinashi Road, Tiruppur',
    is_active: true,
    created_at: '2026-10-01'
  }
]

export const MOCK_JOBWORK_CHALLANS: JobworkChallan[] = [
  {
    id: 'ch-1',
    tenant_id: 'tirupur-demo',
    challan_number: 'DC-OUT-2026-041',
    challan_type: 'OUTWARD_ISSUE',
    processor_id: 'proc-1',
    processor_name: 'Sri Balaji Modern Dyeing Unit',
    order_id: 'ord-1',
    process_name: 'Reactive Jet Soft-Flow Dyeing',
    material_description: 'Grey Single Jersey Tubing 34"',
    issued_qty: 3200,
    issued_weight_kg: 850.00,
    expected_return_date: '2026-11-04',
    actual_return_date: '2026-11-04',
    received_qty: 3200,
    received_weight_kg: 825.00,
    status: 'COMPLETED',
    notes: 'Navy Blue reactive shade pass',
    created_at: '2026-10-28',
    weight_loss_kg: 25.00,
    weight_loss_pct: 2.94,
    is_loss_anomaly: false
  },
  {
    id: 'ch-2',
    tenant_id: 'tirupur-demo',
    challan_number: 'DC-OUT-2026-052',
    challan_type: 'OUTWARD_ISSUE',
    processor_id: 'proc-2',
    processor_name: 'Premier Rotary & Screen Printers',
    order_id: 'ord-2',
    process_name: 'Plastisol Chest Logo Screen Print',
    material_description: 'Cut panels front body piece',
    issued_qty: 6500,
    issued_weight_kg: 1200.00,
    expected_return_date: '2026-11-16',
    actual_return_date: null,
    received_qty: 0,
    received_weight_kg: 0,
    status: 'ISSUED',
    notes: '4-Color chest print high density',
    created_at: '2026-11-08',
    weight_loss_kg: 0,
    weight_loss_pct: 0,
    is_loss_anomaly: false
  }
]

export const MOCK_RISK_MATRIX: OrderRiskSummary[] = [
  {
    order_id: 'ord-2',
    order_number: 'PO-NXT-9014',
    buyer_name: 'Next Sourcing UK',
    max_severity: 'HIGH',
    risks: [
      {
        rule: 'R1_FABRIC_DEFICIT',
        rule_name: 'Fabric Stock Readiness',
        order_id: 'ord-2',
        order_number: 'PO-NXT-9014',
        buyer_name: 'Next Sourcing UK',
        triggered: true,
        severity: 'HIGH',
        deficit_qty: 480,
        days_delayed: 0,
        headline: '480 kg Fabric Shortage Before Sewing Start',
        explanation: 'Available inventory (750 kg) falls short of gross BOM requirement (1,230 kg) by 480 kg with only 6 days before sewing start.',
        evidence: { required_kg: 1230, available_kg: 750, deficit_kg: 480 }
      },
      {
        rule: 'R5_MILESTONE_GATE',
        rule_name: 'Approval Gate Violation',
        order_id: 'ord-2',
        order_number: 'PO-NXT-9014',
        buyer_name: 'Next Sourcing UK',
        triggered: true,
        severity: 'HIGH',
        deficit_qty: 0,
        days_delayed: 3,
        headline: 'PP Sample Milestone Gate BLOCKED',
        explanation: 'PP Sample Approval gate is currently BLOCKED awaiting UK buyer fit comments. Sewing line cannot proceed.',
        evidence: { blocked_milestone: 'PP Sample Approval', delay_days: 3 }
      }
    ]
  },
  {
    order_id: 'ord-1',
    order_number: 'PO-DEC-8821',
    buyer_name: 'Decathlon Sports France',
    max_severity: 'NORMAL',
    risks: [
      {
        rule: 'R3_SEWING_PACING',
        rule_name: 'Sewing Output Pacing',
        order_id: 'ord-1',
        order_number: 'PO-DEC-8821',
        buyer_name: 'Decathlon Sports France',
        triggered: false,
        severity: 'NORMAL',
        deficit_qty: 0,
        days_delayed: 0,
        headline: 'Sewing Pacing on Schedule',
        explanation: 'Rolling output is 1,180 pcs/day against target requirement of 1,100 pcs/day. Efficiency is 70.1%.',
        evidence: { daily_actual: 1180, daily_required: 1100 }
      }
    ]
  }
]
