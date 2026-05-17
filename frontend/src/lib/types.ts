export type StatusPayload = {
  version: string;
  health: string;
  activeModel: string;
  profile: string;
  uiPort: number;
  uiUrl: string;
  localUrl: string;
  tailscaleUrl: string;
  accessMode: string;
  bindHost: string;
  runtimeStatus: string;
  runtimeSummary: string;
  activeRuntimeLabel: string;
  availableRuntimes: string[];
  llamaRuntimeAvailable: boolean;
  turboQuantRuntimeAvailable: boolean;
  llamaCppStatus: string;
  turboQuantStatus: string;
  turboQuantReason: string;
  activeRuntimeBinary: string;
  activeRuntimeBinarySource: string;
  runtimeLiveStatus: string;
  runtimeLiveReason: string;
};

export type ModelEntry = {
  id: string;
  label: string;
  source: string;
  active: boolean;
  installed: boolean;
  filename?: string;
  family?: string;
  description?: string;
  isCustom?: boolean;
};

export type ModelsPayload = {
  curated: ModelEntry[];
  local: ModelEntry[];
  huggingFace: ModelEntry[];
  unsloth: ModelEntry[];
};

export type SettingsPayload = {
  profile: string;
  context: number;
  outputTokens: number;
  workingDirectory: string;
  thinkingMode: string;
  buildSteps: number;
  planSteps: number;
  generalSteps: number;
  exploreSteps: number;
  settingsScope: string;
  activeModelId: string;
  activeModelLabel: string;
  modelOverrideExists: boolean;
  accessMode: string;
};

export type TurboQuantConfig = {
  context: number;
  ctk: string;
  ctv: string;
  ncmoe: number;
  flashAttention: boolean;
  mlock: boolean;
  mmapMode: string;
  runtimePreference: string;
};

export type TurboQuantParameter = {
  id: string;
  label: string;
  whatIsIt: string;
  effect: string;
  recommendation: string;
  safeChoices: string[];
  advancedChoices: string[];
  defaultValue: string | number | boolean;
};

export type TurboQuantPreset = {
  id: string;
  name: string;
  description: string;
  targetModelPattern: string;
  notes: string;
  settings: TurboQuantConfig;
};

export type RecommendedModel = {
  id: string;
  label: string;
  repo: string;
  filename: string;
  quantization: string;
  fitNote: string;
  mtp: boolean;
};

export type TurboQuantSchemaPayload = {
  parameters: TurboQuantParameter[];
  builtInPresets: TurboQuantPreset[];
  userPresets: TurboQuantPreset[];
  currentConfig: TurboQuantConfig;
  recommendedModels: RecommendedModel[];
};

export type ActionResult = {
  status: string;
  action: string;
  summary: string;
  details: {
    returncode: number;
    stdout: string;
    stderr: string;
  };
};
