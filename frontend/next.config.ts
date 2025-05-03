import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  // Keep configuration simple with relative paths
  trailingSlash: false,
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
