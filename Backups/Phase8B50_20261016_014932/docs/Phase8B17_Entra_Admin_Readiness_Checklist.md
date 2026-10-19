# Microsoft Entra ID — CIRT DFIR API Readiness Checklist

## Current status
- Authentication gate: fail-closed.
- Production OIDC token verification: not implemented.
- Trusted Entra role mapping: not implemented.
- Tenant ID and API client ID: not configured in the checked environment.
- Do not expose the API to the organizational network yet.

## Information to obtain from the Entra administrator
- [ ] Approved Microsoft Entra tenant ID.
- [ ] Approved API application (client) ID.
- [ ] Confirmation of the API app registration and intended audience.
- [ ] Approved issuer/tenant configuration for the organization.
- [ ] Approved app-role names and assignments for Administrator, DFIR Analyst, and Viewer.
- [ ] Confirmation of the intended frontend sign-in flow and API access-token audience.
- [ ] Approved redirect URI(s), if required by the chosen sign-in flow.
- [ ] Approval of the organization's deployment location and TLS/reverse-proxy arrangement.

## Required implementation and validation before deployment
- [ ] Use a maintained OIDC/JWT validation library to verify token signatures against trusted Microsoft signing keys.
- [ ] Validate issuer, audience, expiry, not-before, permitted algorithms, and tenant restrictions.
- [ ] Map roles only from validated, approved Entra claims; never trust client-supplied roles.
- [ ] Enforce authentication and role-based authorization on every protected API route.
- [ ] Record the verified subject in case-update audit events instead of DEVELOPMENT-API.
- [ ] Test missing, malformed, expired, wrong-issuer, wrong-audience, invalid-signature, and wrong-role tokens.
- [ ] Verify health endpoint exposure is approved and no sensitive information is returned.
- [ ] Review frontend login, token handling, HTTPS, CORS, logging, and deployment settings.
- [ ] Obtain security review and deployment approval.

## Safety
Never place client secrets, access tokens, private keys, or passwords in this checklist or a source-control repository. Use the organization's approved secret/configuration management process.
