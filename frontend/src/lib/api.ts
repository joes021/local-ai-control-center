import type {
  ActionResult,
  ModelsPayload,
  SettingsPayload,
  StatusPayload,
  TurboQuantConfig,
  TurboQuantSchemaPayload,
} from "./types";

export async function fetchStatus(): Promise<StatusPayload> {
  const response = await fetch("/api/status");
  if (!response.ok) {
    throw new Error(`Status request failed: ${response.status}`);
  }
  return response.json() as Promise<StatusPayload>;
}

export async function fetchModels(): Promise<ModelsPayload> {
  const response = await fetch("/api/models");
  if (!response.ok) {
    throw new Error(`Models request failed: ${response.status}`);
  }
  return response.json() as Promise<ModelsPayload>;
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

async function postJson<TRequest, TResponse>(url: string, body: TRequest): Promise<TResponse> {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`POST ${url} failed: ${response.status}`);
  }
  return response.json() as Promise<TResponse>;
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

export async function pickLocalGguf(): Promise<{ status: string; summary: string; path: string }> {
  return postJson("/api/system/pick-local-gguf", {});
}

export async function pickWorkingDirectory(): Promise<{ status: string; summary: string; path: string }> {
  return postJson("/api/system/pick-working-directory", {});
}

export async function selectRuntime(runtime: string): Promise<ActionResult> {
  return postJson("/api/runtime/select", { runtime });
}
