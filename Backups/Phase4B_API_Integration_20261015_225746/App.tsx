import { useState } from "react";

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

const demoCases = [
  { id: "DEMO-2026-001", title: "Endpoint Alert Review", severity: "High", status: "Investigating" },
  { id: "DEMO-2026-002", title: "Suspicious Login Review", severity: "Medium", status: "Triage" },
  { id: "DEMO-2026-003", title: "Mailbox Rule Assessment", severity: "Medium", status: "Evidence review" },
  { id: "DEMO-2026-004", title: "Policy Compliance Check", severity: "Low", status: "Monitoring" },
];

function App() {
  const [page, setPage] = useState("Dashboard");
  const [search, setSearch] = useState("");

  const filteredCases = demoCases.filter((item) =>
    `${item.id} ${item.title} ${item.status}`
      .toLowerCase()
      .includes(search.toLowerCase()),
  );

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
            >
              <span aria-hidden="true">{item === "Dashboard" ? "▦" : "◇"}</span>
              {item}
            </button>
          ))}
        </nav>
        <div className="side-note">
          <span className="status-dot" /> Prototype mode
          <small>Fictional records only. No live systems connected.</small>
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

          <div className="notice">
            DEVELOPMENT ONLY — all displayed records are synthetic. This frontend is
            not connected to a scanner, production API, or evidence repository.
          </div>

          {page === "Dashboard" || page === "Cases" ? (
            <>
              <div className="metrics">
                <article className="metric"><span>Open Cases</span><strong>08</strong><small>Demo metric</small></article>
                <article className="metric"><span>Assets in Scope</span><strong>24</strong><small>Fictional inventory</small></article>
                <article className="metric"><span>Priority Findings</span><strong>05</strong><small>Sample metric</small></article>
                <article className="metric"><span>Evidence Items</span><strong>37</strong><small>Demo records only</small></article>
              </div>

              <section className="panel">
                <div className="panel-heading">
                  <h2>Case Register</h2>
                  <input
                    aria-label="Search demo cases"
                    placeholder="Search demo cases..."
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                  />
                </div>
                <div className="table-wrap">
                  <table>
                    <thead><tr><th>Case ID</th><th>Incident</th><th>Severity</th><th>Status</th></tr></thead>
                    <tbody>
                      {filteredCases.map((item) => (
                        <tr key={item.id}>
                          <td>{item.id}</td><td>{item.title}</td>
                          <td><span className={`pill ${item.severity.toLowerCase()}`}>{item.severity}</span></td>
                          <td>{item.status}</td>
                        </tr>
                      ))}
                      {filteredCases.length === 0 && (
                        <tr><td colSpan={4}>No matching demo cases.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          ) : (
            <section className="panel placeholder">
              <h2>{page}</h2>
              <p>This module is a scaffold only. API integration is not implemented.</p>
              <p>Production access controls, audit logging, and security review are required before operational use.</p>
            </section>
          )}
        </div>
        <footer> CIRT DFIR · Development scaffold · Synthetic data · Not for operational use</footer>
      </main>
    </div>
  );
}

export default App;
