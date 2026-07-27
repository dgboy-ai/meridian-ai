import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import React from 'react'
import ConsoleLayout from '../../components/ConsoleLayout'

const mockUsePathname = jest.fn().mockReturnValue('/dashboard')
const mockPush = jest.fn()

jest.mock('next/navigation', () => ({
  usePathname: () => mockUsePathname(),
  useRouter: () => ({ push: mockPush }),
}))

jest.mock('framer-motion', () => {
  const mkEl = (tag: string) => ({ children, ...props }: { children?: React.ReactNode; [key: string]: unknown }) => React.createElement(tag, props, children)
  return {
    motion: {
      div: mkEl('div'),
      header: mkEl('header'),
      nav: mkEl('nav'),
      main: mkEl('main'),
      span: mkEl('span'),
      aside: mkEl('aside'),
      button: mkEl('button'),
    },
    AnimatePresence: ({ children }: { children?: React.ReactNode }) => React.createElement('div', null, children),
  }
})

jest.mock('../../components/InvestigateButton', () => ({
  __esModule: true,
  default: () => React.createElement('button', { 'data-testid': 'investigate-btn' }, 'Run Investigation'),
}))

describe('ConsoleLayout', () => {
  beforeEach(() => {
    mockUsePathname.mockReturnValue('/dashboard')
    mockPush.mockClear()
  })

  it('renders sidebar navigation', () => {
    const { container } = render(React.createElement(ConsoleLayout, null, React.createElement('div', null, 'Content')))
    expect(container.querySelector('aside')).toBeTruthy()
  })

  it('renders brand name', () => {
    render(React.createElement(ConsoleLayout, null, React.createElement('div', null, 'Content')))
    const brandElements = screen.getAllByText(/Meridian AI/)
    expect(brandElements.length).toBeGreaterThanOrEqual(1)
  })

  it('renders RELIABILITY ENGINE subtitle', () => {
    render(React.createElement(ConsoleLayout, null, React.createElement('div', null, 'Content')))
    expect(screen.getByText('RELIABILITY ENGINE')).toBeTruthy()
  })

  it('renders children content', () => {
    render(React.createElement(ConsoleLayout, null, React.createElement('div', { 'data-testid': 'page-content' }, 'Dashboard Content')))
    expect(screen.getByTestId('page-content')).toHaveTextContent('Dashboard Content')
  })

  it('renders all 5 navigation items', () => {
    render(React.createElement(ConsoleLayout, null, React.createElement('div', null, 'Content')))
    expect(screen.getByText('Incident Console')).toBeTruthy()
    expect(screen.getByText('Analytics Control')).toBeTruthy()
    expect(screen.getByText('Model Registry')).toBeTruthy()
    expect(screen.getByText('Reflexion Engine')).toBeTruthy()
    expect(screen.getByText('Compliance & Audit')).toBeTruthy()
  })

  it('renders status widget with agent cluster and MCP statuses', () => {
    render(React.createElement(ConsoleLayout, null, React.createElement('div', null, 'Content')))
    expect(screen.getByText('Agent Cluster')).toBeTruthy()
    expect(screen.getByText('DataHub MCP')).toBeTruthy()
    expect(screen.getByText('GMS Webhook')).toBeTruthy()
  })

  it('renders ONLINE, SYNC, LISTENING status badges', () => {
    render(React.createElement(ConsoleLayout, null, React.createElement('div', null, 'Content')))
    expect(screen.getByText('ONLINE')).toBeTruthy()
    expect(screen.getByText('SYNC')).toBeTruthy()
    expect(screen.getByText('LISTENING')).toBeTruthy()
  })

  it('renders InvestigateButton in sidebar', () => {
    render(React.createElement(ConsoleLayout, null, React.createElement('div', null, 'Content')))
    expect(screen.getByTestId('investigate-btn')).toBeTruthy()
  })

  it('renders top control bar with auditor role', () => {
    render(React.createElement(ConsoleLayout, null, React.createElement('div', null, 'Content')))
    expect(screen.getByText(/Lead AI Auditor/)).toBeTruthy()
  })

  it('renders SECURE_AUDIT_CONSOLE header with path', () => {
    render(React.createElement(ConsoleLayout, null, React.createElement('div', null, 'Content')))
    expect(screen.getByText(/SECURE_AUDIT_CONSOLE/)).toBeTruthy()
  })

  it('skips sidebar layout on root path /', () => {
    mockUsePathname.mockReturnValue('/')
    render(React.createElement(ConsoleLayout, null, React.createElement('div', { 'data-testid': 'page-content' }, 'Landing')))
    expect(screen.getByTestId('page-content')).toHaveTextContent('Landing')
  })

  it('skips sidebar layout on docs paths', () => {
    mockUsePathname.mockReturnValue('/docs/getting-started')
    render(React.createElement(ConsoleLayout, null, React.createElement('div', { 'data-testid': 'page-content' }, 'Docs Content')))
    expect(screen.getByTestId('page-content')).toHaveTextContent('Docs Content')
  })
})
