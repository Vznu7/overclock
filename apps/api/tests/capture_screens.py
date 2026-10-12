import os

from playwright.sync_api import sync_playwright


def capture_ui():
    os.makedirs("../../docs/screens", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # 1. Company Portal Home Page (Desktop) - Shows OVERCLOCK details + Company description + About section + Tools Grid
        page = browser.new_page(viewport={"width": 1440, "height": 1300})
        page.goto("http://localhost:5173", wait_until="networkidle")
        page.screenshot(path="../../docs/screens/phase1_company_portal.png", full_page=True)

        # 2. Dedicated About OVERCLOCK Page
        page.goto("http://localhost:5173/about", wait_until="networkidle")
        page.screenshot(path="../../docs/screens/phase1_about_page.png", full_page=True)

        # 3. Live Risk Dashboard
        page.goto("http://localhost:5173/dashboard", wait_until="networkidle")
        page.screenshot(path="../../docs/screens/phase1_tool_dashboard.png", full_page=True)

        # 4. PO Ingestion & AI Inspection
        page.goto("http://localhost:5173/po-review", wait_until="networkidle")
        page.screenshot(path="../../docs/screens/phase1_tool_po_review.png", full_page=True)

        # 5. Mobile View of Portal
        mobile_page = browser.new_page(viewport={"width": 390, "height": 844})
        mobile_page.goto("http://localhost:5173", wait_until="networkidle")
        mobile_page.screenshot(path="../../docs/screens/phase1_portal_mobile.png", full_page=True)

        browser.close()
    print("Screenshots captured successfully.")


if __name__ == "__main__":
    capture_ui()
