# Phase 8B.21 — Microsoft Entra Frontend Integration Plan

## Current status
The frontend is a React/Vite application. Phase 8B.20 found no established MSAL/OIDC sign-in implementation. The backend authentication gate remains fail-closed. Tenant and application registration details must be confirmed by the Entra administrator.

## Required administrator-approved configuration
- Tenant ID
- Frontend application client ID
- Backend API application ID or audience
- Approved redirect URI
- Backend API scope and consent
- Approved app-role definitions and assignments
- Deployment HTTPS and reverse-proxy arrangement

## Implementation sequence
1. Confirm the approved Entra app registrations and permissions.
2. Integrate the supported MSAL browser/React libraries using authorization code flow with PKCE.
3. Request an access token specifically for the backend API; do not use an ID token as an API access token.
4. Implement trusted backend token verification using Microsoft discovery/JWKS, signature, algorithm, issuer, audience, time, and tenant checks.
5. Map validated app-role claims to server-side RBAC.
6. Attribute audit events to the verified principal.
7. Test invalid tokens, expired tokens, wrong issuer/audience, missing roles, role denials, and normal sign-in/sign-out.
8. Obtain security review before network deployment.

## Security restrictions
- Keep protected routes fail-closed until production authentication is implemented.
- Never trust roles supplied by the browser or request body.
- Do not place client secrets or private keys in frontend code or Vite VITE_* variables.
- Do not use the synthetic JWT harness as a production verifier.
- Do not expose the API to the organizational network before authentication, authorization, HTTPS, and security tests are approved.
- This document is a plan, not a production implementation or deployment approval.
