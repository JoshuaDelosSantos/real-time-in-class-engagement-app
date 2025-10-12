-- 0001_sessions.sql
--
-- Establish the core schema for ClassEngage, covering users, sessions,
-- session participants, questions, and question votes. The design mirrors
-- docs/data-model.md and uses host terminology (formerly moderator).

-- Users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    display_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Sessions
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    host_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'ended')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ NULL,
    ended_at TIMESTAMPTZ NULL
);

-- Session Participants
CREATE TABLE IF NOT EXISTS session_participants (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('host', 'participant')),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (session_id, user_id)
);

-- Questions
CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    author_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'answered')),
    likes INTEGER NOT NULL DEFAULT 0 CHECK (likes >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    answered_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS questions_session_status_idx
    ON questions (session_id, status);

CREATE INDEX IF NOT EXISTS questions_session_likes_idx
    ON questions (session_id, likes DESC);

-- Question Votes
CREATE TABLE IF NOT EXISTS question_votes (
    id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    voter_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (question_id, voter_user_id)
);
