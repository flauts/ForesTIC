import json
from pathlib import Path

from app.data_store import DataStore
from app.rules import ConsistencyEngine


def test_real_dataset_is_available_and_evaluable():
    path = Path("data/real_forest.json")
    assert path.exists()

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert len(raw["censo_forestal"]) >= 7600
    assert len(raw["muestra_supervisada"]) >= 700
    assert len(raw["gtf"]) >= 1000

    store = DataStore(path)
    engine = ConsistencyEngine(store)
    result = engine.evaluate_gtf(raw["gtf"][0]["gtf_id"])

    assert result.score_confianza >= 0
    assert result.version_reglas == "rules-v1.0.0"
    assert result.evidencias
