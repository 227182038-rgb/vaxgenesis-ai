"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@vaxgenesis.ai");
  const [password, setPassword] = useState("admin123");

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg)" }}>
      <div className="card" style={{ width: 400, padding: 32 }}>
        <div style={{ fontSize: 28, fontWeight: 800, marginBottom: 24, textAlign: "center" }}>
          <span style={{ color: "var(--accent)" }}>◆</span> VaxGenesis AI
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
          <button className="primary" onClick={() => router.push("/dashboard")}>Sign In</button>
        </div>
        <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 16, textAlign: "center" }}>
          Default: admin@vaxgenesis.ai / admin123
        </div>
      </div>
    </div>
  );
}
