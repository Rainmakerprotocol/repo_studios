-- Repo Studios Database Schema
-- Version: 1.0
-- Last Updated: 2025-12-11
-- Target: PostgreSQL 14+ with JSONB and full-text search extensions
--
-- DB_INTEGRATION_MARKER: This schema will be deployed in the main repo's
-- air-gapped environment. Repo Studios scripts write to these tables.

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;    -- Trigram matching for fuzzy search
CREATE EXTENSION IF NOT EXISTS btree_gin;  -- Additional JSONB indexing

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Main report runs table (orchestrator level)
CREATE TABLE IF NOT EXISTS report_runs (
    id BIGSERIAL PRIMARY KEY,
    viewer_slug VARCHAR(50) NOT NULL,        -- Position 1: healthview, commandview, rawview, jarvis, vscode
    topic VARCHAR(100) NOT NULL,             -- Position 2: test_execution_telemetry, duplicate_scan, etc.
    run_timestamp TIMESTAMPTZ NOT NULL,      -- Position 3: From folder name YYYYMMDD-HHMM
    git_sha VARCHAR(40),                     -- Current git commit hash
    repo_root TEXT,                          -- Absolute repo path
    status VARCHAR(20),                      -- 'ok', 'warning', 'error'
    generated_at TIMESTAMPTZ DEFAULT NOW(),  -- Insert timestamp
    
    -- Provenance metadata (NOT in filesystem path)
    requested_by VARCHAR(255),               -- Agent name or 'scheduled' or 'manual'
    trigger_type VARCHAR(50),                -- 'investigation', 'routine', 'ci_triggered', 'git_hook'
    request_id VARCHAR(100),                 -- Optional correlation ID for agent request tracking
    
    -- Flexible metadata
    inputs JSONB,                            -- Script inputs and configuration
    catalog JSONB,                           -- Pipeline script manifest
    
    CONSTRAINT uniq_run UNIQUE(viewer_slug, topic, run_timestamp)
);

CREATE INDEX idx_runs_viewer_topic ON report_runs(viewer_slug, topic);
CREATE INDEX idx_runs_timestamp ON report_runs(run_timestamp DESC);
CREATE INDEX idx_runs_git_sha ON report_runs(git_sha) WHERE git_sha IS NOT NULL;
CREATE INDEX idx_runs_status ON report_runs(status);
CREATE INDEX idx_runs_inputs ON report_runs USING GIN(inputs);
CREATE INDEX idx_runs_requested_by ON report_runs(requested_by) WHERE requested_by IS NOT NULL;
CREATE INDEX idx_runs_trigger_type ON report_runs(trigger_type) WHERE trigger_type IS NOT NULL;

COMMENT ON TABLE report_runs IS 'Main orchestrator run records with positional path encoding';
COMMENT ON COLUMN report_runs.viewer_slug IS 'Position 1: Target viewer per REPORT_NAMING_STANDARDS.md';
COMMENT ON COLUMN report_runs.topic IS 'Position 2: Report topic/scope slug';
COMMENT ON COLUMN report_runs.run_timestamp IS 'Position 3: UTC timestamp from report folder (YYYYMMDD-HHMM)';
COMMENT ON COLUMN report_runs.requested_by IS 'Agent ID, "scheduled", or "manual" - tracks WHO requested';
COMMENT ON COLUMN report_runs.trigger_type IS 'WHY it ran: investigation, routine, ci_triggered, git_hook';
COMMENT ON COLUMN report_runs.catalog IS 'Array of {role, script_path, topic} for pipeline scripts';

-- ============================================================================
-- ARTIFACT STORAGE
-- ============================================================================

-- Generic artifact storage (manifests, summaries, reports)
CREATE TABLE IF NOT EXISTS report_artifacts (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES report_runs(id) ON DELETE CASCADE,
    artifact_role VARCHAR(50) NOT NULL,      -- manifest, summary, matrix, telemetry, report, metrics
    artifact_type VARCHAR(10) NOT NULL,      -- json, md, csv, tsv
    file_path TEXT,                          -- Original file system path (optional)
    file_size_bytes BIGINT,
    content_json JSONB,                      -- For JSON files
    content_text TEXT,                       -- For Markdown/text files
    checksum VARCHAR(64),                    -- SHA256 for deduplication
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_artifacts_run ON report_artifacts(run_id);
CREATE INDEX idx_artifacts_role ON report_artifacts(artifact_role);
CREATE INDEX idx_artifacts_type ON report_artifacts(artifact_type);
CREATE INDEX idx_artifacts_content ON report_artifacts USING GIN(content_json);
CREATE INDEX idx_artifacts_fts ON report_artifacts USING GIN(to_tsvector('english', content_text));

COMMENT ON TABLE report_artifacts IS 'Full report artifacts with file and JSONB storage';
COMMENT ON COLUMN report_artifacts.artifact_role IS 'Role per REPORT_NAMING_STANDARDS.md artifact registry';
COMMENT ON COLUMN report_artifacts.content_json IS 'Full JSON payload with GIN indexing for queries';
COMMENT ON COLUMN report_artifacts.content_text IS 'Markdown or plain text content with FTS indexing';

-- ============================================================================
-- TIME-SERIES METRICS
-- ============================================================================

-- Extracted test execution metrics for time-series queries
CREATE TABLE IF NOT EXISTS test_metrics (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES report_runs(id) ON DELETE CASCADE,
    metric_timestamp TIMESTAMPTZ NOT NULL,
    
    -- Coverage metrics
    coverage_pct DECIMAL(5,2),
    covered_functions INTEGER,
    total_functions INTEGER,
    total_files INTEGER,
    files_below_threshold INTEGER,
    
    -- Test execution metrics
    total_tests INTEGER,
    passed_tests INTEGER,
    failed_tests INTEGER,
    slow_tests_count INTEGER,
    warnings_total INTEGER,
    
    -- Code quality metrics
    duplicate_function_count INTEGER,
    high_complexity_count INTEGER,
    high_churn_files INTEGER,
    
    -- Detailed metrics (JSONB for flexible queries)
    hardening_issues JSONB,              -- Test hardening analysis results
    churn_stats JSONB,                   -- Churn-complexity heatmap data
    coverage_details JSONB,              -- Files below threshold, status
    
    CONSTRAINT uniq_metric UNIQUE(run_id)  -- One metric record per run
);

CREATE INDEX idx_metrics_timestamp ON test_metrics(metric_timestamp DESC);
CREATE INDEX idx_metrics_run ON test_metrics(run_id);
CREATE INDEX idx_metrics_coverage ON test_metrics(coverage_pct) WHERE coverage_pct IS NOT NULL;
CREATE INDEX idx_metrics_failures ON test_metrics(failed_tests) WHERE failed_tests > 0;
CREATE INDEX idx_metrics_hardening ON test_metrics USING GIN(hardening_issues);
CREATE INDEX idx_metrics_churn ON test_metrics USING GIN(churn_stats);

COMMENT ON TABLE test_metrics IS 'Extracted time-series metrics for agent queries';
COMMENT ON COLUMN test_metrics.hardening_issues IS 'Full test hardening payload (JSONB)';
COMMENT ON COLUMN test_metrics.churn_stats IS 'Churn-complexity heatmap data (JSONB)';

-- ============================================================================
-- FUNCTION INVENTORY
-- ============================================================================

-- Function-level inventory from CommandView (for duplicate tracking)
CREATE TABLE IF NOT EXISTS functions (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES report_runs(id) ON DELETE CASCADE,
    
    -- Location
    module_id VARCHAR(255) NOT NULL,         -- Dotted module path
    function_name VARCHAR(255) NOT NULL,     -- Function/method name
    relative_path TEXT NOT NULL,             -- Relative file path
    line_number INTEGER NOT NULL,
    line_count INTEGER,
    
    -- Function metadata
    signature TEXT,                          -- Full function signature
    complexity_score INTEGER,                -- Cyclomatic complexity
    is_test BOOLEAN DEFAULT FALSE,
    is_abstract BOOLEAN DEFAULT FALSE,
    
    -- Rich metadata (JSONB)
    git_churn JSONB,                         -- {commit_count, additions, deletions, ...}
    code_smells JSONB,                       -- {long_function, high_branch_count, ...}
    call_graph JSONB,                        -- {edges: [...], summary: {...}}
    dependency_summary JSONB,                -- {internal, third_party, standard_library}
    
    CONSTRAINT uniq_function UNIQUE(run_id, module_id, function_name, line_number)
);

CREATE INDEX idx_functions_run ON functions(run_id);
CREATE INDEX idx_functions_name ON functions(function_name);
CREATE INDEX idx_functions_module ON functions(module_id);
CREATE INDEX idx_functions_path ON functions(relative_path);
CREATE INDEX idx_functions_complexity ON functions(complexity_score) WHERE complexity_score IS NOT NULL;
CREATE INDEX idx_functions_test ON functions(is_test);
CREATE INDEX idx_functions_churn ON functions USING GIN(git_churn);
CREATE INDEX idx_functions_smells ON functions USING GIN(code_smells);

COMMENT ON TABLE functions IS 'Function-level inventory from CommandView with git churn and complexity';
COMMENT ON COLUMN functions.module_id IS 'Dotted Python module path (e.g., scripts.producers.generate_commandview_inventory)';
COMMENT ON COLUMN functions.git_churn IS 'Git churn stats: {commit_count, additions, deletions, net_changes, latest_commit}';

-- ============================================================================
-- DUPLICATE GROUPS
-- ============================================================================

-- Duplicate function groups from duplicate scan reports
CREATE TABLE IF NOT EXISTS duplicate_groups (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES report_runs(id) ON DELETE CASCADE,
    group_identifier VARCHAR(255) NOT NULL,  -- Unique duplicate group ID
    duplicate_count INTEGER NOT NULL,        -- Number of instances
    instances JSONB NOT NULL,                -- Array of {path, line, name, line_count}
    
    CONSTRAINT uniq_duplicate_group UNIQUE(run_id, group_identifier)
);

CREATE INDEX idx_duplicates_run ON duplicate_groups(run_id);
CREATE INDEX idx_duplicates_count ON duplicate_groups(duplicate_count) WHERE duplicate_count > 2;
CREATE INDEX idx_duplicates_instances ON duplicate_groups USING GIN(instances);

COMMENT ON TABLE duplicate_groups IS 'Duplicate function groups from scan_duplicates.py';
COMMENT ON COLUMN duplicate_groups.group_identifier IS 'Stable ID like duplicate-def-configure-logging-level--str-----none';
COMMENT ON COLUMN duplicate_groups.instances IS 'Array of duplicate locations with path, line, name, line_count';

-- ============================================================================
-- MATERIALIZED VIEWS FOR AGENT QUERIES
-- ============================================================================

-- Test coverage trends (daily rollup)
CREATE MATERIALIZED VIEW IF NOT EXISTS test_coverage_trends AS
SELECT 
    DATE_TRUNC('day', metric_timestamp) as date,
    viewer_slug,
    topic,
    AVG(coverage_pct) as avg_coverage,
    MIN(coverage_pct) as min_coverage,
    MAX(coverage_pct) as max_coverage,
    AVG(failed_tests) as avg_failures,
    COUNT(*) as run_count
FROM test_metrics tm
JOIN report_runs rr ON tm.run_id = rr.id
WHERE metric_timestamp > NOW() - INTERVAL '90 days'
GROUP BY 1, 2, 3;

CREATE UNIQUE INDEX idx_coverage_trends_date ON test_coverage_trends(date, viewer_slug, topic);

COMMENT ON MATERIALIZED VIEW test_coverage_trends IS 'Daily test coverage rollups for fast trend queries';

-- Top duplicate functions (across all runs)
CREATE MATERIALIZED VIEW IF NOT EXISTS top_duplicates AS
SELECT 
    dg.group_identifier,
    MAX(dg.duplicate_count) as max_count,
    COUNT(DISTINCT dg.run_id) as run_occurrences,
    MAX(rr.run_timestamp) as last_seen,
    (dg.instances->0->>'name')::text as function_name  -- Extract first instance name
FROM duplicate_groups dg
JOIN report_runs rr ON dg.run_id = rr.id
WHERE dg.duplicate_count >= 3
GROUP BY dg.group_identifier, dg.instances->0->>'name';

CREATE UNIQUE INDEX idx_top_duplicates_id ON top_duplicates(group_identifier);
CREATE INDEX idx_top_duplicates_count ON top_duplicates(max_count DESC);

COMMENT ON MATERIALIZED VIEW top_duplicates IS 'Most frequently duplicated functions across all runs';

-- High-risk files (complexity + churn)
CREATE MATERIALIZED VIEW IF NOT EXISTS high_risk_files AS
SELECT 
    f.relative_path,
    AVG(f.complexity_score) as avg_complexity,
    AVG((f.git_churn->>'commit_count')::int) as avg_churn,
    COUNT(*) as function_count,
    MAX(rr.run_timestamp) as last_analyzed
FROM functions f
JOIN report_runs rr ON f.run_id = rr.id
WHERE f.complexity_score > 10
  AND (f.git_churn->>'commit_count')::int > 5
GROUP BY f.relative_path;

CREATE UNIQUE INDEX idx_high_risk_path ON high_risk_files(relative_path);

COMMENT ON MATERIALIZED VIEW high_risk_files IS 'Files with high complexity and high churn (refactor candidates)';

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Function to refresh all materialized views (call from cron/agent)
CREATE OR REPLACE FUNCTION refresh_all_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY test_coverage_trends;
    REFRESH MATERIALIZED VIEW CONCURRENTLY top_duplicates;
    REFRESH MATERIALIZED VIEW CONCURRENTLY high_risk_files;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_all_views IS 'Refresh all materialized views concurrently (call after new reports)';

-- ============================================================================
-- SAMPLE QUERIES FOR AI AGENTS
-- ============================================================================

-- Query 1: Test coverage trend over last 30 days
PREPARE test_coverage_trend AS
SELECT date, avg_coverage, avg_failures
FROM test_coverage_trends
WHERE date > NOW() - INTERVAL '30 days'
  AND topic = 'test_execution_telemetry'
ORDER BY date;

-- Query 2: Find runs where coverage dropped below threshold
PREPARE coverage_regressions AS
SELECT rr.run_timestamp, rr.git_sha, tm.coverage_pct, tm.files_below_threshold
FROM report_runs rr
JOIN test_metrics tm ON rr.id = tm.run_id
WHERE tm.coverage_pct < $1
  AND rr.topic = 'test_execution_telemetry'
ORDER BY rr.run_timestamp DESC;

-- Query 3: Top duplicate functions that appear most often
PREPARE top_duplicate_functions AS
SELECT function_name, max_count, run_occurrences, last_seen
FROM top_duplicates
ORDER BY max_count DESC, run_occurrences DESC
LIMIT 20;

-- Query 4: Files with both high complexity and high churn
PREPARE high_risk_file_candidates AS
SELECT relative_path, avg_complexity, avg_churn, function_count
FROM high_risk_files
ORDER BY (avg_complexity * avg_churn) DESC
LIMIT 50;

-- Query 5: Recent test failures with full context
PREPARE recent_test_failures AS
SELECT 
    rr.run_timestamp,
    rr.viewer_slug,
    rr.topic,
    rr.git_sha,
    tm.failed_tests,
    tm.total_tests,
    ra.content_json->'failures'->'examples' as failure_examples
FROM report_runs rr
JOIN test_metrics tm ON rr.id = tm.run_id
LEFT JOIN report_artifacts ra ON rr.id = ra.run_id AND ra.artifact_role = 'summary'
WHERE tm.failed_tests > 0
ORDER BY rr.run_timestamp DESC
LIMIT 10;

-- ============================================================================
-- DB_INTEGRATION_MARKER: Deployment Notes
-- ============================================================================
-- 
-- This schema should be deployed to the main repo's PostgreSQL instance.
-- 
-- Setup checklist:
-- 1. Create database: CREATE DATABASE repo_studios;
-- 2. Create user: CREATE USER repo_agent WITH PASSWORD 'secure_password';
-- 3. Grant permissions: GRANT ALL ON DATABASE repo_studios TO repo_agent;
-- 4. Run this schema file: psql -U postgres -d repo_studios -f schema.sql
-- 5. Set up connection in .repo_studios/db_config.json
-- 6. Test with REPO_STUDIOS_DB_ENABLED=true
-- 
-- For TimescaleDB time-series optimization (optional):
-- 1. Install TimescaleDB extension
-- 2. Convert test_metrics to hypertable: SELECT create_hypertable('test_metrics', 'metric_timestamp');
-- 3. Add compression policy for old data
-- 
-- For pgvector semantic search (future):
-- 1. Install pgvector extension
-- 2. Add embedding column to report_artifacts
-- 3. Create IVF or HNSW index on embeddings
-- ============================================================================
