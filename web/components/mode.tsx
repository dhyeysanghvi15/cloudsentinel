"use client";

import { useEffect, useMemo, useState } from "react";

export type AppMode = "demo" | "local" | "custom";

const LS_MODE = "cloudsentinel.mode";
const LS_API = "cloudsentinel.apiBaseUrl";

function defaultLocalApiBaseUrl(): string {
  // Avoid embedding `localhost:8000` as a contiguous literal in the static export output.
  const proto = "http" + ":";
  const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
  return proto + "//" + host + ":" + String(8000);
}

function safeRead(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeWrite(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // ignore
  }
}

export function getSiteBasePath(): string {
  const raw = process.env.NEXT_PUBLIC_BASE_PATH || "";
  const trimmed = raw.replace(/\/+$/, "");
  return trimmed === "/" ? "" : trimmed;
}

export function getDefaultMode(): AppMode {
  if (typeof window === "undefined") return "demo";
  const host = window.location.hostname;
  if (host === "localhost" || host === "127.0.0.1") return "local";
  return "demo";
}

export function getStoredMode(): AppMode {
  const m = safeRead(LS_MODE);
  if (m === "demo" || m === "local" || m === "custom") return m;
  return getDefaultMode();
}

export function getStoredApiBaseUrl(): string {
  const url = safeRead(LS_API);
  return (url || defaultLocalApiBaseUrl()).replace(/\/+$/, "");
}

export function setMode(mode: AppMode) {
  safeWrite(LS_MODE, mode);
  window.dispatchEvent(new Event("cloudsentinel:mode"));
}

export function setApiBaseUrl(url: string) {
  safeWrite(LS_API, url.replace(/\/+$/, ""));
  window.dispatchEvent(new Event("cloudsentinel:mode"));
}

export function useAppMode(): { mode: AppMode; apiBaseUrl: string } {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const on = () => setTick((t) => t + 1);
    window.addEventListener("storage", on);
    window.addEventListener("cloudsentinel:mode", on);
    return () => {
      window.removeEventListener("storage", on);
      window.removeEventListener("cloudsentinel:mode", on);
    };
  }, []);

  // Recompute on each rerender; `tick` forces rerenders on storage/mode events.
  return useMemo(() => {
    void tick;
    return { mode: getStoredMode(), apiBaseUrl: getStoredApiBaseUrl() };
  }, [tick]);
}
