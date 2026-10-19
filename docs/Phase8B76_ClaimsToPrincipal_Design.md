# Phase 8B.76 — Claims-to-Principal Mapping

## Scope

This phase adds an isolated mapping function from already-verified Microsoft
Entra access-token claims to the application's internal `Principal` model.

## Security boundary

- The mapper does not verify JWT signatures, issuer, audience, token lifetime,
  or tenant. Those checks must succeed in the existing trusted verifier first.
- Only pass claims returned by `verify_entra_access_token` after successful
  verification.
- Role mappings must be explicitly supplied by trusted server-side
  configuration. Do not load them from a browser request or token-controlled
  configuration.
- The mapper accepts only a non-empty `roles` array. It rejects malformed,
  duplicate, missing, and unmapped application roles.
- It does not grant roles from `groups`, `scp`, browser input, or display names.
- This phase does not wire the mapper into `auth_dependencies.py`. The API
  authentication gate must continue returning 401 until the organization
  completes and approves the production integration.

## Synthetic test role values

`CIRT.DFIR.Viewer`, `CIRT.DFIR.Analyst`, and `CIRT.DFIR.Administrator` are
test-only examples, not claims that these values exist in the organization's
Entra tenant. Confirm exact application-role values with the Entra administrator
before creating any production mapping.

## Validation

Run the focused mapper tests and the complete backend regression suite.
Run the frontend build as a regression check. These tests do not establish that
a real Entra tenant, production token, or deployment is configured correctly.
