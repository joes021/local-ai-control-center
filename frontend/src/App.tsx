import { useEffect, useState } from "react";

import { Layout } from "./components/Layout";
import { fetchStatus } from "./lib/api";
import type { StatusPayload } from "./lib/types";
import { HomePage } from "./pages/HomePage";
import { LogsPage } from "./pages/LogsPage";
import { ModelsPage } from "./pages/ModelsPage";
import { RepairPage } from "./pages/RepairPage";
import { SettingsPage } from "./pages/SettingsPage";
import { UpdatesPage } from "./pages/UpdatesPage";

const PAGES = {
  home: "Home",
  models: "Models",
  settings: "Settings",
  logs: "Logs",
  repair: "Repair",
  updates: "Updates",
} as const;

type PageKey = keyof typeof PAGES;

export default function App() {
  const [page, setPage] = useState<PageKey>("home");
  const [status, setStatus] = useState<StatusPayload | null>(null);

  useEffect(() => {
    let active = true;

    fetchStatus()
      .then((payload) => {
        if (active) {
          setStatus(payload);
        }
      })
      .catch(() => {
        if (active) {
          setStatus(null);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const nav = (
    <>
      {Object.entries(PAGES).map(([key, label]) => (
        <button
          className={`nav-button ${page === key ? "nav-button-active" : ""}`}
          key={key}
          onClick={() => setPage(key as PageKey)}
          type="button"
        >
          {label}
        </button>
      ))}
    </>
  );

  return (
    <Layout
      title="Local Qwen Control Center Next"
      eyebrow={status?.hostShellLabel ?? "Local Qwen Desktop GUI Shell"}
      subtitle={`Web UI + lokalni backend pravac za ${status?.hostPlatformLabel ?? "desktop"}.`}
      nav={nav}
    >
      {page === "home" ? <HomePage /> : null}
      {page === "models" ? <ModelsPage /> : null}
      {page === "settings" ? <SettingsPage /> : null}
      {page === "logs" ? <LogsPage /> : null}
      {page === "repair" ? <RepairPage /> : null}
      {page === "updates" ? <UpdatesPage /> : null}
    </Layout>
  );
}
