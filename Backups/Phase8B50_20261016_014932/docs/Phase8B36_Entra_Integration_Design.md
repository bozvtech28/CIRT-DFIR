# Phase 8B.36 — Microsoft Entra Integration Design

## Status

DESIGN ONLY — NOT APPROVED FOR PRODUCTION

## Objective

Prepare a secure, provider-specific Microsoft Entra integration
without enabling authentication before administrator configuration
and security approval are available.

## 1. Proposed authentication architecture

Frontend:
- React application
- Microsoft Authentication Library (MSAL), pending approval
- Authorization Code Flow with PKCE
- Obtain an access token specifically intended for the DFIR API
- Attach the access token as an Authorization: Bearer header
- Do not place access tokens in URLs or application logs

Backend:
- FastAPI authentication dependency
- Extract bearer token from the Authorization header
- Reject missing or malformed credentials
- Resolve trusted Microsoft Entra signing keys
- Verify the JWT signature using a fixed approved algorithm
- Validate tenant, issuer, audience, expiration, not-before
  and other required claims
- Map trusted token app-role claims to application permissions
- Reject unknown or unauthorized roles
- Attribute audit actions to a validated principal

## 2. Trusted signing-key lifecycle

Production implementation must:
- Use the approved tenant-specific Microsoft discovery metadata
- Obtain signing keys only from the trusted configured JWKS endpoint
- Use HTTPS with certificate validation
- Restrict redirect behavior and network destinations
- Enforce response-size and timeout limits
- Cache validated public keys with controlled expiration
- Support approved key rotation
- Fail closed when required trusted keys are unavailable
- Never trust JWKS supplied by a browser or untrusted token header

## 3. Authentication and authorization boundary

The current fail-closed authentication dependency must remain
active until the replacement integration is approved and tested.

The verifier proves token validity only after trusted key
resolution and all required token validation succeed.

Authorization is a separate decision performed using trusted
identity claims and the application's RBAC policy.

A role name in a token is not sufficient unless its origin,
audience, issuer, signature, and role assignment are trusted.

## 4. Proposed role mapping

Exact Microsoft Entra app-role values must be approved by the
administrator before implementation.

Proposed application roles for review:
- Viewer: cases:read
- Analyst: cases:read, cases:update
- Admin: cases:read, cases:update, users:manage, audit:read

These are design proposals, not approved Entra app-role values.

## 5. Configuration requirements

Required approved configuration:
- Tenant ID
- API audience
- Expected issuer
- Frontend application/client ID
- API application scope
- Exact Entra app-role values
- Redirect and logout URIs
- Approved deployment origin
- HTTPS, CORS and reverse-proxy requirements
- Token version and required claim contract

Never place secrets, private keys, or access tokens in documentation.

## 6. Security controls

- Fail-closed authentication and authorization
- Least-privilege access
- No browser-supplied role trust
- No JWT algorithm negotiation from untrusted headers
- No unverified JWT claim trust
- No sensitive tokens in logs
- Validated audit-subject attribution
- Appropriate TLS and security headers
- Controlled CORS configuration
- Error responses without token disclosure
- Security approval before deployment

## 7. Implementation order

1. Receive approved Entra administrator configuration
2. Validate issuer, audience, scopes, roles and redirect values
3. Implement trusted discovery and JWKS retrieval
4. Integrate verified-token authentication dependency
5. Implement trusted Entra app-role mapping
6. Implement authenticated audit-subject attribution
7. Add frontend MSAL authentication
8. Add API bearer-token acquisition and attachment
9. Execute negative and positive integration tests
10. Complete security review and deployment approval

## 8. Deployment decision

BLOCKED

Offline synthetic JWT tests are not equivalent to a live
Microsoft Entra authentication integration.

No production authentication should be enabled during
this design-review phase.
