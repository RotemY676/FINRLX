/** @type {import('next').NextConfig} */
const nextConfig = {
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
