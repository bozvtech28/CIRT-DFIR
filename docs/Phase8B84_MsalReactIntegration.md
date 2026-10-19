# Phase 8B.84 - React MSAL Integration

- Adds a React MSAL bootstrap and sign-in/sign-out controls.
- Requests an API access token silently for the active account.
- Sends the token in the Authorization Bearer header for the case-list request.
- Missing/placeholder configuration prevents MSAL initialization.
- Backend token verification and role mapping remain server-side.
- The backend must remain fail-closed until trusted verification and role mapping are integrated and tested.
- No tenant credentials, client secrets, or private keys are stored in frontend code.
- Live sign-in requires approved tenant ID, SPA client ID, API scope, redirect URI, and app registration configuration.
- Existing App.tsx layout and footer are preserved except for routing the existing case-list fetch through authenticatedFetch.
