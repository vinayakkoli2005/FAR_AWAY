import type { Metadata } from "next";
import Link from "next/link";
import GuideModal from "@/components/GuideModal";
import "./globals.css";

export const metadata: Metadata = {
  title: "OrbitGuard — conjunction screening for small operators",
  description:
    "Free, explainable, validated satellite conjunction assessment on public data.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        {/* Cesium widget styles are served from the copied static assets */}
        <link rel="stylesheet" href="/cesium/Widgets/widgets.css" />
        <link
          rel="icon"
          href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🛰</text></svg>"
        />
      </head>
      <body>
        <nav className="topnav">
          <Link href="/" className="brand">
            🛰 ORBITGUARD
          </Link>
          <div className="navlinks">
            <Link href="/">Mission Control</Link>
            <Link href="/scorecard">Validation Scorecard</Link>
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/docs`}
              target="_blank"
            >
              API
            </a>
            <GuideModal />
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
