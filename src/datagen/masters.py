"""Master data generation module for Procure-to-Pay Synthetic Data Generator.

Generates realistic, deterministic organizational and vendor master records:
- Departments
- Budgets
- Requesters (with valid hierarchical manager relationships)
- Suppliers (with risk scores, currencies, and lead times)
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional
import numpy as np

from datagen.ids import IDFactory


DEPARTMENT_CATALOG: List[tuple[str, str]] = [
    ("Engineering", "CC-ENG-100"),
    ("Information Technology", "CC-IT-200"),
    ("Finance", "CC-FIN-300"),
    ("Human Resources", "CC-HR-400"),
    ("Procurement", "CC-PROC-500"),
    ("Operations", "CC-OPS-600"),
    ("Marketing", "CC-MKT-700"),
    ("Sales", "CC-SAL-800"),
    ("Administration", "CC-ADM-900"),
    ("Research and Development", "CC-RND-110"),
    ("Legal", "CC-LEG-120"),
    ("Facilities", "CC-FAC-130"),
]

SYNTHETIC_FIRST_NAMES: List[str] = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Sam",
    "Chris", "Pat", "Robin", "Dakota", "Jamie", "Logan", "Kendall", "Reese",
    "Hayden", "Cameron", "Quinn", "Skyler", "Jesse", "Rowan", "Peyton", "Finley",
    "Emerson", "Adrian", "Kai", "Sage", "River", "Elliott", "Dana", "Drew"
]

SYNTHETIC_LAST_NAMES: List[str] = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young"
]

SUPPLIER_NAME_PREFIXES: List[str] = [
    "Apex", "Global", "Summit", "Vertex", "Prime", "Nexus", "Pinnacle",
    "Vanguard", "Horizon", "Quantum", "Alliance", "Optima", "Integrity",
    "Dynamic", "Starlight", "Pacific", "Atlantic", "Continental", "Beacon", "Crestview"
]

SUPPLIER_NAME_CORES: List[str] = [
    "Tech", "Industrial", "Logistics", "Solutions", "Materials", "Systems",
    "Networks", "Equip", "Supplies", "Energy", "Analytics", "Manufacturing",
    "Dynamics", "Components", "Enterprises"
]

SUPPLIER_NAME_SUFFIXES: List[str] = [
    "Corp", "Inc", "LLC", "Ltd", "Group", "Global", "Enterprises", "International"
]

CURRENCY_COUNTRY_MAP: Dict[str, str] = {
    "USD": "USA",
    "EUR": "DEU",
    "GBP": "GBR",
    "INR": "IND",
    "JPY": "JPN",
}


def _get_scale_name(config: Mapping[str, Any]) -> str:
    """Retrieve default or configured scale tier name."""
    return str(config.get("generation", {}).get("default_scale", "starter"))


def generate_departments(
    config: Mapping[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
) -> List[Dict[str, Any]]:
    """Generate department master records based on configuration.

    Args:
        config: Central configuration dictionary.
        rng: Deterministic NumPy RNG instance.
        id_factory: Centralized IDFactory instance.

    Returns:
        List[Dict[str, Any]]: Generated department records.
    """
    scale_name = _get_scale_name(config)
    dept_count = int(config["scale"][scale_name]["departments"])

    if dept_count > len(DEPARTMENT_CATALOG):
        raise ValueError(
            f"Configured department count ({dept_count}) exceeds available presets ({len(DEPARTMENT_CATALOG)})."
        )

    departments: List[Dict[str, Any]] = []
    for i in range(dept_count):
        dept_name, cost_center = DEPARTMENT_CATALOG[i]
        dept_id = id_factory.next_department_id()
        departments.append({
            "department_id": dept_id,
            "name": dept_name,
            "cost_center_code": cost_center,
            "cost_centre": cost_center,
            "effective_from": "2026-01-01",
            "effective_to": "2026-12-31",
            "created_at": "2026-01-01T00:00:00Z",
        })

    return departments


def generate_budgets(
    config: Mapping[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    departments: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate initial fiscal year budget records for all departments.

    Budget allocations scale with the dataset volume to comfortably fund
    all clean-path procurement operations without budget overruns.

    Args:
        config: Central configuration dictionary.
        rng: Deterministic NumPy RNG instance.
        id_factory: Centralized IDFactory instance.
        departments: List of generated department master records.

    Returns:
        List[Dict[str, Any]]: Generated budget records.
    """
    fiscal_year = int(config["project"]["fiscal_year"])
    currency = str(config["project"]["base_currency"])
    scale_name = _get_scale_name(config)

    # Scale budget limits with requisition volume
    scale_factor = 4 if scale_name == "full" else 1

    budgets: List[Dict[str, Any]] = []
    for dept in departments:
        budget_id = id_factory.next_budget_id()
        # Variance between $750k - $3.5M (starter) or $3M - $14M (full) in $50,000 steps
        budget_steps = rng.integers(15 * scale_factor, 71 * scale_factor)
        allocated_usd = float(budget_steps * 50000)
        allocated_minor = int(allocated_usd * 100)

        budgets.append({
            "budget_id": budget_id,
            "department_id": dept["department_id"],
            "fiscal_year": fiscal_year,
            "currency": currency,
            "allocated": allocated_usd,
            "allocated_amount": allocated_minor,
            "reserved": 0.0,
            "reserved_amount": 0,
            "committed": 0.0,
            "committed_amount": 0,
            "spent": 0.0,
            "spent_amount": 0,
            "created_at": "2026-01-01T00:00:00Z",
        })

    return budgets


def generate_requesters(
    config: Mapping[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    departments: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate corporate requesters with realistic organizational hierarchies.

    Guarantees:
    - Every department has at least 1 requester.
    - Department leader has manager_id = None.
    - Subsequent requesters reference an eligible senior in the same department.
    - Strict acyclic tree structure (no circular relationships).

    Args:
        config: Central configuration dictionary.
        rng: Deterministic NumPy RNG instance.
        id_factory: Centralized IDFactory instance.
        departments: List of generated department master records.

    Returns:
        List[Dict[str, Any]]: Generated requester records.
    """
    scale_name = _get_scale_name(config)
    total_requesters = int(config["scale"][scale_name]["requesters"])
    dept_count = len(departments)

    if total_requesters < dept_count:
        raise ValueError(
            f"Requester count ({total_requesters}) cannot be less than department count ({dept_count})."
        )

    # Initial allocation: guarantee at least 1 requester per department
    dept_counts: Dict[str, int] = {d["department_id"]: 1 for d in departments}
    remaining = total_requesters - dept_count

    # Realistic departmental weighting for remaining requesters
    raw_weights = [
        0.22, 0.16, 0.12, 0.10, 0.09, 0.08,
        0.06, 0.05, 0.04, 0.03, 0.03, 0.02
    ][:dept_count]
    normalized_weights = np.array(raw_weights) / sum(raw_weights)

    if remaining > 0:
        additional_assignments = rng.multinomial(remaining, normalized_weights)
        for i, dept in enumerate(departments):
            dept_counts[dept["department_id"]] += int(additional_assignments[i])

    grades = ["DIRECTOR", "SENIOR_MANAGER", "MANAGER", "SENIOR_INDIVIDUAL", "INDIVIDUAL"]

    requesters: List[Dict[str, Any]] = []
    req_sequence = 1

    for dept in departments:
        dept_id = dept["department_id"]
        count_in_dept = dept_counts[dept_id]
        dept_requester_ids: List[str] = []

        for idx in range(count_in_dept):
            req_id = id_factory.next_requester_id()
            first = rng.choice(SYNTHETIC_FIRST_NAMES)
            last = rng.choice(SYNTHETIC_LAST_NAMES)
            name = f"{first} {last}"
            email = f"{first.lower()}.{last.lower()}.{req_sequence:03d}@example.com"
            req_sequence += 1

            if idx == 0:
                # Top department leader
                grade = "DIRECTOR"
                job_title = f"Director of {dept['name']}"
                manager_id = None
            elif idx == 1 and count_in_dept > 3:
                grade = "SENIOR_MANAGER"
                job_title = f"Senior Manager, {dept['name']}"
                manager_id = dept_requester_ids[0]
            elif idx < 4:
                grade = "MANAGER"
                job_title = f"Manager, {dept['name']}"
                # Reports to director or senior manager
                manager_id = dept_requester_ids[0]
            else:
                grade = rng.choice(["SENIOR_INDIVIDUAL", "INDIVIDUAL"], p=[0.4, 0.6])
                job_title = f"{'Senior ' if grade == 'SENIOR_INDIVIDUAL' else ''}Specialist, {dept['name']}"
                # Reports to one of the earlier managers in the department
                eligible_managers = dept_requester_ids[:min(3, len(dept_requester_ids))]
                manager_id = eligible_managers[rng.integers(0, len(eligible_managers))]

            dept_requester_ids.append(req_id)

            requesters.append({
                "requester_id": req_id,
                "department_id": dept_id,
                "name": name,
                "email": email,
                "grade": grade,
                "job_title": job_title,
                "manager_id": manager_id,
                "created_at": "2026-01-01T00:00:00Z",
            })

    return requesters


def generate_suppliers(
    config: Mapping[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
) -> List[Dict[str, Any]]:
    """Generate commercial vendor master records.

    Args:
        config: Central configuration dictionary.
        rng: Deterministic NumPy RNG instance.
        id_factory: Centralized IDFactory instance.

    Returns:
        List[Dict[str, Any]]: Generated supplier records.
    """
    scale_name = _get_scale_name(config)
    supplier_count = int(config["scale"][scale_name]["suppliers"])

    supported_currencies = list(config.get("fx_rates", {"USD": 1.0}).keys())
    # Deterministic currency probability distribution (USD dominant)
    curr_probs = []
    default_prob_map = {"USD": 0.55, "EUR": 0.15, "GBP": 0.12, "INR": 0.10, "JPY": 0.08}
    for c in supported_currencies:
        curr_probs.append(default_prob_map.get(c, 0.05))
    curr_probs = np.array(curr_probs) / sum(curr_probs)

    statuses = ["ACTIVE", "PREFERRED", "PROBATION", "INACTIVE"]
    status_probs = [0.70, 0.15, 0.10, 0.05]

    risk_levels = ["LOW", "MEDIUM", "HIGH"]
    risk_probs = [0.65, 0.25, 0.10]

    suppliers: List[Dict[str, Any]] = []
    used_names: set[str] = set()

    for i in range(supplier_count):
        sup_id = id_factory.next_supplier_id()
        supplier_code = f"SUP-C-{(i + 1):04d}"

        # Generate unique synthetic business name
        while True:
            p = rng.choice(SUPPLIER_NAME_PREFIXES)
            c = rng.choice(SUPPLIER_NAME_CORES)
            s = rng.choice(SUPPLIER_NAME_SUFFIXES)
            name = f"{p} {c} {s}"
            if name not in used_names:
                used_names.add(name)
                break

        slug = "".join(ch for ch in name.lower() if ch.isalnum())
        contact_email = f"sales@{slug}.example.com"

        currency = rng.choice(supported_currencies, p=curr_probs)
        country = CURRENCY_COUNTRY_MAP.get(currency, "USA")

        status = rng.choice(statuses, p=status_probs)
        risk_class = rng.choice(risk_levels, p=risk_probs)

        if risk_class == "LOW":
            risk_score = round(float(rng.uniform(0.05, 0.30)), 2)
        elif risk_class == "MEDIUM":
            risk_score = round(float(rng.uniform(0.31, 0.65)), 2)
        else:
            risk_score = round(float(rng.uniform(0.66, 0.95)), 2)

        lead_time = int(rng.integers(3, 31))  # 3 to 30 days mean lead time

        suppliers.append({
            "supplier_id": sup_id,
            "supplier_code": supplier_code,
            "name": name,
            "contact_email": contact_email,
            "country": country,
            "currency": currency,
            "status": status,
            "status_effective_dates": "2026-01-01 to 2026-12-31",
            "effective_from": "2026-01-01",
            "effective_to": "2026-12-31",
            "risk_flag": risk_class,
            "risk_classification": risk_class,
            "risk_score": risk_score,
            "lead_time_mean": lead_time,
            "created_at": "2026-01-01T00:00:00Z",
        })

    return suppliers


def generate_approvers(
    config: Mapping[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    departments: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate authorized approvers for each department and corporate finance.

    Tiers:
    - Line Managers: limit <= $2,000
    - Department Heads: limit <= $25,000
    - Corporate Finance: limit > $25,000

    Args:
        config: Central configuration dictionary.
        rng: Deterministic NumPy RNG.
        id_factory: Centralized IDFactory instance.
        departments: Generated department master records.

    Returns:
        List[Dict[str, Any]]: Generated approver records.
    """
    thresholds = config.get("approval_thresholds", {})
    mgr_limit = int(thresholds.get("manager_limit", 2000))
    dept_head_limit = int(thresholds.get("department_head_limit", 25000))

    approvers: List[Dict[str, Any]] = []
    approver_seq = 1

    # 1. Line Manager and Department Head per department
    for dept in departments:
        dept_id = dept["department_id"]
        dept_name = dept["name"]

        # Line Manager
        app_id = id_factory.next_approver_id()
        first = rng.choice(SYNTHETIC_FIRST_NAMES)
        last = rng.choice(SYNTHETIC_LAST_NAMES)
        approvers.append({
            "approver_id": app_id,
            "name": f"{first} {last}",
            "email": f"{first.lower()}.{last.lower()}.app{approver_seq:02d}@example.com",
            "department_id": dept_id,
            "role": "LINE_MANAGER",
            "approval_limit": mgr_limit * 100,  # cents
            "approval_limit_usd": mgr_limit,
            "is_active": 1,
            "created_at": "2026-01-01T00:00:00Z",
        })
        approver_seq += 1

        # Department Head
        app_id_head = id_factory.next_approver_id()
        first_h = rng.choice(SYNTHETIC_FIRST_NAMES)
        last_h = rng.choice(SYNTHETIC_LAST_NAMES)
        approvers.append({
            "approver_id": app_id_head,
            "name": f"{first_h} {last_h}",
            "email": f"{first_h.lower()}.{last_h.lower()}.app{approver_seq:02d}@example.com",
            "department_id": dept_id,
            "role": "DEPARTMENT_HEAD",
            "approval_limit": dept_head_limit * 100,  # cents
            "approval_limit_usd": dept_head_limit,
            "is_active": 1,
            "created_at": "2026-01-01T00:00:00Z",
        })
        approver_seq += 1

    # 2. Corporate Finance Approvers (2 officers)
    finance_dept = next((d for d in departments if d["name"] == "Finance"), departments[0])
    for _ in range(2):
        app_id_fin = id_factory.next_approver_id()
        first_f = rng.choice(SYNTHETIC_FIRST_NAMES)
        last_f = rng.choice(SYNTHETIC_LAST_NAMES)
        approvers.append({
            "approver_id": app_id_fin,
            "name": f"{first_f} {last_f}",
            "email": f"{first_f.lower()}.{last_f.lower()}.app{approver_seq:02d}@example.com",
            "department_id": finance_dept["department_id"],
            "role": "FINANCE",
            "approval_limit": 1000000 * 100,  # $1,000,000 limit
            "approval_limit_usd": 1000000,
            "is_active": 1,
            "created_at": "2026-01-01T00:00:00Z",
        })
        approver_seq += 1

    return approvers


def generate_all_masters(
    config: Mapping[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
) -> Dict[str, List[Dict[str, Any]]]:
    """Coordinating entry point for generating all Phase 2 master data entities.

    Args:
        config: Validated configuration dictionary.
        rng: Deterministic NumPy RNG.
        id_factory: Centralized IDFactory instance.

    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary containing master entity lists:
            'departments', 'budgets', 'requesters', 'suppliers', 'approvers'.
    """
    departments = generate_departments(config, rng, id_factory)
    budgets = generate_budgets(config, rng, id_factory, departments)
    requesters = generate_requesters(config, rng, id_factory, departments)
    suppliers = generate_suppliers(config, rng, id_factory)
    approvers = generate_approvers(config, rng, id_factory, departments)

    return {
        "departments": departments,
        "budgets": budgets,
        "requesters": requesters,
        "suppliers": suppliers,
        "approvers": approvers,
    }
