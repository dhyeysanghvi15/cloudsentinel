"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "../../components/api";
import { Button, Card } from "../../components/ui";

type LatestScore = {
  score: number | null;
  scan_id: string | null;
  created_at?: string;
  domain_scores?: Record<string, number>;
};

export default function Dashboard() {
  const [latest, setLatest] = useState<LatestScore>({ score: null, scan_id: null });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function refresh() {
    setErr(null);
    const data = await apiGet<LatestScore>("/api/score/latest");
    setLatest(data);
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

      {err ? (
        <div className="rounded-lg border border-rose-900 bg-rose-950/30 p-3 text-sm text-rose-200">
          {err}
        </div>
      ) : null}

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
        <Card title="Next Actions">
          <ul className="list-disc space-y-2 pl-5 text-sm text-slate-300">
            <li>Review critical failures first (network exposure, root MFA, CloudTrail).</li>
            <li>Use Policy Doctor to harden IAM JSON before deploying.</li>
            <li>Run Attack Simulator to generate CloudTrail telemetry safely.</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}

