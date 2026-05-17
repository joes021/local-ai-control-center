import { useState } from "react";

import { ActionResultPanel } from "../components/ActionResultPanel";
import { runRepair } from "../lib/api";
import type { ActionResult } from "../lib/types";

export function RepairPage() {
  const [result, setResult] = useState<ActionResult | null>(null);

  return (
    <>
      <section className="status-card wide-card">
        <span className="status-label">Repair akcije</span>
        <div className="inline-actions">
          <button type="button" onClick={() => runRepair("install").then(setResult)}>
            Repair install
          </button>
          <button type="button" onClick={() => runRepair("model").then(setResult)}>
            Repair model
          </button>
          <button type="button" onClick={() => runRepair("runtime").then(setResult)}>
            Repair runtime
          </button>
          <button type="button" onClick={() => runRepair("config").then(setResult)}>
            Repair config
          </button>
        </div>
      </section>
      <ActionResultPanel result={result} />
    </>
  );
}
