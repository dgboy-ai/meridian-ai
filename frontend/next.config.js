/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // Proxy API requests to backend in production
  // This allows the frontend to use relative URLs (/api/*)
  // instead of absolute URLs (http://backend-api:8000/api/*)
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
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
