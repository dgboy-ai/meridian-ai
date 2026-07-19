import React from 'react'

// Suppress console.error for expected test errors
const originalError = console.error
beforeAll(() => { console.error = () => {} })
afterAll(() => { console.error = originalError })

// Dynamically import ErrorBoundary to avoid module-level JSX issues
let ErrorBoundary: any

beforeAll(async () => {
  const mod = await import('../../components/ErrorBoundary')
  ErrorBoundary = mod.default
})

describe('ErrorBoundary', () => {
  it('exports a class component', () => {
    expect(ErrorBoundary).toBeDefined()
    expect(typeof ErrorBoundary).toBe('function')
  })

  it('has getDerivedStateFromError static method', () => {
    expect(typeof ErrorBoundary.getDerivedStateFromError).toBe('function')
  })

  it('getDerivedStateFromError returns error state', () => {
    const error = new Error('test error')
    const state = ErrorBoundary.getDerivedStateFromError(error)
    expect(state.hasError).toBe(true)
    expect(state.error).toBe(error)
  })

  it('renders children when no error occurs', () => {
    const element = React.createElement(ErrorBoundary, null,
      React.createElement('div', null, 'Working content')
    )
    const ReactDOM = require('react-dom')
    const container = document.createElement('div')
    document.body.appendChild(container)
    ReactDOM.render(element, container)
    expect(container.textContent).toContain('Working content')
    document.body.removeChild(container)
  })

  it('renders error UI when child throws', () => {
    const ThrowComponent = () => {
      throw new Error('Component crashed')
    }

    const element = React.createElement(ErrorBoundary, null,
      React.createElement(ThrowComponent)
    )
    const ReactDOM = require('react-dom')
    const container = document.createElement('div')
    document.body.appendChild(container)
    ReactDOM.render(element, container)
    expect(container.textContent).toContain('Something went wrong')
    expect(container.textContent).toContain('Component crashed')
    document.body.removeChild(container)
  })

  it('renders custom fallback when provided', () => {
    const ThrowComponent = () => {
      throw new Error('oops')
    }
    const fallback = React.createElement('div', { 'data-testid': 'custom' }, 'Custom Error UI')

    const element = React.createElement(ErrorBoundary, { fallback },
      React.createElement(ThrowComponent)
    )
    const ReactDOM = require('react-dom')
    const container = document.createElement('div')
    document.body.appendChild(container)
    ReactDOM.render(element, container)
    expect(container.textContent).toContain('Custom Error UI')
    document.body.removeChild(container)
  })
})
