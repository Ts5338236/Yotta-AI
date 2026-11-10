"""Purchase Request and Request Line generation module.

Simulates realistic, category-based log-normal price distributions,
seasonal request timing across 2026, and exact source-derived financial totals.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping
import numpy as np

from datagen.derive import derive_purchase_request_totals
from datagen.ids import IDFactory


DAYS_IN_MONTH_2026: Dict[int, int] = {
    1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31,
}

CATEGORY_ITEM_CATALOG: Dict[str, List[str]] = {
    "IT Hardware": [
        "Dell Latitude 7440 14-inch Business Laptop",
        "MacBook Pro 16-inch M3 Pro Workstation",
        "Dell UltraSharp 27-inch 4K USB-C Monitor",
        "Cisco Catalyst 9300 48-Port Network Switch",
        "Logitech MX Master 3S Wireless Performance Mouse",
        "Lenovo ThinkPad X1 Carbon Gen 11 Laptop",
        "HP LaserJet Enterprise M608dn High-Speed Printer",
        "APC Smart-UPS 1500VA LCD Tower Backup Power",
        "Samsung 34-inch Ultra-Wide Curved Office Display",
        "Poly Studio USB Video Bar for Conference Rooms",
    ],
    "Software": [
        "Enterprise Cloud Infrastructure Annual Subscription",
        "Project Portfolio Management SaaS Team License",
        "Advanced Data Analytics & Modeling Platform Seat",
        "Cybersecurity Endpoint Detection & Response Subscription",
        "Enterprise CRM System Annual User License",
        "Developer IDE & Code Intelligence Team Subscription",
        "Business Intelligence Visual Analytics Dashboard License",
        "Enterprise Collaboration & Communication Suite Seat",
    ],
    "Office Supplies": [
        "Ergonomic Non-Slip Desk Blotter Pads (Box of 10)",
        "Premium Rollerball Gel Ink Pens (Pack of 50)",
        "Multi-Purpose Recycled Copy Paper (10-Ream Case)",
        "Self-Adhesive Color Note Pads Value Multipack",
        "Heavy-Duty Commercial Desktop Stapler Set",
        "Low-Odor Chisel-Tip Dry Erase Markers (Pack of 12)",
        "Standard File Folders with Reinforced Tabs (Box of 100)",
        "Universal Document Shredder Conditioning Sheets",
    ],
    "Furniture": [
        "High-Back Ergonomic Mesh Executive Desk Chair",
        "Dual-Motor Electric Height-Adjustable Standing Desk",
        "Conference Room Mid-Back Leather Swivel Chair",
        "Commercial 3-Drawer Under-Desk Mobile Pedestal",
        "Acoustic Fabric Desk Partition Privacy Screen",
        "Modular Executive Reception Lounge Sectional Sofa",
        "Magnetic Whiteboard Mobile Double-Sided Easel",
        "Heavy-Duty Locking Steel Storage Cabinet 72-inch",
    ],
    "Industrial Equipment": [
        "Heavy-Duty Hydraulic Pallet Jack 5500 lbs Capacity",
        "Digital Precision Torque Wrench Calibration Kit",
        "High-Precision Analytical Laboratory Bench Scale",
        "Two-Stage Industrial Air Compressor 60 Gallon",
        "Laser Distance Meter with Bluetooth Connectivity",
        "Wall-Mounted Emergency Eye Wash & Drench Station",
        "Electric Hydraulic Lift Scissor Table 2000 lbs",
        "Multi-Channel Vibration Analysis Diagnostic Meter",
    ],
    "Maintenance": [
        "Commercial HVAC Synthetic Air Filters MERV 13 (Pack of 12)",
        "Energy-Efficient Commercial LED Troffer Light Fixtures",
        "Universal Emergency Exit Light with Battery Backup",
        "Heavy-Duty Industrial Floor Degreaser Cleaner (5 Gallon)",
        "Anti-Wear Hydraulic Machine Lubricant Oil ISO 46",
        "Stainless Steel Replacement Industrial Ball Valves 2-inch",
        "Molded Case Circuit Breaker 20A Three-Phase Set",
        "Facility Maintenance Electrical & Hand Tool Kit",
    ],
    "Professional Services": [
        "Enterprise Cloud Architecture Consulting (Block of Hours)",
        "External Cybersecurity Penetration Testing Assessment",
        "Corporate Financial & Tax Compliance Advisory Services",
        "Commercial Contract Legal Review & Drafting Retainer",
        "Data Engineering & Warehouse Migration Consulting",
        "Cloud Cost Optimization & Performance Audit Engagement",
        "Executive Leadership & Management Workshop Training",
        "Global Supply Chain Operational Risk Assessment",
    ],
    "Logistics": [
        "Double-Wall Corrugated Heavy-Duty Shipping Boxes (Pack of 50)",
        "Industrial Cast Hand Stretch Film Wrap (Case of 4)",
        "Direct Thermal Shipping Address Labels (Pack of 6 Rolls)",
        "Commercial Grade Packaging Carton Sealing Tape (Case of 36)",
        "Heat-Treated Standard Wooden Shipping Pallets (Stack of 10)",
        "Precision Impact Indicator Shipping Monitors (Box of 50)",
        "Industrial Rugged Wireless Barcode Handheld Scanner",
        "Manual Pallet Strapping Tensioner & Sealer Tool Kit",
    ],
    "Facilities": [
        "Commercial Grade Medical HEPA Air Filtration Unit",
        "Touchless Automatic Hand Sanitizer Floor Stands (Set of 4)",
        "Commercial Reverse Osmosis Drinking Water Filtration Core",
        "Comprehensive OSHA Compliant Workplace First Aid Station",
        "RFID Smart Keycard Electronic Door Access Reader",
        "Heavy-Duty Multi-Purpose ABC Dry Chemical Fire Extinguisher",
        "Commercial High-Capacity Upright HEPA Vacuum Cleaner",
        "Dual-Stream Waste & Recycling Receptacle Station",
    ],
    "Marketing": [
        "Digital Performance Advertising Creative Asset Package",
        "Custom Modular Tradeshow Exhibition Booth Backdrop",
        "Annual Corporate ESG & Investor Report Print Production",
        "Eco-Friendly Sustainable Client Gift Swag Packages",
        "Professional Video Production & Post-Editing Services",
        "Quarterly Consumer Market Research & Brand Sentiment Study",
        "Heavy-Duty Retractable Standing Event Banners (Set of 3)",
        "Strategic Omni-Channel Digital Campaign Advisory Services",
    ],
}


def _get_scale_name(config: Mapping[str, Any]) -> str:
    return str(config.get("generation", {}).get("default_scale", "starter"))


def _sample_2026_date(
    rng: np.random.Generator,
    monthly_weights: Mapping[Any, float],
) -> tuple[str, str]:
    """Sample a deterministic valid business date in 2026 based on monthly weights.

    Returns:
        tuple[str, str]: (YYYY-MM-DD date string, ISO 8601 UTC timestamp).
    """
    weights = [float(monthly_weights.get(m, monthly_weights.get(str(m), 1.0 / 12.0))) for m in range(1, 13)]
    probs = np.array(weights) / sum(weights)

    month = int(rng.choice(np.arange(1, 13), p=probs))
    max_days = DAYS_IN_MONTH_2026[month]
    day = int(rng.integers(1, max_days + 1))
    hour = int(rng.integers(8, 18))  # Business hours 08:00 to 17:00
    minute = int(rng.integers(0, 60))
    second = int(rng.integers(0, 60))

    date_str = f"2026-{month:02d}-{day:02d}"
    time_str = f"2026-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}Z"
    return date_str, time_str


def generate_purchase_requests(
    config: Mapping[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    departments: List[Dict[str, Any]],
    budgets: List[Dict[str, Any]],
    requesters: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate initial Purchase Request headers within pre-approval workflow.

    Enforces:
    - Every PR references a valid Requester.
    - Department matches Requester's Department.
    - Budget references that Department's Budget.
    - Dates strictly fall within 2026 adhering to configured monthly seasonality.
    - Pre-approval statuses only ('DRAFT', 'SUBMITTED').

    Args:
        config: Central configuration dictionary.
        rng: Deterministic NumPy RNG.
        id_factory: Centralized IDFactory instance.
        departments: Generated department master records.
        budgets: Generated budget master records.
        requesters: Generated requester records.

    Returns:
        List[Dict[str, Any]]: Generated purchase request headers.
    """
    scale_name = _get_scale_name(config)
    pr_count = int(config["scale"][scale_name]["purchase_requests"])

    # Lookup mapping from department_id to budget_id
    dept_to_budget: Dict[str, str] = {b["department_id"]: b["budget_id"] for b in budgets}

    # Monthly weights from config
    seasonality_cfg = config.get("seasonality", {})
    monthly_weights = seasonality_cfg.get("monthly_weights", {m: 1.0 / 12.0 for m in range(1, 13)})

    priorities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    priority_probs = [0.20, 0.55, 0.20, 0.05]

    statuses = ["SUBMITTED", "DRAFT"]
    status_probs = [0.85, 0.15]

    justifications = [
        "Replacement of deprecated departmental equipment",
        "Quarterly consumable and operational supplies replenishment",
        "Critical project milestone software tools and infrastructure",
        "Scheduled preventive facility maintenance and safety supplies",
        "Departmental expansion and onboarding equipment",
        "External specialized advisory support for compliance requirements",
        "Client delivery commitment and fulfillment hardware",
        "Annual renewal of enterprise business subscriptions",
    ]

    purchase_requests: List[Dict[str, Any]] = []

    for _ in range(pr_count):
        pr_id = id_factory.next_purchase_request_id()

        # Deterministically select a requester
        requester = requesters[rng.integers(0, len(requesters))]
        req_id = requester["requester_id"]
        dept_id = requester["department_id"]
        budget_id = dept_to_budget[dept_id]

        request_date, timestamp = _sample_2026_date(rng, monthly_weights)
        priority = rng.choice(priorities, p=priority_probs)
        status = rng.choice(statuses, p=status_probs)
        justification = justifications[rng.integers(0, len(justifications))]

        purchase_requests.append({
            "request_id": pr_id,
            "requester_id": req_id,
            "department_id": dept_id,
            "budget_id": budget_id,
            "currency": "USD",
            "request_date": request_date,
            "created_date": request_date,
            "status": status,
            "priority": priority,
            "justification": justification,
            "total_estimate_usd": 0.0,  # Computed in generate_all_requests from lines
            "total_estimated_amount": 0,
            "created_at": timestamp,
            "updated_at": timestamp,
        })

    # Sort stably by request_date and request_id for consistent chronological progression
    purchase_requests.sort(key=lambda r: (r["request_date"], r["request_id"]))
    return purchase_requests


def generate_request_lines(
    config: Mapping[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    purchase_requests: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate itemized request lines for every purchase request.

    Utilizes category-specific log-normal price distributions.
    Guarantees:
    - Every PR has at least one request line.
    - line_total == qty * unit_estimate.
    - Prices respect configured min_price and max_price bounds.

    Args:
        config: Central configuration dictionary.
        rng: Deterministic NumPy RNG.
        id_factory: Centralized IDFactory instance.
        purchase_requests: List of purchase request header records.

    Returns:
        List[Dict[str, Any]]: Generated request line records.
    """
    category_dists = config.get("category_distributions", {})
    available_categories = list(CATEGORY_ITEM_CATALOG.keys())

    line_count_probs = [0.40, 0.30, 0.15, 0.10, 0.05]  # 1, 2, 3, 4, 5 lines per PR

    all_request_lines: List[Dict[str, Any]] = []

    for pr in purchase_requests:
        pr_id = pr["request_id"]
        timestamp = pr["created_at"]
        num_lines = int(rng.choice([1, 2, 3, 4, 5], p=line_count_probs))

        # Select primary category for this requisition (some lines may share or vary)
        primary_category = rng.choice(available_categories)

        for line_idx in range(1, num_lines + 1):
            rl_id = id_factory.next_request_line_id()

            # 80% chance same category as primary, 20% related category
            if line_idx == 1 or rng.uniform() < 0.80:
                category = primary_category
            else:
                category = rng.choice(available_categories)

            # Sample item description
            items_for_cat = CATEGORY_ITEM_CATALOG[category]
            item_desc = items_for_cat[rng.integers(0, len(items_for_cat))]

            # Category-based log-normal price generation
            cat_cfg = category_dists.get(category, {})
            log_mean = float(cat_cfg.get("log_mean", 5.0))
            log_sigma = float(cat_cfg.get("log_sigma", 0.6))
            min_p = float(cat_cfg.get("min_price", 10.0))
            max_p = float(cat_cfg.get("max_price", 15000.0))

            raw_sample = float(rng.lognormal(mean=log_mean, sigma=log_sigma))
            bounded_unit_price = max(min_p, min(raw_sample, max_p))
            unit_estimate = round(bounded_unit_price, 2)

            # Quantity based on unit price magnitude
            if unit_estimate > 5000.0:
                qty = int(rng.integers(1, 4))
            elif unit_estimate > 1000.0:
                qty = int(rng.integers(1, 7))
            elif unit_estimate > 100.0:
                qty = int(rng.integers(1, 15))
            else:
                qty = int(rng.integers(1, 35))

            line_total = round(qty * unit_estimate, 2)
            unit_price_cents = int(round(unit_estimate * 100))
            line_total_cents = int(round(line_total * 100))

            all_request_lines.append({
                "request_line_id": rl_id,
                "request_id": pr_id,
                "line_number": line_idx,
                "item": item_desc,
                "item_description": item_desc,
                "category": category,
                "qty": qty,
                "quantity": qty,
                "unit_estimate": unit_estimate,
                "estimated_unit_price": unit_price_cents,
                "line_total": line_total,
                "estimated_line_total": line_total_cents,
                "created_at": timestamp,
            })

    return all_request_lines


def generate_all_requests(
    config: Mapping[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    departments: List[Dict[str, Any]],
    budgets: List[Dict[str, Any]],
    requesters: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Coordinating entry point for generating Purchase Requests and Request Lines.

    Calculates exact derived totals:
    total_estimate_usd = SUM(request_line.line_total).

    Args:
        config: Central configuration dictionary.
        rng: Deterministic NumPy RNG.
        id_factory: Centralized IDFactory instance.
        departments: Generated department master records.
        budgets: Generated budget master records.
        requesters: Generated requester records.

    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary with:
            'purchase_requests', 'request_lines'.
    """
    purchase_requests = generate_purchase_requests(
        config, rng, id_factory, departments, budgets, requesters
    )
    request_lines = generate_request_lines(
        config, rng, id_factory, purchase_requests
    )

    # Calculate exact derived totals from lines for each purchase request
    derive_purchase_request_totals(request_lines, purchase_requests)

    return {
        "purchase_requests": purchase_requests,
        "request_lines": request_lines,
    }
