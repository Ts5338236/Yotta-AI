"""Procure-to-Pay Synthetic Data Generator package."""

from __future__ import annotations

from typing import Any, Dict, Optional
import numpy as np

from datagen.config import load_config
from datagen.ids import IDFactory
from datagen.masters import (
    generate_all_masters,
    generate_budgets,
    generate_departments,
    generate_requesters,
    generate_suppliers,
)
from datagen.requests import (
    generate_all_requests,
    generate_purchase_requests,
    generate_request_lines,
)

__version__ = "1.0.0"


def generate_phase2_dataset(
    config_path: Optional[str] = None,
    scale: Optional[str] = None,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Coordinating entry point to generate Phase 2 synthetic datasets.

    Initializes exactly one deterministic NumPy RNG and centralized IDFactory.

    Args:
        config_path: Optional custom path to YAML config.
        scale: Optional scale tier ('starter' or 'full').
        seed: Optional custom integer seed.

    Returns:
        Dict[str, Any]: In-memory dictionary containing generated dataset lists:
            'departments', 'budgets', 'requesters', 'suppliers',
            'purchase_requests', 'request_lines', and 'metadata'.
    """
    config = load_config(config_path)

    if scale is not None:
        if scale not in config["scale"]:
            raise ValueError(f"Unknown scale '{scale}'. Options: {list(config['scale'].keys())}")
        config["generation"]["default_scale"] = scale

    used_scale = config["generation"]["default_scale"]
    used_seed = seed if seed is not None else int(config["generation"]["default_seed"])
    fiscal_year = int(config["project"]["fiscal_year"])

    # Hard technical constraint: Exactly one RNG initialized at entry point
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
    "generate_phase2_dataset",
    "generate_all_masters",
    "generate_departments",
    "generate_budgets",
    "generate_requesters",
    "generate_suppliers",
    "generate_all_requests",
    "generate_purchase_requests",
    "generate_request_lines",
]
