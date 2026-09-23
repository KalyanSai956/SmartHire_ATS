import { useEffect, useState } from "react";
import { Eye, EyeOff, KeyRound, CheckCircle2, XCircle } from "lucide-react";

import {
  getLLMSettings,
  connectLLMProvider,
  disconnectLLMProvider,
  getUsageQuota,
} from "../services/api";

import { supabase } from "../context/AuthContext";

import "../CSS/Settings.css";

const PROVIDER_INFO = {
  groq: {
    name: "Groq",
    description: "Fast inference for LLM-powered features.",
  },
  openai: {
    name: "OpenAI",
    description: "OpenAI models for career intelligence.",
  },
  anthropic: {
    name: "Anthropic",
    description: "Claude models for reasoning.",
  },
  google: {
    name: "Google Gemini",
    description: "Gemini models for AI-powered career workflows.",
  },
};

export default function Settings() {
  const [providers, setProviders] = useState([]);
  const [usage, setUsage] = useState(null);

  const [loading, setLoading] = useState(true);
  const [savingProvider, setSavingProvider] = useState(null);

  const [selectedProvider, setSelectedProvider] = useState("groq");

  const [apiKeys, setApiKeys] = useState({});
  const [models, setModels] = useState({});

  const [visibleKeys, setVisibleKeys] = useState({});

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function getAccessToken() {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      throw new Error("Your session has expired. Please sign in again.");
    }

    return session.access_token;
  }

  async function loadSettings() {
    try {
      setLoading(true);
      setError("");

      const token = await getAccessToken();

      const [settingsData, usageData] = await Promise.all([
        getLLMSettings(token),
        getUsageQuota(token),
      ]);

      setProviders(settingsData.providers || []);
      setUsage(usageData);

      const connected = (settingsData.providers || []).filter(
        (provider) => provider.connected,
      );

      if (connected.length > 0) {
        setSelectedProvider(connected[0].provider);
      }
    } catch (err) {
      setError(err.message || "Failed to load AI settings.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSettings();
  }, []);

  function toggleKeyVisibility(provider) {
    setVisibleKeys((current) => ({
      ...current,
      [provider]: !current[provider],
    }));
  }

  function handleKeyChange(provider, value) {
    setApiKeys((current) => ({
      ...current,
      [provider]: value,
    }));
  }

  function handleModelChange(provider, value) {
    setModels((current) => ({
      ...current,
      [provider]: value,
    }));
  }

  async function handleConnect(provider) {
    const apiKey = apiKeys[provider]?.trim();

    if (!apiKey) {
      setError(`Enter your ${PROVIDER_INFO[provider].name} API key.`);
      return;
    }

    try {
      setSavingProvider(provider);
      setError("");
      setMessage("");

      const token = await getAccessToken();

      const providerInfo = providers.find((item) => item.provider === provider);

      const model =
        models[provider] ||
        providerInfo?.model ||
        providerInfo?.default_model ||
        "";

      await connectLLMProvider(token, provider, apiKey, model);

      setApiKeys((current) => ({
        ...current,
        [provider]: "",
      }));

      setMessage(`${PROVIDER_INFO[provider].name} connected successfully.`);

      await loadSettings();
    } catch (err) {
      setError(err.message || "Failed to connect provider.");
    } finally {
      setSavingProvider(null);
    }
  }

  async function handleDisconnect(provider) {
    try {
      setSavingProvider(provider);
      setError("");
      setMessage("");

      const token = await getAccessToken();

      await disconnectLLMProvider(token, provider);

      if (selectedProvider === provider) {
        setSelectedProvider("groq");
      }

      setMessage(`${PROVIDER_INFO[provider].name} disconnected.`);

      await loadSettings();
    } catch (err) {
      setError(err.message || "Failed to disconnect provider.");
    } finally {
      setSavingProvider(null);
    }
  }

  if (loading) {
    return (
      <div className="settings-page">
        <div className="settings-loading">Loading AI settings...</div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-2 settings-page">
      <div className="settings-container">
        {error && (
          <div className="settings-alert settings-alert-error">
            <XCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        {message && (
          <div className="settings-alert settings-alert-success">
            <CheckCircle2 size={18} />
            <span>{message}</span>
          </div>
        )}

        {/* Provider Selection */}

        <section className="settings-section">
          <div className="settings-section-heading">
            <div>
              <h2>Active AI Provider</h2>

              <p>Select the provider SmartHire should use.</p>
            </div>
          </div>

          <div className="provider-selection-grid">
            {providers.map((provider) => {
              const connected = provider.connected;

              return (
                <button
                  key={provider.provider}
                  type="button"
                  className={`provider-select-card ${
                    selectedProvider === provider.provider ? "selected" : ""
                  } ${!connected ? "not-connected" : ""}`}
                  onClick={() => {
                    if (connected) {
                      setSelectedProvider(provider.provider);
                    }
                  }}
                  disabled={!connected}
                >
                  <div className="provider-select-top">
                    <div className="provider-icon">
                      <KeyRound size={18} />
                    </div>

                    {connected ? (
                      <span className="provider-status connected">
                        Connected
                      </span>
                    ) : (
                      <span className="provider-status">Not connected</span>
                    )}
                  </div>

                  <strong>
                    {PROVIDER_INFO[provider.provider]?.name || provider.name}
                  </strong>

                  <span>
                    {PROVIDER_INFO[provider.provider]?.description || ""}
                  </span>

                  {connected && <small>Model: {provider.model}</small>}
                </button>
              );
            })}
          </div>
        </section>

        {/* Provider Credentials */}

        <section className="settings-section">
          <div className="settings-section-heading">
            <div>
              <h2>Provider Credentials</h2>

              <p>API keys are encrypted before being stored.</p>
            </div>
          </div>

          <div className="provider-list">
            {providers.map((provider) => {
              const providerName =
                PROVIDER_INFO[provider.provider]?.name || provider.name;

              const connected = provider.connected;

              return (
                <div
                  className={`provider-card ${
                    selectedProvider === provider.provider ? "active" : ""
                  }`}
                  key={provider.provider}
                >
                  <div className="provider-card-header">
                    <div>
                      <h3>{providerName}</h3>

                      <p>{PROVIDER_INFO[provider.provider]?.description}</p>
                    </div>

                    {connected && (
                      <span className="connected-pill">
                        <CheckCircle2 size={15} />
                        Connected
                      </span>
                    )}
                  </div>

                  <div className="provider-form">
                    <label>API Key</label>

                    <div className="api-key-wrapper">
                      <input
                        type={
                          visibleKeys[provider.provider] ? "text" : "password"
                        }
                        value={apiKeys[provider.provider] || ""}
                        onChange={(event) =>
                          handleKeyChange(provider.provider, event.target.value)
                        }
                        placeholder={
                          connected
                            ? `Connected ••••${provider.key_last4}`
                            : "Enter API key"
                        }
                        autoComplete="off"
                      />

                      <button
                        type="button"
                        className="key-visibility-button"
                        onClick={() => toggleKeyVisibility(provider.provider)}
                      >
                        {visibleKeys[provider.provider] ? (
                          <EyeOff size={17} />
                        ) : (
                          <Eye size={17} />
                        )}
                      </button>
                    </div>

                    <label>Model</label>

                    <input
                      type="text"
                      value={
                        models[provider.provider] ??
                        provider.model ??
                        provider.default_model ??
                        ""
                      }
                      onChange={(event) =>
                        handleModelChange(provider.provider, event.target.value)
                      }
                      placeholder={provider.default_model}
                    />

                    <div className="provider-actions">
                      <button
                        type="button"
                        className="settings-primary-button"
                        onClick={() => handleConnect(provider.provider)}
                        disabled={savingProvider === provider.provider}
                      >
                        {savingProvider === provider.provider
                          ? "Saving..."
                          : connected
                            ? "Replace API Key"
                            : "Connect"}
                      </button>

                      {connected && (
                        <button
                          type="button"
                          className="settings-danger-button"
                          onClick={() => handleDisconnect(provider.provider)}
                          disabled={savingProvider === provider.provider}
                        >
                          Disconnect
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Usage */}

        {usage && (
          <section className="settings-section">
            <div className="settings-section-heading">
              <div>
                <h2>AI Usage</h2>

                <p>Track your SmartHire platform allowance.</p>
              </div>
            </div>

            <div className="usage-grid">
              <div className="usage-card">
                <span>Resume Analyses</span>

                <strong>
                  {usage.resume.used}
                  <small>/ {usage.resume.limit}</small>
                </strong>

                <p>{usage.resume.remaining} free remaining</p>
              </div>
            </div>

            {usage.byok?.connected && (
              <div className="byok-info">
                <strong>BYOK enabled</strong>

                <span>
                  You have {usage.byok.providers.length} connected AI provider
                  {usage.byok.providers.length !== 1 ? "s" : ""}.
                </span>
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
