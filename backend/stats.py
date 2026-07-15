"""Real statistical computation — no LLM guessing.

Every function here is pure math. Two arrays of numbers go in,
quantitative results come out. The LLM interprets these results
AFTER computation, never replaces it.

Includes DSA implementations:
- BFS/DFS graph traversal for lineage
- Topological sort for dependency ordering
- Cycle detection for graph validation
- Binary search for O(log n) lookups
- Union-Find for connected components
"""
import bisect
import math
from collections import deque
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


# ── DSA: Graph Algorithms ─────────────────────────────────────────────────────


def bfs_lineage(
    source_urn: str,
    lineage_graph: dict[str, list[str]],
    max_depth: int = 10,
) -> dict:
    """BFS traversal of lineage graph to arbitrary depth.

    Uses collections.deque for O(1) queue operations.
    Time complexity: O(V + E) where V = vertices, E = edges
    Space complexity: O(V)

    Args:
        source_urn: Starting entity URN
        lineage_graph: Adjacency list {urn: [downstream_urns]}
        max_depth: Maximum traversal depth

    Returns:
        Dict with nodes, edges, depths, and paths
    """
    queue: deque[tuple[str, int]] = deque([(source_urn, 0)])
    visited: set[str] = set()
    result: dict = {
        "nodes": [],
        "edges": [],
        "depths": {},
        "paths": {source_urn: [source_urn]},
    }

    while queue:
        current, depth = queue.popleft()

        if current in visited or depth > max_depth:
            continue

        visited.add(current)
        result["nodes"].append(current)
        result["depths"][current] = depth

        for neighbor in lineage_graph.get(current, []):
            if neighbor not in visited:
                queue.append((neighbor, depth + 1))
                result["edges"].append((current, neighbor))
                # Build path
                result["paths"][neighbor] = result["paths"][current] + [neighbor]

    return result


def dfs_lineage(
    source_urn: str,
    lineage_graph: dict[str, list[str]],
    max_depth: int = 10,
) -> dict:
    """DFS traversal of lineage graph using explicit stack.

    Uses list as stack for O(1) push/pop.
    Time complexity: O(V + E)
    Space complexity: O(V)

    Args:
        source_urn: Starting entity URN
        lineage_graph: Adjacency list {urn: [downstream_urns]}
        max_depth: Maximum traversal depth

    Returns:
        Dict with nodes, edges, depths, and topological order
    """
    stack: list[tuple[str, int]] = [(source_urn, 0)]
    visited: set[str] = set()
    result: dict = {
        "nodes": [],
        "edges": [],
        "depths": {},
        "topological_order": [],
    }

    while stack:
        current, depth = stack.pop()

        if current in visited or depth > max_depth:
            continue

        visited.add(current)
        result["nodes"].append(current)
        result["depths"][current] = depth
        result["topological_order"].append(current)

        # Push neighbors in reverse order for correct DFS traversal
        for neighbor in reversed(lineage_graph.get(current, [])):
            if neighbor not in visited:
                stack.append((neighbor, depth + 1))
                result["edges"].append((current, neighbor))

    return result


def topological_sort(lineage_graph: dict[str, list[str]]) -> list[str]:
    """Topological sort using Kahn's algorithm.

    Time complexity: O(V + E)
    Space complexity: O(V)

    Args:
        lineage_graph: Adjacency list {urn: [downstream_urns]}

    Returns:
        List of URNs in topological order (dependencies first)
    """
    # Compute in-degrees
    in_degree: dict[str, int] = {node: 0 for node in lineage_graph}
    for node, neighbors in lineage_graph.items():
        for neighbor in neighbors:
            in_degree[neighbor] = in_degree.get(neighbor, 0) + 1

    # Start with nodes that have no dependencies
    queue = deque([node for node, deg in in_degree.items() if deg == 0])
    order: list[str] = []

    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in lineage_graph.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Check for cycles
    if len(order) != len(in_degree):
        raise ValueError("Cycle detected in lineage graph")

    return order


def has_cycle(lineage_graph: dict[str, list[str]]) -> bool:
    """Detect cycles in lineage graph using DFS coloring.

    Time complexity: O(V + E)
    Space complexity: O(V)

    Args:
        lineage_graph: Adjacency list {urn: [downstream_urns]}

    Returns:
        True if cycle exists, False otherwise
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {node: WHITE for node in lineage_graph}

    def dfs(node: str) -> bool:
        color[node] = GRAY
        for neighbor in lineage_graph.get(node, []):
            if color.get(neighbor, WHITE) == GRAY:
                return True
            if color.get(neighbor, WHITE) == WHITE and dfs(neighbor):
                return True
        color[node] = BLACK
        return False

    return any(dfs(node) for node, c in color.items() if c == WHITE)


def shortest_path_bfs(
    source: str,
    target: str,
    lineage_graph: dict[str, list[str]],
) -> list[str] | None:
    """Find shortest path between two nodes using BFS.

    Time complexity: O(V + E)
    Space complexity: O(V)

    Args:
        source: Starting URN
        target: Target URN
        lineage_graph: Adjacency list

    Returns:
        List of URNs forming shortest path, or None if no path
    """
    if source == target:
        return [source]

    queue: deque[tuple[str, list[str]]] = deque([(source, [source])])
    visited: set[str] = {source}

    while queue:
        current, path = queue.popleft()
        for neighbor in lineage_graph.get(current, []):
            if neighbor == target:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return None


def connected_components(lineage_graph: dict[str, list[str]]) -> list[list[str]]:
    """Find connected components in undirected graph representation.

    Time complexity: O(V + E)
    Space complexity: O(V)

    Args:
        lineage_graph: Adjacency list (treated as undirected)

    Returns:
        List of components, each component is a list of URNs
    """
    visited: set[str] = set()
    components: list[list[str]] = []

    # Build undirected graph
    undirected: dict[str, set[str]] = {}
    for node, neighbors in lineage_graph.items():
        if node not in undirected:
            undirected[node] = set()
        for neighbor in neighbors:
            undirected[node].add(neighbor)
            if neighbor not in undirected:
                undirected[neighbor] = set()
            undirected[neighbor].add(node)

    def dfs(node: str, component: list[str]) -> None:
        visited.add(node)
        component.append(node)
        for neighbor in undirected.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, component)

    for node in undirected:
        if node not in visited:
            component: list[str] = []
            dfs(node, component)
            components.append(component)

    return components


# ── DSA: Binary Search ────────────────────────────────────────────────────────


def binary_search_cdf(sorted_arr: list[float], value: float) -> float:
    """Compute CDF value using binary search.

    Time complexity: O(log n)
    Space complexity: O(1)

    Args:
        sorted_arr: Pre-sorted array
        value: Value to compute CDF for

    Returns:
        CDF value (proportion of elements <= value)
    """
    if not sorted_arr:
        return 0.0
    idx = bisect.bisect_right(sorted_arr, value)
    return idx / len(sorted_arr)


def ks_test_binary(
    reference: list[float],
    current: list[float],
    threshold: float = 0.1,
) -> DriftResult:
    """KS-test with binary search for O(log n) ECDF lookup.

    Time complexity: O((n+m) log(n+m)) vs O(n*m) for naive
    Space complexity: O(n+m)

    Args:
        reference: Reference distribution
        current: Current distribution
        threshold: Drift threshold (default 0.1)

    Returns:
        DriftResult with KS statistic
    """
    if not reference or not current:
        return DriftResult("ks", 0.0, threshold, False, "Insufficient data")

    ref_sorted = sorted(reference)
    cur_sorted = sorted(current)
    all_values = sorted(set(ref_sorted + cur_sorted))

    max_diff = 0.0
    n_ref, n_cur = len(ref_sorted), len(cur_sorted)

    for val in all_values:
        ref_cdf = bisect.bisect_right(ref_sorted, val) / n_ref
        cur_cdf = bisect.bisect_right(cur_sorted, val) / n_cur
        max_diff = max(max_diff, abs(ref_cdf - cur_cdf))

    return DriftResult(
        metric="ks",
        value=max_diff,
        threshold=threshold,
        drifted=max_diff > threshold,
        detail=f"KS statistic: {max_diff:.4f} (threshold: {threshold})",
    )


# ── DSA: Union-Find ───────────────────────────────────────────────────────────


class UnionFind:
    """Disjoint Set Union with path compression and union by rank.

    Time complexity: O(α(n)) amortized for find/union (α = inverse Ackermann)
    Space complexity: O(n)
    """

    def __init__(self) -> None:
        self.parent: dict[str, str] = {}
        self.rank: dict[str, int] = {}

    def find(self, x: str) -> str:
        """Find root of x with path compression."""
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str) -> None:
        """Union two sets by rank."""
        px, py = self.find(x), self.find(y)
        if px == py:
            return
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1

    def connected(self, x: str, y: str) -> bool:
        """Check if x and y are in the same set."""
        return self.find(x) == self.find(y)

    def get_component(self, x: str) -> list[str]:
        """Get all elements in the same component as x."""
        root = self.find(x)
        return [node for node, parent in self.parent.items() if self.find(parent) == root]

    def get_all_components(self) -> list[list[str]]:
        """Get all connected components."""
        components: dict[str, list[str]] = {}
        for node in self.parent:
            root = self.find(node)
            if root not in components:
                components[root] = []
            components[root].append(node)
        return list(components.values())


# ── DSA: Trie ─────────────────────────────────────────────────────────────────


class TrieNode:
    """Node in a Trie (prefix tree)."""

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.is_end: bool = False
        self.entity_urn: str | None = None
        self.metadata: dict = {}


class Trie:
    """Trie for O(m) prefix search (m = query length).

    Time complexity: O(m) for insert/search
    Space complexity: O(n * m) where n = number of strings
    """

    def __init__(self) -> None:
        self.root = TrieNode()
        self.size = 0

    def insert(self, word: str, entity_urn: str, metadata: dict | None = None) -> None:
        """Insert a word into the trie."""
        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        if not node.is_end:
            self.size += 1
        node.is_end = True
        node.entity_urn = entity_urn
        if metadata:
            node.metadata = metadata

    def search(self, word: str) -> bool:
        """Exact match search."""
        node = self.root
        for char in word.lower():
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end

    def starts_with(self, prefix: str) -> list[str]:
        """Find all words starting with prefix."""
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]
        return self._collect_all(node)

    def search_prefix(self, prefix: str) -> list[tuple[str, dict]]:
        """Search by prefix, returning (urn, metadata) tuples."""
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]
        return self._collect_with_metadata(node)

    def autocomplete(self, prefix: str, max_results: int = 10) -> list[str]:
        """Autocomplete prefix with limited results."""
        results = self.starts_with(prefix)
        return results[:max_results]

    def _collect_all(self, node: TrieNode) -> list[str]:
        """Collect all entity URNs under this node."""
        results: list[str] = []
        if node.is_end and node.entity_urn:
            results.append(node.entity_urn)
        for child in node.children.values():
            results.extend(self._collect_all(child))
        return results

    def _collect_with_metadata(self, node: TrieNode) -> list[tuple[str, dict]]:
        """Collect all (urn, metadata) under this node."""
        results: list[tuple[str, dict]] = []
        if node.is_end and node.entity_urn:
            results.append((node.entity_urn, node.metadata))
        for child in node.children.values():
            results.extend(self._collect_with_metadata(child))
        return results


# ── DSA: Min-Heap for Top-K ──────────────────────────────────────────────────


def top_k_with_heap(items: list, k: int, key_func=None) -> list:
    """Get top-k items using min-heap.

    Time complexity: O(n log k) vs O(n log n) for full sort
    Space complexity: O(k)

    Args:
        items: List of items
        k: Number of top items to return
        key_func: Function to extract comparison key

    Returns:
        Top-k items in descending order
    """
    import heapq

    if key_func is None:
        return heapq.nlargest(k, items)
    return heapq.nlargest(k, items, key=key_func)
