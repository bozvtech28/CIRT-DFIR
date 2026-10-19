# Phase 8B.13 — Microsoft Entra ID OIDC Integration Plan

**Project:** CIRT DFIR Professional  
**Target deployment:** Internal organization network  
**Status:** Planning only — production authentication is not implemented  
**Security posture:** Keep the existing fail-closed authentication gate enabled

## 1. Scope

Prepare the integration plan for Microsoft Entra ID using OpenID Connect (OIDC).
This phase does not contact Microsoft, create an app registration, configure tenant
secrets, install packages, change application source, or start a service.

## 2. Required organizational decisions

Before implementation, obtain approval for:

- The organization's Entra tenant and responsible identity administrator.
- The application registration and approved redirect URI, if a browser sign-in flow is selected.
- The expected tenant ID, application/client ID, and exact accepted issuer.
- The intended user audience and whether guest or multi-tenant identities are prohibited.
- The authoritative source of application roles or group assignments.
- The role owners and approval process for Administrator, DFIR Analyst, and Viewer.
- The internal deployment hostname, TLS termination, and trusted proxy configuration.
- The account/session lifecycle, sign-out behavior, and incident-response access revocation process.

Do not place client secrets, private keys, bearer tokens, or other credentials in source code,
PowerShell history, reports, or version control.

## 3. Token validation requirements

The production implementation must use a maintained OIDC/JWT library and trusted Entra
metadata/JWKS obtained from the approved tenant. It must:

- Validate the cryptographic signature using keys obtained through the trusted metadata flow.
- Pin the accepted signing algorithms; never trust the token's algorithm selection by itself.
- Validate the exact issuer and expected audience.
- Validate expiry and applicable not-before/time claims.
- Enforce the approved tenant ID and accepted token type/flow.
- Reject malformed tokens, unknown keys, invalid signatures, wrong issuer/audience, expired
  tokens, and identities from unauthorized tenants.
- Handle key rollover safely and use bounded, controlled metadata/JWKS refresh behavior.
- Avoid logging raw tokens, authorization headers, secrets, or sensitive claims.

Decoding JWT claims without verifying the signature is not authentication.

## 4. Authorization requirements

Map only trusted, validated identity claims or administrator-controlled application-role
assignments to server-side roles. Never accept role names supplied by the browser, URL,
request body, or an unvalidated token.

Proposed permissions, subject to organizational approval:

- Viewer: read approved case records.
- DFIR Analyst: read and update permitted case records.
- Administrator: manage users/roles and access restricted audit records.

Apply authorization to every protected API endpoint. Test both allowed and denied requests.
Keep health-check exposure minimal and document whether it is intentionally public.

## 5. Internal deployment safeguards

Before network deployment, require HTTPS, an approved certificate, secure secret handling,
restricted inbound access, dependency review, audit logging, and operational monitoring.
Review CORS, browser session security, CSRF protections if cookie-based authentication is used,
rate limiting, reverse-proxy trust settings, and error handling against the selected sign-in flow.

Do not expose the current development API to the organization network until the real identity
integration and security review have passed.

## 6. Required test plan

Use synthetic test tokens and controlled test identities for automated tests. Include:

- Valid token for the approved tenant and audience.
- Invalid signature and altered payload.
- Wrong issuer, audience, or tenant.
- Expired token and not-yet-valid token.
- Unknown key ID and key rollover.
- Missing or malformed bearer token.
- Missing, unknown, or unauthorized application role.
- Viewer denied case updates.
- Analyst denied administrative operations.
- Administrator access only to approved administrative operations.
- Authentication and authorization enforced on every protected route.
- No accidental acceptance of caller-created principals in production request paths.

## 7. Current limitations

This plan does not establish that production signature verification, Entra metadata/JWKS
integration, tenant restriction, secure session management, or role mapping exists.
Synthetic RS256 tests validate a test harness only; they do not prove integration with Entra ID.

## 8. Approval gate

Do not enable production authentication or start the service for network access until the
organization has approved the Entra application configuration and role model, the implementation
has passed security and negative tests, and the deployment has been reviewed.