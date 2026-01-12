"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "../../components/api";
import { ApiError } from "../../components/api_error";
import { Button, Card } from "../../components/ui";
import { useAppMode } from "../../components/mode";

type LatestScore = {
  score: number | null;
  scan_id: string | null;
  created_at?: string;
  domain_scores?: Record<string, number>;
};

type ScanMeta = {
  scan_id: string;
  created_at: string;
  score: number;
  domain_scores: Record<string, number>;
};

export default function Dashboard() {
  const { mode } = useAppMode();
  const [latest, setLatest] = useState<LatestScore>({ score: null, scan_id: null });
  const [scans, setScans] = useState<ScanMeta[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function refresh() {
    setErr(null);
    const [data, scanList] = await Promise.all([
      apiGet<LatestScore>("/api/score/latest"),
      apiGet<ScanMeta[]>("/api/scans?limit=10"),
    ]);
    setLatest(data);
    setScans(scanList || []);
  }

  async function runScan() {
    setLoading(true);
    setErr(null);
    try {
      await apiPost("/api/scan");
      await refresh();
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh().catch(() => {});
  }, []);

  const domains = useMemo(() => {
    const ds = latest.domain_scores || {};
    return Object.entries(ds).sort((a, b) => b[1] - a[1]);
  }, [latest.domain_scores]);

  const trend = useMemo(() => {
    const scores = (scans || []).slice(0, 6).reverse().map((s) => s.score);
    if (!scores.length) return [];
    const min = Math.min(...scores);
    const max = Math.max(...scores);
    const span = Math.max(1, max - min);
    return scores.map((s) => Math.round(((s - min) / span) * 10));
  }, [scans]);

  return (
    <div className="grid gap-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Security Posture</h1>
          <div className="mt-1 text-sm text-slate-400">
            Latest scan: {latest.scan_id ? `${latest.scan_id} @ ${latest.created_at}` : "none yet"}
          </div>
        </div>
        <Button onClick={runScan} disabled={loading}>
          {loading ? "Scanning…" : "Run Scan"}
        </Button>
      </div>

      {mode === "demo" ? <DemoWhatYoureSeeing /> : null}

      {err ? <ApiError error={err} /> : null}

      <div className="grid gap-6 md:grid-cols-3">
        <Card title="Posture Score (0–100)">
          <div className="text-5xl font-semibold">{latest.score ?? "—"}</div>
          <div className="mt-2 text-xs text-slate-400">Transparent scoring: pass=1, warn=0.5, fail=0.</div>
        </Card>
        <Card title="Top Domains">
          <div className="grid gap-2 text-sm">
            {domains.length ? (
              domains.slice(0, 4).map(([d, s]) => (
                <div key={d} className="flex items-center justify-between">
                  <div className="text-slate-300">{d}</div>
                  <div className="font-medium">{s}</div>
                </div>
              ))
            ) : (
              <div className="text-slate-500">Run your first scan.</div>
            )}
          </div>
        </Card>
        <Card title="Trend (last 6 scans)">
          {trend.length ? (
            <div className="flex items-end gap-1">
              {trend.map((h, i) => (
                <div key={i} className="w-4 rounded bg-indigo-500/70" style={{ height: `${8 + h * 6}px` }} />
              ))}
            </div>
          ) : (
            <div className="text-sm text-slate-500">Run your first scan.</div>
          )}
          <div className="mt-2 text-xs text-slate-400">Compare scans in the Scans view for improvements/regressions.</div>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card title="Top Risks (from latest scan)">
          {latest.scan_id ? (
            <TopRisks scanId={latest.scan_id} />
          ) : (
            <div className="text-sm text-slate-500">Run a scan to populate risks.</div>
          )}
        </Card>
        <Card title="What To Try">
          <ul className="list-disc space-y-2 pl-5 text-sm text-slate-300">
            <li>Run a scan, then compare the last two snapshots.</li>
            <li>Paste a permissive policy in Policy Doctor and see rewrite hints.</li>
            <li>Replay scenarios in Simulator and watch the detection timeline evolve.</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}

function TopRisks({ scanId }: { scanId: string }) {
  const [items, setItems] = useState<
    Array<{ id: string; title: string; severity: string; status: string; recommendation: string }>
  >([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    apiGet<any>(`/api/scans/${scanId}`)
      .then((d) => {
        const results = d?.snapshot?.results || [];
        const rank = (s: string) => (s === "critical" ? 4 : s === "high" ? 3 : s === "medium" ? 2 : 1);
        const top = results
          .filter((r: any) => r.status === "fail" || r.status === "warn")
          .sort((a: any, b: any) => rank(b.severity) - rank(a.severity))
          .slice(0, 6)
          .map((r: any) => ({
            id: r.id,
            title: r.title,
            severity: r.severity,
            status: r.status,
            recommendation: r.recommendation,
          }));
        setItems(top);
      })
      .catch((e) => setErr(String(e)));
  }, [scanId]);

  if (err) return <div className="text-sm text-rose-200">{err}</div>;
  if (!items.length) return <div className="text-sm text-slate-500">No risks detected.</div>;

  return (
    <div className="grid gap-2 text-sm">
      {items.map((r) => (
        <div key={r.id} className="rounded-lg border border-slate-800 bg-slate-950 p-3">
          <div className="flex items-center justify-between gap-4">
            <div className="font-semibold text-white">{r.title}</div>
            <div className="text-xs text-slate-400">
              <span className="font-mono">{r.status}</span> • {r.severity}
            </div>
          </div>
          <div className="mt-2 text-xs text-slate-400">{r.recommendation}</div>
        </div>
      ))}
    </div>
  );
}

function DemoWhatYoureSeeing() {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between text-left"
      >
        <div className="font-medium text-slate-200">What you’re seeing (Demo Mode)</div>
        <div className="text-xs text-slate-400">{open ? "Hide" : "Show"}</div>
      </button>
      {open ? (
        <div className="mt-3 grid gap-2 text-xs text-slate-400">
          <div>
            This UI is fully interactive with bundled sample data (scan history, diffs, policy findings, and a detection
            timeline).
          </div>
          <div>
            Switch to <span className="text-slate-200">Local API</span> in the header to run the real FastAPI backend
            with SQLite persistence on your machine.
          </div>
        </div>
      ) : null}
    </div>
  );
}
