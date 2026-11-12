-- ============================================================================
-- Procure-to-Pay Synthetic Data Generator
-- SQLite Relational Database Schema (Phase 1 Foundation)
--
-- Monetary Representation Design:
-- Financial amounts are stored as INTEGER minor units (e.g. USD cents: $12.50 -> 1250)
-- to avoid IEEE 754 floating-point inaccuracies in financial calculations.
-- Foreign keys are strictly enforced (PRAGMA foreign_keys = ON).
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. Department
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departments (
    department_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    cost_center_code TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

-- ----------------------------------------------------------------------------
-- 2. Budget
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS budgets (
    budget_id TEXT PRIMARY KEY,
    department_id TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL CHECK (fiscal_year >= 2000),
    currency TEXT NOT NULL DEFAULT 'USD',
    allocated_amount INTEGER NOT NULL CHECK (allocated_amount >= 0),
    reserved_amount INTEGER NOT NULL DEFAULT 0 CHECK (reserved_amount >= 0),
    committed_amount INTEGER NOT NULL DEFAULT 0 CHECK (committed_amount >= 0),
    spent_amount INTEGER NOT NULL DEFAULT 0 CHECK (spent_amount >= 0),
    created_at TEXT NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT,
    UNIQUE (department_id, fiscal_year)
);

-- ----------------------------------------------------------------------------
-- 3. Requester
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS requesters (
    requester_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    department_id TEXT NOT NULL,
    job_title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 4. Approver
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS approvers (
    approver_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    department_id TEXT,
    role TEXT NOT NULL CHECK (role IN ('LINE_MANAGER', 'DEPARTMENT_HEAD', 'FINANCE')),
    approval_limit INTEGER NOT NULL CHECK (approval_limit >= 0),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 5. Supplier
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    contact_email TEXT NOT NULL,
    country TEXT NOT NULL,
    currency TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'PREFERRED', 'PROBATION', 'INACTIVE')),
    risk_classification TEXT NOT NULL CHECK (risk_classification IN ('LOW', 'MEDIUM', 'HIGH')),
    created_at TEXT NOT NULL
);

-- ----------------------------------------------------------------------------
-- 6. PurchaseRequest
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS purchase_requests (
    request_id TEXT PRIMARY KEY,
    requester_id TEXT NOT NULL,
    department_id TEXT NOT NULL,
    budget_id TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    total_estimated_amount INTEGER NOT NULL CHECK (total_estimated_amount >= 0),
    status TEXT NOT NULL CHECK (status IN ('DRAFT', 'SUBMITTED', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'CANCELLED', 'IN_SOURCING', 'ORDERED')),
    request_date TEXT NOT NULL,
    justification TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (requester_id) REFERENCES requesters(requester_id) ON DELETE RESTRICT,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT,
    FOREIGN KEY (budget_id) REFERENCES budgets(budget_id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 7. RequestLine
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS request_lines (
    request_line_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    line_number INTEGER NOT NULL CHECK (line_number > 0),
    item_description TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    estimated_unit_price INTEGER NOT NULL CHECK (estimated_unit_price >= 0),
    estimated_line_total INTEGER NOT NULL CHECK (estimated_line_total >= 0),
    FOREIGN KEY (request_id) REFERENCES purchase_requests(request_id) ON DELETE RESTRICT,
    UNIQUE (request_id, line_number)
);

-- ----------------------------------------------------------------------------
-- 8. RFQ
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rfqs (
    rfq_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL UNIQUE,
    issue_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('DRAFT', 'ISSUED', 'CLOSED', 'AWARDED', 'CANCELLED')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (request_id) REFERENCES purchase_requests(request_id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 9. RFQSupplierInvite
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rfq_supplier_invites (
    invite_id TEXT PRIMARY KEY,
    rfq_id TEXT NOT NULL,
    supplier_id TEXT NOT NULL,
    invited_at TEXT NOT NULL,
    invitation_status TEXT NOT NULL CHECK (invitation_status IN ('SENT', 'ACCEPTED', 'DECLINED', 'NO_RESPONSE')),
    FOREIGN KEY (rfq_id) REFERENCES rfqs(rfq_id) ON DELETE RESTRICT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE RESTRICT,
    UNIQUE (rfq_id, supplier_id)
);

-- ----------------------------------------------------------------------------
-- 10. SupplierQuote
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS supplier_quotes (
    quote_id TEXT PRIMARY KEY,
    rfq_id TEXT NOT NULL,
    supplier_id TEXT NOT NULL,
    quote_date TEXT NOT NULL,
    currency TEXT NOT NULL,
    fx_rate_to_base REAL NOT NULL CHECK (fx_rate_to_base > 0),
    total_quoted_amount INTEGER NOT NULL CHECK (total_quoted_amount >= 0),
    total_quoted_amount_base INTEGER NOT NULL CHECK (total_quoted_amount_base >= 0),
    lead_time_days INTEGER NOT NULL CHECK (lead_time_days >= 0),
    status TEXT NOT NULL CHECK (status IN ('SUBMITTED', 'UNDER_REVIEW', 'AWARDED', 'REJECTED', 'EXPIRED')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (rfq_id) REFERENCES rfqs(rfq_id) ON DELETE RESTRICT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE RESTRICT,
    FOREIGN KEY (rfq_id, supplier_id) REFERENCES rfq_supplier_invites(rfq_id, supplier_id) ON DELETE RESTRICT,
    UNIQUE (rfq_id, supplier_id)
);

-- ----------------------------------------------------------------------------
-- 11. QuoteLine
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quote_lines (
    quote_line_id TEXT PRIMARY KEY,
    quote_id TEXT NOT NULL,
    request_line_id TEXT NOT NULL,
    quoted_quantity INTEGER NOT NULL CHECK (quoted_quantity > 0),
    unit_price INTEGER NOT NULL CHECK (unit_price >= 0),
    line_total INTEGER NOT NULL CHECK (line_total >= 0),
    line_total_base INTEGER NOT NULL CHECK (line_total_base >= 0),
    created_at TEXT NOT NULL,
    FOREIGN KEY (quote_id) REFERENCES supplier_quotes(quote_id) ON DELETE RESTRICT,
    FOREIGN KEY (request_line_id) REFERENCES request_lines(request_line_id) ON DELETE RESTRICT,
    UNIQUE (quote_id, request_line_id)
);

-- ----------------------------------------------------------------------------
-- 12. Approval
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    approver_id TEXT NOT NULL,
    approval_level INTEGER NOT NULL CHECK (approval_level IN (1, 2, 3)),
    decision TEXT NOT NULL CHECK (decision IN ('PENDING', 'APPROVED', 'REJECTED')),
    decision_date TEXT,
    comments TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (request_id) REFERENCES purchase_requests(request_id) ON DELETE RESTRICT,
    FOREIGN KEY (approver_id) REFERENCES approvers(approver_id) ON DELETE RESTRICT,
    UNIQUE (request_id, approval_level)
);

-- ----------------------------------------------------------------------------
-- 13. PurchaseOrder
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS purchase_orders (
    po_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    supplier_id TEXT NOT NULL,
    awarded_quote_id TEXT,
    sourcing_type TEXT NOT NULL CHECK (sourcing_type IN ('COMPETITIVE', 'SOLE_SOURCE', 'EMERGENCY', 'CONTRACT_RENEWAL')),
    sourcing_justification TEXT,
    currency TEXT NOT NULL DEFAULT 'USD',
    total_amount INTEGER NOT NULL CHECK (total_amount >= 0),
    status TEXT NOT NULL CHECK (status IN ('ISSUED', 'PARTIALLY_DELIVERED', 'COMPLETED', 'CANCELLED')),
    po_date TEXT NOT NULL,
    expected_delivery_date TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (request_id) REFERENCES purchase_requests(request_id) ON DELETE RESTRICT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE RESTRICT,
    FOREIGN KEY (awarded_quote_id) REFERENCES supplier_quotes(quote_id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 14. PurchaseOrderLine
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS purchase_order_lines (
    po_line_id TEXT PRIMARY KEY,
    po_id TEXT NOT NULL,
    line_number INTEGER NOT NULL CHECK (line_number > 0),
    request_line_id TEXT NOT NULL,
    awarded_quote_line_id TEXT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price INTEGER NOT NULL CHECK (unit_price >= 0),
    line_total INTEGER NOT NULL CHECK (line_total >= 0),
    created_at TEXT NOT NULL,
    FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id) ON DELETE RESTRICT,
    FOREIGN KEY (request_line_id) REFERENCES request_lines(request_line_id) ON DELETE RESTRICT,
    FOREIGN KEY (awarded_quote_line_id) REFERENCES quote_lines(quote_line_id) ON DELETE RESTRICT,
    UNIQUE (po_id, line_number)
);

-- ----------------------------------------------------------------------------
-- 15. Delivery
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id TEXT PRIMARY KEY,
    po_id TEXT NOT NULL,
    delivery_sequence INTEGER NOT NULL CHECK (delivery_sequence > 0),
    delivery_date TEXT NOT NULL,
    received_by TEXT NOT NULL,
    delivery_status TEXT NOT NULL CHECK (delivery_status IN ('PARTIAL', 'FULL', 'DAMAGED', 'RETURNED')),
    items_delivered_count INTEGER NOT NULL CHECK (items_delivered_count >= 0),
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id) ON DELETE RESTRICT,
    UNIQUE (po_id, delivery_sequence)
);

-- ----------------------------------------------------------------------------
-- 16. StatusEvent
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS status_events (
    event_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('PURCHASE_REQUEST', 'RFQ', 'QUOTE', 'PURCHASE_ORDER', 'DELIVERY', 'BUDGET')),
    entity_id TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    actor_type TEXT NOT NULL CHECK (actor_type IN ('REQUESTER', 'APPROVER', 'SUPPLIER', 'BUYER', 'SYSTEM')),
    event_timestamp TEXT NOT NULL,
    reason TEXT
);

-- ----------------------------------------------------------------------------
-- 17. BudgetEvent
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS budget_events (
    budget_event_id TEXT PRIMARY KEY,
    budget_id TEXT NOT NULL,
    request_id TEXT,
    po_id TEXT,
    event_type TEXT NOT NULL CHECK (event_type IN ('ALLOCATE', 'RESERVE', 'COMMIT', 'RELEASE', 'SPEND')),
    amount INTEGER NOT NULL CHECK (amount >= 0),
    currency TEXT NOT NULL DEFAULT 'USD',
    event_timestamp TEXT NOT NULL,
    description TEXT NOT NULL,
    FOREIGN KEY (budget_id) REFERENCES budgets(budget_id) ON DELETE RESTRICT,
    FOREIGN KEY (request_id) REFERENCES purchase_requests(request_id) ON DELETE RESTRICT,
    FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 18. ExceptionLog
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS exception_logs (
    exception_id TEXT PRIMARY KEY,
    exception_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    affected_entity_type TEXT NOT NULL,
    affected_entity_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    logged_at TEXT NOT NULL,
    resolved INTEGER NOT NULL DEFAULT 0 CHECK (resolved IN (0, 1))
);

-- ----------------------------------------------------------------------------
-- Indexes on Foreign Keys and High-Frequency Query Paths
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_budgets_department ON budgets(department_id);
CREATE INDEX IF NOT EXISTS idx_requesters_department ON requesters(department_id);
CREATE INDEX IF NOT EXISTS idx_approvers_department ON approvers(department_id);
CREATE INDEX IF NOT EXISTS idx_pr_requester ON purchase_requests(requester_id);
CREATE INDEX IF NOT EXISTS idx_pr_department ON purchase_requests(department_id);
CREATE INDEX IF NOT EXISTS idx_pr_budget ON purchase_requests(budget_id);
CREATE INDEX IF NOT EXISTS idx_rl_request ON request_lines(request_id);
CREATE INDEX IF NOT EXISTS idx_rfq_request ON rfqs(request_id);
CREATE INDEX IF NOT EXISTS idx_rfq_invites_rfq ON rfq_supplier_invites(rfq_id);
CREATE INDEX IF NOT EXISTS idx_rfq_invites_supplier ON rfq_supplier_invites(supplier_id);
CREATE INDEX IF NOT EXISTS idx_quotes_rfq ON supplier_quotes(rfq_id);
CREATE INDEX IF NOT EXISTS idx_quotes_supplier ON supplier_quotes(supplier_id);
CREATE INDEX IF NOT EXISTS idx_ql_quote ON quote_lines(quote_id);
CREATE INDEX IF NOT EXISTS idx_ql_request_line ON quote_lines(request_line_id);
CREATE INDEX IF NOT EXISTS idx_approvals_request ON approvals(request_id);
CREATE INDEX IF NOT EXISTS idx_approvals_approver ON approvals(approver_id);
CREATE INDEX IF NOT EXISTS idx_po_request ON purchase_orders(request_id);
CREATE INDEX IF NOT EXISTS idx_po_supplier ON purchase_orders(supplier_id);
CREATE INDEX IF NOT EXISTS idx_po_quote ON purchase_orders(awarded_quote_id);
CREATE INDEX IF NOT EXISTS idx_pol_po ON purchase_order_lines(po_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_po ON deliveries(po_id);
CREATE INDEX IF NOT EXISTS idx_status_events_entity ON status_events(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_budget_events_budget ON budget_events(budget_id);
CREATE INDEX IF NOT EXISTS idx_budget_events_request ON budget_events(request_id);
CREATE INDEX IF NOT EXISTS idx_budget_events_po ON budget_events(po_id);
CREATE INDEX IF NOT EXISTS idx_exception_logs_entity ON exception_logs(affected_entity_type, affected_entity_id);

-- ----------------------------------------------------------------------------
-- 19. Ground Truth Anomalies
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ground_truth (
    anomaly_id TEXT PRIMARY KEY,
    issue_type TEXT NOT NULL,
    entity TEXT NOT NULL,
    record_id TEXT NOT NULL,
    expected_decision TEXT NOT NULL,
    reason TEXT NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ground_truth_record ON ground_truth(record_id);
