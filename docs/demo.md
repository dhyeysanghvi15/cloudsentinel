# Demo Script (Recruiter-friendly)

## 1) Local (2 minutes)
1. `cp .env.example .env`
2. `make dev` (API + DynamoDB local)
3. In another terminal: `make web`
4. Open `http://localhost:3000`

## 2) Posture Scanner
1. Go to Dashboard → click **Run Scan**
2. Open Scans → compare two scans to see diff

## 3) IAM Policy Doctor
1. Open Policy Doctor → paste a policy
2. Click **Validate** → review findings and hints

## 4) Attack Simulator (safe)
1. Open Simulator
2. Set `since` to 5 minutes ago
3. Run:
   - **Create IAM User + Inline Policy**
   - **Attempt S3 Public ACL (revert)**
4. Refresh Timeline → review CloudTrail events
5. Click **Cleanup Lab Resources**

## 5) Record a GIF (optional)
- macOS: `Cmd+Shift+5` → record window
- Save as `docs/demo.gif` and embed in `README.md`

