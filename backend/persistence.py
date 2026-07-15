"""SQLite-based persistence layer for Meridian AI.

Provides durable storage for incidents, investigations, cost records,
and provenance records. Falls back to in-memory storage when aiosqlite
is not installed.

Usage::

    from backend.persistence import PersistenceManager

    async with PersistenceManager() as pm:
        await pm.record_incident(incident_id="42", ...)
        incident = await pm.get_incident("42")
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("meridian-ai.persistence")

_DB_PATH = Path("data/meridian.db")


# ---------------------------------------------------------------------------
# Domain dataclasses
# ---------------------------------------------------------------------------

@dataclass
class IncidentRecord:
    """Persistent representation of an incident."""

    incident_id: str
    title: str
    severity: str
    status: str
    detected: str
    duration_seconds: int = 0
    root_cause: str = ""
    pattern_id: str = ""
    affected_models: list[str] | None = None
    timeline: list[dict] | None = None
    blast_radius: dict | None = None
    created_at: float = 0.0

    def __post_init__(self) -> None:
        if self.created_at == 0.0:
            self.created_at = time.time()
        if self.affected_models is None:
            self.affected_models = []
        if self.timeline is None:
            self.timeline = []
        if self.blast_radius is None:
            self.blast_radius = {}


@dataclass
class InvestigationRecord:
    """Persistent representation of an investigation."""

    investigation_id: str
    incident_id: str
    mode: str = "replay"
    status: str = "pending"
    start_time: float = 0.0
    end_time: float = 0.0
    worker_steps: list[dict] | None = None
    final_summary: str = ""
    created_at: float = 0.0

    def __post_init__(self) -> None:
        if self.created_at == 0.0:
            self.created_at = time.time()
        if self.worker_steps is None:
            self.worker_steps = []


@dataclass
class CostRecord:
    """Persistent cost tracking record."""

    cost_id: str
    incident_id: str
    worker_id: str
    tokens_in: int = 0
    tokens_out: int = 0
    duration_ms: float = 0.0
    model_used: str = ""
    cost_usd: float = 0.0
    created_at: float = 0.0

    def __post_init__(self) -> None:
        if self.created_at == 0.0:
            self.created_at = time.time()


@dataclass
class ProvenanceRecord:
    """Persistent provenance tracking record."""

    provenance_id: str
    incident_id: str
    worker_id: str
    source_type: str = ""
    source_urn: str = ""
    source_name: str = ""
    confidence: float = 1.0
    verified: bool = True
    metadata: dict | None = None
    created_at: float = 0.0

    def __post_init__(self) -> None:
        if self.created_at == 0.0:
            self.created_at = time.time()
        if self.metadata is None:
            self.metadata = {}


# ---------------------------------------------------------------------------
# Abstract backend
# ---------------------------------------------------------------------------

class _AbstractBackend(ABC):
    """Interface that SQLite and in-memory backends both implement."""

    @abstractmethod
    async def initialize(self) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...

    # Incidents
    @abstractmethod
    async def insert_incident(self, record: IncidentRecord) -> None: ...
    @abstractmethod
    async def get_incident(self, incident_id: str) -> Optional[IncidentRecord]: ...
    @abstractmethod
    async def list_incidents(self, limit: int = 100, offset: int = 0) -> list[IncidentRecord]: ...
    @abstractmethod
    async def update_incident(self, record: IncidentRecord) -> None: ...

    # Investigations
    @abstractmethod
    async def insert_investigation(self, record: InvestigationRecord) -> None: ...
    @abstractmethod
    async def get_investigation(self, investigation_id: str) -> Optional[InvestigationRecord]: ...
    @abstractmethod
    async def list_investigations(self, incident_id: str | None = None, limit: int = 100) -> list[InvestigationRecord]: ...
    @abstractmethod
    async def update_investigation(self, record: InvestigationRecord) -> None: ...

    # Cost records
    @abstractmethod
    async def insert_cost(self, record: CostRecord) -> None: ...
    @abstractmethod
    async def get_costs_by_incident(self, incident_id: str) -> list[CostRecord]: ...
    @abstractmethod
    async def get_cost_summary(self, incident_id: str) -> dict[str, Any]: ...

    # Provenance records
    @abstractmethod
    async def insert_provenance(self, record: ProvenanceRecord) -> None: ...
    @abstractmethod
    async def get_provenance_by_incident(self, incident_id: str) -> list[ProvenanceRecord]: ...
    @abstractmethod
    async def get_provenance_summary(self, incident_id: str) -> dict[str, Any]: ...


# ---------------------------------------------------------------------------
# In-memory backend (fallback)
# ---------------------------------------------------------------------------

class _InMemoryBackend(_AbstractBackend):
    """Dict-based in-memory backend used when aiosqlite is unavailable."""

    def __init__(self) -> None:
        self._incidents: dict[str, IncidentRecord] = {}
        self._investigations: dict[str, InvestigationRecord] = {}
        self._costs: list[CostRecord] = []
        self._provenances: list[ProvenanceRecord] = []

    async def initialize(self) -> None:
        logger.info("Using in-memory persistence backend (aiosqlite not installed)")

    async def close(self) -> None:
        self._incidents.clear()
        self._investigations.clear()
        self._costs.clear()
        self._provenances.clear()

    # -- Incidents --
    async def insert_incident(self, record: IncidentRecord) -> None:
        self._incidents[record.incident_id] = record

    async def get_incident(self, incident_id: str) -> Optional[IncidentRecord]:
        return self._incidents.get(incident_id)

    async def list_incidents(self, limit: int = 100, offset: int = 0) -> list[IncidentRecord]:
        all_sorted = sorted(self._incidents.values(), key=lambda r: r.created_at, reverse=True)
        return all_sorted[offset: offset + limit]

    async def update_incident(self, record: IncidentRecord) -> None:
        self._incidents[record.incident_id] = record

    # -- Investigations --
    async def insert_investigation(self, record: InvestigationRecord) -> None:
        self._investigations[record.investigation_id] = record

    async def get_investigation(self, investigation_id: str) -> Optional[InvestigationRecord]:
        return self._investigations.get(investigation_id)

    async def list_investigations(self, incident_id: str | None = None, limit: int = 100) -> list[InvestigationRecord]:
        items = list(self._investigations.values())
        if incident_id is not None:
            items = [i for i in items if i.incident_id == incident_id]
        return items[:limit]

    async def update_investigation(self, record: InvestigationRecord) -> None:
        self._investigations[record.investigation_id] = record

    # -- Costs --
    async def insert_cost(self, record: CostRecord) -> None:
        self._costs.append(record)

    async def get_costs_by_incident(self, incident_id: str) -> list[CostRecord]:
        return [c for c in self._costs if c.incident_id == incident_id]

    async def get_cost_summary(self, incident_id: str) -> dict[str, Any]:
        costs = await self.get_costs_by_incident(incident_id)
        total_tokens_in = sum(c.tokens_in for c in costs)
        total_tokens_out = sum(c.tokens_out for c in costs)
        total_cost = sum(c.cost_usd for c in costs)
        total_duration = sum(c.duration_ms for c in costs)
        return {
            "incident_id": incident_id,
            "record_count": len(costs),
            "total_tokens_in": total_tokens_in,
            "total_tokens_out": total_tokens_out,
            "total_cost_usd": round(total_cost, 6),
            "total_duration_ms": round(total_duration, 2),
        }

    # -- Provenance --
    async def insert_provenance(self, record: ProvenanceRecord) -> None:
        self._provenances.append(record)

    async def get_provenance_by_incident(self, incident_id: str) -> list[ProvenanceRecord]:
        return [p for p in self._provenances if p.incident_id == incident_id]

    async def get_provenance_summary(self, incident_id: str) -> dict[str, Any]:
        records = await self.get_provenance_by_incident(incident_id)
        verified = sum(1 for r in records if r.verified)
        total = len(records)
        return {
            "incident_id": incident_id,
            "total_sources": total,
            "verified": verified,
            "unverified": total - verified,
            "provenance_score": round(verified / total, 4) if total > 0 else 1.0,
        }


# ---------------------------------------------------------------------------
# SQLite backend
# ---------------------------------------------------------------------------

class _SQLiteBackend(_AbstractBackend):
    """aiosqlite-backed persistence stored in ``data/meridian.db``."""

    def __init__(self, db_path: Path = _DB_PATH) -> None:
        self._db_path = db_path
        self._conn: Any = None  # aiosqlite.Connection

    async def initialize(self) -> None:
        import aiosqlite

        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(str(self._db_path))
        self._conn.row_factory = aiosqlite.Row
        await self._create_tables()
        logger.info("SQLite persistence initialized at %s", self._db_path)

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    # -- Schema creation --------------------------------------------------

    async def _create_tables(self) -> None:
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id   TEXT PRIMARY KEY,
                title         TEXT NOT NULL,
                severity      TEXT NOT NULL,
                status        TEXT NOT NULL,
                detected      TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL DEFAULT 0,
                root_cause    TEXT NOT NULL DEFAULT '',
                pattern_id    TEXT NOT NULL DEFAULT '',
                affected_models TEXT NOT NULL DEFAULT '[]',
                timeline      TEXT NOT NULL DEFAULT '[]',
                blast_radius  TEXT NOT NULL DEFAULT '{}',
                created_at    REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS investigations (
                investigation_id TEXT PRIMARY KEY,
                incident_id      TEXT NOT NULL,
                mode             TEXT NOT NULL DEFAULT 'replay',
                status           TEXT NOT NULL DEFAULT 'pending',
                start_time       REAL NOT NULL DEFAULT 0,
                end_time         REAL NOT NULL DEFAULT 0,
                worker_steps     TEXT NOT NULL DEFAULT '[]',
                final_summary    TEXT NOT NULL DEFAULT '',
                created_at       REAL NOT NULL,
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            );

            CREATE TABLE IF NOT EXISTS cost_records (
                cost_id      TEXT PRIMARY KEY,
                incident_id  TEXT NOT NULL,
                worker_id    TEXT NOT NULL,
                tokens_in    INTEGER NOT NULL DEFAULT 0,
                tokens_out   INTEGER NOT NULL DEFAULT 0,
                duration_ms  REAL NOT NULL DEFAULT 0,
                model_used   TEXT NOT NULL DEFAULT '',
                cost_usd     REAL NOT NULL DEFAULT 0,
                created_at   REAL NOT NULL,
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            );

            CREATE TABLE IF NOT EXISTS provenance_records (
                provenance_id TEXT PRIMARY KEY,
                incident_id   TEXT NOT NULL,
                worker_id     TEXT NOT NULL,
                source_type   TEXT NOT NULL DEFAULT '',
                source_urn    TEXT NOT NULL DEFAULT '',
                source_name   TEXT NOT NULL DEFAULT '',
                confidence    REAL NOT NULL DEFAULT 1.0,
                verified      INTEGER NOT NULL DEFAULT 1,
                metadata      TEXT NOT NULL DEFAULT '{}',
                created_at    REAL NOT NULL,
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            );
        """)
        await self._conn.commit()

    # -- Helpers ----------------------------------------------------------

    @staticmethod
    def _row_to_incident(row: Any) -> IncidentRecord:
        return IncidentRecord(
            incident_id=row["incident_id"],
            title=row["title"],
            severity=row["severity"],
            status=row["status"],
            detected=row["detected"],
            duration_seconds=row["duration_seconds"],
            root_cause=row["root_cause"],
            pattern_id=row["pattern_id"],
            affected_models=json.loads(row["affected_models"]),
            timeline=json.loads(row["timeline"]),
            blast_radius=json.loads(row["blast_radius"]),
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_investigation(row: Any) -> InvestigationRecord:
        return InvestigationRecord(
            investigation_id=row["investigation_id"],
            incident_id=row["incident_id"],
            mode=row["mode"],
            status=row["status"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            worker_steps=json.loads(row["worker_steps"]),
            final_summary=row["final_summary"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_cost(row: Any) -> CostRecord:
        return CostRecord(
            cost_id=row["cost_id"],
            incident_id=row["incident_id"],
            worker_id=row["worker_id"],
            tokens_in=row["tokens_in"],
            tokens_out=row["tokens_out"],
            duration_ms=row["duration_ms"],
            model_used=row["model_used"],
            cost_usd=row["cost_usd"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_provenance(row: Any) -> ProvenanceRecord:
        return ProvenanceRecord(
            provenance_id=row["provenance_id"],
            incident_id=row["incident_id"],
            worker_id=row["worker_id"],
            source_type=row["source_type"],
            source_urn=row["source_urn"],
            source_name=row["source_name"],
            confidence=row["confidence"],
            verified=bool(row["verified"]),
            metadata=json.loads(row["metadata"]),
            created_at=row["created_at"],
        )

    # -- Incidents --------------------------------------------------------

    async def insert_incident(self, record: IncidentRecord) -> None:
        await self._conn.execute(
            """INSERT OR REPLACE INTO incidents
               (incident_id, title, severity, status, detected, duration_seconds,
                root_cause, pattern_id, affected_models, timeline, blast_radius, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.incident_id,
                record.title,
                record.severity,
                record.status,
                record.detected,
                record.duration_seconds,
                record.root_cause,
                record.pattern_id,
                json.dumps(record.affected_models),
                json.dumps(record.timeline),
                json.dumps(record.blast_radius),
                record.created_at,
            ),
        )
        await self._conn.commit()

    async def get_incident(self, incident_id: str) -> Optional[IncidentRecord]:
        cursor = await self._conn.execute(
            "SELECT * FROM incidents WHERE incident_id = ?", (incident_id,)
        )
        row = await cursor.fetchone()
        return self._row_to_incident(row) if row else None

    async def list_incidents(self, limit: int = 100, offset: int = 0) -> list[IncidentRecord]:
        cursor = await self._conn.execute(
            "SELECT * FROM incidents ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = await cursor.fetchall()
        return [self._row_to_incident(r) for r in rows]

    async def update_incident(self, record: IncidentRecord) -> None:
        await self.insert_incident(record)

    # -- Investigations ---------------------------------------------------

    async def insert_investigation(self, record: InvestigationRecord) -> None:
        await self._conn.execute(
            """INSERT OR REPLACE INTO investigations
               (investigation_id, incident_id, mode, status, start_time, end_time,
                worker_steps, final_summary, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.investigation_id,
                record.incident_id,
                record.mode,
                record.status,
                record.start_time,
                record.end_time,
                json.dumps(record.worker_steps),
                record.final_summary,
                record.created_at,
            ),
        )
        await self._conn.commit()

    async def get_investigation(self, investigation_id: str) -> Optional[InvestigationRecord]:
        cursor = await self._conn.execute(
            "SELECT * FROM investigations WHERE investigation_id = ?",
            (investigation_id,),
        )
        row = await cursor.fetchone()
        return self._row_to_investigation(row) if row else None

    async def list_investigations(
        self, incident_id: str | None = None, limit: int = 100
    ) -> list[InvestigationRecord]:
        if incident_id is not None:
            cursor = await self._conn.execute(
                "SELECT * FROM investigations WHERE incident_id = ? ORDER BY created_at DESC LIMIT ?",
                (incident_id, limit),
            )
        else:
            cursor = await self._conn.execute(
                "SELECT * FROM investigations ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        rows = await cursor.fetchall()
        return [self._row_to_investigation(r) for r in rows]

    async def update_investigation(self, record: InvestigationRecord) -> None:
        await self.insert_investigation(record)

    # -- Cost records -----------------------------------------------------

    async def insert_cost(self, record: CostRecord) -> None:
        await self._conn.execute(
            """INSERT OR REPLACE INTO cost_records
               (cost_id, incident_id, worker_id, tokens_in, tokens_out,
                duration_ms, model_used, cost_usd, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.cost_id,
                record.incident_id,
                record.worker_id,
                record.tokens_in,
                record.tokens_out,
                record.duration_ms,
                record.model_used,
                record.cost_usd,
                record.created_at,
            ),
        )
        await self._conn.commit()

    async def get_costs_by_incident(self, incident_id: str) -> list[CostRecord]:
        cursor = await self._conn.execute(
            "SELECT * FROM cost_records WHERE incident_id = ? ORDER BY created_at",
            (incident_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_cost(r) for r in rows]

    async def get_cost_summary(self, incident_id: str) -> dict[str, Any]:
        cursor = await self._conn.execute(
            """SELECT
                   COUNT(*)        AS record_count,
                   SUM(tokens_in)  AS total_tokens_in,
                   SUM(tokens_out) AS total_tokens_out,
                   SUM(cost_usd)   AS total_cost_usd,
                   SUM(duration_ms) AS total_duration_ms
               FROM cost_records
               WHERE incident_id = ?""",
            (incident_id,),
        )
        row = await cursor.fetchone()
        return {
            "incident_id": incident_id,
            "record_count": row["record_count"] or 0,
            "total_tokens_in": row["total_tokens_in"] or 0,
            "total_tokens_out": row["total_tokens_out"] or 0,
            "total_cost_usd": round(float(row["total_cost_usd"] or 0), 6),
            "total_duration_ms": round(float(row["total_duration_ms"] or 0), 2),
        }

    # -- Provenance records -----------------------------------------------

    async def insert_provenance(self, record: ProvenanceRecord) -> None:
        await self._conn.execute(
            """INSERT OR REPLACE INTO provenance_records
               (provenance_id, incident_id, worker_id, source_type, source_urn,
                source_name, confidence, verified, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.provenance_id,
                record.incident_id,
                record.worker_id,
                record.source_type,
                record.source_urn,
                record.source_name,
                record.confidence,
                int(record.verified),
                json.dumps(record.metadata),
                record.created_at,
            ),
        )
        await self._conn.commit()

    async def get_provenance_by_incident(self, incident_id: str) -> list[ProvenanceRecord]:
        cursor = await self._conn.execute(
            "SELECT * FROM provenance_records WHERE incident_id = ? ORDER BY created_at",
            (incident_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_provenance(r) for r in rows]

    async def get_provenance_summary(self, incident_id: str) -> dict[str, Any]:
        cursor = await self._conn.execute(
            """SELECT
                   COUNT(*)   AS total_sources,
                   SUM(CASE WHEN verified = 1 THEN 1 ELSE 0 END) AS verified
               FROM provenance_records
               WHERE incident_id = ?""",
            (incident_id,),
        )
        row = await cursor.fetchone()
        total = row["total_sources"] or 0
        verified = row["verified"] or 0
        return {
            "incident_id": incident_id,
            "total_sources": total,
            "verified": verified,
            "unverified": total - verified,
            "provenance_score": round(verified / total, 4) if total > 0 else 1.0,
        }


# ---------------------------------------------------------------------------
# Public manager
# ---------------------------------------------------------------------------

class PersistenceManager:
    """Unified async persistence layer for Meridian AI.

    Transparently selects between SQLite (aiosqlite) and in-memory storage.
    Use as an async context manager::

        async with PersistenceManager(db_path=Path("data/meridian.db")) as pm:
            await pm.record_incident(incident_id="42", title="Schema drift", ...)
            incident = await pm.get_incident("42")

    Args:
        db_path: Path to the SQLite database file.  Ignored when falling
                 back to in-memory storage.  Defaults to ``data/meridian.db``.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or _DB_PATH
        self._backend: _AbstractBackend

    async def __aenter__(self) -> "PersistenceManager":
        self._backend = self._select_backend()
        await self._backend.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self._backend.close()

    # -- Backend selection -------------------------------------------------

    def _select_backend(self) -> _AbstractBackend:
        try:
            import aiosqlite  # noqa: F401 — availability check only
            return _SQLiteBackend(db_path=self._db_path)
        except ImportError:
            logger.warning(
                "aiosqlite not installed — falling back to in-memory storage. "
                "Install it with: pip install aiosqlite"
            )
            return _InMemoryBackend()

    # -- Convenience re-exports -------------------------------------------

    @property
    def backend_type(self) -> str:
        """Return ``'sqlite'`` or ``'memory'``."""
        return "sqlite" if isinstance(self._backend, _SQLiteBackend) else "memory"

    # -- Incidents --------------------------------------------------------

    async def record_incident(
        self,
        incident_id: str,
        title: str,
        severity: str,
        status: str,
        detected: str,
        duration_seconds: int = 0,
        root_cause: str = "",
        pattern_id: str = "",
        affected_models: list[str] | None = None,
        timeline: list[dict] | None = None,
        blast_radius: dict | None = None,
    ) -> IncidentRecord:
        """Persist an incident record.

        Returns:
            The fully-populated :class:`IncidentRecord`.
        """
        record = IncidentRecord(
            incident_id=incident_id,
            title=title,
            severity=severity,
            status=status,
            detected=detected,
            duration_seconds=duration_seconds,
            root_cause=root_cause,
            pattern_id=pattern_id,
            affected_models=affected_models,
            timeline=timeline,
            blast_radius=blast_radius,
        )
        await self._backend.insert_incident(record)
        return record

    async def get_incident(self, incident_id: str) -> Optional[IncidentRecord]:
        """Retrieve a single incident by ID."""
        return await self._backend.get_incident(incident_id)

    async def list_incidents(self, limit: int = 100, offset: int = 0) -> list[IncidentRecord]:
        """List incidents ordered by creation time (newest first)."""
        return await self._backend.list_incidents(limit=limit, offset=offset)

    async def update_incident(self, record: IncidentRecord) -> None:
        """Overwrite an existing incident record."""
        await self._backend.update_incident(record)

    # -- Investigations ---------------------------------------------------

    async def record_investigation(
        self,
        investigation_id: str,
        incident_id: str,
        mode: str = "replay",
        status: str = "pending",
        start_time: float = 0.0,
        end_time: float = 0.0,
        worker_steps: list[dict] | None = None,
        final_summary: str = "",
    ) -> InvestigationRecord:
        """Persist an investigation record.

        Returns:
            The fully-populated :class:`InvestigationRecord`.
        """
        record = InvestigationRecord(
            investigation_id=investigation_id,
            incident_id=incident_id,
            mode=mode,
            status=status,
            start_time=start_time,
            end_time=end_time,
            worker_steps=worker_steps,
            final_summary=final_summary,
        )
        await self._backend.insert_investigation(record)
        return record

    async def get_investigation(self, investigation_id: str) -> Optional[InvestigationRecord]:
        """Retrieve a single investigation by ID."""
        return await self._backend.get_investigation(investigation_id)

    async def list_investigations(
        self, incident_id: str | None = None, limit: int = 100
    ) -> list[InvestigationRecord]:
        """List investigations, optionally filtered by incident ID."""
        return await self._backend.list_investigations(incident_id=incident_id, limit=limit)

    async def update_investigation(self, record: InvestigationRecord) -> None:
        """Overwrite an existing investigation record."""
        await self._backend.update_investigation(record)

    # -- Cost records -----------------------------------------------------

    async def record_cost(
        self,
        cost_id: str,
        incident_id: str,
        worker_id: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        duration_ms: float = 0.0,
        model_used: str = "",
        cost_usd: float = 0.0,
    ) -> CostRecord:
        """Persist a cost tracking record.

        Returns:
            The fully-populated :class:`CostRecord`.
        """
        record = CostRecord(
            cost_id=cost_id,
            incident_id=incident_id,
            worker_id=worker_id,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            duration_ms=duration_ms,
            model_used=model_used,
            cost_usd=cost_usd,
        )
        await self._backend.insert_cost(record)
        return record

    async def get_costs_by_incident(self, incident_id: str) -> list[CostRecord]:
        """Retrieve all cost records for an incident."""
        return await self._backend.get_costs_by_incident(incident_id)

    async def get_cost_summary(self, incident_id: str) -> dict[str, Any]:
        """Return aggregate cost metrics for an incident."""
        return await self._backend.get_cost_summary(incident_id)

    # -- Provenance records -----------------------------------------------

    async def record_provenance(
        self,
        provenance_id: str,
        incident_id: str,
        worker_id: str,
        source_type: str = "",
        source_urn: str = "",
        source_name: str = "",
        confidence: float = 1.0,
        verified: bool = True,
        metadata: dict | None = None,
    ) -> ProvenanceRecord:
        """Persist a provenance tracking record.

        Returns:
            The fully-populated :class:`ProvenanceRecord`.
        """
        record = ProvenanceRecord(
            provenance_id=provenance_id,
            incident_id=incident_id,
            worker_id=worker_id,
            source_type=source_type,
            source_urn=source_urn,
            source_name=source_name,
            confidence=confidence,
            verified=verified,
            metadata=metadata,
        )
        await self._backend.insert_provenance(record)
        return record

    async def get_provenance_by_incident(self, incident_id: str) -> list[ProvenanceRecord]:
        """Retrieve all provenance records for an incident."""
        return await self._backend.get_provenance_by_incident(incident_id)

    async def get_provenance_summary(self, incident_id: str) -> dict[str, Any]:
        """Return aggregate provenance metrics for an incident."""
        return await self._backend.get_provenance_summary(incident_id)
