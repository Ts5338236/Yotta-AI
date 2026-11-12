"""Shipment and delivery receipt generation engine.

Simulates on-time, late, and multi-shipment partial deliveries
while ensuring cumulative delivered quantities reconcile with purchase orders.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Mapping
import numpy as np

from datagen.ids import IDFactory
from datagen.masters import SYNTHETIC_FIRST_NAMES, SYNTHETIC_LAST_NAMES


def _add_days(iso_date: str, days: int) -> str:
    base = datetime.date.fromisoformat(iso_date[:10])
    target = base + datetime.timedelta(days=days)
    if target.year > 2026:
        target = datetime.date(2026, 12, 31)
    return target.isoformat()


def generate_deliveries(
    config: Mapping[str, Any],
    rng: np.random.Generator,
    id_factory: IDFactory,
    purchase_orders: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate physical shipment delivery receipts for all issued purchase orders.

    Supports:
    - Standard single on-time shipments (~80%)
    - Late shipments (~10%)
    - Multi-shipment partial fulfillment (~10%)

    Args:
        config: Central configuration dictionary.
        rng: Deterministic NumPy RNG.
        id_factory: Centralized IDFactory instance.
        purchase_orders: List of generated purchase order records.

    Returns:
        Dict[str, Any]:
            'deliveries': List of delivery records.
    """
    deliveries: List[Dict[str, Any]] = []

    for po in purchase_orders:
        po_id = po["po_id"]
        po_date = po["po_date"]
        expected_date = po["expected_delivery_date"]
        po_lines = po.get("_lines", [])

        # Total items across all lines
        total_qty = sum(l["quantity"] for l in po_lines) if po_lines else 1

        pattern_choice = rng.uniform()

        receiver_first = rng.choice(SYNTHETIC_FIRST_NAMES)
        receiver_last = rng.choice(SYNTHETIC_LAST_NAMES)
        received_by = f"{receiver_first} {receiver_last}"

        if pattern_choice < 0.10 and total_qty > 1:
            # Multi-shipment partial fulfillment (2 deliveries)
            # Shipment 1: 50% to 70% of goods
            first_qty = max(1, int(round(total_qty * rng.uniform(0.50, 0.70))))
            second_qty = total_qty - first_qty

            lead_days = int(po.get("lead_time_days", 14))
            ship1_date = _add_days(po_date, max(1, lead_days - 3))
            delivery1_id = id_factory.next_delivery_id(po_id)

            del1_rec = {
                "delivery_id": delivery1_id,
                "po_id": po_id,
                "delivery_sequence": 1,
                "ship_date": ship1_date,
                "delivery_date": ship1_date,
                "received_date": ship1_date,
                "received_by": received_by,
                "delivery_status": "PARTIAL",
                "items_delivered_count": first_qty,
                "qty_received": first_qty,
                "notes": f"Initial partial delivery: {first_qty}/{total_qty} units received",
                "created_at": f"{ship1_date}T14:30:00Z",
            }
            deliveries.append(del1_rec)

            # Shipment 2: Completes the order
            ship2_date = _add_days(ship1_date, int(rng.integers(3, 8)))
            delivery2_id = id_factory.next_delivery_id(po_id)

            del2_rec = {
                "delivery_id": delivery2_id,
                "po_id": po_id,
                "delivery_sequence": 2,
                "ship_date": ship2_date,
                "delivery_date": ship2_date,
                "received_date": ship2_date,
                "received_by": received_by,
                "delivery_status": "FULL",
                "items_delivered_count": second_qty,
                "qty_received": second_qty,
                "notes": f"Final fulfillment delivery: {second_qty} units received, order complete",
                "created_at": f"{ship2_date}T15:00:00Z",
            }
            deliveries.append(del2_rec)

            po["status"] = "COMPLETED"
            po["delivered_quantity"] = total_qty
            po["actual_delivery_date"] = ship2_date
            po["updated_at"] = f"{ship2_date}T15:00:00Z"

        else:
            # Single shipment (on-time or late)
            is_late = pattern_choice < 0.20
            if is_late:
                actual_date = _add_days(expected_date, int(rng.integers(1, 6)))
                note = "Received with minor supplier transit delay"
            else:
                # On time (on or 1-2 days before expected date)
                early_offset = int(rng.integers(-2, 1))
                actual_date = _add_days(expected_date, early_offset)
                if actual_date < po_date:
                    actual_date = po_date
                note = "Delivered on-time in good condition"

            del_id = id_factory.next_delivery_id(po_id)
            del_rec = {
                "delivery_id": del_id,
                "po_id": po_id,
                "delivery_sequence": 1,
                "ship_date": actual_date,
                "delivery_date": actual_date,
                "received_date": actual_date,
                "received_by": received_by,
                "delivery_status": "FULL",
                "items_delivered_count": total_qty,
                "qty_received": total_qty,
                "notes": note,
                "created_at": f"{actual_date}T11:00:00Z",
            }
            deliveries.append(del_rec)

            po["status"] = "COMPLETED"
            po["delivered_quantity"] = total_qty
            po["actual_delivery_date"] = actual_date
            po["updated_at"] = f"{actual_date}T11:00:00Z"

    return {
        "deliveries": deliveries,
    }

