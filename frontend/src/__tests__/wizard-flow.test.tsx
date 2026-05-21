/**
 * Phase WIZ — investor-profile wizard flow contract.
 *
 * Locks in three guarantees independent of design polish:
 *
 *   1. After successful EMAIL signup, the app navigates to /onboarding.
 *      (signup/page.tsx onSubmit → router.push("/onboarding"))
 *
 *   2. After successful EMAIL login, the app probes /profile/me:
 *        - profile present  → navigate to "/"
 *        - profile missing  → navigate to "/onboarding"
 *
 *   3. /profile renders a clearly labeled re-run entry point
 *      (data-testid="rerun-wizard") so a user can re-run the wizard from
 *      the profile page whenever they want.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";

const pushSpy = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushSpy, replace: pushSpy }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/",
}));

vi.mock("@/lib/analytics", () => ({ track: vi.fn() }));

afterEach(() => {
  cleanup();
  pushSpy.mockReset();
  vi.resetModules();
});

describe("signup → onboarding (WIZ-2)", () => {
  beforeEach(() => {
    vi.doMock("@/contexts/AuthContext", () => ({
      useAuth: () => ({ signup: vi.fn().mockResolvedValue(undefined) }),
    }));
  });

  it("navigates to /onboarding after a successful email signup", async () => {
    const { default: SignupPage } = await import("@/app/signup/page");
    render(<SignupPage />);
    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: "operator@finrlx.com" },
    });
    fireEvent.change(screen.getByLabelText(/^password/i), {
      target: { value: "Sup3rSecret-12345" },
    });
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));
    await waitFor(() => expect(pushSpy).toHaveBeenCalledWith("/onboarding"));
  });
});

describe("login → onboarding for incomplete users (WIZ-2)", () => {
  it("routes to /onboarding when the user has no profile yet", async () => {
    vi.doMock("@/contexts/AuthContext", () => ({
      useAuth: () => ({ login: vi.fn().mockResolvedValue(undefined) }),
    }));
    vi.doMock("@/features/wizard/api", () => ({
      fetchMyProfile: vi.fn().mockResolvedValue({ has_profile: false, profile: null }),
    }));
    const { default: LoginPage } = await import("@/app/login/page");
    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: "operator@finrlx.com" },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: "Sup3rSecret-12345" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^sign in$/i }));
    await waitFor(() => expect(pushSpy).toHaveBeenCalledWith("/onboarding"));
  });

  it("routes to / when the user already has a profile", async () => {
    vi.doMock("@/contexts/AuthContext", () => ({
      useAuth: () => ({ login: vi.fn().mockResolvedValue(undefined) }),
    }));
    vi.doMock("@/features/wizard/api", () => ({
      fetchMyProfile: vi.fn().mockResolvedValue({
        has_profile: true,
        profile: { id: "p-1", version: 1 },
      }),
    }));
    const { default: LoginPage } = await import("@/app/login/page");
    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/^email$/i), {
      target: { value: "operator@finrlx.com" },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: "Sup3rSecret-12345" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^sign in$/i }));
    await waitFor(() => expect(pushSpy).toHaveBeenCalledWith("/"));
  });
});

describe("profile page — re-run wizard entry point (WIZ-3)", () => {
  it("renders a 'Re-run the wizard' button with the documented testid", async () => {
    vi.doMock("@/contexts/AuthContext", () => ({
      useAuth: () => ({
        user: { email: "operator@finrlx.com" },
        isLoading: false,
      }),
    }));
    vi.doMock("@/features/wizard/api", () => ({
      fetchMyProfile: vi.fn().mockResolvedValue({
        has_profile: true,
        profile: {
          id: "p-1",
          user_id: "u-1",
          version: 2,
          risk_score: 18,
          risk_bucket: "moderate",
          horizon_band: "3y_5y",
          primary_goal: "growth",
          max_drawdown_pct: 20,
          knowledge_level: "intermediate",
          years_investing: 5,
          instruments_traded: ["etf"],
          investable_amount_band: "50k_250k",
          income_band: "50k_150k",
          liquid_net_worth_band: "100k_500k",
          sector_whitelist: ["Technology"],
          sector_blacklist: [],
          region_preference: "us",
          exclude_leverage: true,
          base_currency: "USD",
          trading_frequency: "monthly",
          completed_at: "2026-05-21T00:00:00Z",
          created_at: "2026-05-01T00:00:00Z",
          updated_at: "2026-05-21T00:00:00Z",
          raw_answers: {},
        },
      }),
      fetchProfileQuestions: vi.fn().mockResolvedValue([]),
      submitProfile: vi.fn(),
      runProfileAwarePipeline: vi.fn(),
    }));

    const { default: ProfilePage } = await import("@/app/profile/page");
    render(<ProfilePage />);
    await waitFor(() => {
      expect(screen.getByTestId("rerun-wizard")).toBeInTheDocument();
    });
    const btn = screen.getByTestId("rerun-wizard");
    expect(btn.textContent).toMatch(/Re-run the wizard/i);
    // The card explains that re-running saves a new revision.
    expect(
      screen.getByText(/A new revision is saved each time\./i),
    ).toBeInTheDocument();
  });
});
