from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DataStore:
    def __init__(self, data_path: Path) -> None:
        self.data_path = data_path
        self.raw = self._load()
        self.censo = {row["cod_arbol"]: row for row in self.raw["censo_forestal"]}
        self.supervision = {
            row["cod_arbol"]: row for row in self.raw["muestra_supervisada"]
        }
        self.trozas = {row["troza_id"]: row for row in self.raw["trozas"]}
        self.gtf = {row["gtf_id"]: row for row in self.raw["gtf"]}
        self.balance_rows = self.raw["balance_extraccion"]
        self.balance = {
            (row["parcela_corta_id"], row["especie"]): row
            for row in self.balance_rows
        }
        self.alertas = self.raw["alertas"]

    def _load(self) -> dict[str, Any]:
        with self.data_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def trozas_for_gtf(self, gtf_id: str) -> list[dict[str, Any]]:
        gtf = self.gtf.get(gtf_id)
        if not gtf:
            return []
        ids = set(gtf["trozas"])
        return [troza for troza in self.trozas.values() if troza["troza_id"] in ids]

    def alertas_for_scope(self, references: set[str]) -> list[dict[str, Any]]:
        return [
            alerta
            for alerta in self.alertas
            if alerta["estado_alerta"] == "vigente"
            and str(alerta["referencia_id"]) in references
        ]
