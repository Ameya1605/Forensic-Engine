import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PREE — Forensic Engine | AI Text Reverse Engineering",
  description:
    "Advanced AI forensic analyzer that reverse-engineers AI-generated text to reconstruct original prompts, detect model fingerprints, and estimate system parameters.",
  keywords: ["AI forensics", "prompt engineering", "LLM analysis", "text forensics"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
