# Microsoft Entra ID Integration Design

## Status

Design and offline regression preparation only.
Live authentication is not configured.
The FastAPI authentication dependency remains fail-closed.
This document does not authorize production deployment.

## Required organization-approved configuration

- Microsoft Entra tenant ID.
- Exact token issuer URL for the selected token version.
- API audience / Application ID URI.
- Single-page application client ID.
- API delegated scope.
- Exact application role values.
- Explicit mapping from Entra application roles to internal roles.
- Approved HTTPS discovery document and JWKS trust configuration.
- Approved frontend redirect URI and deployment origins.
- Operational owner and security approval.

Do not invent these values or commit real credentials.

## Intended request flow

1. The SPA signs in using the approved Microsoft Authentication Library configuration.
2. The SPA requests an access token for the approved API scope.
3. The API extracts a Bearer token from the Authorization header.
4. The API obtains signing keys only from a trusted, validated Entra metadata/JWKS source.
5. The API verifies the JWT signature, allowed algorithm, issuer, audience, expiration, not-before, tenant, and required claims.
6. Only verified claims are passed to the approved application-role mapper.
7. The resulting internal Principal is checked against the permission required by the route.
8. The API records the verified subject as the actor for authorized audit events.

## Fail-closed requirements

- Missing, malformed, expired, invalid, or untrusted tokens must be rejected.
- Authentication failures return HTTP 401.
- Authenticated principals lacking permission receive HTTP 403.
- Browser-supplied roles or identity fields must never grant authorization.
- Unavailable or invalid discovery metadata/JWKS must not result in accepting a token.
- No default development identity may be used for protected production operations.
- Public health endpoints must not expose case data or sensitive configuration.

## Audit attribution

The case-update endpoint currently contains a development actor placeholder.
Before operational deployment, audit attribution must use the subject from the verified Principal.
Audit records should capture the action, target case, actor subject, timestamp, and outcome.
Do not log access tokens or secrets.

## Testing requirements before activation

- Missing and malformed Authorization header.
- Invalid signature, issuer, audience, tenant, expiration, and not-before.
- Unknown signing key and failed JWKS refresh.
- Missing, empty, duplicate, and unapproved roles.
- Viewer cannot update cases.
- Analyst cannot perform administrator-only actions.
- Unauthenticated requests receive 401.
- Authenticated unauthorized requests receive 403.
- Audit actor is derived from the verified Principal.
- Full backend tests and frontend production build pass.

## Activation gate

Do not wire the adapter into the production dependency until the approved values are available, trusted metadata/JWKS loading is reviewed, integration tests cover the actual FastAPI dependency, and the organization authorizes activation.
