import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

// Mock global fetch for health check
global.fetch = vi.fn().mockImplementation(() =>
  Promise.resolve({
    ok: true,
    json: () =>
      Promise.resolve({
        status: 'ready',
        service: 'OVERCLOCK API',
        version: '0.1.0',
        environment: 'test',
        dependencies: {
          database: 'connected',
          storage: 'ready',
          ai_provider: 'mock',
        },
      }),
  })
)

describe('App Suite Routing', () => {
  it('renders OVERCLOCK suite header and company portal', async () => {
    render(<App />)
    expect(screen.getByText('OVERCLOCK')).toBeInTheDocument()
    expect(screen.getByText('Demo Knit Exports (Pvt) Ltd')).toBeInTheDocument()
  })

  it('renders demo environment banner and suite tools section', () => {
    render(<App />)
    expect(screen.getByText('DEMO ENVIRONMENT')).toBeInTheDocument()
    expect(screen.getByText('02 / Connected Workspaces')).toBeInTheDocument()
  })
})
