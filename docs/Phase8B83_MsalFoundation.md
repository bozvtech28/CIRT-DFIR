# Phase 8B.83 - MSAL Authentication Foundation

## Scope
This phase adds a guarded configuration module and a silent API-token helper.
It does not connect them to the application entry point or protected API routes.

## Configuration
Required Vite variables:
- VITE_ENTRA_TENANT_ID
- VITE_ENTRA_CLIENT_ID
- VITE_ENTRA_API_SCOPE
- VITE_ENTRA_REDIRECT_URI

Only public identifiers and scopes belong in frontend Vite variables.
Never place client secrets, private keys, or certificates in frontend configuration.

## Security boundaries
- Placeholder or invalid configuration prevents MSAL configuration from being returned.
- Token helper requires an existing MSAL account and requests the configured API scope.
- This helper does not perform interactive login or call the backend.
- Browser-side roles are not authoritative.
- Backend token verification and role mapping must remain server-side.
- Backend authentication remains fail-closed until trusted token verification,
  issuer/audience/tenant checks, approved role mapping, and audit attribution
  are integrated and tested.

## Not enabled in this phase
- No MsalProvider or login UI integration
- No API bearer-token attachment
- No tenant/network calls
- No production authentication
- No changes to App.tsx, main.tsx, API routes, or the BozV footer
