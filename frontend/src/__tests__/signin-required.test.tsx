/**
 * Logged-out UX: an authed page must show an honest "Sign in" prompt, not a
 * scary "Connection Error" that implies the app is broken. Pins the shared
 * SignInRequired component and the ApiError/isAuthError plumbing that lets a
 * page tell a 401 apart from a real backend failure.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SignInRequired } from "@/components/feedback/SignInRequired";
import { ApiError, isAuthError } from "@/services/api";

describe("SignInRequired", () => {
  it("offers a real Sign in action pointing at /login", () => {
    render(<SignInRequired feature="backtests" />);
    const link = screen.getByRole("link", { name: /sign in/i });
    expect(link.getAttribute("href")).toBe("/login");
  });

  it("names the feature so the message is specific, not generic error text", () => {
    render(<SignInRequired feature="the risk workspace" />);
    expect(screen.getByText(/sign in to view the risk workspace/i)).toBeTruthy();
    // And it must NOT read like a failure.
    expect(screen.queryByText(/connection error/i)).toBeNull();
    expect(screen.queryByText(/error/i)).toBeNull();
  });
});

describe("isAuthError", () => {
  it("is true only for a 401 ApiError", () => {
    expect(isAuthError(new ApiError(401, "nope"))).toBe(true);
  });
  it("is false for other statuses and plain errors", () => {
    expect(isAuthError(new ApiError(500, "boom"))).toBe(false);
    expect(isAuthError(new ApiError(404, "missing"))).toBe(false);
    expect(isAuthError(new Error("generic"))).toBe(false);
    expect(isAuthError(null)).toBe(false);
  });
  it("still carries the status and message for logging", () => {
    const e = new ApiError(401, "API error: 401 Unauthorized");
    expect(e.status).toBe(401);
    expect(e.message).toContain("401");
    expect(e instanceof Error).toBe(true);
  });
});
