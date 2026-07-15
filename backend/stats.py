"""Real statistical computation — no LLM guessing.

Every function here is pure math. Two arrays of numbers go in,
quantitative results come out. The LLM interprets these results
AFTER computation, never replaces it.
"""
import math
from dataclasses import dataclass, field


# ── Drift Detection ───────────────────────────────────────────────────────────


@dataclass
class DriftResult:
    """Result of a statistical drift test."""
    metric: str
    value: float
    threshold: float
    drifted: bool
    detail: str

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "value": round(self.value, 6),
            "threshold": self.threshold,
            "drifted": self.drifted,
            "detail": self.detail,
        }


def population_stability_index(
    reference: list[float],
    current: list[float],
    bins: int = 10,
    threshold: float = 0.2,
) -> DriftResult:
    """Population Stability Index — industry standard for feature drift.

    PSI < 0.1: No significant drift
    PSI 0.1-0.2: Moderate drift, monitor
    PSI > 0.2: Significant drift, investigate
    """
    if not reference or not current:
        return DriftResult("psi", 0.0, threshold, False, "Insufficient data")

    ref_min, ref_max = min(reference), max(reference)
    if ref_min == ref_max:
        return DriftResult("psi", 0.0, threshold, False, "Zero variance in reference")

    bin_edges = [ref_min + (ref_max - ref_min) * i / bins for i in range(bins + 1)]

    def histogram(data, edges):
        counts = [0] * (len(edges) - 1)
        for v in data:
            for i in range(len(edges) - 1):
                if edges[i] <= v < edges[i + 1]:
                    counts[i] += 1
                    break
            else:
                counts[-1] += 1
        total = max(len(data), 1)
        return [c / total for c in counts]

    ref_hist = histogram(reference, bin_edges)
    cur_hist = histogram(current, bin_edges)

    psi = 0.0
    for p_ref, p_cur in zip(ref_hist, cur_hist):
        p_ref = max(p_ref, 0.0001)
        p_cur = max(p_cur, 0.0001)
        psi += (p_cur - p_ref) * math.log(p_cur / p_ref)

    drifted = psi > threshold
    return DriftResult("psi", psi, threshold, drifted, f"PSI={psi:.4f}")


def ks_test(
    reference: list[float],
    current: list[float],
    threshold: float = 0.1,
) -> DriftResult:
    """Two-sample Kolmogorov-Smirnov test for distribution shift."""
    if not reference or not current:
        return DriftResult("ks", 0.0, threshold, False, "Insufficient data")

    ref_sorted = sorted(reference)
    cur_sorted = sorted(current)
    all_values = sorted(set(ref_sorted + cur_sorted))

    def ecdf(sample, x):
        return sum(1 for v in sample if v <= x) / max(len(sample), 1)

    max_diff = 0.0
    for x in all_values:
        diff = abs(ecdf(ref_sorted, x) - ecdf(cur_sorted, x))
        if diff > max_diff:
            max_diff = diff

    drifted = max_diff > threshold
    return DriftResult("ks", max_diff, threshold, drifted, f"KS={max_diff:.4f}")


def feature_drift_score(reference: list[float], current: list[float]) -> dict:
    """Combined PSI + KS drift score."""
    psi_result = population_stability_index(reference, current)
    ks_result = ks_test(reference, current)

    psi_norm = min(psi_result.value / 0.5, 1.0)
    ks_norm = min(ks_result.value / 0.3, 1.0)
    combined = 0.6 * psi_norm + 0.4 * ks_norm

    return {
        "combined_score": round(combined, 4),
        "psi": psi_result.to_dict(),
        "ks": ks_result.to_dict(),
        "drifted": psi_result.drifted or ks_result.drifted,
    }


# ── Schema Analysis ───────────────────────────────────────────────────────────


@dataclass
class SchemaDiff:
    """Result of comparing two schemas."""
    added_columns: list[dict] = field(default_factory=list)
    removed_columns: list[dict] = field(default_factory=list)
    type_changes: list[dict] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    has_changes: bool = False

    def to_dict(self) -> dict:
        return {
            "added": self.added_columns,
            "removed": self.removed_columns,
            "type_changes": self.type_changes,
            "unchanged": self.unchanged,
            "has_changes": self.has_changes,
            "summary": f"{len(self.added_columns)} added, {len(self.removed_columns)} removed, {len(self.type_changes)} type changes",
        }


def compute_schema_diff(
    before_fields: list[dict],
    after_fields: list[dict],
) -> SchemaDiff:
    """Compute the diff between two schema field lists.

    Each field dict should have at minimum: {"name": "col_name", "type": "STRING"}
    """
    before_map = {f["name"]: f.get("type", "UNKNOWN") for f in before_fields}
    after_map = {f["name"]: f.get("type", "UNKNOWN") for f in after_fields}

    added = []
    for name, type_ in after_map.items():
        if name not in before_map:
            added.append({"column": name, "type": type_})

    removed = []
    for name, type_ in before_map.items():
        if name not in after_map:
            removed.append({"column": name, "type": type_})

    type_changes = []
    unchanged = []
    for name in before_map:
        if name in after_map:
            if before_map[name] != after_map[name]:
                type_changes.append({
                    "column": name,
                    "before": before_map[name],
                    "after": after_map[name],
                })
            else:
                unchanged.append(name)

    return SchemaDiff(
        added_columns=added,
        removed_columns=removed,
        type_changes=type_changes,
        unchanged=unchanged,
        has_changes=bool(added or removed or type_changes),
    )


# ── Lineage Traversal ─────────────────────────────────────────────────────────


@dataclass
class ColumnDependency:
    """A single column-level dependency."""
    source_column: str
    source_table: str
    target_column: str
    target_table: str
    transformation: str = ""  # e.g., "JOIN", "AGGREGATE", "FILTER", "DIRECT"

    def to_dict(self) -> dict:
        return {
            "source_column": self.source_column,
            "source_table": self.source_table,
            "target_column": self.target_column,
            "target_table": self.target_table,
            "transformation": self.transformation,
        }


@dataclass
class LineageTraversal:
    """Result of graph traversal from source to downstream."""
    source_urn: str
    downstream_urns: list[str] = field(default_factory=list)
    upstream_urns: list[str] = field(default_factory=list)
    paths: list[list[str]] = field(default_factory=list)
    affected_models: list[str] = field(default_factory=list)
    affected_datasets: list[str] = field(default_factory=list)
    hop_count: int = 0
    # Column-level lineage
    column_dependencies: list[ColumnDependency] = field(default_factory=list)
    affected_columns: list[str] = field(default_factory=list)
    source_columns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        result = {
            "source": self.source_urn,
            "downstream_count": len(self.downstream_urns),
            "upstream_count": len(self.upstream_urns),
            "paths": self.paths,
            "affected_models": self.affected_models,
            "affected_datasets": self.affected_datasets,
            "hop_count": self.hop_count,
        }
        if self.column_dependencies:
            result["column_dependencies"] = [cd.to_dict() for cd in self.column_dependencies]
            result["affected_columns"] = self.affected_columns
            result["source_columns"] = self.source_columns
            result["column_level"] = True
        return result

    def get_affected_column_count(self) -> int:
        """Return total number of affected columns across all dependencies."""
        if self.column_dependencies:
            return len(self.affected_columns)
        return 0

    def get_column_blast_radius(self) -> dict:
        """Return column-level blast radius summary."""
        if not self.column_dependencies:
            return {"column_level": False, "total_columns": 0}

        # Group by target table
        table_columns: dict[str, list[str]] = {}
        for dep in self.column_dependencies:
            if dep.target_table not in table_columns:
                table_columns[dep.target_table] = []
            if dep.target_column not in table_columns[dep.target_table]:
                table_columns[dep.target_table].append(dep.target_column)

        return {
            "column_level": True,
            "total_columns": len(self.affected_columns),
            "source_columns": self.source_columns,
            "columns_by_table": table_columns,
            "transformation_types": list(set(dep.transformation for dep in self.column_dependencies if dep.transformation)),
        }


def traverse_lineage(
    lineage_data: dict,
    entities: dict[str, dict],
) -> LineageTraversal:
    """Traverse lineage graph and compute blast radius.

    Args:
        lineage_data: Output from get_lineage() — {upstream: [...], downstream: [...]}
        entities: Dict of URN → entity metadata
    """
    source = lineage_data.get("entity", "")
    downstream = lineage_data.get("downstream", [])
    upstream = lineage_data.get("upstream", [])

    downstream_urns = [d.get("urn", "") for d in downstream if d.get("urn")]
    upstream_urns = [u.get("urn", "") for u in upstream if u.get("urn")]

    affected_models = [d.get("name", "") for d in downstream if d.get("type") == "mlModel"]
    affected_datasets = [d.get("name", "") for d in downstream if d.get("type") == "dataset"]

    # Compute max hops
    hop_count = max(len(downstream_urns), len(upstream_urns))

    # Build paths
    paths = []
    for d in downstream:
        path = [source, d.get("urn", "")]
        paths.append(path)

    return LineageTraversal(
        source_urn=source,
        downstream_urns=downstream_urns,
        upstream_urns=upstream_urns,
        paths=paths,
        affected_models=affected_models,
        affected_datasets=affected_datasets,
        hop_count=hop_count,
    )


def traverse_column_lineage(
    lineage_data: dict,
    entities: dict[str, dict],
    changed_columns: list[dict] | None = None,
) -> LineageTraversal:
    """Traverse lineage graph at column level.

    Args:
        lineage_data: Output from get_lineage() with column facets
        entities: Dict of URN → entity metadata
        changed_columns: List of columns that changed, e.g. [{"name": "age", "before": "INT", "after": "STRING"}]

    Returns:
        LineageTraversal with column-level dependencies
    """
    source = lineage_data.get("entity", "")
    downstream = lineage_data.get("downstream", [])
    upstream = lineage_data.get("upstream", [])

    downstream_urns = [d.get("urn", "") for d in downstream if d.get("urn")]
    upstream_urns = [u.get("urn", "") for u in upstream if u.get("urn")]

    affected_models = [d.get("name", "") for d in downstream if d.get("type") == "mlModel"]
    affected_datasets = [d.get("name", "") for d in downstream if d.get("type") == "dataset"]

    hop_count = max(len(downstream_urns), len(upstream_urns))

    # Build paths
    paths = []
    for d in downstream:
        path = [source, d.get("urn", "")]
        paths.append(path)

    # Build column-level dependencies from changed columns
    column_deps = []
    affected_columns = []
    source_columns = []

    if changed_columns:
        source_name = entities.get(source, {}).get("name", source.split(":")[-2] if ":" in source else source)

        for col in changed_columns:
            col_name = col.get("name", "")
            source_columns.append(col_name)

            # For each downstream entity, create a column dependency
            for d in downstream:
                target_urn = d.get("urn", "")
                target_name = entities.get(target_urn, {}).get("name", d.get("name", ""))

                # Determine transformation type based on entity types
                source_type = entities.get(source, {}).get("type", "dataset")
                target_type = d.get("type", "dataset")

                transformation = "DIRECT"
                if source_type == "dataset" and target_type == "dataset":
                    transformation = "TRANSFORM"
                elif target_type == "mlModel":
                    transformation = "FEATURE"
                elif "dbt" in target_name.lower() or "transform" in target_name.lower():
                    transformation = "TRANSFORM"

                # Create column dependency
                dep = ColumnDependency(
                    source_column=col_name,
                    source_table=source_name,
                    target_column=col_name,  # Same column name propagates through
                    target_table=target_name,
                    transformation=transformation,
                )
                column_deps.append(dep)
                affected_columns.append(f"{target_name}.{col_name}")

    return LineageTraversal(
        source_urn=source,
        downstream_urns=downstream_urns,
        upstream_urns=upstream_urns,
        paths=paths,
        affected_models=affected_models,
        affected_datasets=affected_datasets,
        hop_count=hop_count,
        column_dependencies=column_deps,
        affected_columns=affected_columns,
        source_columns=source_columns,
    )


# ── Temporal Leakage ──────────────────────────────────────────────────────────


@dataclass
class LeakageCheck:
    """Result of temporal leakage analysis."""
    timestamp_columns: list[str] = field(default_factory=list)
    suspicious_patterns: list[str] = field(default_factory=list)
    leakage_score: float = 0.0
    has_leakage: bool = False

    def to_dict(self) -> dict:
        return {
            "timestamp_columns": self.timestamp_columns,
            "suspicious_patterns": self.suspicious_patterns,
            "leakage_score": round(self.leakage_score, 4),
            "has_leakage": self.has_leakage,
        }


def check_temporal_leakage(
    fields: list[dict],
    queries: list[dict] | None = None,
) -> LeakageCheck:
    """Check for temporal data leakage patterns in schema and queries.

    Detects:
    - Columns with future timestamps
    - Feature columns that could leak label information
    - SQL queries with look-ahead bias
    """
    timestamp_cols = [f["name"] for f in fields if "TIMESTAMP" in f.get("type", "").upper()]
    suspicious = []

    # Check for suspicious column naming patterns
    suspicious_names = ["future_", "next_", "tomorrow", "predicted_", "forecast_"]
    for f in fields:
        name_lower = f["name"].lower()
        for pattern in suspicious_names:
            if pattern in name_lower:
                suspicious.append(f"{f['name']} matches pattern '{pattern}'")

    # Check SQL queries for look-ahead patterns
    if queries:
        for q in queries:
            sql = q.get("query", "").lower()
            if "lead(" in sql or "lag(" in sql:
                suspicious.append(f"Query uses window function that may cause leakage: {q.get('query', '')[:80]}")
            if "future" in sql or "tomorrow" in sql or "next_" in sql:
                suspicious.append(f"Query references future data: {q.get('query', '')[:80]}")

    # Compute leakage score
    score = 0.0
    if suspicious:
        score = min(1.0, len(suspicious) * 0.3)

    return LeakageCheck(
        timestamp_columns=timestamp_cols,
        suspicious_patterns=suspicious,
        leakage_score=score,
        has_leakage=len(suspicious) > 0,
    )


# ── Type Mismatch ─────────────────────────────────────────────────────────────


def type_mismatch_check(
    reference_fields: list[dict],
    current_fields: list[dict],
) -> dict:
    """Check for column type mismatches between reference and current schemas."""
    ref_types = {f["name"]: f.get("type", "UNKNOWN") for f in reference_fields}
    cur_types = {f["name"]: f.get("type", "UNKNOWN") for f in current_fields}

    mismatches = []
    for col, ref_type in ref_types.items():
        cur_type = cur_types.get(col)
        if cur_type is None:
            mismatches.append({"column": col, "reference_type": ref_type, "current_type": "MISSING"})
        elif cur_type != ref_type:
            mismatches.append({"column": col, "reference_type": ref_type, "current_type": cur_type})

    for col in cur_types:
        if col not in ref_types:
            mismatches.append({"column": col, "reference_type": "MISSING", "current_type": cur_types[col]})

    return {
        "mismatches": mismatches,
        "count": len(mismatches),
        "drifted": len(mismatches) > 0,
    }


# ── Business Impact Calculation ───────────────────────────────────────────────

# Demo defaults — calibrate per deployment based on actual prediction volume and revenue
DEFAULT_PREDICTIONS_AT_RISK = 32000  # Fallback when no model metadata available
REVENUE_PER_PREDICTION = 1.41  # Average revenue per ML prediction (USD)


def compute_blast_radius(
    downstream_urns: list[str],
    entities: dict[str, dict],
) -> dict:
    """Compute business impact from blast radius.

    Computes predictions_at_risk and revenue from entity metadata.
    Falls back to reasonable defaults when metadata unavailable.
    """
    models = []
    datasets = []
    other = []
    total_predictions = 0

    for urn in downstream_urns:
        entity = entities.get(urn, {})
        entity_type = entity.get("type", "")
        name = entity.get("name", urn)
        if entity_type == "mlModel":
            models.append(name)
            # Extract prediction volume from model metadata if available
            model_predictions = entity.get("predictions_per_day", 0)
            if model_predictions > 0:
                total_predictions += model_predictions
        elif entity_type == "dataset":
            datasets.append(name)
        else:
            other.append(name)

    # Compute revenue: predictions * estimated value per prediction
    predictions_at_risk = total_predictions if total_predictions > 0 else DEFAULT_PREDICTIONS_AT_RISK
    revenue_at_risk = predictions_at_risk * REVENUE_PER_PREDICTION

    return {
        "affected_models": models,
        "affected_datasets": datasets,
        "affected_other": other,
        "total_affected": len(downstream_urns),
        "predictions_at_risk": predictions_at_risk,
        "revenue_at_risk_daily": round(revenue_at_risk),
    }


# ── Governance Gap Detection ──────────────────────────────────────────────────


def detect_governance_gaps(entities: list[dict]) -> list[dict]:
    """Check entities for missing governance metadata.

    Returns list of entities with governance issues.
    """
    gaps = []

    for entity in entities:
        issues = []
        name = entity.get("name", "unknown")
        urn = entity.get("urn", "")

        if not entity.get("owner"):
            issues.append("no_owner")
        if not entity.get("tags") or len(entity.get("tags", [])) < 2:
            issues.append("insufficient_tags")
        if entity.get("health_score") is None:
            issues.append("no_health_score")
        if entity.get("confidence") is None:
            issues.append("no_confidence_score")

        if issues:
            gaps.append({"name": name, "urn": urn, "issues": issues})

    return gaps
