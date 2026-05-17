import type {
  ActionResult,
  BenchmarkBattery,
  BenchmarkPayload,
  BenchmarkScenario,
  BenchmarkRunStatusPayload,
  DownloadProgressPayload,
  ModelActionStatusPayload,
  ModelsPayload,
  OpenCodeStatusPayload,
  ServerStatusPayload,
  SettingsPayload,
  StatusPayload,
  TurboQuantConfig,
  TurboQuantSchemaPayload,
  UpdateProgressPayload,
} from "./types";

export async function fetchStatus(): Promise<StatusPayload> {
  const response = await fetch("/api/status");
  if (!response.ok) {
    throw new Error(`Status request failed: ${response.status}`);
  }
  return response.json() as Promise<StatusPayload>;
}

export async function fetchBenchmark(): Promise<BenchmarkPayload> {
  const response = await fetch("/api/benchmark");
  if (!response.ok) {
    throw new Error(`Benchmark request failed: ${response.status}`);
  }
  return response.json() as Promise<BenchmarkPayload>;
}

export async function runSelectedBenchmark(scenarioId: string): Promise<{ status: string; summary: string; runId?: string }> {
  return postJson("/api/benchmark/run-selected", { scenarioId });
}

export async function runBatteryBenchmark(batteryId: string): Promise<{ status: string; summary: string; runId?: string }> {
  return postJson("/api/benchmark/run-battery", { batteryId });
}

export async function fetchBenchmarkRunStatus(): Promise<BenchmarkRunStatusPayload> {
  const response = await fetch("/api/benchmark/run-status");
  if (!response.ok) {
    throw new Error(`Benchmark run status request failed: ${response.status}`);
  }
  return response.json() as Promise<BenchmarkRunStatusPayload>;
}

export async function saveBenchmarkBattery(
  name: string,
  scenarios: BenchmarkScenario[],
): Promise<{ status: string; summary: string; battery?: BenchmarkBattery }> {
  return postJson("/api/benchmark/batteries/save", { name, scenarios });
}

export async function loadBenchmarkBattery(
  batteryId: string,
): Promise<{ status: string; summary: string; battery?: BenchmarkBattery }> {
  return postJson("/api/benchmark/batteries/load", { batteryId });
}

export async function restoreDefaultBenchmarkTests(): Promise<{ status: string; summary: string; battery?: BenchmarkBattery }> {
  return postJson("/api/benchmark/batteries/restore-defaults", {});
}

export async function fetchServerStatus(): Promise<ServerStatusPayload> {
  const response = await fetch("/api/server/status");
  if (!response.ok) {
    throw new Error(`Server status request failed: ${response.status}`);
  }
  return response.json() as Promise<ServerStatusPayload>;
}

export async function fetchModels(): Promise<ModelsPayload> {
  const response = await fetch("/api/models");
  if (!response.ok) {
    throw new Error(`Models request failed: ${response.status}`);
  }
  return response.json() as Promise<ModelsPayload>;
}

export async function fetchDownloadProgress(): Promise<DownloadProgressPayload> {
  const response = await fetch("/api/models/download-progress");
  if (!response.ok) {
    throw new Error(`Download progress request failed: ${response.status}`);
  }
  return response.json() as Promise<DownloadProgressPayload>;
}

export async function fetchModelActionStatus(actionId: string): Promise<ModelActionStatusPayload> {
  const response = await fetch(`/api/models/action-status/${encodeURIComponent(actionId)}`);
  if (!response.ok) {
    throw new Error(`Model action status request failed: ${response.status}`);
  }
  return response.json() as Promise<ModelActionStatusPayload>;
}

export async function fetchSettings(): Promise<SettingsPayload> {
  const response = await fetch("/api/settings");
  if (!response.ok) {
    throw new Error(`Settings request failed: ${response.status}`);
  }
  return response.json() as Promise<SettingsPayload>;
}

export async function applySettings(payload: SettingsPayload): Promise<ActionResult> {
  return postJson("/api/settings/apply", payload);
}

export async function fetchTurboQuantSchema(): Promise<TurboQuantSchemaPayload> {
  const response = await fetch("/api/settings/turboquant");
  if (!response.ok) {
    throw new Error(`TurboQuant schema request failed: ${response.status}`);
  }
  return response.json() as Promise<TurboQuantSchemaPayload>;
}

export async function fetchOpenCodeStatus(): Promise<OpenCodeStatusPayload> {
  const response = await fetch("/api/opencode/status");
  if (!response.ok) {
    throw new Error(`OpenCode status request failed: ${response.status}`);
  }
  return response.json() as Promise<OpenCodeStatusPayload>;
}

export async function applyOpenCodeSettings(payload: {
  profile: string;
  context: number;
  outputTokens: number;
  workingDirectory: string;
  buildSteps: number;
  planSteps: number;
  generalSteps: number;
  exploreSteps: number;
  securityMode: string;
  capabilityMode: string;
}): Promise<ActionResult> {
  return postJson("/api/opencode/settings/apply", payload);
}

export async function openOpenCode(profile: string): Promise<ActionResult> {
  return postJson("/api/opencode/open", { profile });
}

export async function saveTurboQuantConfig(payload: TurboQuantConfig): Promise<ActionResult> {
  return postJson("/api/settings/turboquant-config", payload);
}

export async function saveTurboQuantPreset(payload: {
  name: string;
  description: string;
  targetModelPattern: string;
  notes: string;
  settings: TurboQuantConfig;
}): Promise<ActionResult> {
  return postJson("/api/settings/turboquant-presets/save", payload);
}

export async function deleteTurboQuantPreset(presetId: string): Promise<ActionResult> {
  return postJson("/api/settings/turboquant-presets/delete", { presetId });
}

async function postJson<TRequest, TResponse>(
  url: string,
  body: TRequest,
  timeoutMs?: number,
): Promise<TResponse> {
  const controller = typeof AbortController !== "undefined" ? new AbortController() : undefined;
  const timeoutId =
    controller && timeoutMs
      ? window.setTimeout(() => controller.abort(), timeoutMs)
      : undefined;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: controller?.signal,
    });
    if (!response.ok) {
      throw new Error(`POST ${url} failed: ${response.status}`);
    }
    return response.json() as Promise<TResponse>;
  } finally {
    if (timeoutId) {
      window.clearTimeout(timeoutId);
    }
  }
}

export async function activateModel(modelId: string): Promise<ActionResult> {
  return postJson("/api/models/activate", { modelId });
}

export async function downloadModel(modelId: string): Promise<ActionResult> {
  return postJson("/api/models/download", { modelId });
}

export async function addLocalModel(
  path: string,
  label: string,
  family: string,
): Promise<ActionResult> {
  return postJson("/api/models/add-local", { path, label, family });
}

export async function addHfModel(
  repo: string,
  filename: string,
  label: string,
  family: string,
): Promise<ActionResult> {
  return postJson("/api/models/add-hf", { repo, filename, label, family });
}

export async function addUnslothModel(
  repo: string,
  filename: string,
  label: string,
  family: string,
): Promise<ActionResult> {
  return postJson("/api/models/add-unsloth", { repo, filename, label, family });
}

export async function deleteModel(
  modelId: string,
  removeFile: boolean,
  removeRegistry: boolean,
): Promise<ActionResult> {
  return postJson("/api/models/delete", { modelId, removeFile, removeRegistry });
}

export async function fetchLogs(): Promise<ActionResult> {
  const response = await fetch("/api/logs");
  if (!response.ok) {
    throw new Error(`Logs request failed: ${response.status}`);
  }
  return response.json() as Promise<ActionResult>;
}

export async function runRepair(kind: string): Promise<ActionResult> {
  return postJson(`/api/repair/${kind}`, {});
}

export async function checkUpdates(): Promise<ActionResult> {
  const response = await fetch("/api/updates/check");
  if (!response.ok) {
    throw new Error(`Updates request failed: ${response.status}`);
  }
  return response.json() as Promise<ActionResult>;
}

export async function installUpdate(): Promise<ActionResult> {
  return postJson("/api/updates/install", {});
}

export async function fetchUpdateProgress(): Promise<UpdateProgressPayload> {
  const response = await fetch("/api/updates/progress");
  if (!response.ok) {
    throw new Error(`Update progress request failed: ${response.status}`);
  }
  return response.json() as Promise<UpdateProgressPayload>;
}

export async function pickLocalGguf(): Promise<{ status: string; summary: string; path: string }> {
  return postJson("/api/system/pick-local-gguf", {});
}

export async function pickWorkingDirectory(): Promise<{ status: string; summary: string; path: string }> {
  return postJson("/api/system/pick-working-directory", {});
}

export async function selectRuntime(runtime: string): Promise<ActionResult> {
  return postJson("/api/runtime/select", { runtime });
}

export async function startServer(): Promise<ActionResult> {
  return postJson("/api/server/start", {});
}

export async function stopServer(): Promise<ActionResult> {
  return postJson("/api/server/stop", {});
}

export async function openServerWeb(): Promise<ActionResult> {
  return postJson("/api/server/open-web", {});
}
