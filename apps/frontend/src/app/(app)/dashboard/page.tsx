"use client";
export default function DashboardPage() {
  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 4 }}>Dashboard</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 24 }}>
        Self-learning vaccine digital twin platform.
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
        <div className="card"><div style={{ color: "var(--text-muted)", fontSize: 11 }}>PROJECTS</div><div style={{ fontSize: 36, fontWeight: 800, color: "var(--accent)" }}>0</div></div>
        <div className="card"><div style={{ color: "var(--text-muted)", fontSize: 11 }}>CANDIDATES</div><div style={{ fontSize: 36, fontWeight: 800, color: "var(--accent)" }}>0</div></div>
        <div className="card"><div style={{ color: "var(--text-muted)", fontSize: 11 }}>MODULES</div><div style={{ fontSize: 36, fontWeight: 800, color: "var(--accent)" }}>31</div></div>
        <div className="card"><div style={{ color: "var(--text-muted)", fontSize: 11 }}>ALERTS</div><div style={{ fontSize: 36, fontWeight: 800, color: "var(--accent)" }}>0</div></div>
      </div>
    </div>
  );
}
