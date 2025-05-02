/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  // Configure asset prefix based on environment
  assetPrefix: process.env.NODE_ENV === 'production' ? 'http://35.237.222.42.sslip.io' : '',
  // Configure public path for assets
  publicRuntimeConfig: {
    basePath: process.env.NODE_ENV === 'production' ? 'http://35.237.222.42.sslip.io' : '',
  },
  // Configure trailing slash behavior
  trailingSlash: true,
  // Ensure images are properly handled
  images: {
    unoptimized: true,
    domains: ['35.237.222.42.sslip.io'],
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
