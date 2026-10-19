# Phase 8B.7 — Provider-neutral OIDC design

## Status

Design and test foundation only. No identity provider has been selected.
No production token verifier is configured. Authentication is NOT operational.

## Trust boundaries

1. The identity provider is an organization-approved OIDC issuer.
2. The backend validates tokens using a maintained OIDC/JWT library.
3. Signature verification uses provider metadata and JWKS, with approved algorithms.
4. The backend validates issuer, audience, expiry, not-before, and required subject.
5. Roles come only from validated, approved claims or a server-controlled role store.
6. RBAC is enforced on each protected API route.
7. The frontend is not trusted to assert identity or permissions.

## Required provider configuration

- Official issuer URL and discovery metadata URL
- API audience/client identifier
- Approved signing algorithms and JWKS handling
- Trusted role/group claim mapping and provisioning process
- Exact redirect URIs if an interactive browser login is selected
- Secret storage and rotation process if confidential client credentials are required
- HTTPS, trusted proxy settings, and deployment network controls

Do not put client secrets, private keys, bearer tokens, or real user data in source code,
test fixtures, reports, or version control.

## Required security tests

- Missing credential: HTTP 401
- Malformed or invalid token: HTTP 401
- Expired token: HTTP 401
- Wrong issuer: HTTP 401
- Wrong audience: HTTP 401
- Valid identity with insufficient permission: HTTP 403
- Valid authorized identity: expected route-specific response
- Signature failure, unknown signing key, and disallowed algorithm: HTTP 401
- Key rotation and issuer/JWKS outage behavior: fail closed

The Phase 8B.7 claim tests validate claims after cryptographic verification.
They do not perform signature verification and must not be treated as end-to-end OIDC tests.

## Deployment gate

Keep the service stopped until the provider is approved, a real verifier is implemented,
all protected routes are enforced, integration tests pass, and deployment controls are reviewed.
