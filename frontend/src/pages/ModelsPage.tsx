import { useEffect, useMemo, useState } from "react";

import { ActionResultPanel } from "../components/ActionResultPanel";
import {
  activateModel,
  addHfModel,
  addLocalModel,
  addUnslothModel,
  deleteModel,
  downloadModel,
  fetchModels,
  fetchTurboQuantSchema,
  pickLocalGguf,
} from "../lib/api";
import type {
  ActionResult,
  ModelEntry,
  ModelsPayload,
  RecommendedModel,
} from "../lib/types";

type GroupKey = "curated" | "local" | "huggingFace" | "unsloth";

function ModelGroup({
  title,
  groupKey,
  items,
  collapsed,
  onToggle,
  onChanged,
}: {
  title: string;
  groupKey: GroupKey;
  items: ModelEntry[];
  collapsed: boolean;
  onToggle: (group: GroupKey) => void;
  onChanged: () => Promise<void>;
}) {
  const [result, setResult] = useState<ActionResult | null>(null);
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [removeFile, setRemoveFile] = useState(true);
  const [removeRegistry, setRemoveRegistry] = useState(true);

  async function handleAction(label: string, run: () => Promise<ActionResult>) {
    setPendingAction(label);
    setResult({
      status: "pending",
      action: "models",
      summary: `Pokrecem model akciju: ${label}`,
      details: {
        returncode: 0,
        stdout: "",
        stderr: "",
      },
    });
    try {
      const actionResult = await run();
      setResult(actionResult);
      await onChanged();
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <section className="status-card wide-card">
      <div className="section-header">
        <span className="status-label">{title}</span>
        <button type="button" className="secondary-button" onClick={() => onToggle(groupKey)}>
          {collapsed ? "Expand" : "Collapse"}
        </button>
      </div>
      {!collapsed ? (
        <div className="model-list">
          {items.map((item) => (
            <article className="model-item" key={item.id}>
              <div className="model-item-header">
                <div>
                  <strong>{item.label}</strong>
                  <div className="muted-line">
                    {item.active ? "Aktivan" : "Nije aktivan"} |{" "}
                    {item.installed ? "Skinut" : "Nije skinut"} | {item.family ?? "Unknown"}
                  </div>
                  <div className="muted-line">
                    ID: <code>{item.id}</code>
                  </div>
                  {item.description ? <p className="helper-text">{item.description}</p> : null}
                </div>
                <div className="inline-actions">
                  <button
                    disabled={Boolean(pendingAction)}
                    onClick={() => handleAction(`activate ${item.id}`, () => activateModel(item.id))}
                    type="button"
                  >
                    Activate
                  </button>
                  <button
                    disabled={Boolean(pendingAction)}
                    onClick={() => handleAction(`download ${item.id}`, () => downloadModel(item.id))}
                    type="button"
                  >
                    Download
                  </button>
                  <button
                    className="danger-button"
                    disabled={Boolean(pendingAction)}
                    onClick={() => {
                      setDeleteTargetId(item.id);
                      setRemoveFile(true);
                      setRemoveRegistry(Boolean(item.isCustom));
                    }}
                    type="button"
                  >
                    Delete
                  </button>
                </div>
              </div>
              {deleteTargetId === item.id ? (
                <div className="helper-text">
                  <strong>Potvrdi delete:</strong>
                  <div className="inline-actions compact-actions">
                    <label>
                      <input
                        type="checkbox"
                        checked={removeRegistry}
                        onChange={(event) => setRemoveRegistry(event.target.checked)}
                      />{" "}
                      Ukloni iz liste
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={removeFile}
                        onChange={(event) => setRemoveFile(event.target.checked)}
                      />{" "}
                      Obriši sa diska
                    </label>
                    <button
                      type="button"
                      className="danger-button"
                      disabled={Boolean(pendingAction)}
                      onClick={async () => {
                        await handleAction(`delete ${item.id}`, () =>
                          deleteModel(item.id, removeFile, removeRegistry),
                        );
                        setDeleteTargetId(null);
                      }}
                    >
                      Potvrdi delete
                    </button>
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => setDeleteTargetId(null)}
                    >
                      Otkaži
                    </button>
                  </div>
                </div>
              ) : null}
            </article>
          ))}
        </div>
      ) : (
        <div className="helper-text">Sekcija je sklopljena.</div>
      )}
      <ActionResultPanel result={result} />
    </section>
  );
}

export function ModelsPage() {
  const [models, setModels] = useState<ModelsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [localPath, setLocalPath] = useState("");
  const [unslothRepo, setUnslothRepo] = useState("");
  const [unslothFilename, setUnslothFilename] = useState("");
  const [hfRepo, setHfRepo] = useState("");
  const [hfFilename, setHfFilename] = useState("");
  const [result, setResult] = useState<ActionResult | null>(null);
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [recommendedModels, setRecommendedModels] = useState<RecommendedModel[]>([]);
  const [collapsedGroups, setCollapsedGroups] = useState<Record<GroupKey, boolean>>({
    curated: false,
    local: false,
    huggingFace: false,
    unsloth: false,
  });

  function showClientError(summary: string) {
    setResult({
      status: "error",
      action: "models-ui",
      summary,
      details: {
        returncode: 1,
        stdout: "",
        stderr: summary,
      },
    });
  }

  function showPendingAction(label: string) {
    setPendingAction(label);
    setResult({
      status: "pending",
      action: "models",
      summary: `Pokrecem model akciju: ${label}`,
      details: {
        returncode: 0,
        stdout: "",
        stderr: "",
      },
    });
  }

  async function reloadModels() {
    try {
      const payload = await fetchModels();
      setModels(payload);
      setError(null);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Nepoznata greska");
    }
  }

  useEffect(() => {
    void reloadModels();
    fetchTurboQuantSchema()
      .then((payload) => setRecommendedModels(payload.recommendedModels))
      .catch(() => setRecommendedModels([]));
  }, []);

  const summary = useMemo(() => {
    if (!models) {
      return { total: 0, installed: 0 };
    }
    const items = [...models.curated, ...models.local, ...models.huggingFace, ...models.unsloth];
    return {
      total: items.length,
      installed: items.filter((item) => item.installed).length,
    };
  }, [models]);

  if (error) {
    return <div className="error-panel">{error}</div>;
  }

  if (!models) {
    return <div className="status-card wide-card">Ucitavam modele...</div>;
  }

  return (
    <>
      <section className="status-card wide-card">
        <div className="section-header">
          <span className="status-label">Model browser</span>
          <div className="inline-actions compact-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={() =>
                setCollapsedGroups({
                  curated: false,
                  local: false,
                  huggingFace: false,
                  unsloth: false,
                })
              }
            >
              Expand all
            </button>
            <button
              type="button"
              className="secondary-button"
              onClick={() =>
                setCollapsedGroups({
                  curated: true,
                  local: true,
                  huggingFace: true,
                  unsloth: true,
                })
              }
            >
              Collapse all
            </button>
          </div>
        </div>
        <strong className="status-value">
          Ukupno modela: {summary.total} | Skinuto: {summary.installed}
        </strong>
      </section>

      <section className="status-card wide-card">
        <span className="status-label">Dodaj lokalni GGUF</span>
        <div className="form-grid">
          <input
            placeholder="/putanja/do/model.gguf"
            value={localPath}
            onChange={(event) => setLocalPath(event.target.value)}
          />
          <button
            type="button"
            disabled={Boolean(pendingAction)}
            onClick={() =>
              pickLocalGguf().then((payload) => {
                if (payload.path) {
                  setLocalPath(payload.path);
                  setResult({
                    status: "ok",
                    action: "pick-local-gguf",
                    summary: payload.summary,
                    details: {
                      returncode: 0,
                      stdout: payload.path,
                      stderr: "",
                    },
                  });
                } else {
                  setResult({
                    status: payload.status === "cancelled" ? "cancelled" : "error",
                    action: "pick-local-gguf",
                    summary: payload.summary,
                    details: {
                      returncode: payload.status === "cancelled" ? 0 : 1,
                      stdout: "",
                      stderr: payload.summary,
                    },
                  });
                }
              })
            }
          >
            Browse
          </button>
          <button
            type="button"
            disabled={Boolean(pendingAction)}
            onClick={async () => {
              if (!localPath.trim()) {
                showClientError("Izaberi lokalni GGUF fajl pre dodavanja.");
                return;
              }
              try {
                showPendingAction("add local");
                const actionResult = await addLocalModel(localPath, "", "Custom");
                setResult(actionResult);
                await reloadModels();
              } catch (reason: unknown) {
                showClientError(
                  reason instanceof Error ? reason.message : "Dodavanje lokalnog modela nije uspelo.",
                );
              } finally {
                setPendingAction(null);
              }
            }}
          >
            Add local
          </button>
        </div>
      </section>
      <section className="status-card wide-card">
        <span className="status-label">Dodaj Unsloth model</span>
        <div className="form-grid">
          <input
            placeholder="unsloth/Qwen3.6-35B-A3B-GGUF"
            value={unslothRepo}
            onChange={(event) => setUnslothRepo(event.target.value)}
          />
          <input
            placeholder="Qwen3.6-35B-A3B-UD-IQ2_M.gguf"
            value={unslothFilename}
            onChange={(event) => setUnslothFilename(event.target.value)}
          />
          <button
            type="button"
            onClick={async () => {
              if (!unslothRepo.trim() || !unslothFilename.trim()) {
                showClientError("Popuni Unsloth repo i tacan GGUF filename sa kvantizacijom.");
                return;
              }
              try {
                showPendingAction("add unsloth");
                const actionResult = await addUnslothModel(
                  unslothRepo.trim(),
                  unslothFilename.trim(),
                  "",
                  "Unsloth",
                );
                setResult(actionResult);
                await reloadModels();
              } catch (reason: unknown) {
                showClientError(
                  reason instanceof Error
                    ? reason.message
                    : "Dodavanje Unsloth modela nije uspelo.",
                );
              } finally {
                setPendingAction(null);
              }
            }}
          >
            Add Unsloth
          </button>
        </div>
        <p className="helper-text">
          Unsloth je poseban izvor modela. Unesi tacan GGUF filename sa kvantizacijom.
        </p>
      </section>
      <section className="status-card wide-card">
        <span className="status-label">Dodaj Hugging Face model</span>
        <div className="form-grid">
          <input
            placeholder="Qwen/Qwen3-0.6B-GGUF"
            value={hfRepo}
            onChange={(event) => setHfRepo(event.target.value)}
          />
          <input
            placeholder="Qwen3-0.6B-Q8_0.gguf"
            value={hfFilename}
            onChange={(event) => setHfFilename(event.target.value)}
          />
          <button
            type="button"
            onClick={async () => {
              if (!hfRepo.trim() || !hfFilename.trim()) {
                showClientError("Popuni repo i tacan GGUF filename sa kvantizacijom.");
                return;
              }
              try {
                showPendingAction("add hf");
                const actionResult = await addHfModel(hfRepo.trim(), hfFilename.trim(), "", "Custom");
                setResult(actionResult);
                await reloadModels();
              } catch (reason: unknown) {
                showClientError(
                  reason instanceof Error ? reason.message : "Dodavanje HF modela nije uspelo.",
                );
              } finally {
                setPendingAction(null);
              }
            }}
          >
            Add HF
          </button>
        </div>
        <p className="helper-text">
          Unesi tačan GGUF filename sa kvantizacijom, na primer{" "}
          <code>Qwen3-0.6B-Q8_0.gguf</code>.
        </p>
      </section>
      <ActionResultPanel result={result} />
      <section className="status-card wide-card">
        <span className="status-label">Unsloth GGUF preporuke</span>
        <p className="helper-text">
          Ovo su preporuceni non-MTP izbori za RTX 3060 12 GB + llama.cpp + TurboQuant.
        </p>
        <p className="helper-text">
          Fokus je na Qwen3.6 35B A3B i Qwen3.6 27B varijantama kao sto su UD-IQ2_M i
          UD-IQ3_XXS.
        </p>
        <div className="model-list">
          {recommendedModels.map((item) => (
            <article className="model-item" key={item.id}>
              <div className="model-item-header">
                <div>
                  <strong>
                    {item.label} | {item.quantization}
                  </strong>
                  <div className="muted-line">{item.repo}</div>
                  <div className="muted-line">{item.filename}</div>
                  <p className="helper-text">{item.fitNote}</p>
                </div>
                <div className="inline-actions">
                  <button
                    type="button"
                    disabled={Boolean(pendingAction)}
                    onClick={async () => {
                      try {
                        showPendingAction(`add unsloth ${item.filename}`);
                        const actionResult = await addUnslothModel(
                          item.repo,
                          item.filename,
                          item.label,
                          "Unsloth",
                        );
                        setResult(actionResult);
                        setUnslothRepo(item.repo);
                        setUnslothFilename(item.filename);
                        await reloadModels();
                      } catch (reason: unknown) {
                        showClientError(
                          reason instanceof Error
                            ? reason.message
                            : "Dodavanje Unsloth modela nije uspelo.",
                        );
                      } finally {
                        setPendingAction(null);
                      }
                    }}
                  >
                    Dodaj Unsloth model
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
      <ModelGroup
        title="Kurirani modeli"
        groupKey="curated"
        items={models.curated}
        collapsed={collapsedGroups.curated}
        onToggle={(group) =>
          setCollapsedGroups((current) => ({ ...current, [group]: !current[group] }))
        }
        onChanged={reloadModels}
      />
      <ModelGroup
        title="Lokalni modeli"
        groupKey="local"
        items={models.local}
        collapsed={collapsedGroups.local}
        onToggle={(group) =>
          setCollapsedGroups((current) => ({ ...current, [group]: !current[group] }))
        }
        onChanged={reloadModels}
      />
      <ModelGroup
        title="Hugging Face modeli"
        groupKey="huggingFace"
        items={models.huggingFace}
        collapsed={collapsedGroups.huggingFace}
        onToggle={(group) =>
          setCollapsedGroups((current) => ({ ...current, [group]: !current[group] }))
        }
        onChanged={reloadModels}
      />
      <ModelGroup
        title="Unsloth modeli"
        groupKey="unsloth"
        items={models.unsloth}
        collapsed={collapsedGroups.unsloth}
        onToggle={(group) =>
          setCollapsedGroups((current) => ({ ...current, [group]: !current[group] }))
        }
        onChanged={reloadModels}
      />
    </>
  );
}
