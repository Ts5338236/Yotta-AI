"""Unit tests for StatusEvent lifecycle audit history."""

import pytest

from datagen.workflow import generate_procurement_workflow


@pytest.fixture(scope="module")
def workflow_dataset():
    """Generate workflow dataset for status event testing."""
    return generate_procurement_workflow(scale="starter", seed=20261022)


def test_status_events_entity_coverage(workflow_dataset):
    """Verify that status events audit all 4 lifecycle entities."""
    events = workflow_dataset["status_events"]
    entities = {e["entity"] for e in events}

    expected_entities = {"PURCHASE_REQUEST", "RFQ", "PURCHASE_ORDER", "DELIVERY"}
    assert expected_entities.issubset(entities)

    assert len(events) > 500  # Detailed transition history


def test_status_events_chronological_sequence(workflow_dataset):
    """Verify that event transitions for every entity follow valid chronological order."""
    events = workflow_dataset["status_events"]

    events_by_entity: dict[tuple[str, str], list] = {}
    for ev in events:
        key = (ev["entity"], ev["entity_id"])
        events_by_entity.setdefault(key, []).append(ev)

    for (ent_type, ent_id), ev_list in events_by_entity.items():
        assert len(ev_list) >= 1
        for i in range(1, len(ev_list)):
            prev_ts = ev_list[i - 1]["event_ts"]
            curr_ts = ev_list[i]["event_ts"]
            assert curr_ts >= prev_ts, f"Out of order transition on {ent_type} {ent_id}: {curr_ts} < {prev_ts}"
