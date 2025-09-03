export const metadata = {
  title: 'DiViz UI',
  description: 'Simple SPA served by FastAPI',
}

import { AuthProvider } from './auth-context'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Helvetica, Arial, Apple Color Emoji, Segoe UI Emoji', margin: 0, background: '#0b0f19', color: '#e2e8f0' }}>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}

