// API configuration — points to backend server
// Set NEXT_PUBLIC_API_URL env var to deploy backend separately (e.g. Render)
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

// Helper for fetch calls in pages
export function apiUrl(path: string): string {
  return `${API_BASE}${path}`
}
