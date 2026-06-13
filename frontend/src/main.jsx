import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertTriangle,
  BadgeCheck,
  ClipboardCheck,
  Download,
  FileClock,
  Gauge,
  KeyRound,
  QrCode,
  RefreshCcw,
  Search,
  ShieldCheck,
  Truck,
} from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const roleTabs = [
  { id: "productor", label: "Productor", icon: QrCode },
  { id: "control", label: "Control", icon: ShieldCheck },
  { id: "comprador", label: "Comprador", icon: BadgeCheck },
  { id: "admin", label: "Admin", icon: KeyRound },
];

const toneByLight = {
  Verde: { className: "green", label: "Confiable", icon: BadgeCheck },
  Amarillo: { className: "yellow", label: "Requiere revision", icon: AlertTriangle },
  Rojo: { className: "red", label: "Bloqueo o alto riesgo", icon: AlertTriangle },
};

function App() {
  const [passports, setPassports] = useState([]);
  const [audit, setAudit] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [selectedDetail, setSelectedDetail] = useState(null);
  const [activeRole, setActiveRole] = useState("productor");
  const [verificationToken, setVerificationToken] = useState("");
  const [verification, setVerification] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const selected = useMemo(
    () => selectedDetail ?? passports.find((passport) => passport.passport_id === selectedId) ?? passports[0],
    [passports, selectedDetail, selectedId],
  );

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    if (selectedId) {
      loadPassport(selectedId);
    }
  }, [selectedId]);

  useEffect(() => {
    if (selectedDetail?.qr_token) {
      setVerificationToken(selectedDetail.qr_token);
    }
  }, [selectedDetail]);

  async function api(path, options) {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail ?? "No se pudo completar la accion.");
    }
    return response.json();
  }

  async function refresh() {
    setError("");
    setLoading(true);
    try {
      const [passportData, auditData] = await Promise.all([api("/v1/passports/summary"), api("/v1/audit")]);
      setPassports(passportData);
      setAudit(auditData);
      if (!selectedId && passportData[0]) {
        setSelectedId(passportData[0].passport_id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadPassport(passportId) {
    setError("");
    try {
      const passport = await api(`/v1/passports/${passportId}`);
      setSelectedDetail(passport);
    } catch (err) {
      setError(err.message);
    }
  }

  async function verifyToken(token = verificationToken) {
    setError("");
    setLoading(true);
    try {
      const payload = await api(`/verify/${encodeURIComponent(token)}`);
      setVerification(payload);
    } catch (err) {
      setVerification(null);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function issue(gtfId) {
    setError("");
    setLoading(true);
    try {
      const passport = await api("/v1/passports/issue", {
        method: "POST",
        body: JSON.stringify({ gtf_id: gtfId }),
      });
      await refresh();
      setSelectedId(passport.passport_id);
      setSelectedDetail(passport);
      setVerificationToken(passport.qr_token);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }

  async function revoke() {
    if (!selected) return;
    setError("");
    setLoading(true);
    try {
      const updated = await api(`/v1/passports/${selected.passport_id}/revoke`, {
        method: "POST",
        body: JSON.stringify({
          reason: "Revocacion demo por nueva evidencia institucional",
          user: "admin-osinfor-demo",
        }),
      });
      await refresh();
      setSelectedDetail(updated);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">OSINFOR · Archivos reales integrados</p>
          <h1>Pasaporte Digital de Madera Legal</h1>
        </div>
        <button className="icon-button" onClick={refresh} disabled={loading} title="Actualizar datos">
          <RefreshCcw size={20} />
        </button>
      </header>

      {error && (
        <div className="alert" role="alert">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      <section className="workspace">
        <aside className="passport-list" aria-label="Pasaportes emitidos">
          <div className="section-title">
            <Truck size={18} />
            <h2>Despachos</h2>
          </div>
          <div className="list-stack">
            {passports.map((passport) => (
              <PassportRow
                key={passport.passport_id}
                passport={passport}
                selected={selected?.passport_id === passport.passport_id}
                onSelect={() => {
                  setSelectedId(passport.passport_id);
                  setVerification(null);
                }}
              />
            ))}
          </div>
        </aside>

        <section className="main-panel">
          {selected && <PassportSummary passport={selected} onVerify={() => verifyToken(selectedDetail?.qr_token ?? verificationToken)} />}

          <div className="tabs" role="tablist" aria-label="Vistas por rol">
            {roleTabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  className={activeRole === tab.id ? "active" : ""}
                  onClick={() => setActiveRole(tab.id)}
                  role="tab"
                  aria-selected={activeRole === tab.id}
                >
                  <Icon size={18} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {activeRole === "productor" && selectedDetail && (
            <ProducerView passport={selected} onIssue={issue} token={verificationToken} setToken={setVerificationToken} />
          )}
          {activeRole === "control" && (
            <ControlView
              token={verificationToken}
              setToken={setVerificationToken}
              verification={verification}
              onVerify={() => verifyToken()}
            />
          )}
          {activeRole === "comprador" && <BuyerView verification={verification} selected={selected} onVerify={() => verifyToken()} />}
          {activeRole === "admin" && selectedDetail && <AdminView passport={selectedDetail} audit={audit} onRevoke={revoke} />}
        </section>
      </section>
    </main>
  );
}

function PassportRow({ passport, selected, onSelect }) {
  const tone = toneByLight[passport.semaforo];
  const Icon = tone.icon;
  return (
    <button className={`passport-row ${selected ? "selected" : ""}`} onClick={onSelect}>
      <span className={`status-dot ${tone.className}`} aria-hidden="true" />
      <span>
        <strong>{passport.gtf_id}</strong>
        <small>{passport.lote_id}</small>
      </span>
      <span className={`pill ${tone.className}`}>
        <Icon size={14} />
        {passport.semaforo}
      </span>
    </button>
  );
}

function PassportSummary({ passport, onVerify }) {
  const tone = toneByLight[passport.semaforo];
  const Icon = tone.icon;
  const importantReasons = (passport.razones ?? []).filter((reason) => reason.level !== "ok").slice(0, 3);
  return (
    <section className={`summary-band ${tone.className}`}>
      <div>
        <p className="eyebrow">Pasaporte {passport.estado_pasaporte}</p>
        <h2>{passport.passport_id}</h2>
        <p>{tone.label} · score {passport.score_confianza}/100 · reglas {passport.version_reglas}</p>
      </div>
      <div className="summary-actions">
        <span className={`signal ${tone.className}`}>
          <Icon size={22} />
          {passport.semaforo}
        </span>
        <button onClick={onVerify}>
          <Search size={18} />
          Verificar
        </button>
      </div>
      <ul className="reason-strip">
        {(importantReasons.length ? importantReasons : [{ message: "Evidencia consistente sin contradicciones." }]).map(
          (reason) => (
            <li key={reason.message}>{reason.message}</li>
          ),
        )}
      </ul>
    </section>
  );
}

function ProducerView({ passport, onIssue, token, setToken }) {
  return (
    <section className="role-grid">
      <div className="tool-surface">
        <div className="section-title">
          <QrCode size={18} />
          <h2>QR de despacho</h2>
        </div>
        <div className="qr-box">
          <QrCode size={96} strokeWidth={1.4} />
          <span>{passport.gtf_id}</span>
        </div>
        <label>
          Token firmado
          <textarea value={token} onChange={(event) => setToken(event.target.value)} rows={5} />
        </label>
      </div>
      <div className="tool-surface">
        <div className="section-title">
          <Download size={18} />
          <h2>Emision demo</h2>
        </div>
        <div className="button-grid">
          <button onClick={() => onIssue("GTF-2026-001")}>Emitir Verde</button>
          <button onClick={() => onIssue("GTF-2026-002")}>Emitir Amarillo</button>
          <button onClick={() => onIssue("GTF-2026-003")}>Emitir Rojo</button>
        </div>
        <Metric label="GTF" value={passport.gtf_id} />
        <Metric label="Hash" value={passport.hash_integridad.slice(0, 18)} />
      </div>
    </section>
  );
}

function ControlView({ token, setToken, verification, onVerify }) {
  return (
    <section className="role-grid">
      <div className="tool-surface wide">
        <div className="section-title">
          <ClipboardCheck size={18} />
          <h2>Verificacion en ruta</h2>
        </div>
        <label>
          Token escaneado
          <textarea value={token} onChange={(event) => setToken(event.target.value)} rows={4} />
        </label>
        <button onClick={onVerify}>
          <Search size={18} />
          Validar QR
        </button>
      </div>
      {verification && <VerificationResult verification={verification} />}
    </section>
  );
}

function BuyerView({ verification, selected, onVerify }) {
  return (
    <section className="role-grid">
      <div className="tool-surface">
        <div className="section-title">
          <BadgeCheck size={18} />
          <h2>Constancia publica</h2>
        </div>
        <p className="body-copy">
          Vista minimizada para comprador: estado, especie, volumen, origen general, hash y fecha de ultima evaluacion.
        </p>
        <button onClick={onVerify}>
          <ShieldCheck size={18} />
          Abrir constancia
        </button>
        {selected && <Metric label="Pasaporte seleccionado" value={selected.passport_id} />}
      </div>
      {verification && <VerificationResult verification={verification} compact />}
    </section>
  );
}

function AdminView({ passport, audit, onRevoke }) {
  return (
    <section className="role-grid">
      <div className="tool-surface">
        <div className="section-title">
          <Gauge size={18} />
          <h2>Reglas activadas</h2>
        </div>
        <div className="rule-list">
          {passport.razones.map((reason) => (
            <div className={`rule-item ${reason.level}`} key={`${reason.code}-${reason.message}`}>
              <strong>{reason.code}</strong>
              <span>{reason.message}</span>
            </div>
          ))}
        </div>
        <button className="danger" onClick={onRevoke}>
          <AlertTriangle size={18} />
          Revocar pasaporte
        </button>
      </div>
      <div className="tool-surface">
        <div className="section-title">
          <FileClock size={18} />
          <h2>Auditoria</h2>
        </div>
        <div className="audit-list">
          {audit.slice(-8).reverse().map((event) => (
            <div key={event.event_id}>
              <strong>{event.event_type}</strong>
              <small>{event.event_hash.slice(0, 20)}</small>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function VerificationResult({ verification, compact = false }) {
  const tone = toneByLight[verification.semaforo];
  const Icon = tone.icon;
  return (
    <div className={`verification ${tone.className}`}>
      <div className="verification-head">
        <span className={`signal ${tone.className}`}>
          <Icon size={20} />
          {verification.semaforo}
        </span>
        <strong>{verification.gtf.numero_gtf}</strong>
      </div>
      <div className="metric-grid">
        <Metric label="Estado" value={verification.estado_pasaporte} />
        <Metric label="Volumen" value={`${verification.volumen_total_m3} m3`} />
        <Metric label="Especies" value={verification.especies.join(", ")} />
        <Metric label="Destino" value={verification.gtf.destino} />
      </div>
      {!compact && (
        <ul className="reason-strip inline">
          {verification.razones.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      )}
      <small className="hash-line">Hash {verification.hash_integridad}</small>
      <p className="disclaimer">{verification.disclaimer}</p>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
