import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { DisclaimerBanner } from "./DisclaimerBanner";

describe("<DisclaimerBanner />", () => {
  it("renders the canonical not-investment-advice copy", () => {
    render(<DisclaimerBanner />);
    expect(screen.getByText(/Not investment advice/i)).toBeInTheDocument();
  });

  it("carries the data-disclaimer marker the guard skill scans for", () => {
    const { container } = render(<DisclaimerBanner />);
    const banner = container.querySelector('[data-disclaimer="true"]');
    expect(banner).not.toBeNull();
  });

  it("links to all three legal pages", () => {
    render(<DisclaimerBanner />);
    expect(screen.getByRole("link", { name: /full disclaimer/i })).toHaveAttribute(
      "href",
      "/disclaimer"
    );
    expect(screen.getByRole("link", { name: /^terms$/i })).toHaveAttribute(
      "href",
      "/terms"
    );
    expect(screen.getByRole("link", { name: /^privacy$/i })).toHaveAttribute(
      "href",
      "/privacy"
    );
  });

  it("is identified as a content-info landmark for screen readers", () => {
    render(<DisclaimerBanner />);
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
  });
});
