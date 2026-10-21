# CIRT-DFIR Phase Automation Runbook

**Authority:** `main` only  
**Related ledger:** [PHASE_PROGRESS.md](PHASE_PROGRESS.md)  
**Current production status:** development scaffold; security gates remain open  
**Last reviewed:** 2026-10-19

## Goal

Use a bounded, repeatable process to advance each phase that can be safely completed from verified repository evidence. This runbook is intentionally not a workflow that blindly copies backups, changes identity configuration automatically, executes endpoint collection, triggers CI, or pushes around repository protections.

## Phase state machine

A phase must use one of these states:

- **UNVERIFIED** — the phase's goal/acceptance evidence is not established.
- **READY** — scope, source of truth, preconditions and non-destructive tests are defined.
- **IN_PROGRESS** — authorized source changes are being made on the current `main` working baseline.
- **VALIDATION_FAILED** — at least one required local check failed or could not demonstrate acceptance.
- **BLOCKED_APPROVAL** — a security owner, identity administrator, CIRT owner, production resource or required safeguard is missing.
- **COMPLETE** — acceptance criteria are demonstrably met, applicable local checks are recorded, and the reviewed task change is on `main` with post-commit verification.

Do not move to COMPLETE because a phase file exists, because a backup is numbered later, because a test plan says “pass,” or because a synthetic test passed.

## Per-phase automation procedure

### 1. Resolve authority and baseline

1. Resolve repository by full name `bozvtech28/CIRT-DFIR`.
2. Read latest `main` SHA and relevant branch/protection rules.
3. If repository identity or main SHA cannot be confirmed, stop without writes.
4. Never create/switch branches, reset, force-push, replace concurrent work, create a PR as workaround, or use hosted CI.

### 2. Build phase scope from evidence

1. Read `README.md`, `ARCHITECTURE.md`, `docs/Architecture.md`, `docs/Requirements.md`, `UI_UX.md` where relevant, and this ledger.
2. Locate the phase document and associated active implementation/tests.
3. Use `Backups/` only to understand history. Never copy a backup over active code without a specific, reviewed reason.
4. Write acceptance criteria as observable behavior, including security negatives (forbidden requests remain denied).
5. Identify external approvals, required configuration and potentially destructive behavior before implementation.

### 3. Prioritize

Use this order:
1. Security/privacy, authorization and evidence integrity.
2. Broken critical case workflow.
3. Reliability, recovery and compatibility.
4. Performance/resource limits.
5. Accessibility/usability.
6. Maintainability.

Within a security issue, document impact and root cause before changing code. Do not confuse architecture plans with implementation.

### 4. Implement minimally

1. Patch the smallest complete correction for the verified root cause.
2. Preserve real project logic, data, contracts and behavior outside scope.
3. Never trust browser-supplied roles or identities.
4. Never use synthetic principals in runtime paths or default identities outside tests.
5. Do not enable live authentication without approved tenant, issuer, audience, metadata/JWKS allowlists, roles, redirect/origin policies and owner approval.
6. Do not accept real evidence uploads or response actions before the filesystem-containment P1 is independently resolved.
7. Add focused tests and update project docs only when the verified behavior or acceptance criteria change.

### 5. Validate locally; no CI

Run the strongest available non-CI checks for changed behavior (e.g. focused pytest, full backend pytest, TypeScript/Vite build, static checks, SQL/schema validation, deterministic synthetic temp-directory tests). Do not contact real Entra endpoints or production services without explicit approval. Never trigger, poll, rerun or depend on hosted pipelines or runners.

For every command, record:
- exact command and working directory,
- exit code/result actually observed,
- whether it passed, failed, was skipped or could not run,
- what the check does and does not prove.

A source review is not an executed test. A synthetic token is not proof of production SSO. A database audit trigger is not proof of tamper-proof logging. A file hash is not proof of acquisition completeness.

### 6. Review and commit gate

Before any commit:
- re-resolve `main` and inspect current commit;
- review the complete diff and changed-file list;
- ensure only reviewed task files are included;
- preserve existing and concurrent work;
- ensure applicable safe local tests pass or explicitly assess acceptable residual risks;
- ensure no unresolved issue makes the patch materially unsafe;
- confirm direct-to-main is permitted by actual repository rules.

If direct commit is blocked by branch protection or required approvals, do not bypass it and do not commit.

After a direct commit:
- record SHA and message;
- re-resolve `main`;
- fetch every changed file from that SHA/main and verify intended content;
- update the ledger to reflect what was actually validated.

### 7. Reassess; no endless loop

After each completed phase, reassess the highest-priority open work. Continue only when another task is meaningful, in scope, safe and independently actionable. Stop at external approvals or unsafe validation gaps.

## Current stop conditions

These conditions prevent unsafe automatic completion until evidence changes:

1. **P1 filesystem containment remains OPEN.** Find the currently relevant Case Manager implementation from the source inventory; verify parent junction/reparse-point, traversal, race, cleanup and finalization controls. Do not integrate a prototype that failed the recorded synthetic junction test.
2. **Entra config/approval is absent.** Existing backend token-verification components are not wired into the FastAPI dependency, which intentionally rejects protected requests. Never invent tenant, audience, issuer, JWKS hosts or app-role values.
3. **Evidence intake/storage is not a production path.** Do not add live ingest before containment and auth gates.
4. **Many phase histories are backup-only.** Mark them UNVERIFIED or HISTORICAL until active implementation and acceptance evidence is identified.
5. **No hosted CI.** Local-only validation must be used, and unavailable local dependencies must be reported accurately.

## Recommended next run

1. Locate current Case Manager/P1 source and test paths using `Reports/Baseline_Inventory_20261015_223611.csv` and referenced source inventory. Confirm that the file still exists in current repository and resolve its exact path before reading or executing it.
2. Trace the known parent-junction acceptance from the current implementation and write deterministic tests against synthetic temporary directories.
3. Implement a containment correction only after the active code and path-handling contract are confirmed.
4. Run focused non-CI tests with no real evidence, then the relevant local regression tests if the dependencies/environment are available.
5. Update [PHASE_PROGRESS.md](PHASE_PROGRESS.md) with evidence and remaining risks.
6. Commit directly to `main` only if the change is safe, reviewed, validated to an appropriate level, and repository rules permit it.

This runbook defines a process; it does not itself assert that any phase is complete.

## P0-A Source Gap Confirmation

**Current disposition: BLOCKED pending canonical-source decision.**

The 2026-10-22 read-only provenance review found no authoritative Case Manager or evidence-ingestion implementation in the inspected active paths, and the reviewed candidate filenames were not found by the targeted Git-history search. Because the search was bounded, do not interpret this result as proof that no related implementation exists elsewhere.

Before implementation:

1. Confirm the canonical module location, maintainers, and intended API contract.
2. Design the shared containment policy and the platform-specific Windows and Linux enforcement adapters.
3. Write adversarial tests against real temporary filesystem objects before adding an evidence-intake endpoint.
4. Include traversal, absolute paths, symlinks/junctions/reparse points, concurrent path replacement, partial writes, cleanup ownership, preservation of existing files, atomic finalization, resource limits, and server-computed hashes.
5. Run the relevant tests on native Windows and Linux and inspect actual filesystem outcomes.
6. Keep evidence intake disabled. Do not wire recovered prototypes into the application. P0-B must independently pass before P0-C can proceed.
