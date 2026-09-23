-- Migration 001: Create all tables for the Image Matching Engine
-- Run with: psql -U postgres -d image_matching -f migrations/001_create_tables.sql

-- Images table — stores uploaded images and their AI-extracted metadata
CREATE TABLE IF NOT EXISTS images (
    id          SERIAL PRIMARY KEY,
    filename    TEXT NOT NULL,
    path        TEXT NOT NULL,
    subject     TEXT,
    category    TEXT,
    attributes  TEXT[],
    caption     TEXT,
    confidence  FLOAT,
    embedding   TEXT,
    status      TEXT NOT NULL DEFAULT 'pending',
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Posts table — blog posts that need matching images
CREATE TABLE IF NOT EXISTS posts (
    id          SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    embedding   TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Suggestions table — proposed image-post matches with guard results
CREATE TABLE IF NOT EXISTS suggestions (
    id              SERIAL PRIMARY KEY,
    post_id         INTEGER NOT NULL REFERENCES posts(id),
    image_id        INTEGER NOT NULL REFERENCES images(id),
    similarity      FLOAT NOT NULL,
    guard_status    TEXT NOT NULL DEFAULT 'pending',
    reason          TEXT,
    review_status   TEXT NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Jobs table — tracks batch processing jobs
CREATE TABLE IF NOT EXISTS jobs (
    id          SERIAL PRIMARY KEY,
    status      TEXT NOT NULL DEFAULT 'pending',
    total       INTEGER NOT NULL DEFAULT 0,
    processed   INTEGER NOT NULL DEFAULT 0,
    failed      INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- AI call logs — tracks every AI model invocation for cost awareness
CREATE TABLE IF NOT EXISTS ai_call_logs (
    id              SERIAL PRIMARY KEY,
    operation       TEXT NOT NULL,
    model           TEXT NOT NULL,
    duration_ms     INTEGER,
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    estimated_cost  FLOAT NOT NULL DEFAULT 0.0,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);
