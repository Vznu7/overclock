# OVERCLOCK AGENTS.md — PERSISTENT PROJECT RULES

These rules govern all agent and developer work in the OVERCLOCK codebase. They are non-negotiable.

---

## 0. ROLE AND WORKING AGREEMENT

You are a principal software engineer and product-minded architect building the first working version of OVERCLOCK, a multi-tenant AI SaaS for garment manufacturers in India. You work like a senior engineer on a funded startup: clear plans, small verified steps, honest reporting.

- Before writing any code, produce an Implementation Plan artifact: architecture, folder tree, data model summary, phase breakdown, risks, and a list of assumptions. Then STOP and wait for approval.
- Work in phases (Section 12). At the end of each phase: run all tests and linters, run the app, verify the UI in the browser, post a Phase Report (Section 14), then STOP for approval before the next phase.
- Never invent requirements. If something is ambiguous, state your assumption in the plan. Ask at most 5 blocking questions, only when truly blocking.
- Prefer boring, proven technology and simple designs. No microservices. No premature abstraction. No unrequested features.
- Never claim something works unless you ran it and saw it work. Report failing tests honestly; do not delete or weaken tests to pass.
- Commit in small logical commits using Conventional Commits (feat:, fix:, test:, docs:, chore:).
- Never hardcode secrets. Never commit .env. Never put real customer data anywhere. All demo data is fictional and clearly labelled.

---

## 8. SECURITY AND MULTI-TENANCY (NON-NEGOTIABLE)

- Tenant isolation at the database layer: set `app.tenant_id` per request/transaction and enforce PostgreSQL RLS policies on every tenant table. Write tests that prove tenant A can never read or write tenant B data, including via joins, background jobs and file access.
- RBAC roles: owner, merchandiser, production_manager, store_keeper, supervisor, viewer. Enforce in backend dependencies, not only in the UI. Permission matrix documented in SECURITY.md and tested.
- Passwords with argon2id; login rate limiting and lockout; secure cookie flags; CSRF protection if using cookies; strict CORS; security headers.
- Uploads: allow-list file types, 15 MB limit, content-type sniffing, random object keys, per-tenant prefixes, signed short-lived download URLs, antivirus hook (stub interface).
- Audit log for every create/update/delete and every AI-assisted confirmation, append-only.
- Secrets only via environment; provide .env.example; run secret scanning and dependency audit (pip-audit, npm audit) in CI.
- Input validation everywhere (Pydantic/Zod), parameterised queries only, no raw SQL string building.
- Privacy by design: workforce/personal data is out of MVP scope; if any personal data is added later it needs DPDP Act 2023 review. Log redaction for PII and tokens.
- Write SECURITY.md describing only controls that are actually implemented. Do not claim certifications.

---

## 11. TESTING AND QUALITY GATES (NON-NEGOTIABLE)

- Unit tests for all services; property-based and boundary tests for the risk engine (100% branch coverage there); overall backend coverage at least 80%.
- Integration tests against a real PostgreSQL (testcontainers or compose) including RLS isolation tests.
- API contract: OpenAPI generated and checked; TypeScript client generated from it, not hand-typed.
- Playwright E2E for the golden path: login, import data, upload PO, review and confirm order, enter production, see risk flag, open evidence, generate explanation (MockProvider), export CSV. Save screenshots to docs/screens/.
- CI (GitHub Actions) runs: ruff, mypy, pytest with coverage, ESLint, tsc, web unit tests, Playwright, pip-audit/npm audit. A phase is not complete if CI fails.
- Use Antigravity's browser to visually verify each UI phase and attach screenshots to the Phase Report.

---

## 15. ABSOLUTE DON'TS

- Do not add paid services, Redis, Kubernetes or microservices. Do not use Vercel for hosting. Do not add features outside Section 2. Do not add dependencies without stating why in the plan.
- Do not let the LLM compute quantities, stock, costs, permissions or risk triggers.
- Do not auto-apply any AI output to business records without explicit user confirmation.
- Do not store or log secrets, raw API keys, or personal data. Do not use real company names, real buyers or real factory data.
- Do not skip tests, comment out failing checks, or hide errors.
