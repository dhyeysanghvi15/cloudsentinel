"use client";

import { useAppMode } from "./mode";

export function DemoBanner() {
  const { mode } = useAppMode();
  if (mode !== "demo") return null;
  return (
    <div className="rounded-lg border border-amber-900 bg-amber-950/30 px-4 py-2 text-sm text-amber-200">
      Demo Mode: bundled sample data. Run locally for full features.
    </div>
  );
}
