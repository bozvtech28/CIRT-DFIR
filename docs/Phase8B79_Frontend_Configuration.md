# Phase 8B.79 — Frontend Configuration Template

## Purpose

This document defines placeholder settings for a future Microsoft Entra SPA
integration. It does not implement sign-in, acquire tokens, or enable API access.

## Required organization-approved values

- Tenant ID: approved Microsoft Entra tenant identifier.
- SPA client ID: application registration for the frontend.
- API scope: approved delegated scope exposed by the backend API registration.
- Redirect URI: must exactly match an approved SPA redirect URI.
- API base URL: must match the approved frontend/backend deployment arrangement.

## Security rules

- Values prefixed with `VITE_` are public browser configuration, not secrets.
- Never place client secrets, private keys, certificates, or access tokens in
  frontend environment variables.
- The localhost redirect URI is for local development only; production must
  use the approved HTTPS URI.
- A configured client ID or scope does not establish that the API validates
  access tokens.
- Keep the backend authentication dependency fail-closed until signature,
  issuer, audience, tenant, expiry, role mapping, audit attribution, and
  deployment controls are integrated and reviewed.
- Do not invent or guess tenant IDs, client IDs, scopes, or production URLs.

## Current status

The configuration template contains placeholders. MSAL dependencies and
sign-in/token acquisition are not installed or implemented by this phase.
