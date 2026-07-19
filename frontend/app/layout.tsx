import type { Metadata } from 'next'
import './globals.css'
import ErrorBoundary from '../components/ErrorBoundary'

export const metadata: Metadata = {
  title: 'Meridian AI — The AI Reliability Engineer',
  description: 'Silent ML failures cost $45,000/day. Meridian AI catches them in 8 minutes. Autonomous investigation, DataHub write-back, EU AI Act compliance.',
  keywords: ['ML reliability', 'DataHub', 'AI agent', 'incident response', 'MLOps'],
  openGraph: {
    title: 'Meridian AI — The AI Reliability Engineer',
    description: 'Silent ML failures cost $45,000/day. We catch them in 8 minutes.',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ErrorBoundary>{children}</ErrorBoundary>
      </body>
    </html>
  )
}
