// API configuration — points to backend server
// Set NEXT_PUBLIC_API_URL env var to deploy backend separately (e.g. Render)
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

// Helper for fetch calls in pages
export function apiUrl(path: string): string {
  return `${API_BASE}${path}`
}

// Auth-aware fetch — includes Bearer token from localStorage when available
export async function authFetch<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('meridian_token') : null
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const res = await fetch(apiUrl(path), { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || `API error ${res.status}`)
  }
  return res.json()
}

// Clear auth state (for logout)
export function clearAuth(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('meridian_token')
    localStorage.removeItem('meridian_user')
  }
}

// Get current user from localStorage
export function getCurrentUser(): { email: string; role: string; name: string } | null {
  if (typeof window === 'undefined') return null
  const raw = localStorage.getItem('meridian_user')
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}
