from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class TrafficLight(str, Enum):
    green = "Verde"
    yellow = "Amarillo"
    red = "Rojo"


class PassportStatus(str, Enum):
    active = "vigente"
    observed = "observado"
    revoked = "revocado"
    expired = "expirado"


class IssuePassportRequest(BaseModel):
    gtf_id: str = Field(..., examples=["GTF-2026-001"])
    lote_id: str | None = Field(default=None, examples=["LOTE-VERDE-001"])


class RevokePassportRequest(BaseModel):
    reason: str = Field(..., min_length=5)
    user: str = Field(default="admin-osinfor")


class EvaluateRequest(BaseModel):
    gtf_id: str | None = None
    cod_arbol: str | None = None


class RuleResult(BaseModel):
    code: str
    level: Literal["ok", "warning", "critical"]
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class ConsistencyResult(BaseModel):
    semaforo: TrafficLight
    score_confianza: int
    razones: list[RuleResult]
    evidencias: list[dict[str, Any]]
    version_reglas: str


class Passport(BaseModel):
    passport_id: str
    gtf_id: str
    lote_id: str
    estado_pasaporte: PassportStatus
    semaforo: TrafficLight
    score_confianza: int
    razones: list[RuleResult]
    evidencias: list[dict[str, Any]]
    hash_integridad: str
    qr_token: str
    qr_token_hash: str
    version_reglas: str
    fecha_emision: str
    fecha_ultima_evaluacion: str


class PublicVerification(BaseModel):
    estado_pasaporte: PassportStatus
    semaforo: TrafficLight
    gtf: dict[str, Any]
    especies: list[str]
    volumen_total_m3: float
    evidencias_resumidas: list[dict[str, Any]]
    razones: list[str]
    hash_integridad: str
    fecha_ultima_evaluacion: str
    disclaimer: str
