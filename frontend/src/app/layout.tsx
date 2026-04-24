import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/shell/AppShell";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { ScopeProvider } from "@/contexts/ScopeContext";

export const metadata: Metadata = {
  title: "FINRLX",
  description: "Private decision-intelligence platform for medium-term investing",
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
        <ThemeProvider>
          <ScopeProvider>
            <AppShell>{children}</AppShell>
          </ScopeProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
