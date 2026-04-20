
-- Database initialization script for Simple Login System
-- Creates all required tables with indexes and constraints per the DB schema

-- login_user: Stores user credentials for authentication
-- Table name is strictly mandated by FR-005 and BR-002; must not be renamed
CREATE TABLE IF NOT EXISTS login_user (
    email_id   TEXT        NOT NULL,
    password   TEXT        NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT login_user_pkey PRIMARY KEY (email_id),
    CONSTRAINT login_user_email_format CHECK (email_id ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$')
);

CREATE INDEX IF NOT EXISTS idx_login_user_email_id ON login_user (email_id);

-- user_session: Tracks authenticated sessions created upon successful login
CREATE TABLE IF NOT EXISTS user_session (
    session_id UUID        NOT NULL DEFAULT gen_random_uuid(),
    email_id   TEXT        NOT NULL,
    status     TEXT        NOT NULL DEFAULT 'active'
                           CHECK (status IN ('active', 'expired', 'invalidated')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT user_session_pkey   PRIMARY KEY (session_id),
    CONSTRAINT user_session_email_fk FOREIGN KEY (email_id)
        REFERENCES login_user (email_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_session_session_id  ON user_session (session_id);
CREATE INDEX IF NOT EXISTS idx_user_session_email_id    ON user_session (email_id);
CREATE INDEX IF NOT EXISTS idx_user_session_status      ON user_session (status);
CREATE INDEX IF NOT EXISTS idx_user_session_created_at  ON user_session (created_at);
CREATE INDEX IF NOT EXISTS idx_user_session_expires_at  ON user_session (expires_at);

-- login_attempt: Immutable audit log of every login attempt
CREATE TABLE IF NOT EXISTS login_attempt (
    attempt_id  BIGSERIAL   NOT NULL,
    email_id    TEXT,
    success     BOOLEAN     NOT NULL,
    attempt_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address  TEXT,
    user_agent  TEXT,
    failure_reason TEXT,
    CONSTRAINT login_attempt_pkey    PRIMARY KEY (attempt_id),
    CONSTRAINT login_attempt_email_fk FOREIGN KEY (email_id)
        REFERENCES login_user (email_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_login_attempt_email_id   ON login_attempt (email_id);
CREATE INDEX IF NOT EXISTS idx_login_attempt_attempt_at ON login_attempt (attempt_at);
CREATE INDEX IF NOT EXISTS idx_login_attempt_success    ON login_attempt (success);
CREATE INDEX IF NOT EXISTS idx_login_attempt_email_success_time ON login_attempt (email_id, success, attempt_at DESC);

-- Insert default test user (password is 'password123' hashed with bcrypt)
-- This is for development/testing only - remove or change in production
INSERT INTO login_user (email_id, password)
VALUES ('test@example.com', '$2b$12$rwJ3NAbMTZnnbl/hCl6ZJ.uCT7ba.4HOxwlKvpaY9tw.QSugoS3pG')
ON CONFLICT (email_id) DO UPDATE SET password = EXCLUDED.password;
