#!/usr/bin/env python3
"""Database integration layer for Repo Studios reporting suite.

DB_INTEGRATION_MARKER: This module provides dormant database connectivity
for parallel writes (file + DB) during the migration from standalone Repo Studios
to integration with the main orchestration layer.

Architecture Context:
- Main repo (air-gapped): Hosts the shared database
- Main repo agents: Request reports from Repo Studios
- Repo Studios agents: Fulfill requests, write to DB + files
- Transition phase: Dual-write until file outputs are phased out

Configuration:
    DB connection is controlled via:
    - Environment variable: REPO_STUDIOS_DB_URL
    - Config file: .repo_studios/db_config.json
    - Explicit enable_db=True in storage constructors

Schema Version: 1.0
Last Updated: 2025-12-11
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)


# DB_INTEGRATION_MARKER: Configuration schema
@dataclass
class DatabaseConfig:
    """Database connection configuration.
    
    DB_INTEGRATION_MARKER: Wire these fields when integrating with main repo DB.
    """
    host: str = "localhost"
    port: int = 5432
    database: str = "repo_studios"
    user: str = ""
    password: str = ""
    enabled: bool = False
    
    @classmethod
    def from_env(cls) -> DatabaseConfig:
        """Load config from environment variables.
        
        DB_INTEGRATION_MARKER: Main repo will provide REPO_STUDIOS_DB_URL.
        """
        db_url = os.getenv("REPO_STUDIOS_DB_URL", "")
        enabled = bool(db_url) or os.getenv("REPO_STUDIOS_DB_ENABLED", "").lower() == "true"
        
        return cls(enabled=enabled)
    
    @classmethod
    def from_file(cls, config_path: Path) -> DatabaseConfig:
        """Load config from JSON file.
        
        DB_INTEGRATION_MARKER: Air-gapped systems can use local config file.
        """
        if not config_path.exists():
            return cls(enabled=False)
        
        try:
            data = json.loads(config_path.read_text())
            return cls(
                host=data.get("host", "localhost"),
                port=data.get("port", 5432),
                database=data.get("database", "repo_studios"),
                user=data.get("user", ""),
                password=data.get("password", ""),
                enabled=data.get("enabled", False),
            )
        except Exception as e:
            logger.warning(f"Failed to load DB config from {config_path}: {e}")
            return cls(enabled=False)


# DB_INTEGRATION_MARKER: Storage protocol for polymorphic file/DB operations
class ReportStorage(Protocol):
    """Protocol for report persistence - file-based or database-backed."""
    
    def write_manifest(self, data: dict[str, Any]) -> None:
        """Write manifest.json equivalent."""
        ...
    
    def write_summary(self, data: dict[str, Any], format: str = "json") -> None:
        """Write summary artifact (JSON or Markdown)."""
        ...
    
    def write_telemetry(self, data: dict[str, Any]) -> None:
        """Write telemetry.json equivalent."""
        ...
    
    def write_matrix(self, data: dict[str, Any]) -> None:
        """Write matrix.json equivalent (duplicates, coverage, etc.)."""
        ...
    
    def write_metrics(self, data: dict[str, Any]) -> None:
        """Write metrics.json equivalent."""
        ...


# DB_INTEGRATION_MARKER: File-based storage (current implementation)
class FileSystemStorage:
    """Current file-based storage implementation.
    
    Writes timestamped artifacts to disk per REPORT_NAMING_STANDARDS.md.
    """
    
    def __init__(self, output_dir: Path, viewer_slug: str, topic: str, timestamp: str):
        self.output_dir = output_dir
        self.viewer_slug = viewer_slug
        self.topic = topic
        self.timestamp = timestamp
        self.bundle_dir = output_dir / viewer_slug / topic / timestamp
        self.bundle_dir.mkdir(parents=True, exist_ok=True)
    
    def write_manifest(self, data: dict[str, Any]) -> None:
        """Write manifest.json to bundle directory."""
        manifest_path = self.bundle_dir / "manifest.json"
        manifest_path.write_text(json.dumps(data, indent=2))
        logger.debug(f"Wrote manifest to {manifest_path}")
    
    def write_summary(self, data: dict[str, Any], format: str = "json") -> None:
        """Write summary artifact."""
        if format == "json":
            summary_path = self.bundle_dir / "summary.json"
            summary_path.write_text(json.dumps(data, indent=2))
        else:
            summary_path = self.bundle_dir / "summary.md"
            summary_path.write_text(data.get("markdown", ""))
        logger.debug(f"Wrote summary to {summary_path}")
    
    def write_telemetry(self, data: dict[str, Any]) -> None:
        """Write telemetry.json."""
        telemetry_path = self.bundle_dir / "telemetry.json"
        telemetry_path.write_text(json.dumps(data, indent=2))
        logger.debug(f"Wrote telemetry to {telemetry_path}")
    
    def write_matrix(self, data: dict[str, Any]) -> None:
        """Write matrix.json."""
        matrix_path = self.bundle_dir / "matrix.json"
        matrix_path.write_text(json.dumps(data, indent=2))
        logger.debug(f"Wrote matrix to {matrix_path}")
    
    def write_metrics(self, data: dict[str, Any]) -> None:
        """Write metrics.json."""
        metrics_path = self.bundle_dir / "metrics.json"
        metrics_path.write_text(json.dumps(data, indent=2))
        logger.debug(f"Wrote metrics to {metrics_path}")


# DB_INTEGRATION_MARKER: Database storage (dormant until configured)
class DatabaseStorage:
    """Database-backed storage for integration with main repo orchestration layer.
    
    DB_INTEGRATION_MARKER: This class contains stub implementations that will be
    wired when Repo Studios integrates with the main repo's database.
    
    Current State: No-op when db_config.enabled=False
    Future State: Parallel writes to PostgreSQL alongside file outputs
    Phase-out: File outputs removed once agents are trained and trustworthy
    
    Schema Notes:
    - See individual write_* methods for table/column mapping
    - Each method documents its INSERT/UPDATE strategy
    - Timestamps use UTC (timestamptz in PostgreSQL)
    - JSON fields use JSONB for indexing
    """
    
    def __init__(self, db_config: DatabaseConfig | None = None):
        self.db_config = db_config or DatabaseConfig(enabled=False)
        self._enabled = self.db_config.enabled
        
        if self._enabled:
            logger.info("DB_INTEGRATION_MARKER: Database writes ENABLED")
            # DB_INTEGRATION_MARKER: Connection pool initialization here
            self._connection = None  # Placeholder for DB connection
        else:
            logger.debug("DB_INTEGRATION_MARKER: Database writes DORMANT")
    
    def write_manifest(self, data: dict[str, Any]) -> None:
        """Write manifest data to report_runs table.
        
        DB_INTEGRATION_MARKER: Target schema
        ────────────────────────────────────
        INSERT INTO report_runs (
            viewer_slug,
            topic,
            run_timestamp,
            git_sha,
            repo_root,
            status,
            generated_at,
            inputs,        -- JSONB: data['inputs']
            catalog        -- JSONB: data['catalog']
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        
        Store returned id for foreign key relationships in subsequent writes.
        """
        if not self._enabled:
            return
        
        # DB_INTEGRATION_MARKER: Actual INSERT logic here
        logger.debug(f"DB_INTEGRATION_MARKER: Would write manifest for {data.get('topic', 'unknown')}")
    
    def write_summary(self, data: dict[str, Any], format: str = "json") -> None:
        """Write summary artifact to report_artifacts table.
        
        DB_INTEGRATION_MARKER: Target schema
        ────────────────────────────────────
        INSERT INTO report_artifacts (
            run_id,              -- FK from write_manifest
            artifact_role,       -- 'summary'
            artifact_type,       -- 'json' or 'md'
            file_path,           -- Optional file system path
            content_json,        -- JSONB for JSON summaries
            content_text,        -- TEXT for Markdown summaries
            checksum
        ) VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        if not self._enabled:
            return
        
        # DB_INTEGRATION_MARKER: Actual INSERT logic here
        artifact_role = "summary"
        artifact_type = format
        logger.debug(f"DB_INTEGRATION_MARKER: Would write {artifact_type} summary")
    
    def write_telemetry(self, data: dict[str, Any]) -> None:
        """Write telemetry to both report_artifacts and test_metrics tables.
        
        DB_INTEGRATION_MARKER: Target schemas
        ────────────────────────────────────
        1. Full telemetry in report_artifacts:
           INSERT INTO report_artifacts (run_id, artifact_role, content_json)
           VALUES (%s, 'telemetry', %s);
        
        2. Extracted metrics in test_metrics:
           INSERT INTO test_metrics (
               run_id,
               metric_timestamp,
               coverage_pct,
               total_tests,
               passed_tests,
               failed_tests,
               slow_tests_count,
               total_functions,
               duplicate_function_count,
               hardening_issues,   -- JSONB
               churn_stats         -- JSONB
           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        
        Extract metrics from data structure:
        - data['metrics']['coverage_status'] → coverage_pct
        - data['components']['coverage']['summary'] → test counts
        - data['components']['hardening']['payload'] → hardening_issues
        """
        if not self._enabled:
            return
        
        # DB_INTEGRATION_MARKER: Actual INSERT logic here
        logger.debug("DB_INTEGRATION_MARKER: Would write telemetry + extracted metrics")
    
    def write_matrix(self, data: dict[str, Any]) -> None:
        """Write matrix data (duplicates, coverage) to specialized tables.
        
        DB_INTEGRATION_MARKER: Target schema
        ────────────────────────────────────
        For duplicate matrices:
        INSERT INTO duplicate_groups (
            run_id,
            group_identifier,
            duplicate_count,
            instances          -- JSONB array of locations
        ) VALUES (%s, %s, %s, %s);
        
        For each function in matrix:
        INSERT INTO functions (
            run_id,
            module_id,
            function_name,
            relative_path,
            line_number,
            line_count,
            signature,
            complexity_score,
            git_churn,         -- JSONB
            code_smells,       -- JSONB
            call_graph         -- JSONB
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        
        Also store full matrix in report_artifacts as backup.
        """
        if not self._enabled:
            return
        
        # DB_INTEGRATION_MARKER: Actual INSERT logic here
        logger.debug("DB_INTEGRATION_MARKER: Would write matrix data + function inventory")
    
    def write_metrics(self, data: dict[str, Any]) -> None:
        """Write aggregated metrics to report_artifacts.
        
        DB_INTEGRATION_MARKER: Target schema
        ────────────────────────────────────
        INSERT INTO report_artifacts (
            run_id,
            artifact_role,       -- 'metrics'
            artifact_type,       -- 'json'
            content_json         -- Full metrics payload
        ) VALUES (%s, 'metrics', 'json', %s);
        
        For time-series metrics, also populate test_metrics table
        (see write_telemetry for schema).
        """
        if not self._enabled:
            return
        
        # DB_INTEGRATION_MARKER: Actual INSERT logic here
        logger.debug("DB_INTEGRATION_MARKER: Would write aggregated metrics")


# DB_INTEGRATION_MARKER: Dual-write orchestrator
class DualWriteStorage:
    """Orchestrates parallel writes to file system AND database.
    
    DB_INTEGRATION_MARKER: Use this class in all scripts during transition phase.
    
    Guarantees:
    - File writes always succeed (primary output during transition)
    - DB writes attempted when enabled, failures logged but don't abort
    - Markers in logs for post-migration validation
    """
    
    def __init__(
        self,
        output_dir: Path,
        viewer_slug: str,
        topic: str,
        timestamp: str,
        db_config: DatabaseConfig | None = None,
    ):
        self.file_storage = FileSystemStorage(output_dir, viewer_slug, topic, timestamp)
        self.db_storage = DatabaseStorage(db_config)
        self._db_enabled = self.db_storage._enabled
    
    def write_manifest(self, data: dict[str, Any]) -> None:
        """Dual-write manifest."""
        self.file_storage.write_manifest(data)
        try:
            self.db_storage.write_manifest(data)
        except Exception as e:
            logger.warning(f"DB_INTEGRATION_MARKER: DB write failed (manifest): {e}")
    
    def write_summary(self, data: dict[str, Any], format: str = "json") -> None:
        """Dual-write summary."""
        self.file_storage.write_summary(data, format)
        try:
            self.db_storage.write_summary(data, format)
        except Exception as e:
            logger.warning(f"DB_INTEGRATION_MARKER: DB write failed (summary): {e}")
    
    def write_telemetry(self, data: dict[str, Any]) -> None:
        """Dual-write telemetry."""
        self.file_storage.write_telemetry(data)
        try:
            self.db_storage.write_telemetry(data)
        except Exception as e:
            logger.warning(f"DB_INTEGRATION_MARKER: DB write failed (telemetry): {e}")
    
    def write_matrix(self, data: dict[str, Any]) -> None:
        """Dual-write matrix."""
        self.file_storage.write_matrix(data)
        try:
            self.db_storage.write_matrix(data)
        except Exception as e:
            logger.warning(f"DB_INTEGRATION_MARKER: DB write failed (matrix): {e}")
    
    def write_metrics(self, data: dict[str, Any]) -> None:
        """Dual-write metrics."""
        self.file_storage.write_metrics(data)
        try:
            self.db_storage.write_metrics(data)
        except Exception as e:
            logger.warning(f"DB_INTEGRATION_MARKER: DB write failed (metrics): {e}")


# DB_INTEGRATION_MARKER: Factory for easy script integration
def create_storage(
    output_dir: Path,
    viewer_slug: str,
    topic: str,
    timestamp: str | None = None,
    enable_db: bool | None = None,
) -> DualWriteStorage:
    """Create storage instance with automatic DB config detection.
    
    DB_INTEGRATION_MARKER: Scripts should call this to get storage instance.
    
    Args:
        output_dir: Base reports directory (e.g., .repo_studios/command_center/reports)
        viewer_slug: Viewer name (healthview, commandview, etc.)
        topic: Report topic (test_execution_telemetry, duplicate_scan, etc.)
        timestamp: Optional explicit timestamp (defaults to current UTC)
        enable_db: Override DB enable flag (None = auto-detect from config)
    
    Returns:
        DualWriteStorage instance ready for parallel writes
    
    Example:
        storage = create_storage(
            Path(".repo_studios/command_center/reports"),
            "healthview",
            "test_execution_telemetry",
        )
        storage.write_manifest(manifest_data)
        storage.write_telemetry(telemetry_data)
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    
    # DB_INTEGRATION_MARKER: Try config file first, then env vars
    config_path = Path(".repo_studios/db_config.json")
    if config_path.exists():
        db_config = DatabaseConfig.from_file(config_path)
    else:
        db_config = DatabaseConfig.from_env()
    
    # Override enable flag if explicitly provided
    if enable_db is not None:
        db_config.enabled = enable_db
    
    return DualWriteStorage(output_dir, viewer_slug, topic, timestamp, db_config)
