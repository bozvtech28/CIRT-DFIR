# P0-A Filesystem Containment Design and Adversarial Test Plan

**Status:** DESIGN ONLY — P0-A remains OPEN and is a release blocker.

**Scope:** Define the filesystem-containment contract and test requirements before implementing or enabling evidence intake. This document does not authorize an upload endpoint, production evidence storage, or restoration of historical candidate code.

## 1. Authority and current-state constraints

- GitHub `main` is the sole repository authority.
- `README.md`, `ARCHITECTURE.md`, `docs/Architecture.md`, `docs/Requirements.md`, `docs/PHASE_PROGRESS.md`, and `docs/PHASE_AUTOMATION_RUNBOOK.md` remain the governing project documents.
- The current workspace is a development scaffold, not a production DFIR evidence-ingestion system.
- Do not execute, copy, or promote recovered scripts, backup prototypes, or historical candidates as the implementation.
- P0-A must be independently accepted before evidence intake is considered.
- P0-B authentication remains fail-closed pending approved identity configuration and verified server-side enforcement.
- P0-C remains blocked until P0-A and P0-B pass.
- No real evidence may be used for development or testing.

## 2. Design goals

The eventual implementation must:

1. Constrain every filesystem effect to an explicitly configured storage root.
2. Fail closed if the platform cannot enforce the required containment guarantees.
3. Resist traversal, absolute-path injection, link/reparse-point escape, and concurrent path replacement.
4. Preserve pre-existing files and avoid deleting resources not created and owned by the current operation.
5. Prevent incomplete content from being published as finalized evidence.
6. Compute integrity hashes on the server from the bytes actually accepted.
7. Apply explicit limits to upload size, time, concurrency, disk consumption, archive entry count, nesting depth, and expanded content.
8. Produce auditable outcomes without exposing secrets or sensitive evidence content in logs.
9. Use the same security contract on Windows and Linux, with separate platform-specific enforcement where required.

## 3. Proposed API-independent contract

These are requirements to validate during design, not claims about existing implementation.

### 3.1 Inputs and authority

- Accept only a server-selected storage root and a validated application-generated object identifier.
- Treat client filenames, archive entry names, and client-provided paths as untrusted display metadata, never as storage authority.
- Reject absolute paths, drive-qualified paths, UNC paths, device paths, traversal components, invalid encodings, and platform-specific path ambiguities.
- Define explicit behavior for duplicate names, reserved names, alternate data streams, trailing dots/spaces, case collisions, and Unicode normalization.
- Do not permit callers to select arbitrary destination paths.

### 3.2 Containment and race resistance

- Do not rely solely on string-prefix comparisons, `Path.resolve()`, or a check followed by an ordinary open.
- Ensure the containment guarantee remains valid across the operation that creates, writes, finalizes, or removes a file.
- Detect or prevent symbolic-link, junction, mount/reparse-point, and equivalent escape paths where applicable.
- Avoid following attacker-controlled links during traversal and mutation.
- Treat a path that changes between validation and use as adversarial.
- If a safe platform primitive is unavailable, reject the operation rather than silently downgrade security.

### 3.3 Windows adapter requirements

- Specify handle-based operations and reparse-point handling for every relevant create/open/write/rename/delete operation.
- Define how the implementation verifies that opened handles refer to objects within the authorized root.
- Cover junctions, symbolic links, reparse points, directory replacement, and concurrent path mutation.
- Verify the actual resulting filesystem objects and effects in native Windows tests; mocked API results alone are insufficient.

### 3.4 Linux adapter requirements

- Prefer directory-descriptor-relative operations with no-follow semantics and restrictive creation flags.
- Evaluate whether `openat2` resolution restrictions or an equivalent supported mechanism is required for the threat model.
- Define a fail-closed policy for unsupported kernels or filesystem behavior.
- Cover symlinks, mount boundaries where relevant, concurrent rename/replacement, and descriptor-relative cleanup.
- Verify actual filesystem effects in native Linux tests.

### 3.5 Partial writes and finalization

- Write into an operation-owned staging location that is not exposed as finalized evidence.
- Ensure failures cannot overwrite or delete pre-existing unrelated objects.
- Define explicit state transitions for creation, writing, validation, hashing, finalization, and failure cleanup.
- Publish the finalized object only after all required checks succeed.
- Use an atomic finalization primitive where its guarantees are documented and sufficient; do not assume a cross-filesystem rename is atomic.
- Define recovery behavior for process termination, disk-full conditions, cancellation, and failed finalization.
- Cleanup must operate only on resources demonstrably owned by the failed operation.

### 3.6 Integrity and resource limits

- Compute the cryptographic hash server-side from the bytes actually accepted.
- Do not trust a client-supplied hash as proof of content integrity.
- Define maximum upload bytes, elapsed time, concurrent operations, per-case storage, archive entries, path depth, decompressed bytes, expansion ratio, and processing time.
- Reject limit violations without publishing partial content.
- Specify safe handling for malformed, encrypted, nested, or unsupported archives.

## 4. Adversarial acceptance matrix

Every applicable test must assert both the reported outcome and the actual filesystem state.

| ID | Attack or failure | Required acceptance result |
|---|---|---|
| FS-01 | `../` and equivalent traversal | Rejected; no out-of-root object created or modified |
| FS-02 | Absolute, drive-qualified, UNC, and device paths | Rejected; no unauthorized filesystem effect |
| FS-03 | Symlink escape on Linux | Rejected or safely prevented; outside target unchanged |
| FS-04 | Junction/reparse-point escape on Windows | Rejected or safely prevented; outside target unchanged |
| FS-05 | Link or directory swapped after validation | Operation remains contained or fails closed |
| FS-06 | Destination replaced concurrently | No write, overwrite, or deletion outside the authorized operation |
| FS-07 | Pre-existing destination collision | Existing bytes and metadata remain protected according to the contract |
| FS-08 | Write fails partway through | No incomplete finalized object; owned staging content is safely handled |
| FS-09 | Disk full, quota exceeded, or I/O failure | Fail closed; no success response for incomplete content |
| FS-10 | Cancellation or process interruption | No false finalization; recovery behavior matches the documented state model |
| FS-11 | Cleanup after failure | Only operation-owned resources are removed |
| FS-12 | Finalization collision or rename failure | No overwrite; no false success; safe recoverable state |
| FS-13 | Hash mismatch or client-supplied hash manipulation | Server-computed digest represents accepted bytes; client hash is not authoritative |
| FS-14 | Oversized upload or excessive concurrency | Limits enforced; bounded resource consumption |
| FS-15 | Archive traversal, symlink entries, or hostile member names | No extraction outside root |
| FS-16 | Archive expansion or nesting limit exceeded | Rejected before unbounded resource consumption |
| FS-17 | Unsupported platform primitive | Operation fails closed; no weaker fallback |
| FS-18 | Repeated and concurrent adversarial operations | No escape, unintended overwrite, or cross-operation cleanup |

## 5. Test execution and evidence requirements

- Use synthetic data and isolated temporary directories only.
- Run the relevant tests on native Windows and native Linux; a result from one platform does not establish the other platform's acceptance.
- Use real filesystem objects for link/reparse-point and race tests.
- For race tests, use controlled synchronization to make replacement timing reproducible; repeated probabilistic tests may supplement but not replace deterministic cases.
- Capture platform, OS version, filesystem, Python version, test command, exit code, and test results.
- Assert that outside sentinel files remain byte-for-byte unchanged.
- Assert that pre-existing destination files remain unchanged on failure.
- Assert that no incomplete content is reported as finalized.
- Inspect cleanup results and verify that unrelated files survive.
- Record every skipped or unsupported test as an unresolved acceptance item.
- Existing regression-suite success is necessary where applicable but is not proof of filesystem security.

## 6. Implementation sequence

1. Confirm the canonical implementation location, ownership, and interface contract.
2. Review this design against the active requirements and architecture documents.
3. Write deterministic tests for the contract before implementing the filesystem adapters.
4. Implement the shared policy and the separate Windows/Linux enforcement adapters.
5. Run focused adversarial tests on each native platform.
6. Run relevant backend regression tests on each supported platform.
7. Review actual filesystem effects, failure cleanup, resource limits, and integrity-hash behavior.
8. Update the roadmap with concrete test evidence and any remaining limitations.
9. Require independent review and explicit acceptance before changing the P0-A release gate.
10. Keep P0-B independently fail-closed until its own approved authentication criteria pass.

## 7. Explicit non-goals

This design task does not:

- Add or enable an evidence upload endpoint.
- Connect real evidence storage or production case management.
- Configure or bypass authentication.
- Promote historical scripts or recovered prototypes.
- Declare P0-A, P0-B, or P0-C complete.
- Claim that any tests have run or passed.

## 8. Exit criteria for the design phase

The design phase is complete only when the canonical implementation location is agreed, platform-specific enforcement choices are reviewed, the adversarial tests are mapped to requirements, and maintainers approve the test-first implementation plan. P0-A remains OPEN until implementation and native test evidence are independently accepted.
