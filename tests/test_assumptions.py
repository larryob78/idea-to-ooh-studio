from pathlib import Path

import pytest

from producer_amplifier.analysis.assumptions import AssumptionsRepository
from producer_amplifier.analysis.persistence import JsonStore


def _repo(path: Path) -> AssumptionsRepository:
    return AssumptionsRepository(JsonStore(path))


def test_assumptions_crud(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "store.json")
    added = repo.add(
        {
            "title": "Permit window stable",
            "description": "Based on municipal quote",
            "source_type": "quote",
            "confidence": 0.9,
        }
    )
    assert added.assumption_id.startswith("asm-")

    listed = repo.list()
    assert len(listed) == 1

    updated = repo.update(added.assumption_id, {"confidence": 0.7})
    assert updated.confidence == 0.7

    assert repo.delete(added.assumption_id) is True
    assert repo.list() == []


def test_assumption_validation(tmp_path: Path) -> None:
    repo = _repo(tmp_path / "store.json")
    with pytest.raises(ValueError):
        repo.add(
            {
                "title": "Bad",
                "description": "bad",
                "source_type": "quote",
                "confidence": 1.5,
            }
        )
    with pytest.raises(ValueError):
        repo.add(
            {
                "title": "Bad type",
                "description": "bad",
                "source_type": "unsupported",
                "confidence": 0.5,
            }
        )
