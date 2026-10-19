import { useEffect, useMemo, useState } from "react";

type DemoCase = {
  case_id: string;
  title: string;
  severity: string;
  status: string;
};

const navigation = [
  "Dashboard",
  "Cases",
  "Assets & Scans",
  "Findings",
  "Evidence Vault",
  "Response Actions",
  "Reports",
  "Administration",
];

const fallbackCases: DemoCase[] = [
  { case_id: "DEMO-2026-001", title: "Endpoint Alert Review", severity: "High", status: "Investigating" },
  { case_id: "DEMO-2026-002", title: "Suspicious Login Review", severity: "Medium", status: "Triage" },
  { case_id: "DEMO-2026-003", title: "Mailbox Rule Assessment", severity: "Medium", status: "Evidence review" },
];

const API_BASE = "";

function App() {
  const [page, setPage] = useState("Dashboard");
  const [search, setSearch] = useState("");
  const [cases, setCases] = useState<DemoCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [usingFallback, setUsingFallback] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [caseSeverityFilter, setCaseSeverityFilter] = useState("All");
  const [caseStatusFilter, setCaseStatusFilter] = useState("All");
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadCases() {
      setLoading(true);
      setError("");
      setUsingFallback(false);

      try {
        const response = await fetch(`${API_BASE}/api/v1/demo/cases`, {
          headers: { Accept: "application/json" },
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`API returned HTTP ${response.status}`);
        }

        const payload: unknown = await response.json();

        if (
          !Array.isArray(payload) ||
          !payload.every(
            (item) =>
              item !== null &&
              typeof item === "object" &&
              typeof item.case_id === "string" &&
              typeof item.title === "string" &&
              typeof item.severity === "string" &&
              typeof item.status === "string",
          )
        ) {
          throw new Error("Unexpected API response format.");
        }

        if (!controller.signal.aborted) setCases(payload as DemoCase[]);
      } catch (err) {
        if (controller.signal.aborted) return;

        const message = err instanceof Error ? err.message : "Unknown connection error";
        setError(`Could not load cases from the localhost development API: ${message}`);
        setCases(fallbackCases);
        setUsingFallback(true);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    void loadCases();
    return () => controller.abort();
  }, [refreshKey]);

  const filteredCases = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return cases;

    return cases.filter((item) =>
      `${item.case_id} ${item.title} ${item.severity} ${item.status}`
        .toLowerCase()
        .includes(term),
    );
  }, [cases, search]);

  const severityOptions = useMemo(
    () => ["All", ...Array.from(new Set(cases.map((item) => item.severity))).sort()],
    [cases],
  );
  const statusOptions = useMemo(
    () => ["All", ...Array.from(new Set(cases.map((item) => item.status))).sort()],
    [cases],
  );
  const visibleCases = useMemo(() => filteredCases.filter((item) =>
    (caseSeverityFilter === "All" || item.severity === caseSeverityFilter) &&
    (caseStatusFilter === "All" || item.status === caseStatusFilter)
  ), [filteredCases, caseSeverityFilter, caseStatusFilter]);
  const selectedCase = cases.find((item) => item.case_id === selectedCaseId) ?? null;

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">DFIR</div>
          <div><strong>CIRT RESPONSE</strong><small>Investigation Platform</small></div>
        </div>
        <p className="nav-label">WORKSPACE</p>
        <nav aria-label="Main navigation">
          {navigation.map((item) => (
            <button
              className={`nav-item ${page === item ? "active" : ""}`}
              key={item}
              onClick={() => setPage(item)}
              aria-current={page === item ? "page" : undefined}
            >
              <span aria-hidden="true">{item === "Dashboard" ? "▦" : "◇"}</span>
              {item}
            </button>
          ))}
        </nav>
        <div className="side-note">
          <span className="status-dot" /> Development mode
          <small>Synthetic records only. No scanner or evidence repository connected.</small>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <span>CIRT / DFIR <span className="muted"> / {page}</span></span>
          <span className="demo-label">DEVELOPMENT SCAFFOLD</span>
        </header>

        <div className="content">
          <div className="page-heading">
            <div>
              <span className="eyebrow">SECURITY OPERATIONS</span>
              <h1>{page === "Dashboard" ? "Incident Response Overview" : page}</h1>
              <p className="muted">Case management and forensic workflow development.</p>
            </div>
          </div>

          <div className="notice" role="note">
            DEVELOPMENT ONLY — records are synthetic. This is not an operational
            incident-response or evidence-management system.
          </div>

          {page === "Dashboard" || page === "Cases" ? (
            <>
              <div className="metrics">
                <article className="metric"><span>Cases returned</span><strong>{loading ? "…" : cases.length}</strong><small>Current case-list response</small></article>
                <article className="metric"><span>High severity</span><strong>{cases.filter((item) => item.severity.toLowerCase() === "high").length}</strong><small>Synthetic records only</small></article>
                <article className="metric"><span>Investigating</span><strong>{cases.filter((item) => item.status.toLowerCase() === "investigating").length}</strong><small>Returned case data</small></article>
                <article className="metric"><span>API state</span><strong>{loading ? "Loading" : usingFallback ? "Offline" : "Ready"}</strong><small>Local development endpoint</small></article>
              </div>

              {loading && <section className="panel" role="status">Loading synthetic cases from the development API…</section>}

              {error && (
                <section className="panel" role="alert">
                  <h2>API connection notice</h2>
                  <p>{error}</p>
                  <p>Showing clearly identified local synthetic fallback records.</p>
                </section>
              )}

              <section className="panel">
                <div className="panel-heading">
                  <h2>Case Register</h2>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <input
                      aria-label="Search synthetic cases"
                      placeholder="Search cases..."
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                    />
                    <select
                      aria-label="Filter cases by severity"
                      value={caseSeverityFilter}
                      onChange={(event) => setCaseSeverityFilter(event.target.value)}
                    >
                      {severityOptions.map((value) => <option key={value} value={value}>{value === "All" ? "All severities" : value}</option>)}
                    </select>
                    <select
                      aria-label="Filter cases by status"
                      value={caseStatusFilter}
                      onChange={(event) => setCaseStatusFilter(event.target.value)}
                    >
                      {statusOptions.map((value) => <option key={value} value={value}>{value === "All" ? "All statuses" : value}</option>)}
                    </select>
                    <button type="button" onClick={() => setRefreshKey((value) => value + 1)} disabled={loading}>
                      {loading ? "Loading…" : "Refresh"}
                    </button>
                  </div>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead><tr><th>Case ID</th><th>Incident</th><th>Severity</th><th>Status</th></tr></thead>
                    <tbody>
                      {visibleCases.map((item) => (
                        <tr key={item.case_id} className={selectedCaseId === item.case_id ? "selected-case-row" : ""}>
                          <td>
                            <button
                              type="button"
                              className="case-link"
                              onClick={() => setSelectedCaseId((current) => current === item.case_id ? null : item.case_id)}
                              aria-expanded={selectedCaseId === item.case_id}
                            >
                              {item.case_id}
                            </button>
                          </td>
                          <td>{item.title}</td>
                          <td><span className={`pill ${item.severity.toLowerCase()}`}>{item.severity}</span></td>
                          <td>{item.status}</td>
                        </tr>
                      ))}
                      {!loading && visibleCases.length === 0 && <tr><td colSpan={4}>No cases match the current search and filters.</td></tr>}
                    </tbody>
                  </table>
                </div>
                <p className="muted">
                  Showing {visibleCases.length} of {cases.length} synthetic cases.
                  {" "}{usingFallback ? "Data source: local fallback; API unavailable." : "Data source: development API response."}
                </p>
              </section>

              {selectedCase && (
                <section className="panel case-detail-panel" aria-labelledby="case-detail-title">
                  <div className="panel-heading">
                    <h2 id="case-detail-title">Case details</h2>
                    <button type="button" onClick={() => setSelectedCaseId(null)}>Close details</button>
                  </div>
                  <dl className="case-detail-grid">
                    <div><dt>Case ID</dt><dd>{selectedCase.case_id}</dd></div>
                    <div><dt>Incident</dt><dd>{selectedCase.title}</dd></div>
                    <div><dt>Severity</dt><dd><span className={`pill ${selectedCase.severity.toLowerCase()}`}>{selectedCase.severity}</span></dd></div>
                    <div><dt>Status</dt><dd>{selectedCase.status}</dd></div>
                  </dl>
                  <p className="muted">Read-only details from synthetic development data. Editing and persistence are not enabled.</p>
                </section>
              )}
            </>
          ) : (
            <section className="panel placeholder">
              <h2>{page}</h2>
              <p>This module is a scaffold; its workflow has not been implemented.</p>
              <p>Production access controls, audit logging, evidence safeguards, and security review are required before operational use.</p>
            </section>
          )}
        </div>
        <footer className="app-footer">
          <div>CIRT DFIR · Development scaffold · Synthetic data · Not for operational use</div>
          <div className="bozv-signature">
            <span>Developed by: <strong>BozV</strong></span>
            <span>Powered by: <strong>BozV</strong></span>
          </div>
        </footer>
      </main>
    </div>
  );
}

export default App;