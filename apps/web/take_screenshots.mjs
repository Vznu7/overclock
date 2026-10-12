import { chromium } from '@playwright/test'
import fs from 'fs'
import path from 'path'

const artifactDir = 'C:/Users/vishn/.gemini/antigravity/brain/34f31c62-9e91-4f21-84f4-a1463e892e69/screens'
const docsScreensDir = 'd:/overclock/docs/screens'

fs.mkdirSync(artifactDir, { recursive: true })
fs.mkdirSync(docsScreensDir, { recursive: true })

async function run() {
  // 1. Fetch demo auth token from live API
  const loginRes = await fetch('http://127.0.0.1:8000/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      tenant_id: 'tirupur-demo',
      email: 'owner@tirupur-demo.com',
      password: 'OwnerDemo123!',
    }),
  })
  const authData = await loginRes.json()
  const token = authData.access_token
  const user = {
    id: authData.user_id,
    email: authData.email,
    full_name: authData.full_name,
    role: authData.role,
    tenant_id: authData.tenant_id,
  }

  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: 1366, height: 850 },
    deviceScaleFactor: 1,
  })

  // Pre-seed localStorage with authenticated session
  await context.addInitScript(({ token, user }) => {
    localStorage.setItem('overclock_token', token)
    localStorage.setItem('overclock_user', JSON.stringify(user))
  }, { token, user })

  const page = await context.newPage()

  const pagesToCapture = [
    {
      url: 'http://127.0.0.1:5173/',
      name: 'milestone2_company_portal.png',
      waitFor: 2000,
    },
    {
      url: 'http://127.0.0.1:5173/dashboard',
      name: 'milestone2_control_tower.png',
      waitFor: 2500,
    },
    {
      url: 'http://127.0.0.1:5173/jobwork',
      name: 'milestone2_jobwork_hub.png',
      waitFor: 2500,
    },
    {
      url: 'http://127.0.0.1:5173/risk-evidence',
      name: 'milestone2_risk_evidence.png',
      waitFor: 2500,
    },
    {
      url: 'http://127.0.0.1:5173/production',
      name: 'milestone2_production_floor.png',
      waitFor: 2500,
    },
  ]

  for (const item of pagesToCapture) {
    console.log(`Navigating to ${item.url}...`)
    try {
      await page.goto(item.url, { waitUntil: 'domcontentloaded', timeout: 15000 })
      await page.waitForTimeout(item.waitFor)
      const artifactPath = path.join(artifactDir, item.name)
      const docsPath = path.join(docsScreensDir, item.name)
      await page.screenshot({ path: artifactPath, fullPage: false })
      await page.screenshot({ path: docsPath, fullPage: false })
      console.log(`[OK] Saved screenshot to ${artifactPath} and ${docsPath}`)
    } catch (e) {
      console.error(`Error capturing ${item.url}:`, e.message)
    }
  }

  await browser.close()
  console.log('All authenticated screenshots captured successfully!')
}

run()
