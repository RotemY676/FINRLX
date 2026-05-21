"use client";

/**
 * Google OAuth finish page.
 *
 * The backend redirects here with either:
 *   ?error=...                              (failure)
 *   #access_token=...&refresh_token=...     (success — URL fragment)
 *
 * Fragments don't get sent to the server, so the tokens never hit any
 * proxy / access log on this page either. We pull them off the hash,
 * stuff them into localStorage via the same setters the password
 * login uses, then navigate to "/".
 */
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import {
  setAccessToken,
  setRefreshToken,
} from "@/services/auth";
import { fetchMyProfile } from "@/features/wizard/api";

function GoogleFinishInner() {
  const router = useRouter();
  const search = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const queryError = search?.get("error");
    if (queryError) {
      setError(queryError);
      return;
    }
    if (typeof window === "undefined") return;
    const hash = window.location.hash.replace(/^#/, "");
    if (!hash) {
      setError("Missing tokens in the redirect URL — start sign-in again.");
      return;
    }
    const params = new URLSearchParams(hash);
    const access = params.get("access_token");
    const refresh = params.get("refresh_token");
    if (!access || !refresh) {
      setError("Sign-in payload was incomplete.");
      return;
    }
    setAccessToken(access);
    setRefreshToken(refresh);
    // Clean the hash so a refresh doesn't leak tokens via copy-paste.
    window.history.replaceState(null, "", window.location.pathname);
    // WIZ-2: First-time Google users must complete the investor profile
    // wizard before landing on the decision center. Probe /profile/me; if
    // there's no profile, send them to /onboarding. Returning users go
    // straight to the home page. Network errors fall back to "/" so a
    // probe failure does not block the sign-in flow.
    fetchMyProfile()
      .then((me) => {
        router.replace(me.has_profile ? "/" : "/onboarding");
      })
      .catch(() => {
        router.replace("/");
      });
  }, [router, search]);

  return (
    <div style={styles.wrap}>
      <div style={styles.card}>
        <h1 style={styles.h1}>Finishing sign-in…</h1>
        {error ? (
          <>
            <p role="alert" style={styles.error}>
              {decodeURIComponent(error)}
            </p>
            <p style={styles.foot}>
              <a href="/login" style={styles.link}>
                Back to sign in
              </a>
            </p>
          </>
        ) : (
          <p style={styles.body}>
            We&apos;re completing your sign-in with Google. If this takes more
            than a few seconds, go back to <a href="/login" style={styles.link}>sign in</a>.
          </p>
        )}
      </div>
    </div>
  );
}

export default function GoogleFinishPage() {
  return (
    <Suspense fallback={null}>
      <GoogleFinishInner />
    </Suspense>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrap: { minHeight: "100vh", display: "grid", placeItems: "center", padding: 24, background: "var(--bg, #0a0a0a)" },
  card: { width: "100%", maxWidth: 420, padding: 32, background: "var(--card, #131316)", border: "1px solid var(--border, #2a2a30)", borderRadius: 12, color: "var(--fg, #e9e9ee)" },
  h1: { margin: 0, fontSize: 22, fontWeight: 600 },
  body: { marginTop: 12, fontSize: 13, opacity: 0.85, lineHeight: 1.55 },
  error: { marginTop: 12, padding: 10, background: "rgba(255,80,80,0.12)", border: "1px solid rgba(255,80,80,0.4)", borderRadius: 6, fontSize: 13, color: "#ffbebe" },
  foot: { marginTop: 18, fontSize: 13, textAlign: "center", opacity: 0.85 },
  link: { color: "#7fb8ff", textDecoration: "underline" },
};
