/** @type {import('next').NextConfig} */
const nextConfig = {
  // LEAP S7b (D33): manual surfaces live under /pro; legacy URLs redirect
  // permanently so bookmarks and old links keep working.
  async redirects() {
    return [
      { source: "/admin", destination: "/pro/admin", permanent: true },
      { source: "/admin/:path*", destination: "/pro/admin/:path*", permanent: true },
      { source: "/analyze", destination: "/pro/analyze", permanent: true },
      { source: "/analyze/:path*", destination: "/pro/analyze/:path*", permanent: true },
      { source: "/backtests", destination: "/pro/backtests", permanent: true },
      { source: "/backtests/:path*", destination: "/pro/backtests/:path*", permanent: true },
      { source: "/comparison", destination: "/pro/comparison", permanent: true },
      { source: "/comparison/:path*", destination: "/pro/comparison/:path*", permanent: true },
      { source: "/decision", destination: "/pro/decision", permanent: true },
      { source: "/decision/:path*", destination: "/pro/decision/:path*", permanent: true },
      { source: "/integrations", destination: "/pro/integrations", permanent: true },
      { source: "/integrations/:path*", destination: "/pro/integrations/:path*", permanent: true },
      { source: "/news", destination: "/pro/news", permanent: true },
      { source: "/news/:path*", destination: "/pro/news/:path*", permanent: true },
      { source: "/operator", destination: "/pro/operator", permanent: true },
      { source: "/operator/:path*", destination: "/pro/operator/:path*", permanent: true },
      { source: "/ops", destination: "/pro/ops", permanent: true },
      { source: "/ops/:path*", destination: "/pro/ops/:path*", permanent: true },
      { source: "/paper", destination: "/pro/paper", permanent: true },
      { source: "/paper/:path*", destination: "/pro/paper/:path*", permanent: true },
      { source: "/policies", destination: "/pro/policies", permanent: true },
      { source: "/policies/:path*", destination: "/pro/policies/:path*", permanent: true },
      { source: "/replay", destination: "/pro/replay", permanent: true },
      { source: "/replay/:path*", destination: "/pro/replay/:path*", permanent: true },
      { source: "/research", destination: "/pro/research", permanent: true },
      { source: "/research/:path*", destination: "/pro/research/:path*", permanent: true },
      { source: "/risk", destination: "/pro/risk", permanent: true },
      { source: "/risk/:path*", destination: "/pro/risk/:path*", permanent: true },
      { source: "/templates", destination: "/pro/templates", permanent: true },
      { source: "/templates/:path*", destination: "/pro/templates/:path*", permanent: true },
      { source: "/universe", destination: "/pro/universe", permanent: true },
      { source: "/universe/:path*", destination: "/pro/universe/:path*", permanent: true },
    ];
  },
  experimental: {
    // Phase MVP-7: enables `src/instrumentation.ts` (Sentry init at server
    // startup). Stable as of Next 15; opt-in flag on 14.x.
    instrumentationHook: true,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
