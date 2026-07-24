"use client";

import { PageEmpty } from "@/components/feedback/PageEmpty";

interface Props {
  /** What the page shows, e.g. "backtests", "the risk workspace". Lower-case;
   *  it is dropped into "Sign in to view {feature}." */
  feature?: string;
}

/**
 * The one honest logged-out state for an authenticated page. Replaces the
 * scary "Connection Error" / "Backtest Error" that a 401 used to render: those
 * implied the app was broken, when the real cause is simply that the viewer is
 * not signed in (the operator/decision surfaces were auth-gated in US-P0-03).
 *
 * Carries a real "Sign in" call to action so the viewer is never dead-ended.
 */
export function SignInRequired({ feature = "this page" }: Props) {
  return (
    <PageEmpty
      icon="user"
      title="Sign in to continue"
      message={`Sign in to view ${feature}. It's part of the operator workspace, which requires an account.`}
      action={{ label: "Sign in", href: "/login" }}
    />
  );
}
