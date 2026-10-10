"use client";

import { useState } from "react";

/**
 * Epitope Explanation Viewer (Pillar 3 — Explainable AI Visualization)
 *
 * Renders a SHAP-style waterfall chart showing how each feature
 * contributed to an epitope's predicted score.
 *
 * Each bar represents a feature's attribution:
 *   - Positive (blue, right): pushed the score UP
 *   - Negative (red, left): pushed the score DOWN
 *   - Bar width = |contribution|
 */

interface FeatureAttribution {
  feature_name: string;
  feature_value: string | number;
  attribution: number;
  contribution_pct: number;
}

interface EpitopeExplanationViewerProps {
  attributions: FeatureAttribution[];
  score: number;
  threshold?: number;
}

export function EpitopeExplanationViewer({
  attributions,
  score,
  threshold = 0.5,
}: EpitopeExplanationViewerProps) {
  const [hoveredBar, setHoveredBar] = useState<number | null>(null);

  const maxAbs = Math.max(...attributions.map((a) => Math.abs(a.attribution)), 0.001);

  return (
    <div className="card" style={{ padding: 16 }}>
      <h3 style={{ fontSize: 14, marginBottom: 8 }}>Feature Attribution (SHAP)</h3>
      <div style={{ marginBottom: 12, fontSize: 12 }}>
        <span className="text-muted">Predicted score: </span>
        <span
          style={{
            fontFamily: "monospace",
            fontWeight: 700,
            color: score >= threshold ? "var(--success)" : "var(--warning)",
          }}
        >
          {score.toFixed(4)}
        </span>
        <span className="text-muted"> (threshold: {threshold})</span>
      </div>

      {/* Waterfall bars */}
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {attributions.slice(0, 10).map((attr, i) => {
          const isPositive = attr.attribution > 0;
          const barWidth = (Math.abs(attr.attribution) / maxAbs) * 50; // max 50% width
          return (
            <div
              key={i}
              style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11 }}
              onMouseEnter={() => setHoveredBar(i)}
              onMouseLeave={() => setHoveredBar(null)}
            >
              {/* Feature name (left) */}
              <div
                style={{
                  width: 140,
                  textAlign: "right",
                  color: hoveredBar === i ? "var(--accent)" : "var(--text)",
                  fontFamily: "monospace",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {attr.feature_name}
              </div>

              {/* Negative bar (left of center) */}
              <div style={{ width: 200, display: "flex", justifyContent: "flex-end" }}>
                {!isPositive && (
                  <div
                    style={{
                      width: `${barWidth * 2}%`,
                      height: 16,
                      background: "var(--accent-warm)",
                      borderRadius: "2px 0 0 2px",
                      opacity: hoveredBar === i ? 1 : 0.8,
                    }}
                  />
                )}
              </div>

              {/* Center line */}
              <div
                style={{
                  width: 1,
                  height: 20,
                  background: "var(--border)",
                }}
              />

              {/* Positive bar (right of center) */}
              <div style={{ width: 200 }}>
                {isPositive && (
                  <div
                    style={{
                      width: `${barWidth * 2}%`,
                      height: 16,
                      background: "var(--accent)",
                      borderRadius: "0 2px 2px 0",
                      opacity: hoveredBar === i ? 1 : 0.8,
                    }}
                  />
                )}
              </div>

              {/* Value (right) */}
              <div
                style={{
                  width: 80,
                  color: "var(--text-muted)",
                  fontFamily: "monospace",
                  fontSize: 10,
                }}
              >
                {attr.attribution > 0 ? "+" : ""}
                {attr.attribution.toFixed(4)}
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div
        style={{
          display: "flex",
          gap: 16,
          marginTop: 12,
          fontSize: 10,
          color: "var(--text-muted)",
        }}
      >
        <div>
          <span
            style={{
              display: "inline-block",
              width: 10,
              height: 10,
              background: "var(--accent)",
              marginRight: 4,
            }}
          />
          Positive contribution (↑ score)
        </div>
        <div>
          <span
            style={{
              display: "inline-block",
              width: 10,
              height: 10,
              background: "var(--accent-warm)",
              marginRight: 4,
            }}
          />
          Negative contribution (↓ score)
        </div>
      </div>
    </div>
  );
}
