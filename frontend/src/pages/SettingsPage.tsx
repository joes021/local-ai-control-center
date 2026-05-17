import { useEffect, useState } from "react";

import { ActionResultPanel } from "../components/ActionResultPanel";
import {
  applySettings,
  deleteTurboQuantPreset,
  fetchSettings,
  fetchTurboQuantSchema,
  pickWorkingDirectory,
  saveTurboQuantConfig,
  saveTurboQuantPreset,
} from "../lib/api";
import type {
  ActionResult,
  SettingsPayload,
  TurboQuantConfig,
  TurboQuantPreset,
  TurboQuantSchemaPayload,
} from "../lib/types";

function applyPresetToConfig(preset: TurboQuantPreset): TurboQuantConfig {
  return { ...preset.settings };
}

export function SettingsPage() {
  const [settings, setSettings] = useState<SettingsPayload | null>(null);
  const [schema, setSchema] = useState<TurboQuantSchemaPayload | null>(null);
  const [turboConfig, setTurboConfig] = useState<TurboQuantConfig | null>(null);
  const [presetName, setPresetName] = useState("");
  const [presetDescription, setPresetDescription] = useState("");
  const [presetTargetPattern, setPresetTargetPattern] = useState("");
  const [presetNotes, setPresetNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ActionResult | null>(null);

  async function reload() {
    const [settingsPayload, schemaPayload] = await Promise.all([
      fetchSettings(),
      fetchTurboQuantSchema(),
    ]);
    setSettings(settingsPayload);
    setSchema(schemaPayload);
    setTurboConfig(schemaPayload.currentConfig);
  }

  useEffect(() => {
    reload().catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Nepoznata greska");
    });
  }, []);

  if (error) {
    return <div className="error-panel">{error}</div>;
  }

  if (!settings || !schema || !turboConfig) {
    return <div className="status-card wide-card">Ucitavam settings...</div>;
  }

  const allPresets = [...schema.builtInPresets, ...schema.userPresets];

  return (
    <>
      <section className="status-card wide-card">
        <span className="status-label">Settings scope</span>
        <strong className="status-value">
          Aktivni model: {settings.activeModelLabel || "nema"} ({settings.activeModelId || "--"})
        </strong>
        <p className="helper-text">
          Global defaults vaze za sve modele bez posebnog override-a. Active model override vazi
          samo za trenutno aktivni model.
        </p>
        <select
          value={settings.settingsScope}
          onChange={(event) =>
            setSettings({
              ...settings,
              settingsScope: event.target.value,
            })
          }
        >
          <option value="global">Global defaults</option>
          <option value="model">Active model override</option>
        </select>
        <p className="helper-text">
          {settings.modelOverrideExists
            ? "Za aktivni model vec postoji poseban override."
            : "Za aktivni model trenutno nema posebnog override-a."}
        </p>
      </section>

      <section className="status-card">
        <span className="status-label">Access mode</span>
        <select
          value={settings.accessMode}
          onChange={(event) =>
            setSettings({
              ...settings,
              accessMode: event.target.value,
            })
          }
        >
          <option value="local-only">Local only</option>
          <option value="tailscale">Tailscale</option>
        </select>
        <p className="helper-text">
          Tailscale rezim podize backend tako da moze da se otvori i preko Tailscale adrese.
        </p>
      </section>

      <section className="status-card">
        <span className="status-label">Profil</span>
        <select
          value={settings.profile}
          onChange={(event) =>
            setSettings({
              ...settings,
              profile: event.target.value,
            })
          }
        >
          <option value="speed">speed</option>
          <option value="balanced">balanced</option>
          <option value="video">video</option>
        </select>
      </section>
      <section className="status-card">
        <span className="status-label">Thinking mode</span>
        <select
          value={settings.thinkingMode}
          onChange={(event) =>
            setSettings({
              ...settings,
              thinkingMode: event.target.value,
            })
          }
        >
          <option value="no-thinking">No thinking</option>
          <option value="low">Low</option>
          <option value="mid">Mid</option>
          <option value="high">High</option>
          <option value="extra-high">Extra high</option>
        </select>
      </section>
      <section className="status-card">
        <span className="status-label">Context</span>
        <input
          type="number"
          value={settings.context}
          onChange={(event) =>
            setSettings({
              ...settings,
              context: Number(event.target.value || 0),
            })
          }
        />
      </section>
      <section className="status-card">
        <span className="status-label">Output tokens</span>
        <input
          type="number"
          value={settings.outputTokens}
          onChange={(event) =>
            setSettings({
              ...settings,
              outputTokens: Number(event.target.value || 0),
            })
          }
        />
      </section>
      <section className="status-card wide-card">
        <span className="status-label">Working directory</span>
        <div className="form-grid">
          <input
            value={settings.workingDirectory}
            onChange={(event) =>
              setSettings({
                ...settings,
                workingDirectory: event.target.value,
              })
            }
          />
          <button
            type="button"
            onClick={() =>
              pickWorkingDirectory().then((payload) => {
                if (payload.path) {
                  setSettings({
                    ...settings,
                    workingDirectory: payload.path,
                  });
                }
              })
            }
          >
            Browse
          </button>
        </div>
      </section>
      <section className="status-card wide-card">
        <span className="status-label">Step mapping</span>
        <strong className="status-value">
          Build {settings.buildSteps} | Plan {settings.planSteps} | General{" "}
          {settings.generalSteps} | Explore {settings.exploreSteps}
        </strong>
      </section>

      <section className="status-card wide-card">
        <div className="section-header">
          <span className="status-label">TurboQuant preseti</span>
        </div>
        <p className="helper-text">
          safe je najbezbedniji, daily je preporuceni balans, a max-context je agresivniji kada
          juris sto duzi context.
        </p>
        <div className="model-list">
          {allPresets.map((preset) => (
            <article className="model-item" key={preset.id}>
              <div className="model-item-header">
                <div>
                  <strong>{preset.name}</strong>
                  <div className="muted-line">{preset.description}</div>
                  <div className="muted-line">
                    Context {preset.settings.context} | ctk {preset.settings.ctk} | ctv{" "}
                    {preset.settings.ctv} | ncmoe {preset.settings.ncmoe}
                  </div>
                  {preset.notes ? <p className="helper-text">{preset.notes}</p> : null}
                </div>
                <div className="inline-actions">
                  <button
                    type="button"
                    onClick={() => {
                      setTurboConfig(applyPresetToConfig(preset));
                      setResult({
                        status: "ok",
                        action: "apply-preset-local",
                        summary: `Preset ${preset.name} je ucitan u editor.`,
                        details: { returncode: 0, stdout: "", stderr: "" },
                      });
                    }}
                  >
                    Load preset
                  </button>
                  {schema.userPresets.some((item) => item.id === preset.id) ? (
                    <button
                      type="button"
                      className="danger-button"
                      onClick={async () => {
                        const actionResult = await deleteTurboQuantPreset(preset.id);
                        setResult(actionResult);
                        await reload();
                      }}
                    >
                      Obrisi
                    </button>
                  ) : null}
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="status-card wide-card">
        <span className="status-label">Sacuvaj trenutni preset</span>
        <div className="form-grid">
          <input
            placeholder="Ime preset-a"
            value={presetName}
            onChange={(event) => setPresetName(event.target.value)}
          />
          <input
            placeholder="Kratak opis"
            value={presetDescription}
            onChange={(event) => setPresetDescription(event.target.value)}
          />
          <input
            placeholder="Model pattern, npr qwen36-*"
            value={presetTargetPattern}
            onChange={(event) => setPresetTargetPattern(event.target.value)}
          />
          <input
            placeholder="Napomena"
            value={presetNotes}
            onChange={(event) => setPresetNotes(event.target.value)}
          />
          <button
            type="button"
            onClick={async () => {
              const actionResult = await saveTurboQuantPreset({
                name: presetName,
                description: presetDescription,
                targetModelPattern: presetTargetPattern,
                notes: presetNotes,
                settings: turboConfig,
              });
              setResult(actionResult);
              setPresetName("");
              setPresetDescription("");
              setPresetTargetPattern("");
              setPresetNotes("");
              await reload();
            }}
          >
            Sacuvaj preset
          </button>
        </div>
      </section>

      <section className="status-card wide-card">
        <span className="status-label">TurboQuant parametri</span>
        <div className="model-list">
          {schema.parameters.map((parameter) => (
            <article className="model-item" key={parameter.id}>
              <div className="model-item-header">
                <div>
                  <strong>{parameter.label}</strong>
                  <p className="helper-text">{parameter.whatIsIt}</p>
                  <p className="helper-text">Ucinak: {parameter.effect}</p>
                  <p className="helper-text">Preporuka: {parameter.recommendation}</p>
                  <div className="muted-line">
                    Safe: {parameter.safeChoices.join(", ") || "--"} | Advanced:{" "}
                    {parameter.advancedChoices.join(", ") || "--"}
                  </div>
                </div>
                <div className="inline-actions">
                  {parameter.id === "context" || parameter.id === "ncmoe" ? (
                    <input
                      type="number"
                      value={Number(turboConfig[parameter.id as keyof TurboQuantConfig])}
                      onChange={(event) =>
                        setTurboConfig({
                          ...turboConfig,
                          [parameter.id]: Number(event.target.value || 0),
                        })
                      }
                    />
                  ) : parameter.id === "flashAttention" || parameter.id === "mlock" ? (
                    <label>
                      <input
                        type="checkbox"
                        checked={Boolean(turboConfig[parameter.id as keyof TurboQuantConfig])}
                        onChange={(event) =>
                          setTurboConfig({
                            ...turboConfig,
                            [parameter.id]: event.target.checked,
                          })
                        }
                      />{" "}
                      ukljuceno
                    </label>
                  ) : (
                    <select
                      value={String(turboConfig[parameter.id as keyof TurboQuantConfig])}
                      onChange={(event) =>
                        setTurboConfig({
                          ...turboConfig,
                          [parameter.id]: event.target.value,
                        })
                      }
                    >
                      {[...parameter.safeChoices, ...parameter.advancedChoices].map((choice) => (
                        <option key={choice} value={choice}>
                          {choice}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="status-card wide-card">
        <div className="inline-actions">
          <button type="button" onClick={() => applySettings(settings).then(setResult)}>
            Save settings
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={async () => {
              const actionResult = await saveTurboQuantConfig(turboConfig);
              setResult(actionResult);
              await reload();
            }}
          >
            Save TurboQuant config
          </button>
        </div>
      </section>
      <ActionResultPanel result={result} />
    </>
  );
}
