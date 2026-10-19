# Phase 8B.66 - Microsoft Entra Frontend Integration Design

## 1. Status and scope

This document is a design and readiness review only.
It does not enable production authentication or establish production readiness.

Identity provider selected for planning: Microsoft Entra ID.
Intended environment: organization-approved internal network.

## 2. Current implementation boundary

- The backend authentication dependency must remain fail-closed.
- The existing frontend must not be assumed to authenticate users.
- MSAL browser and React dependencies were not declared in the Phase 8B.65 audit.
- Backend metadata transport, discovery validation, JWKS cache, and token verification must not be connected to production authentication without approved configuration and review.
- Synthetic test tokens and keys are for automated tests only.
- No real identity-provider endpoints are contacted during this phase.

## 3. Frontend integration design

### 3.1 Application registration

Obtain the following from the organization's identity administrator:

- Approved Entra tenant ID.
- Frontend single-page application client ID.
- Backend API application registration and exact audience.
- Exact issuer and tenant policy.
- Approved redirect URI and logout URI.
- Approved API delegated scope or other organization-approved permission model.
- Internal application URL and HTTPS deployment design.

Do not place client secrets, private keys, access tokens, or refresh tokens in source files, documentation, reports, or version control.

### 3.2 Browser sign-in

After approval, evaluate the maintained Microsoft Authentication Library for JavaScript (MSAL):

- @azure/msal-browser
- @azure/msal-react

Dependencies are not installed by this phase.

The eventual implementation must use an approved authorization-code flow with PKCE, a configured tenant authority, registered redirect URIs, and least-privilege API scopes.

### 3.3 Token handling

- Request an access token for the registered backend API.
- Send the access token only to the intended backend over HTTPS.
- Do not send an ID token as a substitute for an API access token.
- Do not trust roles, user IDs, or permissions supplied by editable browser state or request bodies.
- Do not log tokens or credentials.
- Handle expired sessions, denied consent, sign-out, and failed token acquisition without bypassing backend authorization.

### 3.4 Backend verification

Before accepting a token, the backend must use a reviewed implementation that validates:

- Cryptographic signature and permitted algorithm.
- Exact issuer and API audience.
- Expiration and not-before timestamps.
- Approved tenant policy.
- Signing key selection from validated trusted JWKS metadata.
- Required scopes or application roles.
- Appropriate authorization for the requested endpoint.

Unverified token claims must never control metadata URLs or JWKS destinations.

### 3.5 Deployment controls

Before integration is approved, confirm:

- HTTPS and certificate ownership.
- Trusted reverse-proxy settings.
- Exact allowed frontend CORS origins.
- Secure configuration and secret storage.
- Audit events with stable subject attribution.
- Session and browser storage behavior.
- Logout behavior and error handling.
- Security review and end-to-end test plan.

## 4. Required tests

- Unauthenticated backend requests remain rejected.
- Invalid signature, issuer, audience, expiry, not-before, tenant, and signing key are rejected.
- Missing scope or application role is rejected.
- Browser-supplied role changes do not grant permissions.
- JWKS refresh, cache expiry, unknown-key, and provider-failure cases fail safely.
- Frontend sign-in, token acquisition, API request, expiry, denial, and logout behavior are tested.
- No test depends on contacting a real tenant unless separately approved.

## 5. Approval gates

Gate A: Identity administrator confirms tenant and application registrations.
Gate B: API audience, issuer, permissions, and frontend redirect URIs are approved.
Gate C: HTTPS, proxy, CORS, audit, and secret-storage design are approved.
Gate D: Reviewed token verification and authorization integration is implemented.
Gate E: Automated regression and approved end-to-end tests pass.
Gate F: Security and deployment owners approve release.

Production authentication must remain fail-closed until all required gates are satisfied.

## 6. Current decision

Status: DESIGN ONLY - ORGANIZATION CONFIGURATION AND SECURITY APPROVAL PENDING.
