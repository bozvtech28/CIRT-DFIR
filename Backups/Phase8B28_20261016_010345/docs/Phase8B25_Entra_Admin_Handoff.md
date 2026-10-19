# Phase 8B.25 — Microsoft Entra Administrator Handoff

Purpose: Collect approved application-registration details before implementation.
This is a planning document, not an authentication implementation.

## Required details from the Entra administrator

- [ ] Tenant ID (directory/tenant GUID)
- [ ] Frontend single-page application client ID
- [ ] Backend API application/client ID or exact accepted audience
- [ ] Approved API scope, for example the administrator-approved exposed API scope
- [ ] Approved redirect URI for the development environment
- [ ] Approved post-logout redirect URI
- [ ] Supported account type and tenant restrictions
- [ ] API permission consent status
- [ ] App-role values for Administrator, DFIR Analyst, and Viewer
- [ ] Test accounts assigned to each approved role
- [ ] HTTPS and reverse-proxy plan for internal deployment
- [ ] Approved CORS origins, if cross-origin deployment is required

## Security requirements

- Never provide client secrets, private keys, passwords, or access tokens.
- Do not place secrets in React code or Vite VITE_* variables.
- The browser frontend must request an access token for the backend API.
- The backend must validate token signature, permitted algorithm, issuer,
  audience, expiry/not-before, tenant, and required claims using trusted metadata.
- Only validated Entra app-role claims may grant backend permissions.
- Keep protected routes fail-closed until implementation and tests pass.
- Do not expose the backend to the organizational network before security review.

## Required tests before approval

- [ ] No token returns 401
- [ ] Malformed or incorrectly signed token returns 401
- [ ] Wrong issuer, audience, tenant, or expired token is rejected
- [ ] Viewer cannot update cases
- [ ] Analyst and Administrator permissions match the approved policy
- [ ] Missing or unknown roles are denied
- [ ] Audit events record the validated principal
- [ ] Login, logout, and token renewal work correctly
- [ ] HTTPS, CORS, logging, and deployment settings reviewed

Do not mark this packet complete until the Entra administrator confirms the
application registration and permission settings.
