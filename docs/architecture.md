# Architecture

cloudsentinel is a **local-first cloud security lab** with two runtime modes:

- **Demo Mode (GitHub Pages):** zero backend, realistic bundled JSON data, interactive UI.
- **Local Mode (localhost):** FastAPI backend + SQLite storage for full functionality.

## High-level

```mermaid
flowchart LR
  U[User Browser] --> WEB[GitHub Pages\nStatic Next.js export]

  subgraph Demo[Demo Mode (default on Pages)]
    WEB --> DEMO[Bundled demo JSON\nweb/public/demo/*]
    WEB --> LS[(localStorage\nmode + demo state)]
  end

  subgraph Local[Local Mode (full features)]
    WEB -->|HTTP| API[FastAPI\nlocalhost:8000]
    API --> DB[(SQLite\n./data/cloudsentinel.db)]
    API --> TL[(Timeline events\nstored locally)]
  end

  subgraph Optional[Optional: Read-only AWS scan]
    API -->|boto3 read-only| AWS[(Your AWS account)]
  end
```

## Data flow (what feels “real”)

- **CSPM scans:** Snapshot checks → score + breakdown → stored as scan history for diffs.
- **Detections timeline:** Simulator writes events → UI queries timeline → replay scenarios.
- **Policy Doctor:** Paste IAM JSON → findings + rewrite hints (local heuristics by default).

## $0 AWS bill guarantee

- The repo does **not** deploy infrastructure and does **not** create AWS resources.
- `AWS_SCAN_ENABLED=false` by default; enabling it is optional and intended for **read-only** checks only.
