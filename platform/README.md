# CIRT DFIR Platform Scaffold

Separate development scaffold. The original static prototype remains in `../apps/web-prototype/`.

## Frontend
- React + TypeScript + Vite
- Synthetic case records only
- No production API integration yet

## Backend
- FastAPI with a health endpoint and synthetic demo cases
- No database, authentication, evidence upload, or scanner integration yet

## Safety
This is not a production DFIR system. Do not add real case data or evidence.
Do not expose the development API to a network. Authentication, authorization,
audit logging, evidence integrity, safe filesystem handling, and security testing
must be designed and reviewed before operational use.
