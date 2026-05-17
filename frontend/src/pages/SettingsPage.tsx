import { useEffect, useState } from "react";

import { ActionResultPanel } from "../components/ActionResultPanel";
import { CustomSelect } from "../components/CustomSelect";
import {
  applyOpenCodeSettings,
  applySettings,
  deleteTurboQuantPreset,
  fetchOpenCodeStatus,
  fetchSettings,
  fetchTurboQuantSchema,
  openOpenCode,
  pickWorkingDirectory,
  saveTurboQuantConfig,
  saveTurboQuantPreset,
} from "../lib/api";
import type {
  ActionResult,
  OpenCodeStatusPayload,
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
  const [opencode, setOpencode] = useState<OpenCodeStatusPayload | null>(null);
  const [schema, setSchema] = useState<TurboQuantSchemaPayload | null>(null);
  const [turboConfig, setTurboConfig] = useState<TurboQuantConfig | null>(null);
  const [presetName, setPresetName] = useState("");
  const [presetDescription, setPresetDescription] = useState("");
  const [presetTargetPattern, setPresetTargetPattern] = useState("");
  const [presetNotes, setPresetNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ActionResult | null>(null);

  async function reload() {
    const [settingsPayload, schemaPayload, opencodePayload] = await Promise.all([
      fetchSettings(),
      fetchTurboQuantSchema(),
      fetchOpenCodeStatus(),
    ]);
    setSettings(settingsPayload);
    setSchema(schemaPayload);
    setTurboConfig(schemaPayload.currentConfig);
    setOpencode(opencodePayload);
  }

  useEffect(() => {
    reload().catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Nepoznata greska");
    });
  }, []);

  if (error) {
    return <div className="error-panel">{error}</div>;
  }

  if (!settings || !schema || !turboConfig || !opencode) {
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
        <CustomSelect
          value={settings.settingsScope}
          options={[
            { value: "global", label: "Global defaults" },
            { value: "model", label: "Active model override" },
          ]}
          onChange={(value) =>
            setSettings({
              ...settings,
              settingsScope: value,
            })
          }
          ariaLabel="Izaberi settings scope"
        />
        <p className="helper-text">
          {settings.modelOverrideExists
            ? "Za aktivni model vec postoji poseban override."
            : "Za aktivni model trenutno nema posebnog override-a."}
        </p>
      </section>

      <section className="status-card">
        <span className="status-label">Access mode</span>
        <CustomSelect
          value={settings.accessMode}
          options={[
            { value: "local-only", label: "Local only" },
            { value: "tailscale", label: "Tailscale" },
          ]}
          onChange={(value) =>
            setSettings({
              ...settings,
              accessMode: value,
            })
          }
          ariaLabel="Izaberi access mode"
        />
        <p className="helper-text">
          Tailscale rezim podize backend tako da moze da se otvori i preko Tailscale adrese.
        </p>
      </section>

      <section className="status-card">
        <span className="status-label">Profil</span>
        <CustomSelect
          value={settings.profile}
          options={[
            { value: "speed", label: "speed" },
            { value: "balanced", label: "balanced" },
            { value: "video", label: "video" },
          ]}
          onChange={(value) =>
            setSettings({
              ...settings,
              profile: value,
            })
          }
          ariaLabel="Izaberi profil"
        />
      </section>
      <section className="status-card">
        <span className="status-label">Thinking mode</span>
        <CustomSelect
          value={settings.thinkingMode}
          options={[
            { value: "no-thinking", label: "No thinking" },
            { value: "low", label: "Low" },
            { value: "mid", label: "Mid" },
            { value: "high", label: "High" },
            { value: "extra-high", label: "Extra high" },
          ]}
          onChange={(value) =>
            setSettings({
              ...settings,
              thinkingMode: value,
            })
          }
          ariaLabel="Izaberi thinking mode"
        />
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
        <span className="status-label">OpenCode config</span>
        <strong className="status-value">
          {opencode.available ? "OpenCode je dostupan" : "OpenCode nije dostupan"}
        </strong>
        <p className="helper-text">Executable: {opencode.executablePath || "nije pronadjen"}</p>
        <p className="helper-text">OpenCode config: {opencode.configPath || "nije pronadjen"}</p>
        <p className="helper-text">Risk audit: {opencode.auditSummary || "nema sacuvanog audita"}</p>
        <div className="form-grid">
          <label>
            Security mode
            <CustomSelect
              value={opencode.securityMode}
              options={[
                { value: "strict", label: "strict" },
                { value: "workspace-write", label: "workspace-write" },
                { value: "open", label: "open" },
              ]}
              onChange={(value) =>
                setOpencode({
                  ...opencode,
                  securityMode: value,
                })
              }
              ariaLabel="Izaberi OpenCode security mode"
            />
          </label>
          <label>
            Capability mode
            <CustomSelect
              value={opencode.capabilityMode}
              options={[
                { value: "read-only", label: "read-only" },
                { value: "read-write", label: "read-write" },
                { value: "confirm-commands", label: "confirm-commands" },
                { value: "auto-commands", label: "auto-commands" },
              ]}
              onChange={(value) =>
                setOpencode({
                  ...opencode,
                  capabilityMode: value,
                })
              }
              ariaLabel="Izaberi OpenCode capability mode"
            />
          </label>
          <button
            type="button"
            onClick={async () => {
              const actionResult = await applyOpenCodeSettings({
                profile: settings.profile,
                context: settings.context,
                outputTokens: settings.outputTokens,
                workingDirectory: settings.workingDirectory,
                buildSteps: settings.buildSteps,
                planSteps: settings.planSteps,
                generalSteps: settings.generalSteps,
                exploreSteps: settings.exploreSteps,
                securityMode: opencode.securityMode,
                capabilityMode: opencode.capabilityMode,
              });
              setResult(actionResult);
              await reload();
            }}
          >
            Save OpenCode settings
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={async () => {
              const actionResult = await openOpenCode(settings.profile);
              setResult(actionResult);
              await reload();
            }}
          >
            Open OpenCode
          </button>
        </div>
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
                    <CustomSelect
                      value={String(turboConfig[parameter.id as keyof TurboQuantConfig])}
                      options={[...parameter.safeChoices, ...parameter.advancedChoices].map((choice) => ({
                        value: choice,
                        label: choice,
                      }))}
                      onChange={(value) =>
                        setTurboConfig({
                          ...turboConfig,
                          [parameter.id]: value,
                        })
                      }
                      ariaLabel={`Izaberi ${parameter.label}`}
                    />
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
