/** @type {import('next').NextConfig} */
const nextConfig = {
  // Disable image optimization for Vercel (uses external images)
  images: {
    unoptimized: true,
  },
  // rewrites proxy API calls to backend when BACKEND_URL is set
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || 'https://meridian-ai-backend.onrender.com'
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: '/stream/:path*',
        destination: `${backendUrl}/stream/:path*`,
      },
      {
        source: '/health/:path*',
        destination: `${backendUrl}/health/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
