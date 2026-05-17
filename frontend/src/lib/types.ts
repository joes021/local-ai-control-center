export type StatusPayload = {
  hostPlatform: string;
  hostPlatformLabel: string;
  hostShellLabel: string;
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

export type ServerStatusPayload = {
  status: string;
  lifecycleState: string;
  port: number;
  health: string;
  healthReason: string;
  pid: number | null;
  profile: string;
  activeModel: string;
  activeRuntime: string;
  activeRuntimeLabel: string;
  runtimeLiveStatus: string;
  runtimeLiveReason: string;
  lastReason: string;
  updatedAt: string;
  healthUrl: string;
  webUrl: string;
  localWebUrl: string;
  tailscaleWebUrl: string;
};

export type BenchmarkHistoryItem = {
  measuredAt: string;
  chartLabel?: string;
  label: string;
  source?: string;
  promptTokensPerSecond?: number;
  completionTokensPerSecond?: number;
  totalTokensPerSecond?: number;
  totalMs?: number;
};

export type BenchmarkScenario = {
  id: string;
  name: string;
  prompt: string;
  description?: string;
};

export type BenchmarkBattery = {
  id: string;
  name: string;
  source: string;
  updatedAt?: string;
  scenarios: BenchmarkScenario[];
};

export type BenchmarkScenarioStatus = {
  scenarioId: string;
  scenarioName: string;
  status: "queued" | "running" | "done" | "failed";
  summary: string;
};

export type BenchmarkRunStatusPayload = {
  runId: string;
  status: string;
  mode: string;
  batteryId: string;
  batteryName: string;
  scenarioId: string;
  scenarioName: string;
  currentScenarioId: string;
  currentScenarioName: string;
  currentIndex: number;
  totalScenarios: number;
  percent: number;
  startedAt: string;
  finishedAt: string;
  message: string;
  scenarioStatuses: BenchmarkScenarioStatus[];
};

export type SavedBenchmarkRun = {
  runId: string;
  mode: string;
  batteryName: string;
  scenarioName: string;
  modelId: string;
  runtime: string;
  status: string;
  startedAt: string;
  finishedAt: string;
  currentMetric?: BenchmarkHistoryItem;
  scenarioResults?: Array<{
    scenarioId: string;
    scenarioName: string;
    status: string;
    summary: string;
    metric?: BenchmarkHistoryItem;
  }>;
};

export type BenchmarkPayload = {
  current: BenchmarkHistoryItem | null;
  history: BenchmarkHistoryItem[];
  historyCount: number;
  requestCount: number;
  lastMeasuredAt: string | null;
  lastLabel: string | null;
  activity: {
    averageTotalMs: number;
    sources: {
      testPrompt: number;
      opencode: number;
      other: number;
    };
    recentActivities: BenchmarkHistoryItem[];
    stability: {
      level: string;
      label: string;
      score: number;
      reason: string;
    };
    throughputTrend: {
      direction: string;
      label: string;
      signal: string;
      reason: string;
    };
    latencyTrend: {
      direction: string;
      label: string;
      signal: string;
      reason: string;
    };
  };
  averages: {
    promptTokensPerSecond: number;
    completionTokensPerSecond: number;
    totalTokensPerSecond: number;
  };
  liveLog: {
    path: string;
    lines: string[];
  };
  batteries: BenchmarkBattery[];
  selectedBattery: BenchmarkBattery;
  activeRun: BenchmarkRunStatusPayload;
  savedRuns: SavedBenchmarkRun[];
};

export type ModelEntry = {
  id: string;
  label: string;
  source: string;
  active: boolean;
  installed: boolean;
  mtpStatus?: "no-mtp" | "has-mtp" | "unknown";
  mtpStatusLabel?: string;
  filename?: string;
  family?: string;
  description?: string;
  isCustom?: boolean;
  approxSizeGiB?: number | null;
  minimumGpuMiB?: number | null;
  recommendedGpuMiB?: number | null;
  minimumRamGiB?: number | null;
  installedSizeGiB?: number | null;
  diskNeededGiB?: number | null;
  freeDiskGiB?: number | null;
  hasEnoughDisk?: boolean | null;
};

export type ModelsPayload = {
  curated: ModelEntry[];
  local: ModelEntry[];
  huggingFace: ModelEntry[];
  unsloth: ModelEntry[];
};

export type DownloadProgressPayload = {
  status: string;
  isActive: boolean;
  modelId: string;
  fileName: string;
  source: string;
  percent: number | null;
  downloadedGiB: number | null;
  totalGiB: number | null;
  speedMBps: number | null;
  etaSeconds: number | null;
  message: string;
  updatedAt: string;
};

export type UpdateProgressPayload = {
  actionId: string;
  status: string;
  phase: string;
  isActive: boolean;
  currentVersion: string;
  latestVersion: string;
  releaseUrl: string;
  targetPath: string;
  percent: number | null;
  downloadedGiB: number | null;
  totalGiB: number | null;
  speedMBps: number | null;
  etaSeconds: number | null;
  message: string;
  updatedAt: string;
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

export type OpenCodeStatusPayload = {
  available: boolean;
  configExists: boolean;
  configPath: string;
  configDir: string;
  executablePath: string;
  workingDirectory: string;
  buildSteps: number;
  planSteps: number;
  generalSteps: number;
  exploreSteps: number;
  securityMode: string;
  capabilityMode: string;
  profile: string;
  auditRiskLevel: string;
  auditSummary: string;
};

export type ActionResult = {
  status: string;
  action: string;
  summary: string;
  actionId?: string;
  details: {
    returncode: number;
    stdout: string;
    stderr: string;
  };
};

export type ModelActionStatusPayload = {
  actionId: string;
  status: string;
  summary: string;
  isDone: boolean;
  result: ActionResult | null;
};
