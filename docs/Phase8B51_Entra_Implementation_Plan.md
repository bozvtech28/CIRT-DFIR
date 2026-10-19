# Phase 8B.51 - Microsoft Entra Authentication Implementation Plan

## Current state

- Backend authentication gate remains fail-closed.
- Case read and case update routes have permission dependencies.
- Offline RS256 token-verification and local JWKS-resolver components exist.
- The offline components are not wired into the authentication dependency.
- Frontend MSAL Browser and MSAL React dependencies are not declared.
- The configuration worksheet still contains administrator placeholders.
- Synthetic authentication and role-mapping tests do not prove production identity.

## Required administrator-approved configuration

Obtain these values through the authorized Microsoft Entra administrator:

1. Tenant ID.
2. API application ID URI / accepted access-token audience.
3. Exact expected issuer and access-token version.
4. Frontend application client ID.
5. Approved delegated API scope.
6. Exact API app-role values and the group responsible for assignment.
7. Approved sign-in and logout redirect URIs.
8. Approved deployment origin and HTTPS termination arrangement.
9. Required role-to-permission policy and audit access policy.

Do not guess these values. Do not store access tokens, client secrets, private keys,
or other credentials in this worksheet, source control, or reports.

## Backend integration requirements

1. Use trusted Microsoft Entra OpenID Connect discovery metadata for the approved tenant.
2. Validate the discovery issuer and JWKS URI against the approved tenant configuration.
3. Retrieve signing keys only from the trusted metadata endpoint using HTTPS.
4. Implement bounded timeouts, controlled caching, key rotation, and safe refresh on
   an unknown key ID. Do not trust token-provided URLs.
5. Verify access-token signatures using the explicitly allowed RS256 algorithm.
6. Validate issuer, audience, expiry, not-before, tenant ID, subject, and the approved
   access-token version/claim contract.
7. Reject malformed tokens, ID tokens used as API access tokens, wrong audiences,
   unexpected tenants, missing required claims, and unrecognized app roles.
8. Derive roles only from validated claims issued for the approved API contract.
   Never accept roles from request bodies or browser-supplied identity objects.
9. Integrate verification into the existing fail-closed authentication dependency.
10. Preserve permission checks for case reads and case updates.
11. Replace hardcoded audit actors with the validated subject and approved identity
    attributes. Do not log raw tokens.
12. Keep health-check behavior and existing business logic unchanged unless explicitly
    approved and tested.

## Frontend integration requirements

1. Add compatible, pinned MSAL Browser and MSAL React dependencies only after approval.
2. Configure the approved tenant, client ID, redirect URI, and API scope.
3. Implement sign-in, sign-out, account selection, and session restoration.
4. Acquire an access token for the API scope; do not send an ID token to the API.
5. Attach the access token as an Authorization: Bearer header to protected API calls.
6. Handle expired sessions and interaction-required responses without infinite loops.
7. Do not place tokens in logs, URLs, application reports, or persistent browser storage
   without an explicitly approved security design.
8. Preserve the existing BozV footer signature and unrelated application functionality.

## Deployment and security requirements

- HTTPS and trusted reverse-proxy configuration.
- Explicit CORS allowlist for the approved frontend origin.
- Safe authentication and authorization failure logging.
- No bearer-token or secret logging.
- Rate limiting and operational monitoring appropriate to the deployment.
- Security review of token validation, role mapping, audit attribution, and error handling.
- Confirm the deployment does not expose development/demo routes unintentionally.

## Rollout gate

Do not enable production authentication until:
- The authorized configuration is complete.
- Trusted metadata/JWKS retrieval and key lifecycle are implemented and tested.
- Real-token validation is integrated into the fail-closed dependency.
- Frontend sign-in and API access-token handling are implemented.
- Role mapping and audit attribution are validated.
- Backend tests and frontend production build pass.
- An authorized security reviewer approves the deployment.

This document is a plan, not proof of production readiness.