import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";
import { DemoBanner } from "../components/demo_banner";
import { ModeSwitcher } from "../components/mode_switcher";
import { Providers } from "../components/providers";

export const metadata: Metadata = {
  title: "cloudsentinel",
  description: "Interactive cloud security posture + detection lab",
};

const nav = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/scans", label: "Scans" },
  { href: "/policy-doctor", label: "Policy Doctor" },
  { href: "/simulator", label: "Attack Simulator" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-50">
        <Providers>
          <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur">
            <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
              <Link href="/dashboard" className="text-lg font-semibold tracking-tight">
                cloudsentinel
              </Link>
              <nav className="hidden gap-4 text-sm text-slate-300 md:flex">
                {nav.map((n) => (
                  <Link key={n.href} href={n.href} className="hover:text-white">
                    {n.label}
                  </Link>
                ))}
              </nav>
              <ModeSwitcher />
            </div>
          </header>
          <main className="mx-auto grid max-w-6xl gap-4 px-6 py-8">
            <DemoBanner />
            {children}
          </main>
          <footer className="border-t border-slate-800 py-8 text-center text-xs text-slate-500">
            $0 AWS bill: Demo Mode on GitHub Pages. Local Mode runs entirely on localhost.
          </footer>
        </Providers>
      </body>
    </html>
  );
}
