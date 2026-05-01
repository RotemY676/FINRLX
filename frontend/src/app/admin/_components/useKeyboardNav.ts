import { useEffect } from "react";

export function useKeyboardNav(
  activeStep: number,
  setActiveStep: (step: number) => void,
  totalSteps: number,
) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Skip if user is typing in an input
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

      // Skip if Cmd/Ctrl is held (don't interfere with Cmd+K etc.)
      if (e.metaKey || e.ctrlKey) return;

      switch (e.key) {
        case "ArrowRight":
          e.preventDefault();
          setActiveStep(Math.min(activeStep + 1, totalSteps - 1));
          break;
        case "ArrowLeft":
          e.preventDefault();
          setActiveStep(Math.max(activeStep - 1, 0));
          break;
        case "1":
        case "2":
        case "3":
        case "4":
        case "5": {
          const idx = parseInt(e.key) - 1;
          if (idx < totalSteps) {
            e.preventDefault();
            setActiveStep(idx);
          }
          break;
        }
        case "Enter":
          document
            .getElementById("active-panel")
            ?.scrollIntoView({ behavior: "smooth" });
          break;
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [activeStep, setActiveStep, totalSteps]);
}
