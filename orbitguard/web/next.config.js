/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  webpack: (config) => {
    // cesium references some node-only modules it never uses in the browser
    config.resolve.fallback = { ...config.resolve.fallback, fs: false, path: false };
    return config;
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    // On Vercel there is no Python backend: the site serves the baked
    // /public/data snapshot (run `orbitguard bake` before deploying).
    NEXT_PUBLIC_STATIC:
      process.env.NEXT_PUBLIC_STATIC || (process.env.VERCEL ? "1" : "0"),
  },
};

module.exports = nextConfig;
