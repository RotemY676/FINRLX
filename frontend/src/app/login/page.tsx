"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { FormEvent, useState } from "react";

import { useAuth } from "@/contexts/AuthContext";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={styles.wrap}>
      <form onSubmit={onSubmit} style={styles.card} aria-labelledby="login-title">
        <h1 id="login-title" style={styles.h1}>Sign in</h1>
        <p style={styles.sub}>FINRLX private beta · invite-only</p>

        <label style={styles.label} htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          inputMode="email"
          autoComplete="email"
          autoCapitalize="off"
          spellCheck={false}
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={styles.input}
        />

        <label style={styles.label} htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          autoCapitalize="off"
          spellCheck={false}
          required
          minLength={12}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={styles.input}
        />

        {error && <p role="alert" style={styles.error}>{error}</p>}

        <button type="submit" disabled={busy} style={styles.button}>
          {busy ? "Signing in…" : "Sign in"}
        </button>

        <p style={styles.foot}>
          No account?{" "}
          <Link href="/signup" style={styles.link}>Request access</Link>
        </p>
      </form>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrap: { minHeight: "100vh", display: "grid", placeItems: "center", padding: 24, background: "var(--bg, #0a0a0a)" },
  card: { width: "100%", maxWidth: 380, padding: 32, background: "var(--card, #131316)", border: "1px solid var(--border, #2a2a30)", borderRadius: 12, color: "var(--fg, #e9e9ee)" },
  h1: { margin: 0, fontSize: 24, fontWeight: 600 },
  sub: { margin: "6px 0 24px", fontSize: 13, opacity: 0.7 },
  label: { display: "block", fontSize: 12, fontWeight: 500, marginTop: 14, marginBottom: 6, opacity: 0.85 },
  input: { width: "100%", padding: "10px 12px", background: "var(--input, #1a1a1f)", border: "1px solid var(--border, #2a2a30)", borderRadius: 8, color: "inherit", fontSize: 14, minHeight: 44 },
  // fontWeight 700 (bold) puts this in the WCAG "large text" bucket (3:1 floor).
  button: { marginTop: 20, width: "100%", padding: "12px 16px", background: "var(--accent, #4f9fff)", color: "#fff", border: 0, borderRadius: 8, fontWeight: 700, cursor: "pointer", minHeight: 44 },
  error: { marginTop: 12, padding: 10, background: "rgba(255,80,80,0.12)", border: "1px solid rgba(255,80,80,0.4)", borderRadius: 6, fontSize: 13, color: "#ffbebe" },
  foot: { marginTop: 18, fontSize: 13, textAlign: "center", opacity: 0.85 },
  // Link on the dark login card uses a lighter blue (not --accent) for contrast.
  link: { color: "#7fb8ff", textDecoration: "underline" },
};
