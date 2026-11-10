"""Procure-to-Pay Synthetic Data Generator package."""

from __future__ import annotations

from typing import Any, Dict, Optional
import numpy as np

from datagen.approvals import generate_approvals
from datagen.budget import generate_budget_events
from datagen.config import load_config
from datagen.delivery import generate_deliveries
from datagen.events import generate_status_events
from datagen.ids import IDFactory
from datagen.masters import (
    generate_all_masters,
    generate_approvers,
    generate_budgets,
    generate_departments,
    generate_requesters,
    generate_suppliers,
)
from datagen.orders import generate_orders
from datagen.requests import (
    generate_all_requests,
    generate_purchase_requests,
    generate_request_lines,
)
from datagen.sourcing import classify_sourcing_paths, generate_sourcing
from datagen.workflow import generate_procurement_workflow, run_clean_path_validation

__version__ = "1.0.0"


def generate_phase2_dataset(
    config_path: Optional[str] = None,
    scale: Optional[str] = None,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Generate Phase 2 synthetic datasets (master data and purchase requests)."""
    config = load_config(config_path)

    if scale is not None:
        if scale not in config["scale"]:
            raise ValueError(f"Unknown scale '{scale}'. Options: {list(config['scale'].keys())}")
        config["generation"]["default_scale"] = scale

    used_scale = config["generation"]["default_scale"]
    used_seed = seed if seed is not None else int(config["generation"]["default_seed"])
    fiscal_year = int(config["project"]["fiscal_year"])

    rng = np.random.default_rng(used_seed)
    id_factory = IDFactory(fiscal_year=fiscal_year)

    masters = generate_all_masters(config, rng, id_factory)
    requests = generate_all_requests(
        config,
        rng,
        id_factory,
        masters["departments"],
        masters["budgets"],
        masters["requesters"],
    )

    return {
        "departments": masters["departments"],
        "budgets": masters["budgets"],
        "requesters": masters["requesters"],
        "suppliers": masters["suppliers"],
        "approvers": masters["approvers"],
        "purchase_requests": requests["purchase_requests"],
        "request_lines": requests["request_lines"],
        "metadata": {
            "scale": used_scale,
            "seed": used_seed,
            "fiscal_year": fiscal_year,
            "base_currency": config["project"]["base_currency"],
        },
    }


__all__ = [
    "__version__",
    "generate_procurement_workflow",
    "generate_phase2_dataset",
    "run_clean_path_validation",
    "generate_all_masters",
    "generate_departments",
    "generate_budgets",
    "generate_requesters",
    "generate_suppliers",
    "generate_approvers",
    "generate_all_requests",
    "generate_purchase_requests",
    "generate_request_lines",
    "generate_approvals",
    "classify_sourcing_paths",
    "generate_sourcing",
    "generate_orders",
    "generate_deliveries",
    "generate_budget_events",
    "generate_status_events",
]
