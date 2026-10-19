# Backend test fixture isolation patch

## Finding
The previous autouse fixture in `platform/backend/tests/conftest.py` unconditionally overrode `get_current_principal` with a synthetic analyst. That changed the default behavior of every protected API request during pytest unless a test remembered to clear the override. It could therefore hide a fail-closed production gate from unrelated/legacy tests and made suite behavior sensitive to override cleanup/order.

## Change made
- Replaced the global synthetic identity with an autouse fixture that only clears dependency overrides before and after each test.
- Added a synthetic identity override directly in `test_api.py::test_demo_cases_are_synthetic`, the only test in that file that explicitly exercises successful protected case-list retrieval.
- Left production authentication unchanged and fail-closed.
- Dedicated auth-gate and OIDC-negative tests continue to assert unauthenticated/malformed requests receive HTTP 401.

## Validation
Source-level assertions verified the files now contain no global synthetic identity override, the legacy case-list test defines its own synthetic override, and the existing auth-gate tests retain HTTP 401 assertions. The backend pytest suite could not be executed in this environment because the repository is available through the GitHub connector rather than a local checkout with a confirmed Python test environment. Do not treat these source checks as a passing test run.
