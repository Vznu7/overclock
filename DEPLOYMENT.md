# OVERCLOCK — 100% Free-Tier Cloud Deployment Guide

> **Target Architecture:** Zero-Cost Cloud SaaS (₹0 / $0 per month forever)  
> **Database:** Supabase PostgreSQL Cloud (500 MB Free Tier with Row-Level Security)  
> **Backend API:** Koyeb / Render Web Service (Free Tier, Python 3.12, Docker / Native)  
> **Frontend:** Vercel (Hobby Free Tier, Global Edge CDN, SPA Rewrites)  

---

## 1. Free-Tier Architecture Overview

```
                                  [ INTERNET USERS / BROWSER ]
                                               │
                                               ▼
                                      [ Vercel Edge CDN ]
                                   (apps/web React SPA + Vite)
                                               │
                                               │ API Requests (HTTPS)
                                               ▼
                                      [ Koyeb / Render ]
                                   (apps/api FastAPI + Uvicorn)
                                               │
                                               │ SSL (Port 5432 / 6543)
                                               ▼
                                    [ Supabase Cloud Postgres ]
                                  (Multi-Tenant with RLS Policies)
```

---

## 2. Step 1: Database (Supabase PostgreSQL Cloud)

The production database is **already provisioned and operational** on Supabase Cloud.

### Connection Parameters:
- **Host:** `db.mcitgctjhbwcijzuzgez.supabase.co`
- **Port:** `5432` (or `6543` for Transaction Pooler)
- **Database:** `postgres`
- **Username:** `postgres`
- **Password:** Configured via environment secret.

### Running Migrations & Seeding in Production:
From any machine with repository access:
```bash
# 1. Run Alembic migrations against Supabase
DATABASE_URL="postgresql://postgres:[PASSWORD]@db.mcitgctjhbwcijzuzgez.supabase.co:5432/postgres" \
uv run --project apps/api alembic upgrade head

# 2. Seed initial demo cluster (Tiruppur demo)
DATABASE_URL="postgresql://postgres:[PASSWORD]@db.mcitgctjhbwcijzuzgez.supabase.co:5432/postgres" \
uv run --project apps/api python apps/api/scripts/seed_demo_tenant.py
```

---

## 3. Step 2: Backend API Deployment (Koyeb or Render Free Tier)

### Option A: Koyeb (Recommended — Zero Cold Sleep)
1. Sign up for a free account at [koyeb.com](https://www.koyeb.com).
2. Click **Create App** → **GitHub**.
3. Select your repository `overclock`.
4. Choose **Dockerfile** deployment:
   - **Dockerfile location:** `apps/api/Dockerfile`
   - **Context path:** `apps/api`
5. Configure Environment Variables:
   | Variable | Value | Purpose |
   | :--- | :--- | :--- |
   | `DATABASE_URL` | `postgresql://postgres:[PASSWORD]@db.mcitgctjhbwcijzuzgez.supabase.co:5432/postgres` | Cloud database URL |
   | `SECRET_KEY` | *(Generate a 64-char random hex string)* | JWT signing key |
   | `ENVIRONMENT` | `production` | Production mode |
   | `DEBUG` | `false` | Disable debug docs in prod |
   | `CORS_ORIGINS` | `["https://*.pages.dev","https://your-domain.com","http://localhost:5173"]` | Allow web frontend origins |
6. Health Check:
   - Protocol: `HTTP`
   - Path: `/health/live`
   - Port: `8000`
7. Click **Deploy**. Your API will be live at `https://<your-app-name>.koyeb.app`.

### Option B: Render Web Service
1. Sign up at [render.com](https://render.com).
2. Click **New +** → **Web Service**.
3. Connect your GitHub repository.
4. Settings:
   - **Root Directory:** `apps/api`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install uv && uv pip install --system -e .`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add the same Environment Variables as above.
6. Click **Create Web Service**.

---

## 4. Step 3: Frontend Deployment on Vercel (Recommended)

The frontend is fully configured with `vercel.json` and client-side SPA rewrites for instant 1-click deployment on Vercel.

### Deploying via Vercel Web Dashboard:
1. Go to [vercel.com](https://vercel.com) and log in with your GitHub account.
2. Click **Add New...** → **Project**.
3. Import your `overclock` repository.
4. Configure Project Settings:
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click `Edit` and select `apps/web` (or leave as root since root `vercel.json` is configured).
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Add Environment Variable:
   | Key | Value | Notes |
   | :--- | :--- | :--- |
   | `VITE_API_BASE_URL` | `https://<your-backend-app>.koyeb.app` (from Step 2) | Backend API endpoint |
6. Click **Deploy**. In ~30 seconds, your site will be live at `https://overclock-web.vercel.app` (or custom domain).

### Deploying via Vercel CLI (Optional):
```bash
npm install -g vercel
vercel login
cd apps/web
vercel --prod
```

---

## 4.1. Alternative Frontend: Cloudflare Pages
If you prefer Cloudflare Pages:
1. Go to **Workers & Pages** on Cloudflare → **Create application** → **Pages** → **Connect to Git**.
2. Select `overclock`, set Root directory to `apps/web`, Framework to `Vite`, build command to `npm run build`, output to `dist`.
3. Add `VITE_API_BASE_URL`.


---

## 5. Step 4: Verification & Smoke Test Checklist

Once both services are deployed:
1. **Health Verification:**
   ```bash
   curl -i https://<your-backend>.koyeb.app/health/ready
   # Expected: HTTP 200 OK with {"status": "ready", "database": "connected"}
   ```
2. **CORS Verification:**
   Verify that login from `https://<project-name>.pages.dev` succeeds without browser CORS errors.
3. **Cloud Database Audit:**
   Verify that actions in `/po-review`, `/jobwork`, and `/production` insert records directly into Supabase cloud PostgreSQL.
4. **Bilingual Toggle:**
   Click the `EN / தமிழ்` pill in the header to ensure Tamil localization loads instantly on mobile and desktop.
