import { useEffect, useState } from "react";

import { ActionResultPanel } from "../components/ActionResultPanel";
import { StatusCard } from "../components/StatusCard";
import { fetchStatus, selectRuntime } from "../lib/api";
import type { ActionResult, StatusPayload } from "../lib/types";

export function HomePage() {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ActionResult | null>(null);

  async function loadStatus() {
    try {
      const payload = await fetchStatus();
      setStatus(payload);
      setError(null);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Nepoznata greska");
    }
  }

  useEffect(() => {
    let active = true;

    fetchStatus()
      .then((payload) => {
        if (active) {
          setStatus(payload);
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
      <StatusCard label="Aktivan runtime" value={status?.activeRuntimeLabel ?? "--"} />
      <StatusCard
        label="Dostupni runtime-i"
        value={status?.availableRuntimes?.length ? status.availableRuntimes.join(", ") : "--"}
      />
      <StatusCard label="TurboQuant status" value={status?.turboQuantStatus ?? "--"} />
      <StatusCard label="Status runtime servera" value={status?.runtimeLiveStatus ?? "--"} />
      <StatusCard label="Port" value={status ? String(status.uiPort) : "--"} />
      <StatusCard label="Access mode" value={status?.accessMode ?? "--"} />
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
      <ActionResultPanel result={result} />
    </>
  );
}
