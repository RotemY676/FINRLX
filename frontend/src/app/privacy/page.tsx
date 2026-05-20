export const metadata = {
  title: "Privacy Policy — FINRLX",
};

export default function PrivacyPage() {
  return (
    <article className="mx-auto max-w-2xl space-y-4 py-8 text-text-default">
      <h1 className="text-2xl font-semibold">Privacy Policy</h1>
      <p className="text-sm text-text-muted">Last updated: 2026-05-20</p>

      <h2 className="pt-4 text-lg font-semibold">What we collect</h2>
      <ul className="list-inside list-disc space-y-1 pl-1">
        <li>
          <strong>Account data</strong> — your email address and a hashed
          password (we never store your plaintext password).
        </li>
        <li>
          <strong>Session data</strong> — authentication tokens, the device
          User-Agent, and the IP address of your last login. Used to detect
          and recover from token theft.
        </li>
        <li>
          <strong>Usage data</strong> — pages visited and recommendation
          interactions, used to improve the product. No third-party trackers
          during the beta.
        </li>
        <li>
          <strong>Paper-trading data</strong> — the synthetic positions and
          actions you take inside FINRLX. This data never leaves the system.
        </li>
      </ul>

      <h2 className="pt-4 text-lg font-semibold">What we do not collect</h2>
      <ul className="list-inside list-disc space-y-1 pl-1">
        <li>Real brokerage credentials. FINRLX does not connect to your broker.</li>
        <li>Government-issued identification or KYC documents.</li>
        <li>Payment information. The beta is free.</li>
      </ul>

      <h2 className="pt-4 text-lg font-semibold">How we use your data</h2>
      <p>
        Only to operate the service, secure your account, and improve the
        product during the beta. We do not sell or share personal data with
        third parties.
      </p>

      <h2 className="pt-4 text-lg font-semibold">Your rights</h2>
      <p>
        You can request a copy or deletion of your account data at any time by
        contacting the operator. We will action verifiable requests within 30
        days. EU/UK users: this includes your rights under the GDPR/UK-GDPR
        (access, rectification, erasure, restriction, portability, objection).
      </p>

      <h2 className="pt-4 text-lg font-semibold">Data retention</h2>
      <p>
        We retain account data for the lifetime of the account and for up to
        30 days after deletion for backup integrity, after which it is purged.
        Audit logs may be retained longer for security and regulatory
        defensibility.
      </p>

      <h2 className="pt-4 text-lg font-semibold">Security</h2>
      <p>
        Passwords are hashed with bcrypt. Connections are TLS-terminated.
        Refresh tokens are stored as SHA-256 hashes server-side and rotated on
        every refresh. We are not yet certified to any specific standard
        (SOC 2, ISO 27001) during the beta.
      </p>

      <h2 className="pt-4 text-lg font-semibold">Contact</h2>
      <p>
        For any privacy question or data-rights request, contact the operator
        listed in your invite email.
      </p>
    </article>
  );
}
