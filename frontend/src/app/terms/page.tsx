export const metadata = {
  title: "Terms of Service — FINRLX",
};

export default function TermsPage() {
  return (
    <article className="mx-auto max-w-2xl space-y-4 py-8 text-text-default">
      <h1 className="text-2xl font-semibold">Terms of Service</h1>
      <p className="text-sm text-text-muted">Last updated: 2026-05-20</p>

      <h2 className="pt-4 text-lg font-semibold">Acceptance</h2>
      <p>
        By creating an account or using FINRLX you agree to these terms and to
        the <a href="/disclaimer" className="underline">disclaimer</a> and{" "}
        <a href="/privacy" className="underline">privacy policy</a>. If you do
        not agree, do not use the service.
      </p>

      <h2 className="pt-4 text-lg font-semibold">Eligibility</h2>
      <p>
        FINRLX is invited-access during the beta. You may use it only if you
        have been added to the email allowlist by an operator and are at least
        18 years old.
      </p>

      <h2 className="pt-4 text-lg font-semibold">Acceptable use</h2>
      <ul className="list-inside list-disc space-y-1 pl-1">
        <li>Do not attempt to scrape, mirror, or redistribute output.</li>
        <li>Do not reverse-engineer the models or pipelines.</li>
        <li>
          Do not attempt to circumvent authentication, rate limits, or feature
          flags.
        </li>
        <li>Do not represent FINRLX output as licensed financial advice.</li>
      </ul>

      <h2 className="pt-4 text-lg font-semibold">No warranty</h2>
      <p>
        The service is provided &quot;as is&quot; without warranty of any kind,
        express or implied. We do not warrant that the service will be
        uninterrupted, error-free, or accurate.
      </p>

      <h2 className="pt-4 text-lg font-semibold">Limitation of liability</h2>
      <p>
        To the maximum extent permitted by law, FINRLX and its operators are
        not liable for any direct, indirect, incidental, consequential, or
        punitive damages arising from your use of the service, including
        trading losses.
      </p>

      <h2 className="pt-4 text-lg font-semibold">Termination</h2>
      <p>
        We may suspend or remove your access at any time and without notice,
        for any reason. You may request account deletion at any time by
        contacting the operator.
      </p>

      <h2 className="pt-4 text-lg font-semibold">Changes to these terms</h2>
      <p>
        We may update these terms. Material changes will be announced in-app
        and may require re-acceptance.
      </p>
    </article>
  );
}
