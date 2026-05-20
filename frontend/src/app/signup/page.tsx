"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { FormEvent, useState } from "react";

import { useAuth } from "@/contexts/AuthContext";
import { track } from "@/lib/analytics";

export default function SignupPage() {
  const router = useRouter();
  const { signup } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await signup(email, password);
      void track("signup");
      router.push("/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign up failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={styles.wrap}>
      <form onSubmit={onSubmit} style={styles.card} aria-labelledby="signup-title">
        <h1 id="signup-title" style={styles.h1}>Create your account</h1>
        <p style={styles.sub}>
          Invite-only beta. Your email must be pre-approved on the allowlist.
        </p>

        <label style={styles.label} htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={styles.input}
        />

        <label style={styles.label} htmlFor="password">
          Password <span style={styles.hint}>(min 12 chars)</span>
        </label>
        <input
          id="password"
          type="password"
          autoComplete="new-password"
          required
          minLength={12}
          maxLength={128}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={styles.input}
        />

        {error && <p role="alert" style={styles.error}>{error}</p>}

        <button type="submit" disabled={busy} style={styles.button}>
          {busy ? "Creating account…" : "Create account"}
        </button>

        <p style={styles.foot}>
          Already have an account?{" "}
          <Link href="/login" style={styles.link}>Sign in</Link>
        </p>
      </form>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrap: { minHeight: "100vh", display: "grid", placeItems: "center", padding: 24, background: "var(--bg, #0a0a0a)" },
  card: { width: "100%", maxWidth: 380, padding: 32, background: "var(--card, #131316)", border: "1px solid var(--border, #2a2a30)", borderRadius: 12, color: "var(--fg, #e9e9ee)" },
  h1: { margin: 0, fontSize: 24, fontWeight: 600 },
  sub: { margin: "6px 0 24px", fontSize: 13, opacity: 0.7, lineHeight: 1.5 },
  label: { display: "block", fontSize: 12, fontWeight: 500, marginTop: 14, marginBottom: 6, opacity: 0.85 },
  hint: { opacity: 0.5, fontWeight: 400 },
  input: { width: "100%", padding: "10px 12px", background: "var(--input, #1a1a1f)", border: "1px solid var(--border, #2a2a30)", borderRadius: 8, color: "inherit", fontSize: 14, minHeight: 44 },
  button: { marginTop: 20, width: "100%", padding: "12px 16px", background: "var(--accent, #4f9fff)", color: "#fff", border: 0, borderRadius: 8, fontWeight: 600, cursor: "pointer", minHeight: 44 },
  error: { marginTop: 12, padding: 10, background: "rgba(255,80,80,0.12)", border: "1px solid rgba(255,80,80,0.4)", borderRadius: 6, fontSize: 13, color: "#ffbebe" },
  foot: { marginTop: 18, fontSize: 13, textAlign: "center", opacity: 0.85 },
  link: { color: "var(--accent, #4f9fff)", textDecoration: "underline" },
};
