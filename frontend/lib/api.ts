const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

export async function apiFetch<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || `API error ${res.status}`)
  }
  return res.json()
}

export interface Incident {
  id: string
  title: string
  severity: string
  status: string
  detected: string
  duration_seconds: number
  affected_models: string[]
  pattern_id: string
}

export interface InvestigationResult {
  incident_id: string
  status: string
  dataset_urn: string
  workers_fired: string[]
  resolution_time_minutes: number
  health_score: number
  datahub_mutations: number
  timeline_steps: number
  blast_radius_nodes: number
  writeback_artifacts: number
}

export interface SSEEvent {
  step: string
  status: string
  timestamp: string
  finding?: string
  confidence?: number
  message?: string
  severity?: string
  evidence?: any
  business_impact?: any
}

export async function listIncidents(): Promise<Incident[]> {
  try {
    const data = await apiFetch<{ incidents: Incident[] }>('/api/incidents')
    return data.incidents || []
  } catch {
    return []
  }
}

export async function getIncident(id: string): Promise<any> {
  return apiFetch(`/api/incidents/${id}`)
}

export async function runInvestigation(
  datasetUrn: string,
  incidentId?: string
): Promise<InvestigationResult> {
  return apiFetch('/api/investigate', {
    method: 'POST',
    body: JSON.stringify({
      dataset_urn: datasetUrn,
      ...(incidentId ? { incident_id: incidentId } : {}),
    }),
  })
}

export async function getHealthScores(): Promise<any> {
  return apiFetch('/api/health-scores')
}

export async function getCostSummary(): Promise<any> {
  return apiFetch('/api/costs')
}

export async function getArchitecture(): Promise<any> {
  return apiFetch('/api/system/architecture')
}

export async function getAuditTrail(): Promise<any> {
  return apiFetch('/api/compliance/audit-trail')
}

export async function scanPII(datasetUrn: string): Promise<any> {
  return apiFetch('/api/compliance/scan-pii', {
    method: 'POST',
    body: JSON.stringify({ dataset_urn: datasetUrn }),
  })
}

export function streamReplay(
  incidentId: string,
  delay: number = 0.6,
  onEvent: (event: SSEEvent) => void,
  onDone: () => void,
  onError: (err: Event) => void
): EventSource {
  const es = new EventSource(
    `${API_BASE}/stream/replay?incident_id=${incidentId}&delay=${delay}`
  )
  es.onmessage = (msg) => {
    if (msg.data === '[DONE]') {
      es.close()
      onDone()
      return
    }
    try {
      onEvent(JSON.parse(msg.data))
    } catch {}
  }
  es.onerror = (e) => {
    es.close()
    onError(e)
  }
  return es
}
