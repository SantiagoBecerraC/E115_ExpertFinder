/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  // Configure asset prefix based on environment
  assetPrefix: process.env.NODE_ENV === 'production' ? '/' : '',
  // Configure trailing slash behavior
  trailingSlash: true,
  // Configure base path if needed
  // basePath: '',
  // Ensure images are properly handled
  images: {
    unoptimized: true,
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
