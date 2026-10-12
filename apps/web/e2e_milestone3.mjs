import { chromium } from '@playwright/test'
import fs from 'fs'
import path from 'path'

const artifactDir = 'C:/Users/vishn/.gemini/antigravity/brain/34f31c62-9e91-4f21-84f4-a1463e892e69/screens'
const docsScreensDir = 'd:/overclock/docs/screens'

fs.mkdirSync(artifactDir, { recursive: true })
fs.mkdirSync(docsScreensDir, { recursive: true })

async function run() {
  console.log('[*] Starting Milestone 3 E2E test & visual capture...')

  // 1. Authenticate with live Supabase-backed API
  const loginRes = await fetch('http://127.0.0.1:8000/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      tenant_id: 'tirupur-demo',
      email: 'merchandiser@tirupur-demo.com',
      password: 'MerchDemo123!',
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
    viewport: { width: 1400, height: 900 },
    deviceScaleFactor: 1,
  })

  // Pre-seed localStorage with authenticated session
  await context.addInitScript(({ token, user }) => {
    localStorage.setItem('overclock_token', token)
    localStorage.setItem('overclock_user', JSON.stringify(user))
  }, { token, user })

  const page = await context.newPage()

  async function snap(name) {
    const artPath = path.join(artifactDir, name)
    const docPath = path.join(docsScreensDir, name)
    await page.screenshot({ path: artPath, fullPage: false })
    await page.screenshot({ path: docPath, fullPage: false })
    console.log(`[OK] Saved ${name}`)
  }

  // Step 1: Navigate to PO Review Page (Split-screen)
  console.log('Navigating to /po-review...')
  await page.goto('http://127.0.0.1:5173/po-review', { waitUntil: 'domcontentloaded', timeout: 15000 })
  await page.waitForTimeout(3500)
  await snap('milestone3_po_split_screen.png')

  // Step 2: Click H&M Global Preset
  console.log('Testing preset switch to H&M Global...')
  const hmBtn = page.getByRole('button', { name: /H&M Global/i })
  if (await hmBtn.count() > 0) {
    await hmBtn.click()
    await page.waitForTimeout(3000)
    await snap('milestone3_po_hm_preset.png')
  }

  // Step 3: Confirm & Create Order in Supabase
  console.log('Testing Confirm & Create Order in Supabase...')
  const confirmBtn = page.getByRole('button', { name: /Confirm & Create Order in Supabase/i })
  if (await confirmBtn.count() > 0) {
    await confirmBtn.click()
    await page.waitForTimeout(4000)
    await snap('milestone3_po_confirmed.png')
  }

  // Step 4: Switch Language to Tamil (தமிழ்)
  console.log('Testing Tamil language switch...')
  await page.evaluate(() => {
    localStorage.setItem('overclock_lang', 'ta')
  })
  await page.reload({ waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(2000)

  // Step 5: Capture PO Review in Tamil
  await snap('milestone3_tamil_po_review.png')

  // Step 6: Navigate to Company Portal in Tamil
  console.log('Navigating to Company Portal in Tamil...')
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded', timeout: 15000 })
  await page.waitForTimeout(2500)
  await snap('milestone3_tamil_company_portal.png')

  // Step 7: Navigate to Control Tower in Tamil
  console.log('Navigating to Control Tower in Tamil...')
  await page.goto('http://127.0.0.1:5173/dashboard', { waitUntil: 'domcontentloaded', timeout: 15000 })
  await page.waitForTimeout(2500)
  await snap('milestone3_tamil_control_tower.png')

  await browser.close()
  console.log('[*] Milestone 3 E2E test & visual captures completed successfully!')
}

run().catch(err => {
  console.error('[!] E2E script failed:', err)
  process.exit(1)
})
