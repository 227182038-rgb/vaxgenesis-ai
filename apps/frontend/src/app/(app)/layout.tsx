"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/projects", label: "Projects" },
  { href: "/candidates", label: "Candidates" },
  { href: "/modules", label: "Modules" },
  { href: "/surveillance", label: "Surveillance" },
  { href: "/learning", label: "Learning" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside style={{ width: 240, background: "var(--bg-subtle)", borderRight: "1px solid var(--border)", padding: 20 }}>
        <Link href="/dashboard" style={{ fontWeight: 700, fontSize: 18, color: "var(--text)" }}>
          <span style={{ color: "var(--accent)" }}>◆</span> VaxGenesis
        </Link>
        <nav style={{ marginTop: 20, display: "flex", flexDirection: "column", gap: 4 }}>
          {NAV.map((item) => (
            <Link key={item.href} href={item.href}
              style={{ padding: "8px 12px", borderRadius: 4, color: pathname === item.href ? "var(--accent)" : "var(--text)",
                background: pathname === item.href ? "rgba(128,195,228,0.1)" : "transparent",
                borderLeft: pathname === item.href ? "2px solid var(--accent)" : "2px solid transparent" }}>
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main style={{ flex: 1, padding: 32 }}>{children}</main>
    </div>
  );
}
