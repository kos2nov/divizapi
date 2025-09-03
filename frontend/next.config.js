/** @type {import('next').NextConfig} */
const isProd = process.env.NODE_ENV === 'production'

const nextConfig = {
  output: 'export',
  distDir: 'out',
  assetPrefix: isProd ? '/static/' : undefined,
  images: { unoptimized: true },
}

module.exports = nextConfig

