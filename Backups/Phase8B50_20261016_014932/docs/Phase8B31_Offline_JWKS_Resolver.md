# Phase 8B.31 — Offline JWKS Resolver Design

## Scope
- Select an RSA signing key using the JWT header kid.
- Accept RS256 only.
- Reject unknown kid, malformed JWT headers, duplicate key IDs, malformed
  JWKS structures, non-RSA keys, encryption-only keys, and private key fields.
- Exercise key rotation overlap and key removal using synthetic test keys.
- Make no network requests and do not wire this resolver into API routes.

## Trust limitation
A JWKS document is not trusted merely because it parses. Production use requires
an administrator-approved Microsoft Entra issuer and discovery/JWKS URL, HTTPS,
issuer and tenant binding, safe caching and rotation, and a security review.
Never derive a trusted URL from unvalidated token claims. Never accept a JWKS
document from a request body or browser.

## Not implemented
- Live Microsoft OpenID Connect discovery
- Production JWKS download, cache, or refresh
- Tenant, issuer, and audience deployment configuration
- Frontend sign-in or access-token handling
- Production role mapping or audit identity attribution
- Production route integration or deployment approval

The existing API authentication gate must remain fail-closed.
