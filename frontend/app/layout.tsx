import type { Metadata } from "next";
import type { ReactNode } from "react";
import { JetBrains_Mono, Space_Grotesk } from "next/font/google";
import { AppShell } from "@/components/layout/AppShell";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-display",
  subsets: ["latin"],
});

const jetBrainsMono = JetBrains_Mono({
  variable: "--font-code",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "FireGuard DT",
  description: "Intelligent multi-twin ecosystem for fire prediction, evacuation, and emergency response.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${jetBrainsMono.variable} h-full bg-[var(--bg-deep)] antialiased`}
    >
      <body className="min-h-full bg-[var(--bg-deep)]">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
