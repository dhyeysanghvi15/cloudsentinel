import { demoGetLatestScore, demoGetScan, demoGetTimeline, demoListScans, demoPolicyValidate, demoRunScan, demoSimulate } from "./demo_store";
import { getStoredApiBaseUrl, getStoredMode } from "./mode";

async function httpGet<T>(baseUrl: string, path: string): Promise<T> {
  const res = await fetch(`${baseUrl}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as T;
}

async function httpPost<T>(baseUrl: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as T;
}

export async function apiGet<T>(path: string): Promise<T> {
  const mode = getStoredMode();
  if (mode === "demo") {
    if (path.startsWith("/api/score/latest")) return (await demoGetLatestScore()) as T;
    if (path.startsWith("/api/scans/")) return (await demoGetScan(path.split("/api/scans/")[1] || "")) as T;
    if (path.startsWith("/api/scans")) return (await demoListScans()) as T;
    if (path.startsWith("/api/timeline")) {
      const u = new URL(`http://x${path}`);
      return (await demoGetTimeline(u.searchParams.get("since"))) as T;
    }
    throw new Error(`Demo Mode has no GET handler for ${path}`);
  }

  return await httpGet<T>(getStoredApiBaseUrl(), path);
}

export async function apiPost<T>(path: string, body?: any): Promise<T> {
  const mode = getStoredMode();
  if (mode === "demo") {
    if (path === "/api/scan") return (await demoRunScan()) as T;
    if (path === "/api/policy/validate") return (await demoPolicyValidate(String(body?.policy_json || ""))) as T;
    if (path.startsWith("/api/simulate/cleanup")) return (await demoSimulate("cleanup")) as T;
    if (path.startsWith("/api/simulate/")) {
      const scenario = path.split("/api/simulate/")[1] || "unknown";
      return (await demoSimulate(scenario)) as T;
    }
    throw new Error(`Demo Mode has no POST handler for ${path}`);
  }

  return await httpPost<T>(getStoredApiBaseUrl(), path, body);
}

