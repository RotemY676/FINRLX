import { describe, expect, it, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { DisclaimerModal } from "./DisclaimerModal";

const STORAGE_KEY = "finrlx-disclaimer-accepted-v1";

describe("<DisclaimerModal />", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("opens on first visit and closes after accepting", async () => {
    render(<DisclaimerModal />);

    await waitFor(() =>
      expect(screen.getByRole("dialog")).toBeInTheDocument()
    );

    const acceptBtn = screen.getByRole("button", { name: /i understand/i });
    fireEvent.click(acceptBtn);

    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());

    // Acceptance is persisted for future visits.
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("v1");
  });

  it("stays closed when localStorage already has the current version stored", async () => {
    window.localStorage.setItem(STORAGE_KEY, "v1");
    render(<DisclaimerModal />);

    // The effect runs in a microtask; wait briefly to ensure the modal did NOT mount.
    await new Promise((r) => setTimeout(r, 10));
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("reopens when the stored version is stale (forces re-acceptance)", async () => {
    window.localStorage.setItem(STORAGE_KEY, "v0-old");
    render(<DisclaimerModal />);

    await waitFor(() =>
      expect(screen.getByRole("dialog")).toBeInTheDocument()
    );
  });
});
