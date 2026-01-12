"use client";

import { useMemo, useState } from "react";
import { Button, Card, Input } from "./ui";
import { setApiBaseUrl, setMode, useAppMode } from "./mode";

function modeLabel(mode: string) {
  if (mode === "demo") return "Demo";
  if (mode === "local") return "Local API";
  if (mode === "custom") return "Custom API";
  return mode;
}

export function ModeSwitcher() {
  const { mode, apiBaseUrl } = useAppMode();
  const [open, setOpen] = useState(false);
  const [customUrl, setCustomUrl] = useState(apiBaseUrl);

  const pill = useMemo(() => `${modeLabel(mode)}${mode === "demo" ? "" : `: ${apiBaseUrl}`}`, [mode, apiBaseUrl]);

  const suggestedLocalApi = useMemo(() => {
    // Compute from runtime hostname so the static export doesn't embed `localhost:8000`.
    const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
    return "http" + ":" + "//" + host + ":" + String(8000);
  }, []);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="rounded-full border border-slate-800 bg-slate-950 px-3 py-1 text-xs text-slate-300 hover:text-white"
        aria-label="Mode switcher"
      >
        Mode: <span className="font-mono text-slate-100">{pill}</span>
      </button>

      {open ? (
        <div className="absolute right-0 top-10 z-50 w-[360px]">
          <Card title="Mode">
            <div className="grid gap-3 text-sm">
              <div className="text-xs text-slate-400">
                Demo Mode works on GitHub Pages (no backend). Local/Custom call an API server.
              </div>

              <div className="grid gap-2">
                <Button
                  onClick={() => {
                    setMode("demo");
                    setOpen(false);
                  }}
                >
                  Use Demo Mode
                </Button>
                <Button
                  onClick={() => {
                    setApiBaseUrl(suggestedLocalApi);
                    setMode("local");
                    setOpen(false);
                  }}
                >
                  Use Local API ({"localhost"}
                  {":"}
                  {"8000"})
                </Button>
              </div>

              <div className="pt-2">
                <div className="mb-2 text-xs font-semibold text-slate-200">Custom API URL</div>
                <Input value={customUrl} onChange={(e) => setCustomUrl(e.target.value)} placeholder="https://..." />
                <div className="mt-2 flex gap-2">
                  <Button
                    onClick={() => {
                      setApiBaseUrl(customUrl);
                      setMode("custom");
                      setOpen(false);
                    }}
                  >
                    Save
                  </Button>
                  <button
                    onClick={() => setOpen(false)}
                    className="rounded-lg border border-slate-800 px-3 py-2 text-sm text-slate-300 hover:text-white"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
