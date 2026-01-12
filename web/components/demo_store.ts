"use client";

import type { AppMode } from "./mode";
import { getSiteBasePath } from "./mode";

type ScanMeta = {
  scan_id: string;
  created_at: string;
  score: number;
  domain_scores: Record<string, number>;
};

type CheckResult = {
  id: string;
  title: string;
  severity: string;
  status: string;
  domain: string;
  recommendation: string;
  evidence: unknown;
};

type ScanDetail = {
  meta: ScanMeta;
  snapshot: {
    scan_id: string;
    created_at: string;
    score: number;
    breakdown: unknown;
    results: CheckResult[];
  } | null;
};

type TimelineItem = {
  eventTime?: string | null;
  eventName?: string | null;
  eventSource?: string | null;
  username?: string | null;
  resources?: Array<{ ResourceName?: string; ResourceType?: string }>;
};

const LS_SCANS = "cloudsentinel.demo.scans";
const LS_SCAN_DETAILS = "cloudsentinel.demo.scanDetails";
const LS_TIMELINE = "cloudsentinel.demo.timeline";

async function fetchJson<T>(path: string): Promise<T> {
  const base = getSiteBasePath();
  const res = await fetch(`${base}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as T;
}

function safeParse<T>(raw: string | null): T | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

function safeRead<T>(key: string): T | null {
  try {
    return safeParse<T>(localStorage.getItem(key));
  } catch {
    return null;
  }
}

function safeWrite<T>(key: string, value: T) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // ignore
  }
}

export async function demoGetLatestScore(): Promise<{
  score: number | null;
  scan_id: string | null;
  created_at?: string;
  domain_scores?: Record<string, number>;
}> {
  const scans = await demoListScans();
  const latest = scans[0];
  if (!latest) return { score: null, scan_id: null };
  return {
    score: latest.score,
    scan_id: latest.scan_id,
    created_at: latest.created_at,
    domain_scores: latest.domain_scores,
  };
}

export async function demoListScans(): Promise<ScanMeta[]> {
  const stored = safeRead<ScanMeta[]>(LS_SCANS);
  if (stored?.length) return stored;

  const seed = await fetchJson<ScanMeta[]>("/demo/demo_scans.json");
  safeWrite(LS_SCANS, seed);
  return seed;
}

export async function demoGetScan(scanId: string): Promise<ScanDetail> {
  const map = safeRead<Record<string, ScanDetail>>(LS_SCAN_DETAILS) || {};
  if (map[scanId]) return map[scanId]!;

  const seed = await fetchJson<ScanDetail>(`/demo/demo_scan_${encodeURIComponent(scanId)}.json`);
  map[scanId] = seed;
  safeWrite(LS_SCAN_DETAILS, map);
  return seed;
}

function flipStatus(status: string): string {
  if (status === "fail") return "warn";
  if (status === "warn") return "pass";
  if (status === "pass") return "warn";
  return status;
}

export async function demoRunScan(): Promise<{ scan_id: string }> {
  const scans = await demoListScans();
  const latestId = scans[0]?.scan_id;
  const latest = latestId ? await demoGetScan(latestId) : null;

  const scan_id = `demo-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "")}-${Math.floor(
    Math.random() * 1000,
  )
    .toString()
    .padStart(3, "0")}`;
  const created_at = new Date().toISOString();

  const baseSnapshot = latest?.snapshot;
  const results = (baseSnapshot?.results || []).map((r, idx) => {
    if (idx % 4 === 0) return { ...r, status: flipStatus(r.status) };
    return r;
  });

  const pass = results.filter((r) => r.status === "pass").length;
  const warn = results.filter((r) => r.status === "warn").length;
  const fail = results.filter((r) => r.status === "fail").length;
  const score = Math.max(0, Math.min(100, Math.round((pass * 1 + warn * 0.5) / Math.max(1, pass + warn + fail) * 100)));

  const domain_scores: Record<string, number> = {};
  for (const r of results) {
    const d = r.domain || "Other";
    const prev = domain_scores[d] ?? 100;
    if (r.status === "fail") domain_scores[d] = Math.min(prev, 60);
    else if (r.status === "warn") domain_scores[d] = Math.min(prev, 85);
  }
  for (const k of Object.keys(domain_scores)) domain_scores[k] = Math.max(0, Math.min(100, domain_scores[k]!));

  const meta: ScanMeta = { scan_id, created_at, score, domain_scores };
  const detail: ScanDetail = {
    meta,
    snapshot: {
      scan_id,
      created_at,
      score,
      breakdown: { domain_scores, status_counts: { pass, warn, fail } },
      results,
    },
  };

  const newScans = [meta, ...scans].slice(0, 25);
  safeWrite(LS_SCANS, newScans);
  const map = safeRead<Record<string, ScanDetail>>(LS_SCAN_DETAILS) || {};
  map[scan_id] = detail;
  safeWrite(LS_SCAN_DETAILS, map);

  return { scan_id };
}

function seedEventsForScenario(scenario: string): TimelineItem[] {
  const now = new Date();
  const t = (ms: number) => new Date(now.getTime() + ms).toISOString();
  const prefix = "cloudsentinel-sim-";
  if (scenario === "iam-user") {
    return [
      {
        eventTime: t(0),
        eventName: "CreateUser",
        eventSource: "iam.amazonaws.com",
        username: "demo-user",
        resources: [{ ResourceName: `${prefix}user-demo`, ResourceType: "AWS::IAM::User" }],
      },
      {
        eventTime: t(800),
        eventName: "PutUserPolicy",
        eventSource: "iam.amazonaws.com",
        username: "demo-user",
        resources: [{ ResourceName: `${prefix}user-demo`, ResourceType: "AWS::IAM::User" }],
      },
    ];
  }
  if (scenario === "s3-public-acl") {
    return [
      {
        eventTime: t(0),
        eventName: "CreateBucket",
        eventSource: "s3.amazonaws.com",
        username: "demo-user",
        resources: [{ ResourceName: `${prefix}bucket-demo`, ResourceType: "AWS::S3::Bucket" }],
      },
      {
        eventTime: t(1200),
        eventName: "PutBucketAcl",
        eventSource: "s3.amazonaws.com",
        username: "demo-user",
        resources: [{ ResourceName: `${prefix}bucket-demo`, ResourceType: "AWS::S3::Bucket" }],
      },
    ];
  }
  if (scenario === "admin-attach-attempt") {
    return [
      {
        eventTime: t(0),
        eventName: "AttachUserPolicy",
        eventSource: "iam.amazonaws.com",
        username: "demo-user",
        resources: [{ ResourceName: `${prefix}user-demo`, ResourceType: "AWS::IAM::User" }],
      },
    ];
  }
  return [
    { eventTime: t(0), eventName: "Replay", eventSource: "cloudsentinel.local", username: "demo-user", resources: [] },
  ];
}

export async function demoInitTimeline(): Promise<{ items: TimelineItem[] }> {
  const stored = safeRead<{ items: TimelineItem[] }>(LS_TIMELINE);
  if (stored?.items?.length) return stored;
  const seed = await fetchJson<{ items: TimelineItem[] }>("/demo/demo_timeline.json");
  safeWrite(LS_TIMELINE, seed);
  return seed;
}

export async function demoGetTimeline(sinceIso?: string | null): Promise<{ items: TimelineItem[] }> {
  const t = await demoInitTimeline();
  if (!sinceIso) return t;
  const since = Date.parse(sinceIso);
  if (!Number.isFinite(since)) return t;
  return { items: (t.items || []).filter((i) => (i.eventTime ? Date.parse(i.eventTime) >= since : true)) };
}

export async function demoSimulate(scenario: string): Promise<{ operation_id: string }> {
  const op = `demo-op-${Date.now()}`;
  if (scenario === "cleanup") {
    const seed = await fetchJson<{ items: TimelineItem[] }>("/demo/demo_timeline.json");
    safeWrite(LS_TIMELINE, seed);
    return { operation_id: op };
  }

  const t = await demoInitTimeline();
  const items = [...(t.items || []), ...seedEventsForScenario(scenario)].slice(-200);
  safeWrite(LS_TIMELINE, { items });
  return { operation_id: op };
}

export async function demoPolicyValidate(policy_json: string): Promise<{
  mode: "local";
  findings: Array<{ severity: "error" | "warning" | "suggestion"; message: string; why: string; hint?: string | null }>;
}> {
  // Seed file exists for realism; validation here is deterministic and local-only.
  await fetchJson("/demo/demo_policy_validate_examples.json").catch(() => null);

  let parsed: unknown;
  try {
    parsed = JSON.parse(policy_json);
  } catch (e) {
    return {
      mode: "local",
      findings: [
        {
          severity: "error",
          message: "Invalid JSON.",
          why: "IAM policies must be valid JSON to be evaluated.",
          hint: String((e as { message?: unknown } | null)?.message || e),
        },
      ],
    };
  }

  const findings: Array<{
    severity: "error" | "warning" | "suggestion";
    message: string;
    why: string;
    hint?: string | null;
  }> = [];

  const doc = parsed as { Version?: unknown; Statement?: unknown };
  const version = doc.Version;
  if (version !== "2012-10-17" && version !== "2008-10-17") {
    findings.push({
      severity: "warning",
      message: "Policy Version is missing or unusual.",
      why: "Using a standard version avoids evaluation surprises.",
      hint: 'Set `"Version": "2012-10-17"`.',
    });
  }

  const stmtsRaw = doc.Statement;
  if (!stmtsRaw) {
    return {
      mode: "local",
      findings: [
        {
          severity: "error",
          message: "Policy has no Statement.",
          why: "Policies must contain at least one statement.",
          hint: 'Add a `"Statement": [...]` array.',
        },
      ],
    };
  }
  const stmts: unknown[] = Array.isArray(stmtsRaw) ? stmtsRaw : [stmtsRaw];

  const isStar = (v: unknown) => v === "*" || (Array.isArray(v) && v.some((x) => x === "*"));

  for (const s of stmts) {
    const stmt = s as { Effect?: unknown; Action?: unknown; Resource?: unknown; Condition?: unknown };
    if (stmt.Effect !== "Allow" && stmt.Effect !== "Deny") {
      findings.push({
        severity: "error",
        message: "Statement Effect must be Allow or Deny.",
        why: "Invalid effects can make policies fail validation or be ignored.",
        hint: "Use Effect: Allow or Deny.",
      });
    }
    if (isStar(stmt.Action)) {
      findings.push({
        severity: "warning",
        message: "Statement uses Action '*'.",
        why: "Wildcard actions often grant unintended permissions across services.",
        hint: "Replace '*' with specific actions and add conditions where possible.",
      });
    }
    if (isStar(stmt.Resource)) {
      findings.push({
        severity: "warning",
        message: "Statement uses Resource '*'.",
        why: "Resource wildcards can unintentionally expand access beyond intended targets.",
        hint: "Scope Resource to specific ARNs, and add conditions.",
      });
    }
    if (stmt.Effect === "Allow" && !stmt.Condition) {
      findings.push({
        severity: "suggestion",
        message: "Consider adding conditions (MFA, source IP, tags).",
        why: "Conditions reduce blast radius even if identities are compromised.",
        hint: "Add Condition with aws:MultiFactorAuthPresent, aws:SourceIp, aws:RequestTag, etc.",
      });
    }
  }

  if (!findings.length) {
    findings.push({
      severity: "suggestion",
      message: "No issues detected in the demo validator.",
      why: "The policy looks syntactically correct and reasonably scoped.",
      hint: "Still review for least privilege and add conditions.",
    });
  }

  // De-dup common repeated suggestions for multi-statement policies.
  const seen = new Set<string>();
  return {
    mode: "local",
    findings: findings.filter((f) => {
      const k = `${f.severity}:${f.message}`;
      if (seen.has(k)) return false;
      seen.add(k);
      return true;
    }),
  };
}

export function isDemoMode(mode: AppMode): boolean {
  return mode === "demo";
}
