from __future__ import annotations

import re
import unicodedata
from datetime import date

from .data_store import DataStore
from .models import ConsistencyResult, RuleResult, TrafficLight

RULE_VERSION = "rules-v1.0.0"
VOLUME_TOLERANCE = 1.05


class ConsistencyEngine:
    def __init__(self, store: DataStore) -> None:
        self.store = store

    def evaluate_gtf(self, gtf_id: str) -> ConsistencyResult:
        gtf = self.store.gtf.get(gtf_id)
        if not gtf:
            return self._result(
                [self._critical("gtf_not_found", "La GTF no existe en el dataset sintetico.")],
                [],
            )

        trozas = self.store.trozas_for_gtf(gtf_id)
        razones: list[RuleResult] = []
        evidencias: list[dict] = [{"tipo": "GTF", "id": gtf_id, "estado": gtf["estado_gtf"]}]
        cod_arboles = {troza["cod_arbol"] for troza in trozas}
        references = {gtf_id, gtf["lote_id"], *cod_arboles}

        if not trozas:
            razones.append(self._critical("gtf_without_logs", "La GTF no tiene trozas asociadas."))
        else:
            razones.append(self._ok("gtf_has_logs", "La GTF referencia trozas identificables."))

        today = date.today()
        vencimiento = date.fromisoformat(gtf["fecha_vencimiento"])
        if gtf["estado_gtf"] != "vigente" or vencimiento < today:
            razones.append(self._critical("gtf_not_active", "La GTF esta vencida, revocada o no vigente."))
        else:
            razones.append(self._ok("gtf_active", "La GTF esta vigente."))

        for troza in trozas:
            censo = self.store.censo.get(troza["cod_arbol"])
            if not censo:
                razones.append(
                    self._critical(
                        "cod_arbol_missing",
                        f"{troza['cod_arbol']} no existe en el censo forestal autorizado.",
                        {"troza_id": troza["troza_id"]},
                    )
                )
                continue

            evidencias.append(
                {
                    "tipo": "COD_ARBOL",
                    "cod_arbol": censo["cod_arbol"],
                    "especie": censo["especie_declarada"],
                    "parcela_corta_id": censo["parcela_corta_id"],
                }
            )
            razones.append(
                self._ok(
                    "cod_arbol_found",
                    f"{troza['cod_arbol']} existe en censo forestal autorizado.",
                    {"troza_id": troza["troza_id"]},
                )
            )

            gtf_species = gtf.get("especie", "")
            species_match = species_key(troza["especie"]) == species_key(censo["especie_declarada"])
            gtf_match = gtf_species == "Mixto" or species_key(troza["especie"]) == species_key(gtf_species)
            if not species_match or not gtf_match:
                razones.append(
                    self._critical(
                        "species_mismatch",
                        f"La especie de {troza['troza_id']} no coincide entre censo, troza y GTF.",
                    )
                )
            else:
                razones.append(self._ok("species_match", "La especie coincide entre censo, troza y GTF."))

            supervision = self.store.supervision.get(troza["cod_arbol"])
            if supervision:
                evidencias.append(
                    {
                        "tipo": "Muestra OSINFOR",
                        "cod_arbol": troza["cod_arbol"],
                        "estado": supervision["estado_supervision"],
                        "desviacion_metros": supervision["desviacion_metros"],
                    }
                )
                if supervision["estado_supervision"] in {"inexistente", "no_conforme"}:
                    razones.append(
                        self._critical(
                            "field_truth_negative",
                            f"La muestra supervisada marca {troza['cod_arbol']} como {supervision['estado_supervision']}.",
                        )
                    )
                elif supervision["desviacion_metros"] > 25:
                    razones.append(
                        self._warning(
                            "gps_moderate_deviation",
                            f"{troza['cod_arbol']} tiene desviacion GPS moderada.",
                            {"desviacion_metros": supervision["desviacion_metros"]},
                        )
                    )
                else:
                    razones.append(self._ok("field_truth_ok", "La muestra OSINFOR es conforme."))
            else:
                razones.append(
                    self._warning(
                        "missing_field_sample",
                        f"{troza['cod_arbol']} no tiene muestra OSINFOR directa.",
                    )
                )

        declared_volume = sum(float(troza["volumen_m3"]) for troza in trozas)
        if declared_volume > float(gtf["volumen_total_m3"]) * VOLUME_TOLERANCE:
            razones.append(self._critical("gtf_volume_exceeded", "El volumen de trozas excede el volumen de la GTF."))
        else:
            razones.append(self._ok("gtf_volume_ok", "El volumen de trozas es consistente con la GTF."))

        for balance in self.store.balance_rows:
            parcela_id = balance["parcela_corta_id"]
            if gtf.get("especie") != "Mixto" and species_key(balance["especie"]) != species_key(gtf.get("especie", "")):
                continue
            if any(
                self.store.censo.get(cod, {}).get("parcela_corta_id") == parcela_id
                and (
                    gtf.get("especie") == "Mixto"
                    or species_key(self.store.censo.get(cod, {}).get("especie_declarada", ""))
                    == species_key(balance["especie"])
                )
                for cod in cod_arboles
            ):
                if float(balance["volumen_movilizado_m3"]) > float(balance["volumen_autorizado_m3"]) * VOLUME_TOLERANCE:
                    razones.append(
                        self._critical(
                            "authorized_volume_exceeded",
                            "El volumen movilizado excede el autorizado para la parcela/especie.",
                        )
                    )
                elif float(balance["volumen_disponible_m3"]) < float(balance["volumen_autorizado_m3"]) * 0.08:
                    razones.append(
                        self._warning(
                            "low_available_balance",
                            "El balance disponible esta cerca del limite autorizado.",
                        )
                    )
                else:
                    razones.append(self._ok("balance_ok", "El balance de extraccion mantiene saldo disponible."))

        active_alerts = self.store.alertas_for_scope(references)
        for alerta in active_alerts:
            evidencias.append(
                {
                    "tipo": "Alerta OSINFOR",
                    "referencia_id": alerta["referencia_id"],
                    "severidad": alerta["severidad"],
                    "descripcion": alerta["descripcion_normalizada"],
                }
            )
            if alerta["severidad"] == "critica":
                razones.append(self._critical("critical_alert", alerta["descripcion_normalizada"]))
            else:
                razones.append(self._warning("minor_alert", alerta["descripcion_normalizada"]))

        if not active_alerts:
            razones.append(self._ok("no_active_alerts", "No existen alertas vigentes para el lote/GTF."))

        return self._result(razones, evidencias)

    def _result(self, razones: list[RuleResult], evidencias: list[dict]) -> ConsistencyResult:
        critical = sum(1 for reason in razones if reason.level == "critical")
        warnings = sum(1 for reason in razones if reason.level == "warning")
        if critical:
            semaforo = TrafficLight.red
            score = max(0, 45 - critical * 15 - warnings * 5)
        elif warnings:
            semaforo = TrafficLight.yellow
            score = max(55, 82 - warnings * 7)
        else:
            semaforo = TrafficLight.green
            score = 96
        return ConsistencyResult(
            semaforo=semaforo,
            score_confianza=score,
            razones=razones,
            evidencias=evidencias,
            version_reglas=RULE_VERSION,
        )

    def _ok(self, code: str, message: str, evidence: dict | None = None) -> RuleResult:
        return RuleResult(code=code, level="ok", message=message, evidence=evidence or {})

    def _warning(self, code: str, message: str, evidence: dict | None = None) -> RuleResult:
        return RuleResult(code=code, level="warning", message=message, evidence=evidence or {})

    def _critical(self, code: str, message: str, evidence: dict | None = None) -> RuleResult:
        return RuleResult(code=code, level="critical", message=message, evidence=evidence or {})


def species_key(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower().replace("|", " ")
    words = re.findall(r"[a-z]+", text)
    ignored = {"sp", "spp", "var", "cf", "aff"}
    useful = [word for word in words if word not in ignored]
    return " ".join(useful[:2]) if useful else ""
