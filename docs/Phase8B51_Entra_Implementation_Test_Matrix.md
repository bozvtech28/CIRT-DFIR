# Phase 8B.51 - Entra Implementation Security Test Matrix

| Area | Required test | Expected result |
|---|---|---|
| Missing credentials | Call protected endpoint without a bearer token | 401; no data returned |
| Malformed token | Submit malformed bearer token | 401 |
| Signature | Submit token with invalid signature | 401 |
| Algorithm | Submit token using an unapproved algorithm | 401 |
| Expiry | Submit expired token | 401 |
| Not-before | Submit token before its valid time | 401 |
| Issuer | Submit token with unexpected issuer | 401 |
| Audience | Submit token for another API | 401 |
| Tenant | Submit token from an unapproved tenant | 401 |
| Required claims | Omit required subject or tenant claims | 401 |
| Token type | Submit an ID token where an API access token is required | 401 |
| Signing key | Use unknown key ID; refresh trusted metadata/JWKS safely | Reject unless a trusted matching key is obtained |
| Key rotation | Test overlapping keys and retired keys | Accept only currently trusted valid keys |
| Role mapping | Submit unknown or malformed app roles | Deny by default |
| Viewer | Read permitted demo cases | Allowed only with validated Viewer policy |
| Viewer update | Attempt case update | 403 |
| Analyst | Read and update according to approved policy | Allowed only for assigned permissions |
| Admin | Test each explicitly approved administrative permission | Allowed only for approved permissions |
| Audit | Perform an authorized update | Audit actor comes from validated identity |
| Token privacy | Cause authentication failures | No token or secret appears in logs |
| Frontend | Sign in and acquire the approved API access token | Correct API audience/scope |
| Frontend API | Call protected endpoint with valid access token | Expected authorized response |
| CORS/HTTPS | Test unapproved origin and non-HTTPS deployment path | Rejected or redirected according to approved policy |
| Regression | Run complete backend suite and frontend build | Both pass |

All tests must use synthetic credentials or an explicitly approved test tenant.
Do not use production tokens or secrets in automated test output.

This matrix is a planned test specification. Passing status must be recorded only
after each test has actually been implemented and executed.