"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../../components/api";
import { Button, Card, Input } from "../../components/ui";

type TimelineItem = {
  eventTime?: string | null;
  eventName?: string | null;
  eventSource?: string | null;
  username?: string | null;
  resources?: Array<{ ResourceName?: string; ResourceType?: string }>;
};

export default function Simulator() {
  const [since, setSince] = useState<string>(() => new Date(Date.now() - 60 * 60 * 1000).toISOString());
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [op, setOp] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function run(scenario: string) {
    setErr(null);
    setLoading(true);
    try {
      const r = await apiPost<{ operation_id: string }>(`/api/simulate/${scenario}`);
      setOp(r.operation_id);
      await loadTimeline();
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function cleanup() {
    setErr(null);
    setLoading(true);
    try {
      await apiPost(`/api/simulate/cleanup`);
      await loadTimeline();
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function loadTimeline() {
    const r = await apiGet<{ items: TimelineItem[] }>(`/api/timeline?since=${encodeURIComponent(since)}`);
    setTimeline(r.items);
  }

  useEffect(() => {
    loadTimeline().catch(() => {});
  }, []);

  return (
    <div className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Attack Simulator (Detections Lab)</h1>
        <div className="mt-1 text-sm text-slate-400">
          Demo Mode replays a realistic timeline locally. Local Mode runs a localhost-only simulator + timeline store.
        </div>
      </div>

      {err ? (
        <div className="rounded-lg border border-rose-900 bg-rose-950/30 p-3 text-sm text-rose-200">{err}</div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        <Card title="Scenarios">
          <div className="grid gap-2">
            <Button onClick={() => run("iam-user")} disabled={loading}>
              Create IAM User + Inline Policy
            </Button>
            <Button onClick={() => run("s3-public-acl")} disabled={loading}>
              Attempt S3 Public ACL (revert)
            </Button>
            <Button onClick={() => run("admin-attach-attempt")} disabled={loading}>
              Admin Attach Attempt (opt-in)
            </Button>
            <div className="pt-2">
              <Button onClick={cleanup} disabled={loading}>
                Cleanup Lab Resources
              </Button>
            </div>
          </div>
          {op ? <div className="mt-3 text-xs text-slate-400">Last op: {op}</div> : null}
        </Card>

        <Card title="Timeline Window (ISO8601)">
          <Input value={since} onChange={(e) => setSince(e.target.value)} />
          <div className="mt-3 flex gap-2">
            <Button onClick={loadTimeline} disabled={loading}>
              Refresh Timeline
            </Button>
          </div>
          <div className="mt-3 text-xs text-slate-400">
            Tip: set `since` to a few minutes ago before running a scenario.
          </div>
        </Card>

        <Card title="Recent CloudTrail Events">
          <div className="grid gap-2 text-xs">
            {timeline.length ? (
              timeline.map((t, idx) => (
                <div key={idx} className="rounded-lg border border-slate-800 bg-slate-950 p-2">
                  <div className="font-medium text-slate-200">{t.eventName}</div>
                  <div className="text-slate-500">
                    {t.eventTime} — {t.eventSource} — {t.username}
                  </div>
                  <div className="mt-1 text-slate-400">
                    {(t.resources || []).map((r, i) => (
                      <div key={i}>{r.ResourceName}</div>
                    ))}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-slate-500">No events found for the prefix.</div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
