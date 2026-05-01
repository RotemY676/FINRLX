"use client";
import { useRef, useEffect } from "react";

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  opacity: number;
}

interface ParticleBackgroundProps {
  className?: string;
  particleCount?: number;
}

function createParticle(w: number, h: number): Particle {
  return {
    x: Math.random() * w,
    y: Math.random() * h,
    vx: (Math.random() - 0.5) * 0.6, // -0.3 to 0.3
    vy: (Math.random() - 0.5) * 0.6,
    radius: 1.5 + Math.random() * 1.5, // 1.5 to 3
    opacity: 0.1 + Math.random() * 0.15, // 0.1 to 0.25
  };
}

export function ParticleBackground({
  className,
  particleCount = 50,
}: ParticleBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    /* ---- Respect reduced-motion ---- */
    const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (motionQuery.matches) return;

    /* ---- Resolve primary colour from CSS variable ---- */
    const raw = getComputedStyle(document.documentElement)
      .getPropertyValue("--primary")
      .trim();

    // Parse HSL value produced by shadcn/ui (e.g. "221.2 83.2% 53.3%")
    function primaryRgb(): { r: number; g: number; b: number } {
      // Try parsing as "h s% l%" (shadcn-style, no commas)
      const hslMatch = raw.match(
        /^([\d.]+)\s+([\d.]+)%?\s+([\d.]+)%?$/,
      );
      if (hslMatch) {
        const h = parseFloat(hslMatch[1]) / 360;
        const s = parseFloat(hslMatch[2]) / 100;
        const l = parseFloat(hslMatch[3]) / 100;
        return hslToRgb(h, s, l);
      }
      // Fallback: neutral blue-ish
      return { r: 100, g: 140, b: 220 };
    }

    function hslToRgb(
      h: number,
      s: number,
      l: number,
    ): { r: number; g: number; b: number } {
      let r: number, g: number, b: number;
      if (s === 0) {
        r = g = b = l;
      } else {
        const hue2rgb = (p: number, q: number, t: number) => {
          if (t < 0) t += 1;
          if (t > 1) t -= 1;
          if (t < 1 / 6) return p + (q - p) * 6 * t;
          if (t < 1 / 2) return q;
          if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
          return p;
        };
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        const p = 2 * l - q;
        r = hue2rgb(p, q, h + 1 / 3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1 / 3);
      }
      return {
        r: Math.round(r * 255),
        g: Math.round(g * 255),
        b: Math.round(b * 255),
      };
    }

    const color = primaryRgb();

    /* ---- Sizing ---- */
    function resize() {
      if (!canvas) return;
      const parent = canvas.parentElement;
      if (!parent) return;
      canvas.width = parent.clientWidth;
      canvas.height = parent.clientHeight;
    }
    resize();

    /* ---- Particles ---- */
    let particles: Particle[] = Array.from({ length: particleCount }, () =>
      createParticle(canvas.width, canvas.height),
    );

    /* ---- Animation loop ---- */
    let frameId: number;

    function tick() {
      if (!ctx || !canvas) return;
      const w = canvas.width;
      const h = canvas.height;

      ctx.clearRect(0, 0, w, h);

      // Update & draw particles
      for (const p of particles) {
        // Brownian nudge
        p.vx += (Math.random() - 0.5) * 0.05;
        p.vy += (Math.random() - 0.5) * 0.05;
        // Clamp velocity
        p.vx = Math.max(-0.3, Math.min(0.3, p.vx));
        p.vy = Math.max(-0.3, Math.min(0.3, p.vy));

        p.x += p.vx;
        p.y += p.vy;

        // Wrap around edges
        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${color.r},${color.g},${color.b},${p.opacity})`;
        ctx.fill();
      }

      // Draw connecting lines
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 100) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(${color.r},${color.g},${color.b},0.05)`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }

      frameId = requestAnimationFrame(tick);
    }

    frameId = requestAnimationFrame(tick);

    /* ---- Resize handler ---- */
    function handleResize() {
      resize();
      // Re-distribute particles that ended up outside bounds
      if (!canvas) return;
      for (const p of particles) {
        if (p.x > canvas.width) p.x = Math.random() * canvas.width;
        if (p.y > canvas.height) p.y = Math.random() * canvas.height;
      }
    }

    window.addEventListener("resize", handleResize);

    /* ---- Cleanup ---- */
    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener("resize", handleResize);
    };
  }, [particleCount]);

  return (
    <canvas
      ref={canvasRef}
      className={className}
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 0,
        pointerEvents: "none",
      }}
      aria-hidden="true"
    />
  );
}
