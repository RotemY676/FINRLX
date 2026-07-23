"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { FormEvent, useState } from "react";

import { useAuth } from "@/contexts/AuthContext";
import { fetchMyProfile } from "@/features/wizard/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://backend-production-aab8.up.railway.app";

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
      // WIZ-2: a user who signed up via email but never completed the
      // investor profile (e.g. they bailed mid-wizard) lands back on
      // /onboarding on next sign-in. Profile-complete users go home.
      try {
        const me = await fetchMyProfile();
        router.push(me.has_profile ? "/" : "/onboarding");
      } catch {
        router.push("/");
      }
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

        <a
          href={`${API_BASE_URL}/api/v1/auth/google/start`}
          style={styles.googleButton}
          aria-label="Sign in with Google"
        >
          <GoogleGlyph />
          <span>Sign in with Google</span>
        </a>

        <div style={styles.divider}>
          <span style={styles.dividerLine} />
          <span style={styles.dividerText}>or use email</span>
          <span style={styles.dividerLine} />
        </div>

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

function GoogleGlyph() {
  return (
    <svg width={18} height={18} viewBox="0 0 18 18" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M17.64 9.2c0-.64-.06-1.25-.17-1.84H9v3.49h4.84a4.14 4.14 0 0 1-1.79 2.72v2.26h2.9c1.7-1.56 2.69-3.87 2.69-6.63z"
      />
      <path
        fill="#34A853"
        d="M9 18c2.43 0 4.47-.81 5.96-2.18l-2.9-2.26c-.8.54-1.83.86-3.06.86-2.35 0-4.34-1.59-5.05-3.72H.97v2.33A9 9 0 0 0 9 18z"
      />
      <path
        fill="#FBBC05"
        d="M3.95 10.7A5.41 5.41 0 0 1 3.66 9c0-.59.1-1.16.29-1.7V4.97H.97A9 9 0 0 0 0 9c0 1.45.35 2.83.97 4.04l2.98-2.34z"
      />
      <path
        fill="#EA4335"
        d="M9 3.58c1.32 0 2.51.46 3.44 1.35l2.58-2.58A8.92 8.92 0 0 0 9 0 9 9 0 0 0 .97 4.96l2.98 2.33C4.66 5.17 6.65 3.58 9 3.58z"
      />
    </svg>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrap: { minHeight: "100dvh", display: "grid", placeItems: "center", padding: 24, background: "var(--bg, #0a0a0a)" },
  card: { width: "100%", maxWidth: 380, padding: 32, background: "var(--card, #131316)", border: "1px solid var(--border, #2a2a30)", borderRadius: 12, color: "var(--fg, #e9e9ee)" },
  h1: { margin: 0, fontSize: 24, fontWeight: 600 },
  sub: { margin: "6px 0 20px", fontSize: 13, opacity: 0.7 },
  label: { display: "block", fontSize: 12, fontWeight: 500, marginTop: 14, marginBottom: 6, opacity: 0.85 },
  input: { width: "100%", padding: "10px 12px", background: "var(--input, #1a1a1f)", border: "1px solid var(--border, #2a2a30)", borderRadius: 8, color: "inherit", fontSize: 14, minHeight: 44 },
  button: { marginTop: 20, width: "100%", padding: "12px 16px", background: "var(--accent, #4f9fff)", color: "#fff", border: 0, borderRadius: 8, fontWeight: 700, cursor: "pointer", minHeight: 44 },
  error: { marginTop: 12, padding: 10, background: "rgba(255,80,80,0.12)", border: "1px solid rgba(255,80,80,0.4)", borderRadius: 6, fontSize: 13, color: "#ffbebe" },
  foot: { marginTop: 18, fontSize: 13, textAlign: "center", opacity: 0.85 },
  link: { color: "#7fb8ff", textDecoration: "underline" },
  googleButton: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    width: "100%",
    padding: "11px 16px",
    background: "#ffffff",
    color: "#1f1f1f",
    border: "1px solid #d8d8dc",
    borderRadius: 8,
    fontWeight: 600,
    fontSize: 14,
    cursor: "pointer",
    textDecoration: "none",
    minHeight: 44,
  },
  divider: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    margin: "16px 0 4px",
    fontSize: 11,
    opacity: 0.55,
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    background: "var(--border, #2a2a30)",
  },
  dividerText: { whiteSpace: "nowrap" },
};
