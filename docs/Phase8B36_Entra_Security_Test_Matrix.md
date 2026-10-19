# Phase 8B.36 — Entra Security Test Matrix

## Authentication tests

- [ ] Missing bearer token returns HTTP 401
- [ ] Malformed bearer token returns HTTP 401
- [ ] Invalid JWT signature is rejected
- [ ] Unknown signing key ID is rejected
- [ ] Disallowed JWT algorithm is rejected
- [ ] Expired access token is rejected
- [ ] Future not-before claim is rejected
- [ ] Incorrect issuer is rejected
- [ ] Incorrect audience is rejected
- [ ] Incorrect tenant is rejected
- [ ] Missing required claims are rejected
- [ ] ID token is not accepted as an API access token
- [ ] Untrusted token-supplied key URLs are ignored

## Authorization tests

- [ ] Viewer can read permitted cases
- [ ] Viewer cannot update cases
- [ ] Analyst can read permitted cases
- [ ] Analyst can update permitted cases
- [ ] Analyst cannot manage users
- [ ] Admin permissions follow approved policy
- [ ] Unknown role is denied
- [ ] Missing role is denied where a role is required
- [ ] Browser-supplied roles cannot elevate privileges

## JWKS and rotation tests

- [ ] Trusted discovery metadata validated
- [ ] Trusted JWKS endpoint configured
- [ ] HTTPS certificate validation enforced
- [ ] Network timeout enforced
- [ ] Response-size limit enforced
- [ ] Invalid JWKS document rejected
- [ ] Unknown key ID rejected
- [ ] Rotation overlap supported
- [ ] Removed signing key no longer trusted after approved rotation
- [ ] Key retrieval failure fails closed

## Audit and deployment tests

- [ ] Audit actor derived from verified identity
- [ ] Audit events preserve authorization decisions
- [ ] No secrets or tokens written to logs
- [ ] HTTPS deployment verified
- [ ] CORS restricted to approved origins
- [ ] Reverse-proxy security reviewed
- [ ] Frontend token acquisition reviewed
- [ ] Security approval recorded
- [ ] Production deployment approval recorded

## Current execution status

This is a proposed test matrix, not evidence that the
listed production tests have been executed.
