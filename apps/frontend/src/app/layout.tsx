import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VaxGenesis AI",
  description: "Self-learning vaccine digital twin platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
