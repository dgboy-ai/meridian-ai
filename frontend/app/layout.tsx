import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Meridian AI — The AI Reliability Engineer',
  description: 'Silent ML failures cost $45,000/day. We catch them in 8 minutes. And the next one takes 3.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
