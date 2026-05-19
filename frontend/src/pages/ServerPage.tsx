import { useEffect, useState } from "react";

import { ActionResultPanel } from "../components/ActionResultPanel";
import { StatusCard } from "../components/StatusCard";
import { fetchServerStatus, openServerWeb, startServer, stopServer } from "../lib/api";
import type { ActionResult, ServerStatusPayload } from "../lib/types";

export function ServerPage() {
  const [serverStatus, setServerStatus] = useState<ServerStatusPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ActionResult | null>(null);

  async function loadStatus() {
    try {
      const payload = await fetchServerStatus();
      setServerStatus(payload);
      setError(null);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Nepoznata greska");
    }
  }

  async function runAction(action: () => Promise<ActionResult>) {
    try {
      const actionResult = await action();
      setResult(actionResult);
      const details = actionResult.details as { url?: string } | undefined;
      if (actionResult.status === "ok" && actionResult.action === "open-server-web" && details?.url) {
        window.open(details.url, "_blank", "noopener,noreferrer");
      }
      await loadStatus();
    } catch (reason: unknown) {
      const message = reason instanceof Error ? reason.message : "Nepoznata greska";
      setError(message);
    }
  }

  useEffect(() => {
    let active = true;
    fetchServerStatus()
      .then((payload) => {
        if (active) {
          setServerStatus(payload);
        }
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "Nepoznata greska");
        }
      });

    const timer = window.setInterval(() => {
      void loadStatus();
    }, 5000);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  return (
    <>
      {error ? <div className="error-panel">{error}</div> : null}
      <section className="status-card wide-card">
        <span className="status-label">llama.cpp server</span>
        <strong className="status-value">{serverStatus?.lastReason || "Ucitavam server status..."}</strong>
        <p className="helper-text">
          Ovo je mesto za kontrolu rada servera. Home prikazuje samo kratak summary.
        </p>
        <div className="inline-actions">
          <button type="button" onClick={() => void runAction(startServer)}>
            Start llama.cpp server
          </button>
          <button type="button" onClick={() => void runAction(stopServer)}>
            Stop llama.cpp server
          </button>
          <button type="button" onClick={() => void runAction(openServerWeb)}>
            Run llama.cpp web
          </button>
        </div>
      </section>

      <StatusCard label="Server status" value={serverStatus?.status ?? "--"} />
      <StatusCard label="Server health" value={serverStatus?.health ?? "--"} />
      <StatusCard label="Server PID" value={serverStatus?.pid ? String(serverStatus.pid) : "nije potvrden"} />
      <StatusCard label="Server port" value={serverStatus ? String(serverStatus.port) : "--"} />

      <section className="status-card wide-card">
        <span className="status-label">Poslednja poruka</span>
        <strong className="status-value">{serverStatus?.lastReason || "Nema lifecycle poruke."}</strong>
        <p className="helper-text">Health URL: {serverStatus?.healthUrl || "--"}</p>
        <p className="helper-text">Lokalni web: {serverStatus?.localWebUrl || "nije dostupan"}</p>
        <p className="helper-text">Tailscale web: {serverStatus?.tailscaleWebUrl || "nije izlozen kroz Tailscale"}</p>
        <p className="helper-text">
          Runtime live signal: {serverStatus?.runtimeLiveStatus || "--"} | {serverStatus?.runtimeLiveReason || "Nema dodatnih detalja."}
        </p>
      </section>

      <ActionResultPanel result={result} />
    </>
  );
}
