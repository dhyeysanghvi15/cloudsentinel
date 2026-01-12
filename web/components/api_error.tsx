"use client";

import { setMode, useAppMode } from "./mode";

export function ApiError({ error }: { error: string }) {
  const { mode } = useAppMode();
  if (!error) return null;

  return (
    <div className="rounded-lg border border-rose-900 bg-rose-950/30 p-3 text-sm text-rose-200">
      <div className="flex items-center justify-between gap-4">
        <div className="truncate">{error}</div>
        {mode !== "demo" ? (
          <button
            onClick={() => setMode("demo")}
            className="shrink-0 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-500"
          >
            Switch to Demo Mode
          </button>
        ) : null}
      </div>
    </div>
  );
}

