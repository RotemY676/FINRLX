"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/contexts/AuthContext";

type Step = 1 | 2 | 3 | 4;

export default function OnboardingPage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [step, setStep] = useState<Step>(1);

  // Redirect to /login if the user lands here without being signed in.
  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  if (isLoading || !user) return null;

  return (
    <div style={styles.wrap}>
      <ProgressBar step={step} />
      {step === 1 && <Welcome name={user.email} onNext={() => setStep(2)} />}
      {step === 2 && <Disclaimer onAccept={() => setStep(3)} onDecline={() => router.push("/")} />}
      {step === 3 && <Universe onNext={() => setStep(4)} />}
      {step === 4 && <FirstRecommendation onDone={() => router.push("/")} />}
    </div>
  );
}

function ProgressBar({ step }: { step: Step }) {
  const pct = (step / 4) * 100;
  return (
    <div style={styles.progressWrap}>
      <div style={{ ...styles.progressBar, width: `${pct}%` }} />
      <div style={styles.progressLabel}>Step {step} of 4</div>
    </div>
  );
}

function Welcome({ name, onNext }: { name: string; onNext: () => void }) {
  return (
    <div style={styles.card}>
      <h1 style={styles.h1}>Welcome, {name.split("@")[0]}.</h1>
      <p style={styles.p}>
        FINRLX is a decision-intelligence platform for medium-term equity investing.
        Its output is a single recommendation object: a portfolio of weights, with
        confidence, rationale, and full replayability.
      </p>
      <p style={styles.p}>
        In the next three minutes we&apos;ll cover the legal disclaimer, the
        investable universe, and produce your first recommendation.
      </p>
      <button onClick={onNext} style={styles.button}>Begin</button>
    </div>
  );
}

function Disclaimer({ onAccept, onDecline }: { onAccept: () => void; onDecline: () => void }) {
  const [agreed, setAgreed] = useState(false);
  return (
    <div style={styles.card}>
      <h1 style={styles.h1}>Important: this is not investment advice</h1>
      <div style={styles.disclaimer}>
        <p>
          FINRLX is an educational and research tool. The recommendations it
          generates are <strong>not</strong> personal investment advice, are not
          tailored to your financial situation, and must not be the sole basis
          for any trading decision.
        </p>
        <p>
          During the closed beta, the platform shows <strong>paper trading
          only</strong>. No real orders are placed and no real money is at risk.
        </p>
        <p>
          Past performance, including any backtest result, is not predictive of
          future returns. Models can be wrong. Data can be stale. Verify before
          acting.
        </p>
      </div>
      <label style={styles.checkLabel}>
        <input
          type="checkbox"
          checked={agreed}
          onChange={(e) => setAgreed(e.target.checked)}
          style={styles.checkInput}
        />
        I understand FINRLX provides educational research, not investment advice.
      </label>
      <div style={styles.row}>
        <button onClick={onDecline} style={styles.buttonGhost}>Exit</button>
        <button onClick={onAccept} disabled={!agreed} style={styles.button}>
          I agree
        </button>
      </div>
    </div>
  );
}

const SEED_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "JPM", "JNJ", "XOM", "PG", "NVDA", "V"];

function Universe({ onNext }: { onNext: () => void }) {
  return (
    <div style={styles.card}>
      <h1 style={styles.h1}>Your investable universe</h1>
      <p style={styles.p}>
        The beta universe is fixed to 10 large-cap US equities. You can request
        additions after the beta. Your first recommendation is constructed from
        these tickers using real market data (yfinance).
      </p>
      <div style={styles.universeGrid}>
        {SEED_TICKERS.map((t) => (
          <span key={t} style={styles.ticker}>{t}</span>
        ))}
      </div>
      <button onClick={onNext} style={styles.button}>Looks good</button>
    </div>
  );
}

function FirstRecommendation({ onDone }: { onDone: () => void }) {
  return (
    <div style={styles.card}>
      <h1 style={styles.h1}>You&apos;re all set</h1>
      <p style={styles.p}>
        Your first recommendation will be generated on the next operator pipeline
        run. The Overview screen will populate as soon as it&apos;s ready.
      </p>
      <p style={styles.p}>
        Every recommendation comes with: a confidence triplet (model · data · ops),
        a per-asset rationale, and a tamper-evident replay hash so you can
        reproduce the exact result deterministically.
      </p>
      <button onClick={onDone} style={styles.button}>Go to overview</button>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrap: { minHeight: "100vh", display: "grid", placeItems: "center", padding: 24, background: "var(--bg, #0a0a0a)" },
  progressWrap: { position: "fixed", top: 0, left: 0, right: 0, height: 4, background: "var(--border, #2a2a30)" },
  progressBar: { height: "100%", background: "var(--accent, #4f9fff)", transition: "width 240ms ease-out" },
  progressLabel: { position: "absolute", top: 12, right: 16, fontSize: 12, color: "var(--fg, #e9e9ee)", opacity: 0.6 },
  card: { width: "100%", maxWidth: 580, padding: 36, background: "var(--card, #131316)", border: "1px solid var(--border, #2a2a30)", borderRadius: 14, color: "var(--fg, #e9e9ee)" },
  h1: { margin: 0, fontSize: 26, fontWeight: 600, marginBottom: 16 },
  p: { margin: "12px 0", lineHeight: 1.6, fontSize: 14, opacity: 0.85 },
  button: { marginTop: 20, padding: "12px 20px", background: "var(--accent, #4f9fff)", color: "#fff", border: 0, borderRadius: 8, fontWeight: 600, cursor: "pointer", minHeight: 44, fontSize: 14 },
  buttonGhost: { marginTop: 20, padding: "12px 20px", background: "transparent", color: "inherit", border: "1px solid var(--border, #2a2a30)", borderRadius: 8, fontWeight: 500, cursor: "pointer", minHeight: 44, fontSize: 14 },
  disclaimer: { background: "var(--input, #1a1a1f)", border: "1px solid var(--border, #2a2a30)", borderRadius: 8, padding: 16, marginTop: 16, fontSize: 13, lineHeight: 1.6 },
  checkLabel: { display: "flex", alignItems: "flex-start", gap: 8, marginTop: 16, fontSize: 13, lineHeight: 1.5, cursor: "pointer" },
  checkInput: { marginTop: 3, width: 18, height: 18, flexShrink: 0 },
  row: { display: "flex", gap: 12, justifyContent: "flex-end" },
  universeGrid: { display: "flex", flexWrap: "wrap", gap: 8, marginTop: 16 },
  ticker: { padding: "8px 14px", background: "var(--input, #1a1a1f)", border: "1px solid var(--border, #2a2a30)", borderRadius: 999, fontSize: 13, fontFamily: "ui-monospace, monospace", letterSpacing: 0.5 },
};
