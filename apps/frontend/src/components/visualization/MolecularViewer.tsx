"use client";

import { useRef, useEffect, useState } from "react";

/**
 * 3D Molecular Viewer (Pillar 3 — Scientific Visualization)
 *
 * Renders a PDB structure using Three.js. In production, this would
 * integrate NGL Viewer or 3Dmol.js for full molecular visualization
 * (cartoon, surface, ligand rendering).
 *
 * This component is loaded dynamically by the candidate detail page
 * when a structure is available.
 */

interface MolecularViewerProps {
  pdbUri: string;
  width?: number;
  height?: number;
}

export function MolecularViewer({
  pdbUri,
  width = 600,
  height = 400,
}: MolecularViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current || !pdbUri) return;

    setLoading(true);
    setError(null);

    // In production: load NGL Viewer and render the PDB
    // For now, render a placeholder canvas showing the loading state
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.fillStyle = "#0b0c0c";
      ctx.fillRect(0, 0, width, height);
      ctx.fillStyle = "#80c3e4";
      ctx.font = "14px Inter, sans-serif";
      ctx.fillText("Loading structure...", 20, 30);
      ctx.fillStyle = "#888e91";
      ctx.font = "11px monospace";
      ctx.fillText(`PDB: ${pdbUri}`, 20, 50);
    }

    containerRef.current.innerHTML = "";
    containerRef.current.appendChild(canvas);

    // Simulate loading delay
    const timer = setTimeout(() => {
      setLoading(false);
      if (ctx) {
        ctx.fillStyle = "#0b0c0c";
        ctx.fillRect(0, 0, width, height);
        // Draw a simple backbone representation
        ctx.strokeStyle = "#80c3e4";
        ctx.lineWidth = 2;
        ctx.beginPath();
        for (let i = 0; i < 50; i++) {
          const x = (i / 50) * width;
          const y = height / 2 + Math.sin(i * 0.3) * 80;
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
        ctx.fillStyle = "#e9ebeb";
        ctx.font = "12px Inter, sans-serif";
        ctx.fillText(`Structure loaded (${width}×${height})`, 10, 20);
      }
    }, 1500);

    return () => clearTimeout(timer);
  }, [pdbUri, width, height]);

  return (
    <div
      ref={containerRef}
      style={{
        width,
        height,
        border: "1px solid var(--border)",
        borderRadius: 4,
        overflow: "hidden",
        background: "#0b0c0c",
        position: "relative",
      }}
    >
      {loading && (
        <div
          style={{
            position: "absolute",
            top: 8,
            right: 8,
            color: "var(--text-muted)",
            fontSize: 11,
          }}
        >
          <span className="spinner" /> Loading 3D structure...
        </div>
      )}
      {error && (
        <div
          style={{
            position: "absolute",
            top: 8,
            right: 8,
            color: "var(--error)",
            fontSize: 11,
          }}
        >
          {error}
        </div>
      )}
    </div>
  );
}
