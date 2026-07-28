-- ═══════════════════════════════════════════════════════════════
-- V1__init_auth_schema.sql
-- Flyway Migration — Authentication Service
-- Schema: auth
-- Rules: UUID PKs, audit columns, soft deletes, BCrypt passwords
-- ═══════════════════════════════════════════════════════════════

CREATE SCHEMA IF NOT EXISTS auth;

-- ───────────────────────────────────────────────────────────────
-- ROLES
-- ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS auth.roles (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    name        VARCHAR(50)  NOT NULL,
    description VARCHAR(255),
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    created_by  UUID,
    updated_by  UUID,
    is_deleted  BOOLEAN      NOT NULL DEFAULT FALSE,
    version     INTEGER      NOT NULL DEFAULT 0,
    CONSTRAINT pk_roles PRIMARY KEY (id),
    CONSTRAINT uq_roles_name UNIQUE (name)
);

-- ───────────────────────────────────────────────────────────────
-- PERMISSIONS
-- ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS auth.permissions (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    created_by  UUID,
    updated_by  UUID,
    is_deleted  BOOLEAN      NOT NULL DEFAULT FALSE,
    version     INTEGER      NOT NULL DEFAULT 0,
    CONSTRAINT pk_permissions PRIMARY KEY (id),
    CONSTRAINT uq_permissions_code UNIQUE (code)
);

-- ───────────────────────────────────────────────────────────────
-- ROLE_PERMISSIONS (Many-to-Many)
-- ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS auth.role_permissions (
    role_id       UUID NOT NULL,
    permission_id UUID NOT NULL,
    CONSTRAINT pk_role_permissions PRIMARY KEY (role_id, permission_id),
    CONSTRAINT fk_rp_role FOREIGN KEY (role_id) REFERENCES auth.roles(id) ON DELETE CASCADE,
    CONSTRAINT fk_rp_permission FOREIGN KEY (permission_id) REFERENCES auth.permissions(id) ON DELETE CASCADE
);

-- ───────────────────────────────────────────────────────────────
-- USERS
-- ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS auth.users (
    id            UUID         NOT NULL DEFAULT gen_random_uuid(),
    email         VARCHAR(255) NOT NULL,
    username      VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    phone         VARCHAR(20),
    role_id       UUID         NOT NULL,
    status        VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE',
    last_login    TIMESTAMP,
    is_verified   BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMP    NOT NULL DEFAULT NOW(),
    created_by    UUID,
    updated_by    UUID,
    is_deleted    BOOLEAN      NOT NULL DEFAULT FALSE,
    version       INTEGER      NOT NULL DEFAULT 0,
    CONSTRAINT pk_users PRIMARY KEY (id),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES auth.roles(id)
);

CREATE INDEX IF NOT EXISTS idx_users_email    ON auth.users(email)    WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_users_username ON auth.users(username)  WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_users_role_id  ON auth.users(role_id);

-- ───────────────────────────────────────────────────────────────
-- REFRESH TOKENS
-- ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS auth.refresh_tokens (
    id         UUID      NOT NULL DEFAULT gen_random_uuid(),
    user_id    UUID      NOT NULL,
    token      TEXT      NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked    BOOLEAN   NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_refresh_tokens PRIMARY KEY (id),
    CONSTRAINT uq_refresh_tokens_token UNIQUE (token),
    CONSTRAINT fk_rt_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON auth.refresh_tokens(user_id);

-- ───────────────────────────────────────────────────────────────
-- SEED: Default Roles
-- ───────────────────────────────────────────────────────────────
INSERT INTO auth.roles (name, description) VALUES
    ('ADMIN',   'Platform administrator — full access'),
    ('DOCTOR',  'Medical professional — uploads CT scans and reviews diagnoses'),
    ('PATIENT', 'Optional patient access — view own reports and profile')
ON CONFLICT (name) DO NOTHING;

-- ───────────────────────────────────────────────────────────────
-- SEED: Default Permissions
-- ───────────────────────────────────────────────────────────────
INSERT INTO auth.permissions (code, description) VALUES
    ('USER_READ',      'Read user accounts'),
    ('USER_WRITE',     'Create and update users'),
    ('USER_DELETE',    'Delete users'),
    ('PATIENT_READ',   'Read patient records'),
    ('PATIENT_WRITE',  'Create and update patient records'),
    ('PATIENT_DELETE', 'Delete patient records'),
    ('IMAGE_READ',     'View CT scan images'),
    ('IMAGE_WRITE',    'Upload CT scan images'),
    ('IMAGE_DELETE',   'Delete CT scan images'),
    ('DIAGNOSIS_READ', 'View diagnosis results'),
    ('DIAGNOSIS_RUN',  'Trigger AI diagnosis'),
    ('REPORT_READ',    'View clinical reports'),
    ('REPORT_WRITE',   'Generate clinical reports'),
    ('ADMIN_ACCESS',   'Administrative actions')
ON CONFLICT (code) DO NOTHING;

-- ───────────────────────────────────────────────────────────────
-- SEED: Role-Permission assignments
-- ───────────────────────────────────────────────────────────────
-- ADMIN gets all permissions
INSERT INTO auth.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM auth.roles r, auth.permissions p
WHERE r.name = 'ADMIN'
ON CONFLICT DO NOTHING;

-- DOCTOR permissions
INSERT INTO auth.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM auth.roles r, auth.permissions p
WHERE r.name = 'DOCTOR' AND p.code IN (
    'PATIENT_READ','PATIENT_WRITE','IMAGE_READ','IMAGE_WRITE',
    'DIAGNOSIS_READ','DIAGNOSIS_RUN','REPORT_READ','REPORT_WRITE'
)
ON CONFLICT DO NOTHING;

-- PATIENT permissions
INSERT INTO auth.role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM auth.roles r, auth.permissions p
WHERE r.name = 'PATIENT' AND p.code IN (
    'PATIENT_READ','REPORT_READ','DIAGNOSIS_READ'
)
ON CONFLICT DO NOTHING;
