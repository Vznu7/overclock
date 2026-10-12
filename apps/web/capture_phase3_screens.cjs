const { chromium } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

async function capture() {
  const screensDir = path.resolve(__dirname, '../../docs/screens');
  if (!fs.existsSync(screensDir)) {
    fs.mkdirSync(screensDir, { recursive: true });
  }

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  console.log('[*] Navigating to Orders portal at http://localhost:5173/orders...');
  await page.goto('http://localhost:5173/orders', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  const ordersPath = path.join(screensDir, 'phase3_orders_portal.png');
  await page.screenshot({ path: ordersPath });
  console.log(`[+] Captured: ${ordersPath}`);

  // Click on the first row to open the TNA details drawer
  console.log('[*] Opening order details drawer...');
  const firstRow = page.locator('tbody tr').first();
  if (await firstRow.isVisible()) {
    await firstRow.click();
    await page.waitForTimeout(1000);
    const drawerPath = path.join(screensDir, 'phase3_orders_detail_drawer.png');
    await page.screenshot({ path: drawerPath });
    console.log(`[+] Captured: ${drawerPath}`);
  }

  // Navigate to Imports Page
  console.log('[*] Navigating to Data Import Wizard at http://localhost:5173/imports...');
  await page.goto('http://localhost:5173/imports', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  const importsPath = path.join(screensDir, 'phase3_data_imports.png');
  await page.screenshot({ path: importsPath });
  console.log(`[+] Captured: ${importsPath}`);

  await browser.close();
  console.log('[OK] All Phase 3 screenshots captured successfully!');
}

capture().catch((err) => {
  console.error('[!] Capture failed:', err);
  process.exit(1);
});
