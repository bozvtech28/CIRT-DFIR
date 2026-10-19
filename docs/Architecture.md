# CIRT DFIR Platform Architecture (Proposed)

## Purpose
Provide a modular platform for authorized digital-forensics collection and the incident-response lifecycle: preparation, detection and analysis, containment, eradication, recovery, and post-incident review.

## Main workspaces
1. **Endpoint Scanner** — separately packaged and signed endpoint collection application.
2. **DFIR Web Platform** — frontend dashboard, backend API, case management, evidence intake, findings, reporting, and response workflow.

## Target technology stack
- Frontend: React + TypeScript + Vite; Tailwind CSS and a component library such as shadcn/ui.
- Backend: Python + FastAPI + Pydantic.
- Metadata database: PostgreSQL.
- Evidence object storage: S3-compatible storage such as MinIO.
- Optional job queue: Redis + Celery.
- Windows scanner: C# / .NET LTS, signed executable.
- Existing PowerShell/Python tools: reuse only after code review and acceptance testing.
- Deployment: Docker Compose for server services; signed Windows installer for scanner.
- Testing: unit, API integration, UI, security and Windows VM tests.
- Supply chain: pinned dependencies, SBOM, signed release artifacts and release hashes.

## Trust boundaries
- Browser users never receive database or object-storage credentials.
- Endpoint scanners use enrolled identities and short-lived, revocable credentials.
- Case-level authorization is enforced by the backend on every sensitive object.
- Evidence objects are separate from searchable metadata.
- Original packages are preserved; derived artifacts are identified separately.
- Response actions that can disrupt a system require policy checks and approval.
- Offline imports use a controlled verification workflow.

## Deployment modes
### Offline
Local API, database and evidence storage; signed update bundles and controlled export/import.
### Intranet
Internal server over HTTPS, restricted subnets, authenticated uploads and tested backups.
### Hosted
TLS, MFA, private management access, monitoring, retention controls and disaster recovery.

## Evidence ingestion requirements
Use bounded streaming, request deadlines, size and member quotas, private staging, safe path handling, atomic finalization, explicit cleanup ownership, server-side hash verification and audit events. Do not rely on final-component-only path checks. Resolve and independently review the current Case Manager P1 filesystem-containment issue before production integration.

## Known project gate
The current native review prototype accepted a path through a parent junction in a synthetic test. The P1 containment issue remains OPEN. The prototype is not a production security fix.

## Prototype status
The initial frontend is a standalone HTML/CSS/JavaScript mock-up with fictional data. It has no API, authentication, scanner, database, upload or response-action integration.
