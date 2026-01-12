"use client";

import { useState } from "react";
import { apiPost } from "../../components/api";
import { Button, Card, Textarea } from "../../components/ui";

type Finding = { severity: "error" | "warning" | "suggestion"; message: string; why: string; hint?: string | null };
type Resp = { mode: "access-analyzer" | "local"; findings: Finding[] };

const starter = `{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": ["arn:aws:s3:::example-bucket"]
    }
  ]
}`;

export default function PolicyDoctor() {
  const [policy, setPolicy] = useState(starter);
  const [resp, setResp] = useState<Resp | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function validate() {
    setLoading(true);
    setErr(null);
    setResp(null);
    try {
      const data = await apiPost<Resp>("/api/policy/validate", { policy_json: policy, policy_type: "IDENTITY_POLICY" });
      setResp(data);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold">IAM Policy Doctor</h1>
        <div className="mt-1 text-sm text-slate-400">Paste policy JSON; get validation + rewrite hints.</div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card title="Policy JSON">
          <Textarea value={policy} onChange={(e) => setPolicy(e.target.value)} rows={18} />
          <div className="mt-3">
            <Button onClick={validate} disabled={loading}>
              {loading ? "Validating…" : "Validate"}
            </Button>
          </div>
          {err ? <div className="mt-3 text-sm text-rose-200">{err}</div> : null}
        </Card>

        <Card title="Findings">
          {resp ? (
            <div className="grid gap-3 text-sm">
              <div className="text-xs text-slate-400">
                Mode: <span className="font-mono text-slate-200">{resp.mode}</span>
              </div>
              {resp.findings.map((f, idx) => (
                <div key={idx} className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                  <div className="flex items-center justify-between">
                    <div className="font-semibold">{f.message}</div>
                    <div className="text-xs uppercase tracking-wide text-slate-400">{f.severity}</div>
                  </div>
                  <div className="mt-2 text-xs text-slate-400">{f.why}</div>
                  {f.hint ? <div className="mt-2 text-xs text-indigo-200">{f.hint}</div> : null}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-slate-500">Validate a policy to see findings.</div>
          )}
        </Card>
      </div>
    </div>
  );
}

