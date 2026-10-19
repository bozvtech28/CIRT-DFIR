# CIRT-DFIR Phase Progression and Automation Ledger

**Repository:** `bozvtech28/CIRT-DFIR`  
**Branch authority:** `main` only  
**Baseline:** `c5c5dbdc08304c7396cd865528364f4ff81ef3d3`  
**Reviewed:** 2026-10-19  
**Ledger status:** Initial source-grounded inventory; not a claim that every historical phase has passed acceptance.

## Purpose

This file is the canonical index for continuing the project's phased implementation from the earliest recoverable phase records through the latest phase documented in the active source tree. Each phase must be closed by verified source behavior, focused non-CI checks, a reviewed diff and the relevant security/owner gate—not by a filename, an old backup, a successful synthetic test alone, or a commit message.

The currently active phase documents available under `docs/` range from Phase 8B.7 to Phase 8B.84. Repository backups contain many additional snapshots, including Phase 4–7 and Phase 8B milestones above 100. These are historical snapshots and do not define the active implementation. The checked-in evidence does not expose a complete, authoritative list of every Phase 1–8B milestone, so gaps must remain marked **UNVERIFIED / NO ACTIVE PHASE RECORD** until a primary artifact can be found and cross-checked. Do not invent historical phase outcomes.

## Operating rules for every phase

1. Resolve the latest `main` SHA before inspecting the phase.
2. Read the current README, architecture, requirements, phase artefacts, implementation, tests, config/contracts and relevant history.
3. Identify the requirement and observable acceptance criteria. Treat backups as evidence of history only.
4. Classify the phase **COMPLETE**, **PARTIAL**, **BLOCKED**, **OPEN**, or **UNVERIFIED** with links to source/test evidence. A document saying tests passed is historical evidence, not a fresh test run.
5. Implement only the smallest verified correction that is safe and authorized; preserve the fail-closed security boundary.
6. Run applicable local, non-CI checks. Never trigger or depend on GitHub Actions or hosted runners.
7. Inspect the full task diff and re-resolve `main` immediately before committing. Preserve concurrent work. Commit only reviewed task files directly to `main` if branch rules and permissions allow.
8. Re-fetch the committed files and resolve `main` after the commit. If direct commit is blocked, leave it uncommitted and report the exact block.
9. Update this ledger and project architecture/requirements docs only when the evidence materially changes.
10. Stop at external approval, security, tenant configuration, production access, hardware or destructive-work gates. Do not simulate approval or promote test-only identities.

## Current release status

| Priority | Workstream | Status | Evidence / acceptance condition |
|---|---|---|---|
| P0 | Case Manager filesystem containment | **OPEN — RELEASE BLOCKER** | `Reports/Baseline_Report_20261015_223611.txt` records a parent-junction path acceptance. Requires independently reviewed remediation and traversal, junction/reparse point, race/concurrency, cleanup and finalization tests. |
| P0 | Live API authentication and authorization | **BLOCKED — APPROVED CONFIGURATION REQUIRED** | `platform/backend/app/auth_dependencies.py` always raises 401. `entra_authenticator.py` and `entra_bearer_adapter.py` state they are not wired into FastAPI. Need approved issuer, tenant, audience, metadata/JWKS hosts, app roles, role mapping, deployment origins and identity/security approval before wiring. |
| P0 | Evidence intake and custody | **NOT IMPLEMENTED / RELEASE BLOCKER** | Requirements call for bounded authenticated upload, hash verification, preservation of originals, provenance and custody. No production ingest pipeline/storage service is active. |
| P1 | Production identity integration | **PARTIAL / BLOCKED** | Isolated JWT verifier, metadata and JWKS primitives plus synthetic tests exist. Need approved configuration and reviewed FastAPI integration with actual dependency-level tests; no live Entra integration is verified. |
| P1 | Frontend production workflow | **PARTIAL** | React/MSAL bootstrap and bearer fetch exist. The app labels demo/synthetic data; Dashboard/Cases only have list/filter/read-only detail, and other navigation items are placeholders. |
| P1 | Database and operational recovery | **DEVELOPMENT ONLY** | SQLite case store and audit-event schema exist. PostgreSQL/object storage, production migrations, encryption, backup and restoration have not been verified. |
| P2 | Workspace hygiene and provenance | **REVIEW REQUIRED** | Tree includes tracked dependency directories, backend virtual environments and many timestamped backups. Do not bulk-delete without impact/reference review. |

**Release decision:** Not production-ready. Keep auth fail-closed and do not accept real evidence packages until the P0 security gates are independently resolved.

## Phase inventory: active documents

The following are phase artefacts present under `docs/` on the baseline. Their existence means “documented,” not automatically “passed.” “Current source check” refers to repository inspection, not fresh execution of every test.

| Phase / artefact | Intended area | Current classification | Close-out evidence needed |
|---|---|---|---|
| [Phase 8B.7 OIDC design](Phase8B7_OIDC_Design.md) | OIDC design assumptions | PARTIAL / DESIGN | Reconcile to approved tenant/issuer/audience and active dependency behavior |
| [Phase 8B.8 verifier readiness](Phase8B8_OIDC_Verifier_Integration_Readiness.md) | Verifier integration gate | BLOCKED | Approved configuration and dependency integration tests |
| [Phase 8B.9 synthetic JWT harness](Phase8B9_Synthetic_JWT_Test_Harness.md) | Synthetic token test support | PARTIAL | Re-run local tests where available; separate tests from live tenant verification |
| [Phase 8B.10 RS256 preparation](Phase8B10_RS256_Test_Preparation.md) | Signing/verification test prep | PARTIAL | Review test coverage with current verifier; fresh local results |
| [Phase 8B.13 Entra integration plan](Phase8B13_Microsoft_Entra_ID_Integration_Plan.md) | Provider/config/security plan | BLOCKED | Administrator decisions and security approval remain required |
| [Phase 8B.17 admin readiness](Phase8B17_Entra_Admin_Readiness_Checklist.md) | Identity administrator prerequisites | BLOCKED | Completed and reviewed authoritative configuration |
| [Phase 8B.21 frontend Entra plan](Phase8B21_Frontend_Entra_Integration_Plan.md) | SPA identity integration plan | PARTIAL | Validate current MSAL code against approved SPA registration |
| [Phase 8B.25 admin handoff](Phase8B25_Entra_Admin_Handoff.md) | Handoff to identity owner | BLOCKED | Actual owner-supplied configuration, not placeholder values |
| [Phase 8B.25 config template](Phase8B25_Entra_Config_Template.txt) | Non-secret template | PARTIAL | Confirm required values and safety notes match current integration |
| [Phase 8B.29 token verification plan](Phase8B29_Backend_Token_Verification_Plan.md) | Backend JWT verification requirements | PARTIAL | Trace required checks to verifier tests and live dependency |
| [Phase 8B.30 offline verifier](Phase8B30_Offline_Entra_Token_Verifier.md) | Isolated token verifier | PARTIAL | Focused tests and hardening compatibility |
| [Phase 8B.31 offline JWKS resolver](Phase8B31_Offline_JWKS_Resolver.md) | Trusted signing key resolution | PARTIAL | Focused tests, rotation/failure cases and approved runtime config |
| [Phase 8B.32 verifier/JWKS integration](Phase8B32_Offline_Verifier_JWKS_Integration.md) | Isolated verifier composition | PARTIAL | Full offline regression and reviewed dependency composition |
| [Phase 8B.34 config intake](Phase8B34_Entra_Config_Intake.md) | Config intake safeguards | BLOCKED | Actual approved configuration delivered securely |
| [Phase 8B.34 configuration worksheet](Phase8B34_Entra_Config_Worksheet.txt) | Admin-supplied values | BLOCKED | Completed by authorized identity owner; do not guess entries |
| [Phase 8B.36 integration design](Phase8B36_Entra_Integration_Design.md) | Intended authentication flow | PARTIAL / DESIGN | Reconcile with active modules and test API flow after authorized integration |
| [Phase 8B.36 security test matrix](Phase8B36_Entra_Security_Test_Matrix.md) | Auth, roles, JWKS, audit and deployment tests | OPEN | Implement/exercise applicable rows; record actual results |
| [Phase 8B.37 synthetic role mapping](Phase8B37_Synthetic_Role_Mapping.md) | Role mapping test design | PARTIAL | Verify mapper tests; confirm production role values from owner |
| [Phase 8B.51 implementation plan](Phase8B51_Entra_Implementation_Plan.md) | Integration requirements | BLOCKED | Actual config, dependency wiring, security review and regression |
| [Phase 8B.51 implementation test matrix](Phase8B51_Entra_Implementation_Test_Matrix.md) | Acceptance scenarios | OPEN | Test cases with synthetic fixtures; live tenant tests only if approved |
| [Phase 8B.64 configuration gate](Phase8B64_Entra_Configuration_Gate.md) | Configuration approval checklist | BLOCKED | Required checklist completed and approved |
| [Phase 8B.66 frontend design](Phase8B66_Entra_Frontend_Integration_Design.md) | SPA token/login design | PARTIAL / DESIGN | Validate active code with correct registration; handle denied/expired sessions |
| [Phase 8B.76 claims-to-principal design](Phase8B76_ClaimsToPrincipal_Design.md) | Verified claims mapping | PARTIAL | Fresh tests; mapper receives verified claims and trusted role mapping only |
| [Phase 8B.79 frontend config](Phase8B79_Frontend_Configuration.md) | SPA settings | PARTIAL | Approved values, origin policy and deployment settings remain required |
| [Phase 8B.83 MSAL foundation](Phase8B83_MsalFoundation.md) | Browser config/token helper | PARTIAL / IMPLEMENTED BUILDING BLOCK | Source exists; verify no secrets are exposed and do not claim live auth |
| [Phase 8B.84 MSAL React integration](Phase8B84_MsalReactIntegration.md) | Sign-in UI/token attachment | PARTIAL / IMPLEMENTED BUILDING BLOCK | Frontend integration exists; prove live identity only after admin config and server integration |

### Earlier phases (1 through 7 and other historical work)

Earlier phase artefacts are distributed through timestamped `Backups/` snapshots. The current source tree does not contain a single authoritative phase ledger fully identifying Phase 1 through every later milestone with scope, acceptance criteria and status. Do not infer that a backup folder name means a phase is complete.

| Historical range | Artefact evidence found | Status |
|---|---|---|
| Phase 1–3 | No canonical phase index located in active `docs/` during this review | UNVERIFIED — discover baseline/design/source artefacts before assigning status |
| Phase 4–5 | Timestamped frontend/API prototype backups exist | HISTORICAL SNAPSHOTS — compare against active source; acceptance status not reconstructed |
| Phase 6 | SQLite case repository/schema backups exist | HISTORICAL SNAPSHOTS — current implementation has SQLite case storage; phase acceptance not inferred |
| Phase 7 | Repository/schema/audit/test-fix backups exist | HISTORICAL SNAPSHOTS — establish present behavior from current source and tests |
| Phase 8B milestones | Active docs from 8B.7 to 8B.84 and backups above 8B.100 | PARTIAL/BLOCKED as noted; highest numbered backup is history, not proof every intermediate milestone passed |

## Latest verified patch — synthetic identity test isolation

**Status:** PATCH VERIFIED BY SOURCE INSPECTION, TEST EXECUTION NOT AVAILABLE

- Finding: `platform/backend/tests/conftest.py` previously installed a synthetic analyst principal through an `autouse=True` fixture for the entire backend suite. This allowed legacy tests to exercise protected endpoints without declaring that they needed a synthetic identity and could mask the intended fail-closed default.
- Change: the shared fixture now clears dependency overrides before/after each test without creating an identity. `platform/backend/tests/test_api.py::test_demo_cases_are_synthetic` now installs its synthetic analyst only for the successful demo-list test and clears the override afterward.
- Production source unchanged: `platform/backend/app/auth_dependencies.py` still denies protected requests by default.
- Auth-gate regression: existing `test_api_auth_gate.py` and `test_api_oidc_fail_closed.py` retain assertions for HTTP 401 on unauthenticated or malformed-token requests.
- Commits: `99d2cfe8e22d2bac7b994c5d1502248c7c64ce87` (fixture), `da92dfdd645adc88ae3110dff14d98590e7c8fb4` (explicit test override), and `873db9b6da3c52afb27faa5cca521fa8c6b41fe6` (finding record).
- Validation: modified files and existing negative tests were re-fetched from GitHub and inspected. Pytest was **not run** because this execution environment has no local checkout/confirmed dependencies. Do not mark the backend suite passed until `python -m pytest` is executed locally.
- Remaining risk: full test ordering and regression behavior remain unverified at runtime.

## Verification checklist for automation runs

A future run should append only concise, verified entries:

| Field | Required record |
|---|---|
| Starting main | SHA resolved immediately before work |
| Phase/requirement | Exact filename/requirement and observable defect or gap |
| Changed files | Exact path and root-cause justification |
| Checks | Command, environment, exit result and skipped reasons |
| Review | Full task diff and regression risks inspected |
| Commit | SHA/message, only if direct-to-main permitted |
| Post-commit | Re-resolved main SHA and file content verification |
| Remaining blockers | Owner/config/security approvals still needed |

## Safe next-action order

1. **P0-A — filesystem containment:** find the current Case Manager implementation and tests from the baseline inventory; trace parent-junction acceptance; design and test safe root containment before production integration. Use only synthetic temporary roots.
2. **P0-B — identity approval:** obtain actual tenant, exact issuer, API audience, discovery/JWKS allowlists, SPA client ID, API scope, redirect URIs and exact role values from an authorized identity administrator. Do not invent them.
3. **P0-C — wire identity only after approval:** integrate the existing bearer adapter with FastAPI dependency; preserve fail-closed behavior on missing/invalid config, network/key failures, invalid claims and unknown roles. Add FastAPI-level allow/deny/audit tests before enabling.
4. **P0-D — evidence intake:** after independent containment review and auth gates, implement bounded streaming, private staging, strict archive/path handling, preservation of existing files, server-side hashes and atomic finalization.
5. **P1 — operational deployment:** production database/object store, migrations, encryption, backup/restore, monitoring and signed scanner distribution.
6. **P1 — UI modules:** implement asset/scanning, findings, evidence, response, reports and administration only when backend contracts and permissions exist. Keep unsupported screens explicitly labelled as scaffold.
7. Reassess and continue while meaningful, safe work remains; never create an endless loop.

## Safety and authority

- `main` is the only permitted branch. Never create/switch branches, force-push, reset, or use a PR as a workaround.
- Do not trigger, poll, rerun or depend on CI/hosted runners.
- Do not enable authentication by injecting synthetic principals outside tests.
- Do not commit guessed identity settings, secrets, tokens, private keys or credentials.
- Synthetic JWT success is not production SSO validation.
- Do not claim P0 filesystem containment is fixed without independent review and acceptance tests.
- Do not commit when the remaining validation gap makes the change materially unsafe.
- Update this ledger only from observed main/source/test evidence.


## Roadmap checkpoints and web UI test timing

This roadmap orders work by release risk, not by the highest numbered historical backup. Phase 1–3 acceptance evidence is not reconstructed in one canonical active phase document; Phase 4–7 reports/backups show historical development and are not sufficient to declare those phases passed.

| Order | Status on current main | Exit evidence / dependency |
|---|---|---|
| R0 — Repository/build baseline | PARTIAL | README/UI entry corrected; local commands documented. Need fresh local environment verification and ensure generated `dist`, dependency folders and virtual environments are treated correctly. |
| R1 — First UI test | READY NOW, synthetic only | Open `apps/web-prototype/index.html`; separately launch Vite + FastAPI for the React UI using the README commands. Capture pass/fail evidence locally. |
| R2 — P0 filesystem containment | BLOCKED ON ACTIVE SOURCE IDENTIFICATION | Identify the canonical Case Manager source from the baseline inventory and provenance; reproduce the parent-junction failure in synthetic temp roots; implement and test root containment, traversal, reparse/junction behavior, race handling, cleanup ownership and atomic finalization; independent security review required. |
| R3 — Backend regression baseline | NOT RUN HERE | Run focused and full local pytest in the supported Python environment. Preserve unauthenticated/malformed-token 401 behavior. |
| R4 — Entra approval + server wiring | BLOCKED_APPROVAL | An authorized identity/security owner supplies tenant ID, exact issuer, audience, discovery/JWKS allowlists, SPA ID/scope/redirect URIs, app roles and role-to-permission mapping. Only then integrate validated tokens into the FastAPI dependency, with fail-closed errors and API-level tests. |
| R5 — React/API functional integration | PARTIAL | Replace only proven contract gaps; test loading/error/empty states, search/filter/refresh and truthful API state. No fake success or synthetic runtime identity. |
| R6 — Evidence intake and custody | NOT IMPLEMENTED; GATED | Bounded streaming, quotas/deadlines, private staging, safe paths, hashes, atomic finalization, custody/audit, cleanup and failure recovery, after R2 and R4 gates. |
| R7 — Durable production services | NOT IMPLEMENTED / DESIGN TARGET | PostgreSQL/migrations, private object storage, encryption/key management, monitoring, operational deployment and verified backup/restore. |
| R8 — DFIR workflow modules | PARTIAL SCAFFOLD | Build assets/scans, findings, evidence, controlled response, reports and administration against reviewed backend contracts/permissions. Response actions require policy and approval controls. |
| R9 — Enterprise hardening and release | NOT READY | Local unit/API/UI/security testing, browser and accessibility review, signed scanner/release supply chain, threat review, restore drill, documentation, operational runbooks and application/security owner acceptance. |

**First browser test:** start with R1 now, using fictional data. The React + FastAPI UI may be smoke-tested before live auth, but protected case-list/API success is expected to remain unavailable until R4. Do not test real evidence or operational response actions until the security gates are closed. No local runtime test was executed in this connector session.

