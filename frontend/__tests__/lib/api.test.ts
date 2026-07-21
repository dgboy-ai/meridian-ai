import { listIncidents, getIncident, runInvestigation, getHealthScores, getCostSummary, getArchitecture, getAuditTrail } from '../../lib/api'

// Mock global fetch
const mockFetch = jest.fn()
global.fetch = mockFetch

beforeEach(() => {
  mockFetch.mockReset()
})

describe('API Client', () => {
  describe('listIncidents', () => {
    it('returns incidents array from /api/incidents', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          incidents: [
            { id: '42', title: 'Schema Change', severity: 'HIGH', status: 'RESOLVED', detected: '2026-07-16T08:00:00Z', duration_seconds: 180, affected_models: ['churn_model_v3'], pattern_id: 'SCHEMA_DRIFT' },
          ],
        }),
      })

      const incidents = await listIncidents()
      expect(incidents).toHaveLength(1)
      expect(incidents[0].id).toBe('42')
      expect(mockFetch).toHaveBeenCalledWith('/api/incidents', expect.any(Object))
    })

    it('returns empty array on fetch failure', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))
      const incidents = await listIncidents()
      expect(incidents).toEqual([])
    })
  })

  describe('getIncident', () => {
    it('fetches incident by ID', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ id: '42', title: 'Test', timeline: [] }),
      })

      const incident = await getIncident('42')
      expect(incident.id).toBe('42')
      expect(mockFetch).toHaveBeenCalledWith('/api/incidents/42', expect.any(Object))
    })
  })

  describe('runInvestigation', () => {
    it('POSTs to /api/investigate with dataset URN', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          incident_id: '123',
          status: 'completed',
          dataset_urn: 'urn:li:dataset:test',
          workers_fired: ['data_sentinel'],
          resolution_time_minutes: 0.5,
          health_score: 89,
          datahub_mutations: 17,
          timeline_steps: 14,
          blast_radius_nodes: 3,
          writeback_artifacts: 4,
        }),
      })

      const result = await runInvestigation('urn:li:dataset:test')
      expect(result.status).toBe('completed')
      expect(result.health_score).toBe(89)
      expect(mockFetch).toHaveBeenCalledWith('/api/investigate', expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ dataset_urn: 'urn:li:dataset:test' }),
      }))
    })

    it('includes incident_id when provided', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ incident_id: 'custom-123', status: 'completed' }),
      })

      await runInvestigation('urn:li:dataset:test', 'custom-123')
      expect(mockFetch).toHaveBeenCalledWith('/api/investigate', expect.objectContaining({
        body: JSON.stringify({ dataset_urn: 'urn:li:dataset:test', incident_id: 'custom-123' }),
      }))
    })
  })

  describe('getHealthScores', () => {
    it('returns model health data', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ models: [{ name: 'churn_model_v3', health_score: 89 }] }),
      })

      const data = await getHealthScores()
      expect(data.models).toHaveLength(1)
      expect(data.models[0].name).toBe('churn_model_v3')
    })
  })

  describe('getCostSummary', () => {
    it('returns cost data', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ total_cost_usd: 0.03, total_time_saved_minutes: 42 }),
      })

      const data = await getCostSummary()
      expect(data.total_cost_usd).toBe(0.03)
    })
  })

  describe('getArchitecture', () => {
    it('returns system architecture', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ name: 'Meridian AI', workers: [{ id: 'data_sentinel' }], stats: { total_workers: 18 } }),
      })

      const data = await getArchitecture()
      expect(data.name).toBe('Meridian AI')
      expect(data.stats.total_workers).toBe(18)
    })
  })

  describe('getAuditTrail', () => {
    it('returns audit trail data', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ total_records: 5, chain_valid: true }),
      })

      const data = await getAuditTrail()
      expect(data.total_records).toBe(5)
      expect(data.chain_valid).toBe(true)
    })
  })

  describe('error handling', () => {
    it('throws on non-ok response for getIncident', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({ error: 'Not found' }),
      })

      await expect(getIncident('999')).rejects.toThrow('Not found')
    })

    it('listIncidents returns empty array on network error', async () => {
      mockFetch.mockRejectedValue(new Error('fetch failed'))
      const incidents = await listIncidents()
      expect(incidents).toEqual([])
    })
  })
})
