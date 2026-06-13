from __future__ import annotations

from datetime import UTC, datetime

from .audit import AuditLog
from .data_store import DataStore
from .models import Passport, PassportStatus, PublicVerification
from .rules import ConsistencyEngine
from .security import sha256_json, sign_token, token_hash, verify_token


class PassportService:
    def __init__(self, store: DataStore, engine: ConsistencyEngine, audit: AuditLog, secret: str) -> None:
        self.store = store
        self.engine = engine
        self.audit = audit
        self.secret = secret
        self.passports: dict[str, Passport] = {}
        self.token_index: dict[str, str] = {}

    def bootstrap_demo_passports(self) -> None:
        for gtf_id in self.store.gtf:
            self.issue(gtf_id, self.store.gtf[gtf_id]["lote_id"])

    def issue(self, gtf_id: str, lote_id: str | None = None) -> Passport:
        result = self.engine.evaluate_gtf(gtf_id)
        gtf = self.store.gtf.get(gtf_id, {})
        resolved_lote = lote_id or gtf.get("lote_id", "SIN-LOTE")
        now = datetime.now(UTC).isoformat()
        passport_id = f"PASS-{gtf_id}"
        integrity_payload = {
            "passport_id": passport_id,
            "gtf_id": gtf_id,
            "lote_id": resolved_lote,
            "semaforo": result.semaforo,
            "score_confianza": result.score_confianza,
            "razones": [reason.model_dump() for reason in result.razones],
            "evidencias": result.evidencias,
            "version_reglas": result.version_reglas,
        }
        hash_integridad = sha256_json(integrity_payload)
        qr_token = sign_token(
            {
                "passport_id": passport_id,
                "gtf_id": gtf_id,
                "hash_integridad": hash_integridad,
                "iat": now,
            },
            self.secret,
        )
        passport = Passport(
            passport_id=passport_id,
            gtf_id=gtf_id,
            lote_id=resolved_lote,
            estado_pasaporte=PassportStatus.active,
            semaforo=result.semaforo,
            score_confianza=result.score_confianza,
            razones=result.razones,
            evidencias=result.evidencias,
            hash_integridad=hash_integridad,
            qr_token=qr_token,
            qr_token_hash=token_hash(qr_token),
            version_reglas=result.version_reglas,
            fecha_emision=now,
            fecha_ultima_evaluacion=now,
        )
        self.passports[passport_id] = passport
        self.token_index[passport.qr_token_hash] = passport_id
        self.audit.append(
            "passport.issue",
            {
                "passport_id": passport_id,
                "gtf_id": gtf_id,
                "semaforo": passport.semaforo,
                "hash_integridad": passport.hash_integridad,
            },
        )
        return passport

    def revoke(self, passport_id: str, reason: str, user: str) -> Passport | None:
        passport = self.passports.get(passport_id)
        if not passport:
            return None
        updated = passport.model_copy(update={"estado_pasaporte": PassportStatus.revoked})
        self.passports[passport_id] = updated
        self.audit.append("passport.revoke", {"passport_id": passport_id, "reason": reason, "user": user})
        return updated

    def verify_public(self, qr_token: str) -> PublicVerification | None:
        payload = verify_token(qr_token, self.secret)
        if not payload:
            self.audit.append("passport.verify.invalid_token", {"token_hash": token_hash(qr_token)})
            return None
        passport_id = payload.get("passport_id")
        passport = self.passports.get(passport_id)
        if not passport or payload.get("hash_integridad") != passport.hash_integridad:
            self.audit.append("passport.verify.integrity_failed", {"passport_id": passport_id})
            return None
        gtf = self.store.gtf[passport.gtf_id]
        trozas = self.store.trozas_for_gtf(passport.gtf_id)
        especies = sorted({troza["especie"] for troza in trozas} or {gtf["especie"]})
        self.audit.append("passport.verify.public", {"passport_id": passport_id, "semaforo": passport.semaforo})
        return PublicVerification(
            estado_pasaporte=passport.estado_pasaporte,
            semaforo=passport.semaforo,
            gtf={
                "gtf_id": gtf["gtf_id"],
                "numero_gtf": gtf["numero_gtf"],
                "origen": gtf["origen"],
                "destino": gtf["destino"],
                "fecha_emision": gtf["fecha_emision"],
                "fecha_vencimiento": gtf["fecha_vencimiento"],
            },
            especies=especies,
            volumen_total_m3=gtf["volumen_total_m3"],
            evidencias_resumidas=passport.evidencias,
            razones=[
                reason.message
                for reason in passport.razones
                if reason.level in {"warning", "critical"}
            ]
            or ["Evidencia consistente sin contradicciones."],
            hash_integridad=passport.hash_integridad,
            fecha_ultima_evaluacion=passport.fecha_ultima_evaluacion,
            disclaimer="Prototipo con datos sinteticos. No reemplaza SIGO SFC, SNIFFS, LOE ni GTF oficiales.",
        )
