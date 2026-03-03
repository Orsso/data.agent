/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    const origin = process.env.REWRITE_API_ORIGIN ?? process.env.NEXT_PUBLIC_API_ORIGIN ?? 'http://127.0.0.1:8000'
    return [
      {
        source: '/api/:path*',
        destination: `${origin}/api/:path*`,
      },
    ]
  },
}

export default nextConfig
