import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import React from 'react'
import InvestigateButton from '../../components/InvestigateButton'

const mockFetch = jest.fn()
global.fetch = mockFetch

jest.mock('framer-motion', () => {
  const mkEl = (tag: string) => ({ children, ...props }: { children?: React.ReactNode; [key: string]: unknown }) => React.createElement(tag, props, children)
  return {
    motion: {
      button: mkEl('button'),
      div: mkEl('div'),
    },
    AnimatePresence: ({ children }: { children?: React.ReactNode }) => React.createElement('div', null, children),
  }
})

describe('InvestigateButton', () => {
  const originalLocation = window.location

  beforeAll(() => {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, href: '' },
      writable: true,
    })
  })

  afterAll(() => {
    Object.defineProperty(window, 'location', { value: originalLocation, writable: true })
  })

  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('renders the trigger button', () => {
    render(React.createElement(InvestigateButton))
    expect(screen.getByText('Run Investigation')).toBeTruthy()
  })

  it('opens modal on button click', () => {
    render(React.createElement(InvestigateButton))
    fireEvent.click(screen.getByText('Run Investigation'))
    expect(screen.getByText('New Investigation')).toBeTruthy()
    expect(screen.getByText('raw_events')).toBeTruthy()
    expect(screen.getByText('feature_pipeline')).toBeTruthy()
    expect(screen.getByText('feature_store')).toBeTruthy()
  })

  it('shows three dataset options in modal', () => {
    render(React.createElement(InvestigateButton))
    fireEvent.click(screen.getByText('Run Investigation'))
    expect(screen.getByText('Snowflake')).toBeTruthy()
    expect(screen.getByText('dbt')).toBeTruthy()
    expect(screen.getByText('Feast')).toBeTruthy()
  })

  it('shows worker count info text in modal', () => {
    render(React.createElement(InvestigateButton))
    fireEvent.click(screen.getByText('Run Investigation'))
    const workerTexts = screen.getAllByText(/18 workers/)
    expect(workerTexts.length).toBeGreaterThanOrEqual(1)
  })

  it('shows Start Investigation button in modal', () => {
    render(React.createElement(InvestigateButton))
    fireEvent.click(screen.getByText('Run Investigation'))
    expect(screen.getByText('Start Investigation')).toBeTruthy()
  })

  it('calls onInvestigationStarted callback on successful investigation', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ incident_id: 'abc-123' }),
    })

    const onStarted = jest.fn()
    render(React.createElement(InvestigateButton, { onInvestigationStarted: onStarted }))
    fireEvent.click(screen.getByText('Run Investigation'))
    fireEvent.click(screen.getByText('Start Investigation'))

    await waitFor(() => {
      expect(onStarted).toHaveBeenCalledWith('abc-123')
    })
  })

  it('navigates to incident page when no callback provided', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ incident_id: 'xyz-789' }),
    })

    render(React.createElement(InvestigateButton))
    fireEvent.click(screen.getByText('Run Investigation'))
    fireEvent.click(screen.getByText('Start Investigation'))

    await waitFor(() => {
      expect(window.location.href).toBe('/incidents/xyz-789')
    })
  })

  it('shows error message on failed investigation', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      json: async () => ({ error: 'DataHub connection failed' }),
    })

    render(React.createElement(InvestigateButton))
    fireEvent.click(screen.getByText('Run Investigation'))
    fireEvent.click(screen.getByText('Start Investigation'))

    await waitFor(() => {
      expect(screen.getByText('DataHub connection failed')).toBeTruthy()
    })
  })

  it('closes modal when clicking close button', () => {
    render(React.createElement(InvestigateButton))
    fireEvent.click(screen.getByText('Run Investigation'))
    expect(screen.getByText('New Investigation')).toBeTruthy()
  })
})
