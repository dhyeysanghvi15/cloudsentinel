import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "cloudsentinel",
  description: "AWS cloud security posture + detection lab",
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
        <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
            <Link href="/dashboard" className="text-lg font-semibold tracking-tight">
              cloudsentinel
            </Link>
            <nav className="flex gap-4 text-sm text-slate-300">
              {nav.map((n) => (
                <Link key={n.href} href={n.href} className="hover:text-white">
                  {n.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
        <footer className="border-t border-slate-800 py-8 text-center text-xs text-slate-500">
          Lab-only. Use in your own AWS account.
        </footer>
      </body>
    </html>
  );
}

