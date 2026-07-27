import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import React from 'react'
import { DocH1, DocH2, DocH3, DocP, DocBadge, DocCode, DocCard, DocInfo, DocTable, DocDivider } from '../../components/docs/DocElements'

jest.mock('framer-motion', () => {
  const mkEl = (tag: string) => ({ children, ...props }: { children?: React.ReactNode; [key: string]: unknown }) => React.createElement(tag, props, children)
  return {
    motion: {
      h1: mkEl('h1'),
      h2: mkEl('h2'),
      div: mkEl('div'),
    },
  }
})

describe('DocElements', () => {
  describe('DocH1', () => {
    it('renders children as heading', () => {
      render(React.createElement(DocH1, null, 'Test Heading'))
      expect(screen.getByText('Test Heading')).toBeTruthy()
    })
  })

  describe('DocH2', () => {
    it('renders children as subheading', () => {
      render(React.createElement(DocH2, null, 'Sub Heading'))
      expect(screen.getByText('Sub Heading')).toBeTruthy()
    })
  })

  describe('DocH3', () => {
    it('renders children as tertiary heading', () => {
      render(React.createElement(DocH3, null, 'Tertiary Heading'))
      expect(screen.getByText('Tertiary Heading')).toBeTruthy()
    })
  })

  describe('DocP', () => {
    it('renders paragraph text', () => {
      render(React.createElement(DocP, null, 'Paragraph content here'))
      expect(screen.getByText('Paragraph content here')).toBeTruthy()
    })
  })

  describe('DocBadge', () => {
    it('renders badge with default purple color', () => {
      render(React.createElement(DocBadge, null, 'Important'))
      expect(screen.getByText('Important')).toBeTruthy()
    })

    it('renders badge with custom color', () => {
      render(React.createElement(DocBadge, { color: '#10b981' }, 'Success'))
      expect(screen.getByText('Success')).toBeTruthy()
    })
  })

  describe('DocCode', () => {
    it('renders inline code block', () => {
      render(React.createElement(DocCode, { inline: true }, 'npm install'))
      expect(screen.getByText('npm install')).toBeTruthy()
    })

    it('renders block code element', () => {
      render(React.createElement(DocCode, null, 'console.log("hello")'))
      expect(screen.getByText('console.log("hello")')).toBeTruthy()
    })
  })

  describe('DocCard', () => {
    it('renders card with title and icon', () => {
      render(React.createElement(DocCard, { title: 'Feature Card', icon: '\u2605' }, 'Card description text'))
      expect(screen.getByText('Feature Card')).toBeTruthy()
      expect(screen.getByText('\u2605')).toBeTruthy()
      expect(screen.getByText('Card description text')).toBeTruthy()
    })
  })

  describe('DocInfo', () => {
    it('renders info callout', () => {
      render(React.createElement(DocInfo, { type: 'info' }, 'This is informational'))
      expect(screen.getByText(/Info/)).toBeTruthy()
      expect(screen.getByText('This is informational')).toBeTruthy()
    })

    it('renders warning callout', () => {
      render(React.createElement(DocInfo, { type: 'warning' }, 'This is a warning'))
      expect(screen.getByText(/Warning/)).toBeTruthy()
      expect(screen.getByText('This is a warning')).toBeTruthy()
    })

    it('renders tip callout', () => {
      render(React.createElement(DocInfo, { type: 'tip' }, 'This is a tip'))
      expect(screen.getByText(/Tip/)).toBeTruthy()
      expect(screen.getByText('This is a tip')).toBeTruthy()
    })
  })

  describe('DocTable', () => {
    it('renders table with headers and rows', () => {
      const headers = ['Name', 'Type', 'Status']
      const rows = [
        ['churn_model_v3', 'MLModel', 'ACTIVE'],
        ['raw_events', 'Dataset', 'DEGRADED'],
      ]
      render(React.createElement(DocTable, { headers: headers, rows: rows }))
      expect(screen.getByText('Name')).toBeTruthy()
      expect(screen.getByText('Type')).toBeTruthy()
      expect(screen.getByText('Status')).toBeTruthy()
      expect(screen.getByText('churn_model_v3')).toBeTruthy()
      expect(screen.getByText('DEGRADED')).toBeTruthy()
    })
  })

  describe('DocDivider', () => {
    it('renders a divider element', () => {
      const { container } = render(React.createElement(DocDivider))
      expect(container.querySelector('div')).toBeTruthy()
    })
  })
})
