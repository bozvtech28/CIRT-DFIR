# Phase 8B.64 — Microsoft Entra Configuration Readiness Gate

## Purpose

Prepare for a controlled Microsoft Entra ID integration for CIRT DFIR Professional.
This checklist does not enable authentication or certify production readiness.

## Required organization-approved configuration

- [ ] Entra tenant ID confirmed by the organization's identity administrator.
- [ ] Backend API application registration and expected audience confirmed.
- [ ] Exact token issuer and accepted tenant policy approved.
- [ ] API application roles approved and mapped to application permissions.
- [ ] Frontend SPA application registration and client ID confirmed.
- [ ] Approved SPA redirect URI and logout URI registered.
- [ ] Organization-approved internal application URL documented.
- [ ] HTTPS termination, trusted proxy behavior, and certificate ownership confirmed.
- [ ] CORS origins restricted to approved frontend origins.
- [ ] Token validation requirements approved: signature, issuer, audience, expiry, not-before, tenant, and allowed algorithms.
- [ ] JWKS refresh, cache expiry, unknown-key behavior, and failure handling reviewed.
- [ ] Audit events and stable user-subject attribution approved.
- [ ] Secret and configuration storage approved. No secrets committed to source control.
- [ ] Security review and deployment approval recorded.

## Integration boundaries

- Metadata transport must use approved fixed URLs and a trusted hostname allowlist.
- Token-derived URLs must never determine arbitrary metadata or JWKS destinations.
- The metadata validator must validate discovery and JWKS content before use.
- Token verification must use a maintained, reviewed library and trusted issuer configuration.
- Browser-supplied roles must never be treated as authorization proof.
- Production authentication must remain fail-closed until end-to-end tests pass.
- Synthetic test tokens and keys must remain test-only.
- No real Entra endpoints should be contacted without explicit organizational approval.

## Not to record in this document

Do not place client secrets, private keys, access tokens, refresh tokens, passwords, or other credentials in this checklist, reports, or source code.

## Approval gate

Do not connect the transport, metadata client, JWKS cache, or token verifier to the production authentication dependency until the required configuration is confirmed and an approved end-to-end test plan is available.

Status: PENDING ORGANIZATION CONFIGURATION AND SECURITY APPROVAL.
