import type { Metadata, Viewport } from "next";
import "./globals.css";
import { AppShell } from "@/components/shell/AppShell";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { ScopeProvider } from "@/contexts/ScopeContext";
import { AuthProvider } from "@/contexts/AuthContext";
import { FeatureFlagsProvider } from "@/contexts/FeatureFlagsContext";
import { SentryClientInit } from "./sentry-init";

export const metadata: Metadata = {
  title: "FINRLX",
  description: "Private decision-intelligence platform for medium-term investing",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fafbfc" },
    { media: "(prefers-color-scheme: dark)", color: "#1a1d24" },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem("finrlx-theme");if(t==="dark")document.documentElement.setAttribute("data-theme","dark")}catch(e){}})()`,
          }}
        />
      </head>
      <body>
        <SentryClientInit />
        <ThemeProvider>
          <FeatureFlagsProvider>
            <AuthProvider>
              <ScopeProvider>
                <AppShell>{children}</AppShell>
              </ScopeProvider>
            </AuthProvider>
          </FeatureFlagsProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
