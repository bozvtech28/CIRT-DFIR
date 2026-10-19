# Phase 8B.8 — OIDC Verifier Integration Readiness

## Current status

Provider-neutral design and readiness assessment only.
Identity provider: undecided.
Deployment target: organization-managed server.
Real OIDC authentication: not implemented or validated.

## Required verifier contract

The future verifier must:

1. Accept bearer tokens only from the documented authentication mechanism.
2. Verify JWT signatures cryptographically using trusted issuer metadata and JWKS.
3. Allow only explicitly approved signing algorithms.
4. Validate issuer, audience, expiration, and not-before claims.
5. Reject malformed tokens, missing required claims, unknown keys, and invalid signatures.
6. Handle signing-key rotation safely and fail closed when verification cannot be trusted.
7. Map roles only from validated, approved claims or a server-controlled role store.
8. Never trust roles, identity, or permissions supplied by the browser or request body.
9. Return HTTP 401 for missing or invalid authentication.
10. Return HTTP 403 for a valid authenticated identity without the required permission.

## Integration boundaries

- Keep health-check behavior explicitly documented.
- Protect every case, user-management, and audit route according to its policy.
- Preserve the existing RBAC policy as the authorization layer.
- Keep the current authentication gate fail-closed until the verifier is approved.
- Do not add development bypasses to production code.
- Do not log bearer tokens, client secrets, private keys, or sensitive claims.
- Store any required secrets in an organization-approved secret store.
- Require HTTPS and reviewed reverse-proxy and deployment configuration.

## Mandatory automated integration tests

Use synthetic tokens and a controlled test signing key. Never use production tokens or keys.

- Missing bearer token -> 401
- Malformed token -> 401
- Invalid signature -> 401
- Expired token -> 401
- Wrong issuer -> 401
- Wrong audience -> 401
- Future not-before claim -> 401
- Unknown signing key -> 401
- Disallowed signing algorithm -> 401
- JWKS or metadata failure -> fail closed
- Valid Viewer requesting a restricted update -> 403
- Valid authorized Analyst or Administrator -> policy-appropriate response
- Role claim tampering -> rejected
- Signing-key rotation -> validated behavior
- All protected routes -> authentication and authorization enforced

## Acceptance criteria

Do not declare authentication operational until:
- An identity provider is approved and its configuration is verified.
- A maintained OIDC/JWT verification library is selected and reviewed.
- Real signature-verification integration is implemented.
- All mandatory integration tests pass.
- Route-by-route access control is tested.
- Deployment, HTTPS, secrets management, logging, and operational controls are reviewed.
- Security review explicitly approves the deployment.

This phase does not contact a provider, install dependencies, start a server,
or establish that real authentication works.
