"use client";
export default function CandidatesPage() {
  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 16 }}>Vaccine Candidates</h1>
      <div className="card" style={{ textAlign: "center", padding: 40 }}>
        <p style={{ color: "var(--text-muted)" }}>No candidates yet.</p>
      </div>
    </div>
  );
}
