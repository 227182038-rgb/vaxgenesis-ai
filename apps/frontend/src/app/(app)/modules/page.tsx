"use client";
import { useEffect, useState } from "react";

export default function ModulesPage() {
  const [modules, setModules] = useState([]);
  useEffect(() => {
    // In production: fetch from /api/v2/modules
    setModules([
      { id: "genome_analysis", name: "Genome Analysis", category: "perception" },
      { id: "autoimmunity_screening", name: "Autoimmunity Screening", category: "reasoning" },
      { id: "proteasome_cleavage", name: "Proteasome Cleavage", category: "reasoning" },
      { id: "glycosylation_analysis", name: "Glycosylation Analysis", category: "action" },
      { id: "subcellular_localization", name: "Subcellular Localization", category: "perception" },
    ]);
  }, []);

  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 16 }}>Pipeline Modules</h1>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 12 }}>
        {modules.map((m: any) => (
          <div key={m.id} className="card">
            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{m.category}</div>
            <h3 style={{ fontSize: 14 }}>{m.name}</h3>
          </div>
        ))}
      </div>
    </div>
  );
}
