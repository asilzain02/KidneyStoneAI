-- ═══════════════════════════════════════════════════════════════
-- authentication.sql — KidneyStoneAI Platform
-- Schema: Authentication & Authorization
-- Owned by: Authentication Service
-- Convention: UUID PKs, soft deletes, audit columns, BCrypt passwords
-- ═══════════════════════════════════════════════════════════════

CREATE SCHEMA IF NOT EXISTS auth;

-- Roles
CREATE TABLE IF NOT EXISTS auth.roles (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(50) NOT NULL UNIQUE,  -- DOCTOR, ADMIN, PATIENT
    description VARCHAR(255),
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- Users
CREATE TABLE IF NOT EXISTS auth.users (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    email        VARCHAR(255) NOT NULL UNIQUE,
    password     VARCHAR(255) NOT NULL,  -- BCrypt only
    first_name   VARCHAR(100) NOT NULL,
    last_name    VARCHAR(100) NOT NULL,
    role_id      UUID         NOT NULL REFERENCES auth.roles(id),
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    is_verified  BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMP    NOT NULL DEFAULT NOW(),
    deleted_at   TIMESTAMP                           -- Soft delete
);

CREATE INDEX idx_users_email    ON auth.users(email);
CREATE INDEX idx_users_role_id  ON auth.users(role_id);
CREATE INDEX idx_users_active   ON auth.users(is_active) WHERE deleted_at IS NULL;

-- Permissions
CREATE TABLE IF NOT EXISTS auth.permissions (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(100) NOT NULL UNIQUE,  -- e.g. PATIENT_READ, REPORT_WRITE
    description VARCHAR(255),
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- Role-Permission mapping
CREATE TABLE IF NOT EXISTS auth.role_permissions (
    role_id       UUID NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES auth.permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- Refresh Tokens
CREATE TABLE IF NOT EXISTS auth.refresh_tokens (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID         NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token       TEXT         NOT NULL UNIQUE,
    expires_at  TIMESTAMP    NOT NULL,
    revoked     BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user_id ON auth.refresh_tokens(user_id);

-- Seed: default roles
INSERT INTO auth.roles (name, description) VALUES
    ('ADMIN',   'Platform administrator'),
    ('DOCTOR',  'Medical professional — uploads CT scans and reviews diagnoses'),
    ('PATIENT', 'Optional patient access for viewing their own reports')
ON CONFLICT (name) DO NOTHING;
