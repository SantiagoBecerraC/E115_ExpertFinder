/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  // Remove assetPrefix and use relative paths
  // No trailing slash to ensure proper asset loading
  trailingSlash: false,
  // Ensure images are properly handled
  images: {
    unoptimized: true,
  },
  // Important: Make sure webpack properly processes CSS
  webpack: (config) => {
    // Handle CSS properly
    return config;
  },
  eslint: {
    // Warning: This allows production builds to successfully complete even if
    // your project has ESLint errors.
    ignoreDuringBuilds: true,
  },
  typescript: {
    // !! WARN !!
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors.
    ignoreBuildErrors: true,
  },
}

module.exports = nextConfig
