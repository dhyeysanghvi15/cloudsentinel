"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet } from "../../components/api";
import { Card } from "../../components/ui";

type ScanMeta = {
  scan_id: string;
  created_at: string;
  score: number;
  domain_scores: Record<string, number>;
};

type ScanDetail = {
  meta: ScanMeta;
  snapshot: {
    scan_id: string;
    created_at: string;
    score: number;
    breakdown: any;
    results: Array<{
      id: string;
      title: string;
      severity: string;
      status: string;
      domain: string;
      recommendation: string;
      evidence: any;
    }>;
  } | null;
};

export default function Scans() {
  const [scans, setScans] = useState<ScanMeta[]>([]);
  const [a, setA] = useState<string>("");
  const [b, setB] = useState<string>("");
  const [detailA, setDetailA] = useState<ScanDetail | null>(null);
  const [detailB, setDetailB] = useState<ScanDetail | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function refresh() {
    const data = await apiGet<ScanMeta[]>("/api/scans?limit=25");
    setScans(data);
    setA((prev) => prev || data?.[0]?.scan_id || "");
    setB((prev) => prev || data?.[1]?.scan_id || "");
  }

  useEffect(() => {
    refresh().catch((e) => setErr(String(e)));
  }, []);

  useEffect(() => {
    if (!a) return;
    apiGet<ScanDetail>(`/api/scans/${a}`)
      .then(setDetailA)
      .catch((e) => setErr(String(e)));
  }, [a]);

  useEffect(() => {
    if (!b) return;
    apiGet<ScanDetail>(`/api/scans/${b}`)
      .then(setDetailB)
      .catch((e) => setErr(String(e)));
  }, [b]);

  const diff = useMemo(() => {
    const ra = detailA?.snapshot?.results || [];
    const rb = detailB?.snapshot?.results || [];
    const mapA = new Map(ra.map((r) => [r.id, r]));
    const changes: Array<{ id: string; title: string; from?: string; to?: string; severity: string }> = [];
    for (const r of rb) {
      const before = mapA.get(r.id);
      if (!before) continue;
      if (before.status !== r.status) {
        changes.push({ id: r.id, title: r.title, from: before.status, to: r.status, severity: r.severity });
      }
    }
    return changes;
  }, [detailA, detailB]);

  return (
    <div className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Scans</h1>
        <div className="mt-1 text-sm text-slate-400">Compare scans to see improvements/regressions.</div>
      </div>

      {err ? (
        <div className="rounded-lg border border-rose-900 bg-rose-950/30 p-3 text-sm text-rose-200">
          {err}
        </div>
      ) : null}

      <div className="grid gap-6 md:grid-cols-2">
        <Card title="Select Scan A">
          <select
            value={a}
            onChange={(e) => setA(e.target.value)}
            className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm"
          >
            {scans.map((s) => (
              <option key={s.scan_id} value={s.scan_id}>
                {s.scan_id} — {s.score} — {s.created_at}
              </option>
            ))}
          </select>
        </Card>
        <Card title="Select Scan B">
          <select
            value={b}
            onChange={(e) => setB(e.target.value)}
            className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm"
          >
            {scans.map((s) => (
              <option key={s.scan_id} value={s.scan_id}>
                {s.scan_id} — {s.score} — {s.created_at}
              </option>
            ))}
          </select>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card title="Diff (A → B)">
          {diff.length ? (
            <div className="grid gap-2 text-sm">
              {diff.map((c) => (
                <div key={c.id} className="flex items-center justify-between gap-4">
                  <div className="text-slate-300">
                    <div className="font-medium text-white">{c.title}</div>
                    <div className="text-xs text-slate-500">{c.id}</div>
                  </div>
                  <div className="text-right text-xs text-slate-400">
                    <div>
                      {c.from} → <span className="text-white">{c.to}</span>
                    </div>
                    <div>{c.severity}</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-slate-500">No changes detected (or select two scans).</div>
          )}
        </Card>

        <Card title="Latest Scan Snapshot">
          {detailB?.snapshot ? (
            <div className="text-sm">
              <div className="mb-2 text-slate-300">
                Score: <span className="font-semibold text-white">{detailB.snapshot.score}</span>
              </div>
              <div className="grid gap-1 text-xs text-slate-400">
                {(detailB.snapshot.results || []).slice(0, 8).map((r) => (
                  <div key={r.id} className="flex items-center justify-between gap-4">
                    <div className="truncate">{r.title}</div>
                    <div className="font-mono">{r.status}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-sm text-slate-500">Select a scan.</div>
          )}
        </Card>
      </div>
    </div>
  );
}
