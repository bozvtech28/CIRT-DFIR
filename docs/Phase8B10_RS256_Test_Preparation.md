# Phase 8B.10 — Synthetic RS256 test preparation

This phase creates an isolated test-only RS256 harness using ephemeral RSA keys.
It does not authenticate users and is not wired to application routes.

Covered test behavior:
- RS256 signature verification with explicit trusted public keys
- Signature and payload tampering
- Expired token, issuer, audience, and not-before checks
- Unknown key ID and disallowed algorithm rejection
- Key rotation overlap and retired-key rejection

Not covered:
- OIDC discovery metadata
- JWKS fetching, cache behavior, or network failure
- Provider-specific issuer/audience configuration
- Production token verification integration
- Authentication/authorization behavior through real OIDC tokens

The existing application gate must remain fail-closed. Do not use this test
harness in production. No server or identity provider is contacted.
