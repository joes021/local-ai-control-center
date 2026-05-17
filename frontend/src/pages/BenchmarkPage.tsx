import { useEffect, useMemo, useState } from "react";

import {
  fetchBenchmark,
  loadBenchmarkBattery,
  restoreDefaultBenchmarkTests,
  runBatteryBenchmark,
  runSelectedBenchmark,
  saveBenchmarkBattery,
} from "../lib/api";
import { CustomSelect } from "../components/CustomSelect";
import type { BenchmarkPayload, BenchmarkScenario } from "../lib/types";

function buildPolylinePoints(values: number[], width: number, height: number, maxValue: number) {
  if (!values.length) {
    return "";
  }
  return values
    .map((value, index) => {
      const x = values.length === 1 ? width / 2 : (index / (values.length - 1)) * width;
      const y = height - (value / Math.max(maxValue, 1)) * height;
      return `${x},${y}`;
    })
    .join(" ");
}

function offsetPoints(points: string, offsetX: number, offsetY: number) {
  if (!points) {
    return "";
  }
  return points
    .split(" ")
    .map((point) => {
      const [x, y] = point.split(",");
      return `${Number(x) + offsetX},${Number(y) + offsetY}`;
    })
    .join(" ");
}

export function BenchmarkPage({ onOpenLogs }: { onOpenLogs: () => void }) {
  const [benchmark, setBenchmark] = useState<BenchmarkPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedScenarioId, setSelectedScenarioId] = useState("");
  const [batteryName, setBatteryName] = useState("");
  const [scenariosDraft, setScenariosDraft] = useState<BenchmarkScenario[]>([]);
  const [actionMessage, setActionMessage] = useState("");

  async function load() {
    try {
      const payload = await fetchBenchmark();
      setBenchmark(payload);
      setError(null);
      setActionMessage("");
      if (!selectedScenarioId && payload.selectedBattery?.scenarios?.length) {
        setSelectedScenarioId(payload.selectedBattery.scenarios[0].id);
      }
      setBatteryName(payload.selectedBattery?.name ?? "");
      setScenariosDraft(payload.selectedBattery?.scenarios ?? []);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Nepoznata greska");
    }
  }

  useEffect(() => {
    let active = true;
    async function tick() {
      if (!active) {
        return;
      }
      await load();
    }
    void tick();
    const timer = window.setInterval(() => {
      void tick();
    }, 5000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  const selectedBattery = benchmark?.selectedBattery ?? {
    id: "default",
    name: "Default battery",
    source: "default",
    scenarios: [],
  };
  const activeRun = benchmark?.activeRun;

  const promptSeries = useMemo(
    () => (benchmark?.history ?? []).map((item) => Number(item.promptTokensPerSecond || 0)),
    [benchmark],
  );
  const outputSeries = useMemo(
    () => (benchmark?.history ?? []).map((item) => Number(item.completionTokensPerSecond || 0)),
    [benchmark],
  );
  const totalSeries = useMemo(
    () => (benchmark?.history ?? []).map((item) => Number(item.totalTokensPerSecond || 0)),
    [benchmark],
  );
  const chartLabels = useMemo(
    () => (benchmark?.history ?? []).map((item) => item.chartLabel || "--:--:--"),
    [benchmark],
  );

  if (error) {
    return <div className="error-panel">{error}</div>;
  }

  if (!benchmark) {
    return <section className="status-card wide-card">Ucitavam benchmark...</section>;
  }

  const scenarioOptions = selectedBattery.scenarios.map((scenario) => ({
    value: scenario.id,
    label: scenario.name,
  }));
  const batteryOptions = benchmark.batteries.map((battery) => ({
    value: battery.id,
    label: battery.name,
  }));

  const maxValue = Math.max(...promptSeries, ...outputSeries, ...totalSeries, 1);
  const chartHeight = 180;
  const chartWidth = 640;
  const yAxisLabels = [maxValue, maxValue * 0.66, maxValue * 0.33, 0].map((value) =>
    `${Math.round(value)} tok/s`,
  );

  async function handleRunSelected() {
    const result = await runSelectedBenchmark(selectedScenarioId);
    setActionMessage(result.summary);
    await load();
  }

  async function handleRunBattery() {
    const result = await runBatteryBenchmark(selectedBattery.id);
    setActionMessage(result.summary);
    await load();
  }

  async function handleSaveBattery() {
    const result = await saveBenchmarkBattery(batteryName, scenariosDraft);
    setActionMessage(result.summary);
    await load();
  }

  async function handleLoadBattery(batteryId: string) {
    const result = await loadBenchmarkBattery(batteryId);
    setActionMessage(result.summary);
    await load();
  }

  async function handleRestoreDefaults() {
    const result = await restoreDefaultBenchmarkTests();
    setActionMessage(result.summary);
    await load();
  }

  function updateScenario(index: number, patch: Partial<BenchmarkScenario>) {
    setScenariosDraft((current) =>
      current.map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item)),
    );
  }

  return (
    <>
      <section className="status-card wide-card">
        <span className="status-label">Benchmark controls</span>
        <div className="inline-actions" style={{ flexWrap: "wrap", gap: "12px" }}>
          <CustomSelect
            value={selectedScenarioId}
            options={scenarioOptions}
            onChange={setSelectedScenarioId}
            ariaLabel="Izaberi benchmark scenario"
          />
          <button type="button" onClick={handleRunSelected}>
            Run selected test
          </button>
          <button type="button" onClick={handleRunBattery}>
            Run full battery
          </button>
          <button type="button" onClick={handleSaveBattery}>
            Save battery
          </button>
          <span className="helper-text">Load battery</span>
          <CustomSelect
            value={selectedBattery.id}
            options={batteryOptions}
            onChange={(batteryId) => void handleLoadBattery(batteryId)}
            ariaLabel="Ucitaj benchmark bateriju"
          />
          <button type="button" onClick={handleRestoreDefaults}>
            Restore default tests
          </button>
        </div>
        <p className="helper-text">
          {actionMessage || "Benchmark testovi mogu da se pokrenu pojedinacno ili kao cela baterija."}
        </p>
      </section>

      <section className="status-card wide-card">
        <span className="status-label">Battery editor</span>
        <div className="battery-editor-shell">
          <div className="battery-editor-topline">
            <input value={batteryName} onChange={(event) => setBatteryName(event.target.value)} placeholder="Ime baterije" />
            <div className="helper-text">Aktivna baterija: {selectedBattery.name}</div>
          </div>
          <div className="battery-scenario-list">
            {scenariosDraft.map((scenario, index) => {
              const isSelected = scenario.id === selectedScenarioId;
              return (
                <button
                  type="button"
                  key={scenario.id}
                  className={`battery-scenario-row${isSelected ? " battery-scenario-row-active" : ""}`}
                  onClick={() => setSelectedScenarioId(scenario.id)}
                >
                  <span className="battery-scenario-name">{scenario.name}</span>
                  <span className="battery-scenario-preview">{scenario.prompt}</span>
                </button>
              );
            })}
          </div>
          {(() => {
            const activeScenarioIndex = scenariosDraft.findIndex((item) => item.id === selectedScenarioId);
            const activeScenario = activeScenarioIndex >= 0 ? scenariosDraft[activeScenarioIndex] : scenariosDraft[0];
            if (!activeScenario) {
              return null;
            }
            const scenarioIndex = activeScenarioIndex >= 0 ? activeScenarioIndex : 0;
            return (
              <div className="battery-editor-detail">
                <div className="battery-editor-detail-header">
                  <strong>{activeScenario.name}</strong>
                  <span className="helper-text">Uredujes jedan scenario, lista gore ostaje kompaktna.</span>
                </div>
                <div className="battery-editor-detail-grid">
                  <input
                    value={activeScenario.name}
                    onChange={(event) => updateScenario(scenarioIndex, { name: event.target.value })}
                    placeholder="Naziv scenarija"
                  />
                  <textarea
                    value={activeScenario.prompt}
                    onChange={(event) => updateScenario(scenarioIndex, { prompt: event.target.value })}
                    placeholder="Prompt scenarija"
                    rows={4}
                  />
                </div>
              </div>
            );
          })()}
        </div>
      </section>

      <section className="status-card wide-card">
        <span className="status-label">Benchmark run</span>
        <div className="benchmark-run-summary">
          <div className="benchmark-run-main">
            <strong className="status-value">
              {activeRun?.mode === "battery"
                ? `${activeRun.currentIndex}/${activeRun.totalScenarios} | ${activeRun.currentScenarioName || "ceka"}`
                : activeRun?.scenarioName || "nema aktivnog testa"}
            </strong>
            <span className={`scenario-status-badge scenario-status-${activeRun?.status || "idle"}`}>
              {activeRun?.status || "idle"}
            </span>
          </div>
          <div className="benchmark-run-meta">
            <span>{activeRun?.percent ?? 0}%</span>
            <span>{activeRun?.message || "Benchmark nije pokrenut."}</span>
          </div>
        </div>
        <div className="benchmark-run-status-list">
          {(activeRun?.scenarioStatuses ?? []).map((item) => (
            <article className="benchmark-run-status-row" key={item.scenarioId}>
              <strong>{item.scenarioName}</strong>
              <span className={`scenario-status-badge scenario-status-${item.status}`}>{item.status}</span>
              <div className="muted-line">{item.summary}</div>
            </article>
          ))}
        </div>
        <div style={{ display: "none" }}>queued running done failed</div>
      </section>

      <section className="status-card wide-card">
        <span className="status-label">LIVE THROUGHPUT</span>
        <strong className="status-value">
          {benchmark.current ? `${benchmark.current.totalTokensPerSecond ?? 0} tok/s` : "jos nema merenja"}
        </strong>
        <p className="helper-text">
          Signal: {benchmark.activity.throughputTrend.signal} {benchmark.activity.throughputTrend.label} | latency{" "}
          {benchmark.activity.latencyTrend.signal} {benchmark.activity.latencyTrend.label}
        </p>
      </section>

      <section className="status-card">
        <span className="status-label">Input tok/s</span>
        <strong className="status-value">{benchmark.averages.promptTokensPerSecond}</strong>
      </section>
      <section className="status-card">
        <span className="status-label">Output tok/s</span>
        <strong className="status-value">{benchmark.averages.completionTokensPerSecond}</strong>
      </section>
      <section className="status-card">
        <span className="status-label">Ukupno tok/s</span>
        <strong className="status-value">{benchmark.averages.totalTokensPerSecond}</strong>
      </section>
      <section className="status-card">
        <span className="status-label">Avg odgovor</span>
        <strong className="status-value">{benchmark.activity.averageTotalMs} ms</strong>
      </section>

      <section className="status-card wide-card">
        <span className="status-label">Benchmark grafikon</span>
        <div className="inline-actions" style={{ alignItems: "flex-start" }}>
          <div style={{ flex: "1 1 auto" }}>
            <svg
              viewBox={`0 0 ${chartWidth + 60} ${chartHeight + 50}`}
              width="100%"
              height="280"
              role="img"
              aria-label="Benchmark grafikon"
            >
              <line x1="48" y1="10" x2="48" y2={chartHeight + 10} stroke="#8a8177" strokeWidth="1.5" />
              <line x1="48" y1={chartHeight + 10} x2={chartWidth + 40} y2={chartHeight + 10} stroke="#8a8177" strokeWidth="1.5" />
              {yAxisLabels.map((label, index) => {
                const y = 10 + (chartHeight / (yAxisLabels.length - 1)) * index;
                return (
                  <g key={label}>
                    <line x1="44" y1={y} x2={chartWidth + 40} y2={y} stroke="#4f463f" strokeOpacity="0.15" />
                    <text x="0" y={y + 4} fontSize="11" fill="#d8d0c5">
                      {label}
                    </text>
                  </g>
                );
              })}
              {chartLabels.map((label, index) => {
                const x = chartLabels.length === 1 ? chartWidth / 2 : (index / (chartLabels.length - 1)) * (chartWidth - 8);
                return (
                  <text key={`${label}-${index}`} x={x + 48} y={chartHeight + 28} fontSize="10" textAnchor="middle" fill="#d8d0c5">
                    {label}
                  </text>
                );
              })}
              <polyline
                fill="none"
                stroke="#2c7be5"
                strokeWidth="3"
                points={offsetPoints(buildPolylinePoints(promptSeries, chartWidth - 8, chartHeight - 10, maxValue), 48, 10)}
              />
              <polyline
                fill="none"
                stroke="#dc3f3a"
                strokeWidth="3"
                points={offsetPoints(buildPolylinePoints(outputSeries, chartWidth - 8, chartHeight - 10, maxValue), 48, 10)}
              />
              <polyline
                fill="none"
                stroke="#7840b4"
                strokeWidth="3"
                points={offsetPoints(buildPolylinePoints(totalSeries, chartWidth - 8, chartHeight - 10, maxValue), 48, 10)}
              />
            </svg>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px", minWidth: "170px" }}>
            <span className="status-label">Legenda</span>
            <div className="helper-text"><span style={{ display: "inline-block", width: "14px", height: "14px", background: "#2c7be5", marginRight: "8px", borderRadius: "999px" }} />Input tok/s</div>
            <div className="helper-text"><span style={{ display: "inline-block", width: "14px", height: "14px", background: "#dc3f3a", marginRight: "8px", borderRadius: "999px" }} />Output tok/s</div>
            <div className="helper-text"><span style={{ display: "inline-block", width: "14px", height: "14px", background: "#7840b4", marginRight: "8px", borderRadius: "999px" }} />Ukupno tok/s</div>
          </div>
        </div>
      </section>

      <section className="status-card wide-card">
        <span className="status-label">Request activity</span>
        <p className="helper-text">
          Zahtevi: {benchmark.requestCount} | Stabilnost: {benchmark.activity.stability.label} ({benchmark.activity.stability.score})
        </p>
        <p className="helper-text">{benchmark.activity.stability.reason}</p>
        <div className="inline-actions">
          <button type="button" onClick={onOpenLogs}>
            Otvori puni live log
          </button>
        </div>
        <p className="helper-text">Zadnjih 30 linija</p>
        <pre
          className="helper-text"
          style={{
            whiteSpace: "pre-wrap",
            maxHeight: "260px",
            overflowY: "auto",
            background: "rgba(0,0,0,0.12)",
            padding: "12px",
            borderRadius: "12px",
          }}
        >
          {(benchmark.liveLog.lines.length ? benchmark.liveLog.lines : ["Jos nema dostupnog live log preview-ja."]).join("\n")}
        </pre>
      </section>

      <section className="status-card wide-card">
        <span className="status-label">Benchmark istorija</span>
        <div className="model-list">
          {benchmark.savedRuns.length ? (
            benchmark.savedRuns.map((run) => (
              <article className="model-item" key={run.runId}>
                <strong>{run.mode === "battery" ? run.batteryName : run.scenarioName}</strong>
                <div className="muted-line">
                  {run.status} | {run.runtime} | {run.modelId}
                </div>
                <div className="muted-line">
                  {run.startedAt} {run.finishedAt ? `-> ${run.finishedAt}` : ""}
                </div>
              </article>
            ))
          ) : (
            <article className="model-item">
              <div className="muted-line">Jos nema sacuvane benchmark istorije.</div>
            </article>
          )}
        </div>
      </section>
    </>
  );
}
