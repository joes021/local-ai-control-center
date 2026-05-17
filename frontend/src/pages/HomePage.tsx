import { useEffect, useState } from "react";

import { ActionResultPanel } from "../components/ActionResultPanel";
import { StatusCard } from "../components/StatusCard";
import {
  fetchOpenCodeStatus,
  fetchServerStatus,
  fetchStatus,
  openOpenCode,
  selectRuntime,
} from "../lib/api";
import type {
  ActionResult,
  OpenCodeStatusPayload,
  ServerStatusPayload,
  StatusPayload,
} from "../lib/types";

export function HomePage() {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [serverStatus, setServerStatus] = useState<ServerStatusPayload | null>(null);
  const [opencode, setOpencode] = useState<OpenCodeStatusPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ActionResult | null>(null);

  async function loadStatus() {
    try {
      const [statusPayload, serverPayload, opencodePayload] = await Promise.all([
        fetchStatus(),
        fetchServerStatus(),
        fetchOpenCodeStatus(),
      ]);
      setStatus(statusPayload);
      setServerStatus(serverPayload);
      setOpencode(opencodePayload);
      setError(null);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Nepoznata greska");
    }
  }

  useEffect(() => {
    let active = true;

    Promise.all([fetchStatus(), fetchServerStatus(), fetchOpenCodeStatus()])
      .then(([payload, serverPayload, opencodePayload]) => {
        if (active) {
          setStatus(payload);
          setServerStatus(serverPayload);
          setOpencode(opencodePayload);
        }
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "Nepoznata greska");
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <>
      {error ? <div className="error-panel">{error}</div> : null}
      <StatusCard label="Verzija" value={status?.version ?? "--"} />
      <StatusCard label="Health" value={status?.health ?? "--"} />
      <StatusCard label="Aktivni model" value={status?.activeModel ?? "--"} />
      <StatusCard label="Profil" value={status?.profile ?? "--"} />
      <StatusCard label="Server status" value={serverStatus?.status ?? "--"} />
      <StatusCard label="Server health" value={serverStatus?.health ?? "--"} />
      <StatusCard label="Server port" value={serverStatus ? String(serverStatus.port) : "--"} />
      <StatusCard label="Aktivan runtime" value={status?.activeRuntimeLabel ?? "--"} />
      <StatusCard
        label="Dostupni runtime-i"
        value={status?.availableRuntimes?.length ? status.availableRuntimes.join(", ") : "--"}
      />
      <StatusCard label="TurboQuant status" value={status?.turboQuantStatus ?? "--"} />
      <StatusCard label="Status runtime servera" value={status?.runtimeLiveStatus ?? "--"} />
      <section className="status-card">
        <span className="status-label">OpenCode</span>
        <strong className="status-value">
          {opencode?.available ? "Dostupan" : "Nije dostupan"}
        </strong>
        <p className="helper-text">
          Promena modela vazi za novi OpenCode session. Vec otvoren OpenCode prozor ne menja
          model usred sesije.
        </p>
        <div className="inline-actions">
          <button
            type="button"
            onClick={async () => {
              const actionResult = await openOpenCode(status?.profile || opencode?.profile || "balanced");
              setResult(actionResult);
              await loadStatus();
            }}
          >
            Open OpenCode
          </button>
        </div>
      </section>
      <StatusCard label="Port" value={status ? String(status.uiPort) : "--"} />
      <StatusCard label="Access mode" value={status?.accessMode ?? "--"} />
      <section className="status-card wide-card">
        <span className="status-label">Server summary</span>
        <strong className="status-value">{serverStatus?.lastReason || "Ucitavam server lifecycle status..."}</strong>
        <p className="helper-text">
          Status: {serverStatus?.status || "--"} | Health: {serverStatus?.health || "--"} | Port:{" "}
          {serverStatus ? String(serverStatus.port) : "--"} | Runtime: {serverStatus?.activeRuntimeLabel || "--"}
        </p>
      </section>
      <section className="status-card wide-card">
        <span className="status-label">Runtime summary</span>
        <strong className="status-value">
          {status?.runtimeSummary ?? "Ucitavam runtime status..."}
        </strong>
      </section>
      <section className="status-card wide-card">
        <span className="status-label">Binar u upotrebi</span>
        <strong className="status-value">
          {status?.activeRuntimeBinary || "Nije potvrđeno."}
        </strong>
        <p className="helper-text">
          Izvor potvrde: {status?.activeRuntimeBinarySource || "nema potvrde"}
        </p>
        <p className="helper-text">
          Runtime health: {status?.runtimeLiveReason || "Nema dodatnih detalja."}
        </p>
      </section>
      <section className="status-card wide-card">
        <span className="status-label">TurboQuant detalji</span>
        <strong className="status-value">
          {status?.turboQuantReason ?? "Ucitavam TurboQuant stanje..."}
        </strong>
        <div className="inline-actions">
          <button
            type="button"
            onClick={async () => {
              const actionResult = await selectRuntime("llama.cpp");
              setResult(actionResult);
              await loadStatus();
            }}
          >
            Koristi llama.cpp
          </button>
          <button
            type="button"
            onClick={async () => {
              const actionResult = await selectRuntime("turboquant");
              setResult(actionResult);
              await loadStatus();
            }}
          >
            Koristi TurboQuant
          </button>
        </div>
      </section>
      <section className="status-card wide-card">
        <span className="status-label">Local URL</span>
        <strong className="status-value">
          {status ? status.localUrl : "Ucitavam lokalni backend status..."}
        </strong>
      </section>
      <section className="status-card wide-card">
        <span className="status-label">Tailscale URL</span>
        <strong className="status-value">
          {status?.tailscaleUrl || "Tailscale nije aktivan ili UI nije izlozen kroz Tailscale."}
        </strong>
      </section>
      <section className="status-card wide-card">
        <span className="status-label">OpenCode</span>
        <strong className="status-value">
          {opencode?.available ? "Dostupan" : "Nije dostupan"}
        </strong>
        <p className="helper-text">
          OpenCode config: {opencode?.configPath || "nije pronadjen"}
        </p>
        <p className="helper-text">
          Security mode: {opencode?.securityMode || "--"} | Capability mode:{" "}
          {opencode?.capabilityMode || "--"}
        </p>
        <p className="helper-text">
          Audit: {opencode?.auditSummary || "Nema dodatnih OpenCode detalja."}
        </p>
        <p className="helper-text">
          Ako promenis aktivni model u Control Center-u, zatvori i otvori OpenCode ponovo da bi
          novi session preuzeo taj model.
        </p>
      </section>
      <ActionResultPanel result={result} />
    </>
  );
}
