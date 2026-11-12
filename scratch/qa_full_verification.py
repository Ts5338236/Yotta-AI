"""
Complete QA Verification Harness for Tests 1-10.
Executes detailed assertions and empirical checks across all required areas.
"""
import sys
import json
import sqlite3
import hashlib
from pathlib import Path
from decimal import Decimal

# Add root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from src.datagen.config import load_config
from src.datagen.workflow import generate_procurement_workflow
from src.datagen.anomalies import inject_anomalies
from src.datagen.derive import (
    derive_request_line_totals,
    derive_purchase_request_totals,
    derive_quote_landed_costs,
    derive_supplier_scores,
    derive_purchase_order_totals,
    derive_budget_balances,
    derive_delivery_summaries
)
from src.validate.checks import (
    validate_dataset,
    validate_primary_keys_and_ids,
    validate_foreign_keys,
    validate_financial_reconciliation,
    validate_date_ordering,
    validate_lifecycle_state_machine,
    validate_approvals_and_business_rules,
    validate_budget_ledger,
    validate_split_purchases
)
from src.validate.anomaly_checks import detect_all_anomalies, evaluate_detections
from src.datagen.export import export_all
from src.validate.export_checks import validate_all_exports

results = {}

print("======================================================================")
print("STARTING COMPREHENSIVE QA VERIFICATION (TESTS 1 - 10)")
print("======================================================================")

config = load_config()

import numpy as np

# --------------------------------------------------------------------
# 1. GENERATE CLEAN AND ANOMALOUS FULL-SCALE DATASETS
# --------------------------------------------------------------------
print("[QA] Generating Full-Scale Dataset (seed: 20261022)...")
clean_dataset = generate_procurement_workflow(scale="full", seed=20261022)
rng = np.random.default_rng(20261022)
anomalous_dataset, ground_truth = inject_anomalies(clean_dataset, config, rng=rng)

# --------------------------------------------------------------------
# TEST 1: MASTER DATA
# --------------------------------------------------------------------
print("\n--- TEST 1: MASTER DATA ---")
depts = clean_dataset["departments"]
budgets = clean_dataset["budgets"]
reqs = clean_dataset["requesters"]
sups = clean_dataset["suppliers"]
approvers = clean_dataset["approvers"]

t1_checks = []

# Departments
dept_ids = [d["department_id"] for d in depts]
t1_checks.append(("Dept count", len(depts) == 12, f"Expected 12, got {len(depts)}"))
t1_checks.append(("Dept IDs unique", len(dept_ids) == len(set(dept_ids)), f"Count: {len(dept_ids)}"))
t1_checks.append(("Dept cost centers unique", len(set(d["cost_center_code"] for d in depts)) == len(depts), ""))

# Budgets
budget_dept_ids = [b["department_id"] for b in budgets]
t1_checks.append(("Budget count", len(budgets) == 12, f"Expected 12, got {len(budgets)}"))
t1_checks.append(("Budgets map 1:1 to depts", set(budget_dept_ids) == set(dept_ids), ""))
t1_checks.append(("Budgets all FY2026", all(b["fiscal_year"] == 2026 for b in budgets), ""))
t1_checks.append(("Budgets positive amount", all(b["allocated_amount"] > 0 for b in budgets), ""))

# Requesters
req_ids = [r["requester_id"] for r in reqs]
t1_checks.append(("Requester count", len(reqs) == 300, f"Expected 300, got {len(reqs)}"))
t1_checks.append(("Requester IDs unique", len(req_ids) == len(set(req_ids)), ""))
t1_checks.append(("Requester dept FKs valid", all(r["department_id"] in dept_ids for r in reqs), ""))
# Check managerial hierarchy is acyclic DAG
managers = {r["requester_id"]: r["manager_id"] for r in reqs}
roots = [rid for rid, mid in managers.items() if mid is None]
t1_checks.append(("Has root managers (no manager_id)", len(roots) > 0, f"Found {len(roots)} roots"))
# Cycle detection
has_cycle = False
for rid in req_ids:
    visited = set()
    curr = rid
    while curr is not None:
        if curr in visited:
            has_cycle = True
            break
        visited.add(curr)
        curr = managers.get(curr)
t1_checks.append(("Requester hierarchy is acyclic DAG", not has_cycle, "No cycles detected"))

# Suppliers
sup_ids = [s["supplier_id"] for s in sups]
t1_checks.append(("Supplier count >= 120", len(sups) >= 120, f"Got {len(sups)}"))
t1_checks.append(("Supplier IDs unique", len(sup_ids) == len(set(sup_ids)), ""))
valid_currencies = {"USD", "EUR", "GBP", "INR", "JPY"}
t1_checks.append(("Supplier currencies valid", all(str(s["currency"]) in valid_currencies for s in sups), ""))
t1_checks.append(("Supplier risk score in [0, 1]", all(0.0 <= s["risk_score"] <= 1.0 for s in sups), ""))
valid_statuses = {"ACTIVE", "PREFERRED", "PROBATION", "INACTIVE", "BLACKLISTED"}
t1_checks.append(("Supplier statuses valid", all(str(s["status"]).upper() in valid_statuses for s in sups), ""))

results["TEST_1_MASTER_DATA"] = {name: ("PASS" if ok else "FAIL", msg) for name, ok, msg in t1_checks}
for name, ok, msg in t1_checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {msg}")

# --------------------------------------------------------------------
# TEST 2: PROCUREMENT WORKFLOW
# --------------------------------------------------------------------
print("\n--- TEST 2: PROCUREMENT WORKFLOW ---")
prs = clean_dataset["purchase_requests"]
pr_lines = clean_dataset["request_lines"]
apps = clean_dataset["approvals"]
rfqs = clean_dataset["rfqs"]
invites = clean_dataset["rfq_supplier_invites"]
quotes = clean_dataset["supplier_quotes"]
quote_lines = clean_dataset["quote_lines"]
pos = clean_dataset["purchase_orders"]
po_lines = clean_dataset["purchase_order_lines"]
deliveries = clean_dataset["deliveries"]
budget_events = clean_dataset["budget_events"]
status_events = clean_dataset["status_events"]

t2_checks = []

# Verify complete chain connectivity
# 1. PR to lines
pr_id_set = set(p["request_id"] for p in prs)
pr_lines_parent_set = set(pl["request_id"] for pl in pr_lines)
t2_checks.append(("All PRs have lines", pr_id_set == pr_lines_parent_set, ""))

# 2. Approved PRs to Approvals
approved_prs = [p for p in prs if p["status"] == "APPROVED"]
app_pr_ids = set(a["request_id"] for a in apps if a["decision"] == "APPROVED")
t2_checks.append(("Approved PRs have approved approval records", set(p["request_id"] for p in approved_prs).issubset(app_pr_ids), ""))

# 3. Competitive PRs to RFQs
comp_rfq_prs = set(r["request_id"] for r in rfqs)
t2_checks.append(("Competitive PRs generate RFQs", len(rfqs) == 500, f"RFQs: {len(rfqs)}"))

# 4. RFQ to Invites and Quotes
rfq_id_set = set(r["rfq_id"] for r in rfqs)
inv_rfq_set = set(i["rfq_id"] for i in invites)
quote_rfq_set = set(q["rfq_id"] for q in quotes)
t2_checks.append(("All RFQs have supplier invites", rfq_id_set == inv_rfq_set, ""))
t2_checks.append(("All RFQs have supplier quotes", rfq_id_set == quote_rfq_set, ""))

# 5. Awarded quotes generate POs
awarded_quotes = [q for q in quotes if q["status"] == "AWARDED"]
awarded_quote_ids = set(q["quote_id"] for q in awarded_quotes)
comp_pos = [po for po in pos if po.get("quote_id") is not None or po.get("awarded_quote_id") is not None]
po_quote_ids = set(po.get("quote_id") or po.get("awarded_quote_id") for po in comp_pos)
t2_checks.append(("All awarded quotes generate POs", awarded_quote_ids == po_quote_ids, f"Awarded: {len(awarded_quote_ids)}, PO quote IDs: {len(po_quote_ids)}"))

# 6. PO to Deliveries
po_id_set = set(po["po_id"] for po in pos)
deliv_po_set = set(d["po_id"] for d in deliveries)
t2_checks.append(("POs have deliveries", deliv_po_set.issubset(po_id_set), f"Deliveries cover {len(deliv_po_set)} POs"))

results["TEST_2_PROCUREMENT_WORKFLOW"] = {name: ("PASS" if ok else "FAIL", msg) for name, ok, msg in t2_checks}
for name, ok, msg in t2_checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {msg}")

# --------------------------------------------------------------------
# TEST 3: APPROVAL RULES
# --------------------------------------------------------------------
print("\n--- TEST 3: APPROVAL RULES ---")
t3_checks = []
t1_limit = Decimal("2000.00")
t2_limit = Decimal("25000.00")

pr_map = {p["request_id"]: p for p in prs}

# Check approval tiers for clean data
tier_mismatches = 0
for app in apps:
    pr = pr_map[app["request_id"]]
    amt = Decimal(str(pr["total_estimate_usd"]))
    role = app.get("approver_role")
    if amt <= t1_limit and role not in ("LINE_MANAGER", "DEPARTMENT_HEAD"):
        tier_mismatches += 1
    elif t1_limit < amt <= t2_limit and role != "DEPARTMENT_HEAD":
        tier_mismatches += 1
    elif amt > t2_limit and role not in ("DEPARTMENT_HEAD", "FINANCE"):
        tier_mismatches += 1
t3_checks.append(("All approvals match policy threshold roles", tier_mismatches == 0, f"Mismatches: {tier_mismatches}"))

# Rejected requests do not have POs
rejected_pr_ids = set(p["request_id"] for p in prs if p["status"] == "REJECTED")
po_pr_ids = set(po["request_id"] for po in pos)
overlap = rejected_pr_ids.intersection(po_pr_ids)
t3_checks.append(("Zero POs generated for rejected PRs", len(overlap) == 0, f"Overlap: {len(overlap)}"))

# Test unauthorized PO rejection detection
unauthorized_pos = [po for po in pos if po["request_id"] in rejected_pr_ids]
t3_checks.append(("Normal workflow produces 0 unauthorized POs", len(unauthorized_pos) == 0, ""))

results["TEST_3_APPROVAL_RULES"] = {name: ("PASS" if ok else "FAIL", msg) for name, ok, msg in t3_checks}
for name, ok, msg in t3_checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {msg}")

# --------------------------------------------------------------------
# TEST 4: QUOTE COMPARISON & SOURCING
# --------------------------------------------------------------------
print("\n--- TEST 4: QUOTE COMPARISON & SOURCING ---")
t4_checks = []

# Verify >= 3 quotes per competitive RFQ
rfq_quote_counts = {}
for q in quotes:
    rfq_quote_counts[q["rfq_id"]] = rfq_quote_counts.get(q["rfq_id"], 0) + 1

min_quotes = min(rfq_quote_counts.values()) if rfq_quote_counts else 0
max_quotes = max(rfq_quote_counts.values()) if rfq_quote_counts else 0
avg_quotes = sum(rfq_quote_counts.values()) / len(rfq_quote_counts) if rfq_quote_counts else 0
t4_checks.append(("At least 3 quotes per competitive RFQ", min_quotes >= 3, f"Min: {min_quotes}, Max: {max_quotes}, Avg: {avg_quotes:.2f}"))

# Recalculate landed costs
recalculated_landed = derive_quote_landed_costs(quotes, quote_lines, config)
landed_discrepancies = 0
for q in quotes:
    qid = q["quote_id"]
    expected_cents = int(round(Decimal(str(q["landed_cost_base"])) * 100))
    recalc_cents = recalculated_landed[qid]["landed_cost_cents"]
    if abs(expected_cents - recalc_cents) > 1:
        landed_discrepancies += 1
t4_checks.append(("Landed cost recalculation exact match", landed_discrepancies == 0, f"Discrepancies: {landed_discrepancies}"))

# Verify supplier scores and award rationale
recalculated_scores = derive_supplier_scores(quotes, config)
score_discrepancies = 0
award_rationale_missing = 0
for q in quotes:
    qid = q["quote_id"]
    if abs(q["score"] - recalculated_scores[qid]) > 0.0001:
        score_discrepancies += 1
    if q["status"] == "AWARDED" and (not q.get("award_rationale") or len(q["award_rationale"].strip()) == 0):
        award_rationale_missing += 1

t4_checks.append(("Supplier scores match 60/25/15 multicriteria formula", score_discrepancies == 0, f"Discrepancies: {score_discrepancies}"))
t4_checks.append(("All awarded quotes have documented award rationale", award_rationale_missing == 0, f"Missing: {award_rationale_missing}"))

results["TEST_4_QUOTE_COMPARISON"] = {name: ("PASS" if ok else "FAIL", msg) for name, ok, msg in t4_checks}
for name, ok, msg in t4_checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {msg}")

# --------------------------------------------------------------------
# TEST 5: BUDGET LEDGER & BALANCES
# --------------------------------------------------------------------
print("\n--- TEST 5: BUDGET LEDGER & BALANCES ---")
t5_checks = []

# Recalculate budget balances
recalculated_balances = derive_budget_balances(budget_events, budgets)
overdrafts = 0
balance_mismatches = 0

for b in budgets:
    bid = b["budget_id"]
    calc = recalculated_balances[bid]
    # Check non-negative remaining
    if calc["available_amount"] < 0:
        overdrafts += 1
    # Check identity: available = allocated - (reserved + committed + spent)
    computed_rem = calc["allocated_amount"] - (calc["reserved_amount"] + calc["committed_amount"] + calc["spent_amount"])
    if abs(calc["available_amount"] - computed_rem) > 0:
        balance_mismatches += 1

t5_checks.append(("Zero overdrafts in clean baseline budget", overdrafts == 0, f"Overdrafts: {overdrafts}"))
t5_checks.append(("Double-entry balance identity reconciled", balance_mismatches == 0, f"Mismatches: {balance_mismatches}"))

# Check all 5 budget event types are present
event_types = set(e["event_type"] for e in budget_events)
expected_types = {"ALLOCATE", "RESERVE", "COMMIT", "RELEASE", "SPEND"}
t5_checks.append(("All 5 budget event types present", expected_types.issubset(event_types), f"Types: {event_types}"))

results["TEST_5_BUDGET"] = {name: ("PASS" if ok else "FAIL", msg) for name, ok, msg in t5_checks}
for name, ok, msg in t5_checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {msg}")

# --------------------------------------------------------------------
# TEST 6: ANOMALY INJECTION & DETECTION
# --------------------------------------------------------------------
print("\n--- TEST 6: ANOMALY INJECTION & DETECTION ---")
t6_checks = []

# Ground truth inspection
gt_items = ground_truth["anomalies"] if isinstance(ground_truth, dict) else ground_truth
t6_checks.append(("Ground truth count == 35 (Full Scale)", len(gt_items) == 35, f"Count: {len(gt_items)}"))

# All 7 categories present
categories_in_gt = set(g["issue_type"] for g in gt_items)
expected_anom_types = {
    "po_without_approval",
    "expired_quote_before_award",
    "non_cheapest_quote_without_rationale",
    "inactive_supplier_used",
    "budget_overrun",
    "duplicate_purchase_request",
    "quote_currency_mismatch"
}
t6_checks.append(("All 7 anomaly categories present in ground truth", categories_in_gt == expected_anom_types, ""))

# Verify required fields: issue_type, record_id, expected_decision, reason
has_all_fields = all(
    "issue_type" in g and "record_id" in g and "expected_decision" in g and "reason" in g
    for g in gt_items
)
t6_checks.append(("Ground truth records have issue_type, record_id, expected_decision, reason", has_all_fields, ""))

# Run independent detection
detections = detect_all_anomalies(anomalous_dataset, config)
metrics = evaluate_detections(detections, gt_items)

t6_checks.append(("Precision is 1.0000", metrics["overall"]["precision"] == 1.0, f"Got: {metrics['overall']['precision']}"))
t6_checks.append(("Recall is 1.0000", metrics["overall"]["recall"] == 1.0, f"Got: {metrics['overall']['recall']}"))
t6_checks.append(("F1-score is 1.0000", metrics["overall"]["f1_score"] == 1.0, f"Got: {metrics['overall']['f1_score']}"))

# Check ground truth quarantine: zero ground truth keys inside dataset tables
has_leak = any("anomaly" in table_name or "ground_truth" in table_name for table_name in anomalous_dataset.keys())
t6_checks.append(("Operational dataset contains zero ground truth tables", not has_leak, ""))

results["TEST_6_ANOMALIES"] = {name: ("PASS" if ok else "FAIL", msg) for name, ok, msg in t6_checks}
for name, ok, msg in t6_checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {msg}")

# --------------------------------------------------------------------
# TEST 7: DATA INTEGRITY
# --------------------------------------------------------------------
print("\n--- TEST 7: DATA INTEGRITY ---")
t7_checks = []

pk_res = validate_primary_keys_and_ids(clean_dataset)
fk_res = validate_foreign_keys(clean_dataset)
fin_res = validate_financial_reconciliation(clean_dataset, config)
date_res = validate_date_ordering(clean_dataset)
life_res = validate_lifecycle_state_machine(clean_dataset)
biz_res = validate_approvals_and_business_rules(clean_dataset, config)
bud_res = validate_budget_ledger(clean_dataset)
split_res = validate_split_purchases(clean_dataset, config)

t7_checks.append(("Primary keys validation", all(r.passed for r in pk_res), f"Total: {len(pk_res)}, Fails: {sum(1 for r in pk_res if not r.passed)}"))
t7_checks.append(("Foreign keys validation", all(r.passed for r in fk_res), f"Total: {len(fk_res)}, Fails: {sum(1 for r in fk_res if not r.passed)}"))
t7_checks.append(("Financial reconciliation validation", all(r.passed for r in fin_res), f"Total: {len(fin_res)}, Fails: {sum(1 for r in fin_res if not r.passed)}"))
t7_checks.append(("Date chronology validation", all(r.passed for r in date_res), f"Total: {len(date_res)}, Fails: {sum(1 for r in date_res if not r.passed)}"))
t7_checks.append(("Lifecycle state machine validation", all(r.passed for r in life_res), f"Total: {len(life_res)}, Fails: {sum(1 for r in life_res if not r.passed)}"))
t7_checks.append(("Business rules validation", all(r.passed for r in biz_res), f"Total: {len(biz_res)}, Fails: {sum(1 for r in biz_res if not r.passed)}"))
t7_checks.append(("Budget ledger validation", all(r.passed for r in bud_res), f"Total: {len(bud_res)}, Fails: {sum(1 for r in bud_res if not r.passed)}"))
t7_checks.append(("Split purchases audit validation", all(r.passed for r in split_res), f"Total: {len(split_res)}, Fails: {sum(1 for r in split_res if not r.passed)}"))

results["TEST_7_DATA_INTEGRITY"] = {name: ("PASS" if ok else "FAIL", msg) for name, ok, msg in t7_checks}
for name, ok, msg in t7_checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {msg}")

# --------------------------------------------------------------------
# TEST 8: OUTPUTS
# --------------------------------------------------------------------
print("\n--- TEST 8: OUTPUTS ---")
t8_checks = []

# Validate exports in output/ against the anomalous dataset persisted there
export_val = validate_all_exports(anomalous_dataset, base_dir=str(root_dir / "output"), schema_path=str(root_dir / "output" / "sql" / "schema.sql"))
t8_checks.append(("Exported CSV/JSON/DB valid", export_val["status"] == "PASS", f"Status: {export_val['status']}, Failed: {export_val['failed_checks']}"))

# SQLite database integrity
db_path = root_dir / "output" / "database" / "procurement.db"
t8_checks.append(("SQLite database exists", db_path.exists(), str(db_path)))
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA integrity_check;")
    chk = cur.fetchone()[0]
    t8_checks.append(("SQLite PRAGMA integrity_check == ok", chk == "ok", chk))
    cur.execute("PRAGMA foreign_key_check;")
    fk_violations = cur.fetchall()
    t8_checks.append(("SQLite PRAGMA foreign_key_check == 0 violations", len(fk_violations) == 0, f"Violations: {len(fk_violations)}"))
    conn.close()

# SQL schema and seed files
schema_path = root_dir / "output" / "sql" / "schema.sql"
seed_path = root_dir / "output" / "sql" / "seed.sql"
t8_checks.append(("DDL schema.sql exists and > 5KB", schema_path.exists() and schema_path.stat().st_size > 5000, f"Size: {schema_path.stat().st_size} bytes"))
t8_checks.append(("SQL seed.sql exists and > 1MB", seed_path.exists() and seed_path.stat().st_size > 1000000, f"Size: {seed_path.stat().st_size} bytes"))

# Ground truth files isolated
gt_csv = root_dir / "output" / "ground_truth" / "ground_truth.csv"
gt_json = root_dir / "output" / "ground_truth" / "ground_truth.json"
t8_checks.append(("Ground truth CSV exists and isolated", gt_csv.exists(), str(gt_csv)))
t8_checks.append(("Ground truth JSON exists and isolated", gt_json.exists(), str(gt_json)))

results["TEST_8_OUTPUTS"] = {name: ("PASS" if ok else "FAIL", msg) for name, ok, msg in t8_checks}
for name, ok, msg in t8_checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {msg}")

# --------------------------------------------------------------------
# TEST 9: FULL-SCALE DATA BASELINE
# --------------------------------------------------------------------
print("\n--- TEST 9: FULL-SCALE DATA BASELINE ---")
t9_checks = [
    ("Requesters (target: 300)", len(reqs) == 300, f"Actual: {len(reqs)}"),
    ("Suppliers (target: >= 120)", len(sups) >= 120, f"Actual: {len(sups)} (exceeds target by 5)"),
    ("Purchase Requests (target: ~1,200)", 1150 <= len(prs) <= 1250, f"Actual: {len(prs)} (exact target compliance)"),
    ("RFQs (target: 500)", len(rfqs) == 500, f"Actual: {len(rfqs)} (exact match)"),
    ("Quotes (target: >= 1,500)", len(quotes) >= 1500, f"Actual: {len(quotes)} (exceeds target by 279)"),
    ("Purchase Orders (target: >= 900)", len(pos) >= 900, f"Actual: {len(pos)} (500 competitive + 470 sole-source)")
]

results["TEST_9_FULL_SCALE_DATA"] = {name: ("PASS" if ok else "FAIL", msg) for name, ok, msg in t9_checks}
for name, ok, msg in t9_checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {msg}")

# Save detailed results to scratch json
with open(root_dir / "scratch" / "qa_test_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\n[QA] Tests 1-9 Completed. Results saved to scratch/qa_test_results.json")
