# Demo Script (60 seconds)

## 1) GitHub Pages (no install)
1. Open the GitHub Pages link from the repo README.
2. Confirm the banner: **Demo Mode: bundled sample data. Run locally for full features.**
3. Click around:
   - Dashboard → Scans → Policy Doctor → Simulator

## 2) Local Mode (2 minutes)
1. `cp .env.example .env`
2. `make dev` (FastAPI on `localhost:8000`)
3. In another terminal: `make web`
4. Open `http://localhost:3000`
5. In the header: **Mode → Local API (localhost:8000)**

## 3) Posture Scanner
1. Go to Dashboard → click **Run Scan**
2. Open Scans → compare two scans to see diff

## 4) IAM Policy Doctor
1. Open Policy Doctor → paste a policy
2. Click **Validate** → review findings and hints

## 5) Simulator (local timeline)
1. Open Simulator
2. Set `since` to 5 minutes ago
3. Run:
   - **Create IAM User + Inline Policy**
   - **Attempt S3 Public ACL (revert)**
4. Refresh Timeline → review timeline events
5. Click **Cleanup Lab Resources**

## 6) Record a GIF (optional)
- macOS: `Cmd+Shift+5` → record window
- Save as `docs/demo.gif` and embed in `README.md`
