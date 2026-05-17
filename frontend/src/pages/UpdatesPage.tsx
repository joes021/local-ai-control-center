import { useEffect, useState } from "react";

import { ActionResultPanel } from "../components/ActionResultPanel";
import { checkUpdates, installUpdate } from "../lib/api";
import type { ActionResult } from "../lib/types";

export function UpdatesPage() {
  const [result, setResult] = useState<ActionResult | null>(null);

  useEffect(() => {
    checkUpdates().then(setResult).catch(() => {});
  }, []);

  return (
    <>
      <section className="status-card wide-card">
        <span className="status-label">Updates</span>
        <div className="inline-actions">
          <button type="button" onClick={() => checkUpdates().then(setResult)}>
            Check updates
          </button>
          <button type="button" onClick={() => installUpdate().then(setResult)}>
            Install update
          </button>
        </div>
      </section>
      <ActionResultPanel result={result} />
    </>
  );
}
