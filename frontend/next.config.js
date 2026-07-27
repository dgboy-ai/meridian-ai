/** @type {import('next').NextConfig} */
const nextConfig = {
  // Disable image optimization for Vercel (uses external images)
  images: {
    unoptimized: true,
  },
  // Unified Vercel deployment handles /api/* routing directly to Python serverless functions
}

module.exports = nextConfig
