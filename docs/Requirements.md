# CIRT DFIR Platform Requirements (Initial Draft)

## 1. Scope
Build a modular digital-forensics and incident-response platform. Initial production target: authorized Windows endpoint triage and evidence handling. Other operating systems and mobile workflows require separately validated acquisition modules.

## 2. Functional requirements
- Create and manage cases with authority, scope, severity, assignment and lifecycle status.
- Register endpoint assets and associate them with cases.
- Define approved scan profiles and targeted collection scopes.
- Display requested scope, exclusions, privileges and expected impact before a scan.
- Track scan job status, timestamps, errors, skipped items and actual collected artifacts.
- Produce a manifest with scanner version, source context, collection scope, timestamps, file sizes and SHA-256 hashes.
- Ingest evidence packages through a bounded, authenticated workflow.
- Verify evidence integrity and record custody events.
- Record findings, confidence, disposition and analyst notes.
- Propose and approve containment, eradication and recovery actions with an audit trail.
- Generate case summaries, evidence registers, scan reports and custody reports.
- Support offline operation and controlled import/export.
- Support intranet deployment over HTTPS and a separately secured hosted deployment.

## 3. Security requirements
- MFA for privileged accounts and role-based authorization.
- Case/object-level authorization on every API operation.
- Signed scanner releases and verified updates.
- No embedded permanent server secrets in scanner binaries.
- Bounded uploads, request deadlines, quotas and safe staging.
- Filesystem containment against traversal, junctions/reparse points and concurrent path changes.
- Exclusive creation and preservation of pre-existing evidence.
- Atomic finalization and explicit cleanup ownership.
- Audit records for access, evidence operations, approvals and response actions.
- Encryption in transit and at rest, tested backups and restoration.
- Dependency pinning, vulnerability review and SBOM generation.

## 4. Evidence requirements
- Preserve received originals.
- Verify hashes at ingestion and after storage.
- Separate original packages from derived files.
- Record provenance, collection limitations and custody changes.
- Restrict deletion and retention changes.
- Never claim a hash alone proves authenticity or acquisition completeness.

## 5. Usability requirements
- Responsive enterprise dashboard with clear navigation.
- Accessible status labels and readable tables.
- Clear distinction between real, partial, failed and simulated results.
- Explicit confirmation for sensitive or disruptive actions.
- Search and filtering for cases, assets, findings and evidence.
- User manual and administrator manual aligned with the released version.

## 6. Acceptance gates
- Existing source is preserved and baseline hashes are recorded.
- P1 filesystem-containment issue is independently reviewed and resolved.
- Authentication and authorization tests pass.
- Synthetic upload, traversal, junction, concurrency and cleanup tests pass.
- Evidence integrity and custody records are verifiable.
- Offline/intranet deployment and backup restoration are demonstrated.
- Security review and CIRT owner approval are recorded.

## 7. Out of scope for the initial prototype
- Live endpoint scanning.
- Evidence upload or storage.
- Authentication or real user accounts.
- Production database and backend API.
- Automated containment, process termination or deletion.
- Claims of complete disk or mobile acquisition.
