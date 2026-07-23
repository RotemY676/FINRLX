/**
 * Engine status rail — the lane row is explorable, not decorative.
 *
 * The dial row it replaces was a 30px arc whose only affordance was a `title`
 * tooltip: nothing on touch, nothing for keyboards, and no statement of what
 * the lane measured or why it was in that state. These tests pin the fix so it
 * cannot quietly regress back into an ornament.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EngineStatusRail } from "@/components/deskv2/core";
import { deskCopy } from "@/lib/deskCopy";

const SECTIONS = [
  { id: "technical", state: "live" as const },
  {
    id: "tournament",
    state: "degraded" as const,
    reason: "RL leg queued (E7)",
    detail_code: "E7_GATED" as const,
  },
  {
    id: "social",
    state: "unavailable" as const,
    reason: "mentions-only fallback",
    detail_code: "E8_GATED" as const,
    scope: "7d",
    freshness_bar: "2026-07-22",
  },
];

describe("EngineStatusRail", () => {
  it("renders every lane as a real button, not an image", () => {
    render(<EngineStatusRail sections={SECTIONS} />);
    for (const s of SECTIONS) {
      const el = screen.getByTestId(`dial-${s.id}`);
      expect(el.tagName).toBe("BUTTON");
      expect(el.dataset.state).toBe(s.state);
    }
  });

  it("says the state in words, so colour is never the only cue (NFR-4)", () => {
    render(<EngineStatusRail sections={SECTIONS} />);
    expect(screen.getByTestId("dial-technical").textContent).toContain("live");
    expect(screen.getByTestId("dial-tournament").textContent).toContain("degraded");
    expect(screen.getByTestId("dial-social").textContent).toContain("unavailable");
  });

  it("is collapsed until asked", () => {
    render(<EngineStatusRail sections={SECTIONS} />);
    expect(screen.queryByTestId("dial-detail-tournament")).toBeNull();
    expect(screen.getByTestId("dial-tournament").getAttribute("aria-expanded")).toBe("false");
  });

  it("expands with the reasoning behind the state", () => {
    render(<EngineStatusRail sections={SECTIONS} />);
    fireEvent.click(screen.getByTestId("dial-tournament"));

    const panel = screen.getByTestId("dial-detail-tournament");
    // what the lane measures
    expect(panel.textContent).toContain(deskCopy.engineWhat.tournament);
    // what the state means
    expect(panel.textContent).toContain(deskCopy.dialState.degraded.meaning);
    // the server's own reason, verbatim
    expect(panel.textContent).toContain("RL leg queued (E7)");
    // the opaque code, explained
    expect(panel.textContent).toContain(deskCopy.detailCode.E7_GATED);
  });

  it("surfaces scope and freshness when the payload carries them", () => {
    render(<EngineStatusRail sections={SECTIONS} />);
    fireEvent.click(screen.getByTestId("dial-social"));
    const panel = screen.getByTestId("dial-detail-social");
    expect(panel.textContent).toContain("7d");
    expect(panel.textContent).toContain("2026-07-22");
  });

  it("says so plainly when no reason was reported, rather than inventing one", () => {
    render(<EngineStatusRail sections={[{ id: "technical", state: "live" }]} />);
    fireEvent.click(screen.getByTestId("dial-technical"));
    expect(screen.getByTestId("dial-detail-technical").textContent).toContain(
      deskCopy.rail.noReason,
    );
  });

  it("opens one lane at a time — six open panels would bury the desk", () => {
    render(<EngineStatusRail sections={SECTIONS} />);
    fireEvent.click(screen.getByTestId("dial-tournament"));
    fireEvent.click(screen.getByTestId("dial-social"));
    expect(screen.queryByTestId("dial-detail-tournament")).toBeNull();
    expect(screen.getByTestId("dial-detail-social")).toBeTruthy();
  });

  it("toggles closed when the open lane is clicked again", () => {
    render(<EngineStatusRail sections={SECTIONS} />);
    const btn = screen.getByTestId("dial-technical");
    fireEvent.click(btn);
    expect(screen.getByTestId("dial-detail-technical")).toBeTruthy();
    fireEvent.click(btn);
    expect(screen.queryByTestId("dial-detail-technical")).toBeNull();
  });

  it("wires aria-expanded/aria-controls to the panel it opens", () => {
    render(<EngineStatusRail sections={SECTIONS} />);
    const btn = screen.getByTestId("dial-social");
    expect(btn.getAttribute("aria-controls")).toBe("dial-detail-social");
    fireEvent.click(btn);
    expect(btn.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByTestId("dial-detail-social").id).toBe("dial-detail-social");
  });

  it("keeps the lane's accessible label carrying state and reason", () => {
    render(<EngineStatusRail sections={SECTIONS} />);
    const label = screen.getByTestId("dial-tournament").getAttribute("aria-label") ?? "";
    expect(label).toContain("degraded");
    expect(label).toContain("RL leg queued (E7)");
  });

  it("scrolls to the correctly-mapped panel — the dial id is not the panel id", () => {
    // The dial ids are the closed SECTION_IDS (technical/tournament/…) but the
    // DeskV2 panels are lettered (A..F). The old link targeted #panel-technical,
    // which does not exist, so "Go to this panel" did nothing. technical -> A.
    const panelA = document.createElement("section");
    panelA.id = "panel-A";
    const scrollSpy = vi.fn();
    panelA.scrollIntoView = scrollSpy;
    document.body.appendChild(panelA);

    render(<EngineStatusRail sections={SECTIONS} />);
    fireEvent.click(screen.getByTestId("dial-technical"));
    fireEvent.click(screen.getByTestId("jump-technical"));

    expect(scrollSpy).toHaveBeenCalledTimes(1);
    document.body.removeChild(panelA);
  });

  it("tournament jumps to panel B, not a non-existent #panel-tournament", () => {
    const panelB = document.createElement("section");
    panelB.id = "panel-B";
    const scrollSpy = vi.fn();
    panelB.scrollIntoView = scrollSpy;
    document.body.appendChild(panelB);

    render(<EngineStatusRail sections={SECTIONS} />);
    fireEvent.click(screen.getByTestId("dial-tournament"));
    fireEvent.click(screen.getByTestId("jump-tournament"));

    expect(scrollSpy).toHaveBeenCalledTimes(1);
    document.body.removeChild(panelB);
  });

  it("does not throw when the target panel is not in the DOM", () => {
    render(<EngineStatusRail sections={SECTIONS} />);
    fireEvent.click(screen.getByTestId("dial-social"));
    // No panel-C mounted; clicking must be a safe no-op, not a crash.
    expect(() => fireEvent.click(screen.getByTestId("jump-social"))).not.toThrow();
  });

  it("surfaces a non-degrading note on a LIVE dial (rl_note / scored_note)", () => {
    render(
      <EngineStatusRail
        sections={[
          { id: "tournament", state: "live", rl_note: "RL leg queued (E7)" },
          { id: "social", state: "live", scored_note: "mentions-only fallback (E8)" },
        ]}
      />,
    );
    fireEvent.click(screen.getByTestId("dial-tournament"));
    expect(screen.getByTestId("dial-detail-tournament").textContent).toContain(
      "RL leg queued (E7)",
    );
    fireEvent.click(screen.getByTestId("dial-social"));
    expect(screen.getByTestId("dial-detail-social").textContent).toContain(
      "mentions-only fallback (E8)",
    );
  });

  it("explains every code in the closed DetailCode enum", () => {
    // A code with no explanation would put an opaque token back in front of
    // the reader — exactly the problem this replaced.
    for (const code of [
      "E7_GATED", "E8_GATED", "THIN_COVERAGE",
      "SOURCE_DOWN", "STALE_BEYOND_POLICY", "PARTIAL_DATA",
    ]) {
      expect(deskCopy.detailCode[code], `missing copy for ${code}`).toBeTruthy();
    }
  });
});
