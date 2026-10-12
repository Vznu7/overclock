# OVERCLOCK Security Architecture & Controls

> **Scope Notice**: This document details only security controls that are **actually implemented and verified** in the OVERCLOCK codebase. In accordance with project governance rules, no certifications (ISO, SOC 2, etc.) are claimed.

---

## 1. Multi-Tenant Architecture & Database Isolation

OVERCLOCK uses a single shared PostgreSQL database schema with strict, cryptographically and kernel-enforced Row-Level Security (RLS).

### 1.1 PostgreSQL Row-Level Security (RLS)
- Every tenant data table (`tenant_settings`, `users`, `audit_logs`, and future domain tables) has PostgreSQL RLS enabled and forced:
  ```sql
  ALTER TABLE <table_name> ENABLE ROW LEVEL SECURITY;
  ALTER TABLE <table_name> FORCE ROW LEVEL SECURITY;
  ```
- RLS Policies enforce tenant containment using the session setting `app.tenant_id`:
  ```sql
  CREATE POLICY tenant_isolation_policy ON <table_name>
      USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
      WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));
  ```

### 1.2 Dedicated Non-Superuser Database Role
- PostgreSQL superusers bypass RLS by design. Therefore, the OVERCLOCK application executes exclusively under a dedicated, unprivileged role `overclock_app` created with:
  ```sql
  CREATE ROLE overclock_app WITH LOGIN PASSWORD '...' NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
  ```
- This guarantees that PostgreSQL evaluates the RLS security predicate on every `SELECT`, `INSERT`, `UPDATE`, and `DELETE`.

### 1.3 Fail-Closed Tenant Context
- If `app.tenant_id` is not set or is an empty string, `NULLIF(..., '')` evaluates to `NULL`.
- Since `tenant_id = NULL` evaluates to `NULL` (falsy in SQL boolean logic), zero rows are returned and all inserts/updates fail. Unauthenticated or un-scoped queries fail closed automatically.
- Multi-transaction continuity is maintained using an SQLAlchemy ORM `after_begin` event listener that sets `SELECT set_config('app.tenant_id', :tenant_id, true)` at every transaction boundary within an authenticated request.

---

## 2. Authentication & Credential Security

### 2.1 Password Hashing with Argon2id
- User passwords are encrypted using the Argon2id algorithm (the winner of the Password Hashing Competition, memory-hard and GPU-resistant):
  - Memory cost: 65,536 KiB (64 MB)
  - Time cost: 3 iterations
  - Parallelism: 4 threads
- Plaintext passwords are never logged, never cached in memory beyond request verification, and never stored.

### 2.2 Account Lockout Protection
- Consecutive failed login attempts are tracked per user (`failed_login_attempts`).
- Upon 5 consecutive failed login attempts, the account is locked for 15 minutes (`locked_until = now() + 15 minutes`).
- Any login attempt during the lockout period is immediately rejected with HTTP 403 Forbidden.
- Successful login resets the counter to 0.

### 2.3 JWT Token Strategy & Secure Cookies
- Dual-token architecture:
  - **Access Token**: Short-lived (15 minutes), containing `sub` (user UUID), `tenant_id`, and `role`.
  - **Refresh Token**: Long-lived (7 days), stored securely and revocable.
- HTTP-only cookies are used to mitigate XSS-based token theft:
  - `httponly=True`
  - `samesite="lax"`
  - `secure=True` in production environments (`False` only in local development).

---

## 3. Role-Based Access Control (RBAC)

OVERCLOCK enforces 6 strict organizational roles defined in `app/domains/auth/models.py`. Permissions are enforced in backend API dependencies (`require_roles`), not solely in the user interface.

### 3.1 Role Hierarchy & Responsibilities

| Role | Description |
| :--- | :--- |
| `owner` | Factory managing director / owner. Full access to settings, user provisioning, audit logs, financials. |
| `merchandiser` | Buyer coordination, order entry, style management, fabric status, costings. |
| `production_manager`| Line balancing, daily production logs, machine downtime tracking, risk interventions. |
| `store_keeper` | Fabric rolls receipt, trims, lot inspections, stock reconciliation, issuing to floor. |
| `supervisor` | Floor floor-line entry, hourly piece counts, operator attendance, basic defect logging. |
| `viewer` | Read-only auditor or stakeholder access. Cannot create, edit, or delete any records. |

### 3.2 Implemented Permission Matrix

| Resource / Action | Endpoint | Allowed Roles |
| :--- | :--- | :--- |
| **Self Profile** | `GET /api/v1/auth/me` | All authenticated roles |
| **User List** | `GET /api/v1/users` | `owner`, `merchandiser` |
| **User Provisioning** | `POST /api/v1/users` | `owner` only |
| **User Updates** | `PATCH /api/v1/users/{id}` | `owner` only |
| **Tenant Settings Read**| `GET /api/v1/tenants/current` | All authenticated roles |
| **Tenant Settings Update**| `PATCH /api/v1/tenants/current/settings` | `owner`, `merchandiser` |
| **Audit Logs Inspection**| `GET /api/v1/audit-logs` | `owner`, `viewer` |

---

## 4. Append-Only Audit Logging

All security-sensitive operations generate an immutable record in `audit_logs`:
- **Recorded Events**:
  - `LOGIN_SUCCESS`, `LOGIN_FAILED`
  - `CREATE`, `UPDATE`, `DELETE` on operational entities
  - `AI_CONFIRM` (whenever human confirms an AI recommendation)
- **Metadata Captured**:
  - `tenant_id` (RLS protected)
  - `user_id` (actor UUID)
  - `entity_type` and `entity_id`
  - `action` (string enumeration)
  - `changes_json` (structured before/after delta)
  - `ip_address` (client IPv4/IPv6 from request header)
  - `user_agent`
  - `created_at` (UTC timestamp)

---

## 5. Input Validation & Query Parameterization

- All API inputs are strictly validated at the boundaries using **Pydantic v2** models with regex constraints, length boundaries, and email verification.
- **SQL Injection Prevention**: No raw SQL string formatting is permitted. All queries use SQLAlchemy 2.0 ORM or `text()` with named bind parameters (`:param`).

---

## 6. Privacy & Data Protection (DPDP Act 2023)

- **Minimal Personal Data**: The system only processes operational business identity data (corporate name, business email).
- Personal workforce data (Aadhaar numbers, biometric logs, residential addresses) is intentionally out of MVP scope.
- Internal logs redact sensitive authentication tokens, authorization headers, and cookies.

---

## 7. Automated Test Verification

Security controls are verified automatically via test suites:
- `tests/test_rls_isolation.py`: Cross-tenant read/write prevention and fail-closed checks.
- `tests/test_auth.py`: Argon2id verification, lockout after 5 failures, token refresh.
- `tests/test_rbac.py`: Enforcement of the 6 roles across protected endpoints.
- `tests/test_audit.py`: Append-only event generation, metadata verification, and cross-tenant isolation.
