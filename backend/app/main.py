from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .audit import AuditLog
from .data_store import DataStore
from .models import EvaluateRequest, IssuePassportRequest, RevokePassportRequest
from .passports import PassportService
from .rules import ConsistencyEngine

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = (
    BASE_DIR / "data" / "real_forest.json"
    if (BASE_DIR / "data" / "real_forest.json").exists()
    else BASE_DIR / "data" / "synthetic_forest.json"
)
DATA_PATH = Path(os.getenv("FORESTIC_DATA_PATH", DEFAULT_DATA_PATH))
SECRET = os.getenv("FORESTIC_QR_SECRET", "dev-secret-change-me")

store = DataStore(DATA_PATH)
engine = ConsistencyEngine(store)
audit = AuditLog()
passports = PassportService(store, engine, audit, SECRET)
passports.bootstrap_demo_passports()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not passports.passports:
        passports.bootstrap_demo_passports()
    yield


app = FastAPI(
    title="Pasaporte Digital de Madera Legal OSINFOR",
    version="0.1.0",
    description="Prototipo interoperable con datos sinteticos, motor deterministico y QR firmado.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "dataset": DATA_PATH.name}


@app.get("/v1/passports")
def list_passports() -> list:
    return list(passports.passports.values())


@app.get("/v1/passports/summary")
def list_passport_summaries() -> list[dict]:
    return [
        {
            "passport_id": passport.passport_id,
            "gtf_id": passport.gtf_id,
            "lote_id": passport.lote_id,
            "estado_pasaporte": passport.estado_pasaporte,
            "semaforo": passport.semaforo,
            "score_confianza": passport.score_confianza,
            "fecha_ultima_evaluacion": passport.fecha_ultima_evaluacion,
        }
        for passport in passports.passports.values()
    ]


@app.get("/v1/passports/{passport_id}")
def get_passport(passport_id: str):
    passport = passports.passports.get(passport_id)
    if not passport:
        raise HTTPException(status_code=404, detail="Pasaporte no encontrado.")
    return passport


@app.post("/v1/passports/issue")
def issue_passport(request: IssuePassportRequest):
    if request.gtf_id not in store.gtf:
        raise HTTPException(status_code=404, detail="GTF no encontrada.")
    return passports.issue(request.gtf_id, request.lote_id)


@app.post("/v1/passports/{passport_id}/revoke")
def revoke_passport(passport_id: str, request: RevokePassportRequest):
    passport = passports.revoke(passport_id, request.reason, request.user)
    if not passport:
        raise HTTPException(status_code=404, detail="Pasaporte no encontrado.")
    return passport


@app.get("/verify/{qr_token}")
def verify(qr_token: str):
    verification = passports.verify_public(qr_token)
    if not verification:
        raise HTTPException(status_code=400, detail="QR invalido o integridad no verificable.")
    return verification


@app.post("/v1/consistency/evaluate")
def evaluate(request: EvaluateRequest):
    if not request.gtf_id:
        raise HTTPException(status_code=400, detail="La v1 del prototipo evalua por gtf_id.")
    return engine.evaluate_gtf(request.gtf_id)


@app.get("/v1/gtf/{gtf_id}/trust")
def gtf_trust(gtf_id: str):
    passport = passports.passports.get(f"PASS-{gtf_id}") or passports.issue(gtf_id)
    return {
        "gtf_id": gtf_id,
        "estado_gtf": store.gtf.get(gtf_id, {}).get("estado_gtf", "no_encontrada"),
        "estado_pasaporte": passport.estado_pasaporte,
        "semaforo": passport.semaforo,
        "score_confianza": passport.score_confianza,
        "alertas": [reason.message for reason in passport.razones if reason.level == "critical"],
        "passport_id": passport.passport_id,
    }


@app.get("/v1/audit")
def audit_log() -> list:
    return audit.events
