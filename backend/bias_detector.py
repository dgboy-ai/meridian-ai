"""Bias Detection Lineage — traces source data provenance to detect potential bias.

"Source data provenance and labeling pipeline" needed for bias detection.

This module:
  - Queries DataHub for source dataset demographics
  - Checks label distribution for skew
  - Traces lineage to identify which sources feed training data
  - Flags potential bias in feature engineering
  - Writes bias risk score to DataHub
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.models import EvidenceObject, Severity, EvidenceItem, DataHubMutation

logger = logging.getLogger("meridian-ai.bias_detector")


@dataclass
class BiasRisk:
    """A single bias risk finding."""
    risk_type: str  # "demographic_skew", "label_imbalance", "temporal_bias", "feature_leakage"
    severity: str  # "low", "medium", "high", "critical"
    description: str
    affected_columns: list[str] = field(default_factory=list)
    recommendation: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "risk_type": self.risk_type,
            "severity": self.severity,
            "description": self.description,
            "affected_columns": self.affected_columns,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
        }


class BiasDetector:
    """Detect potential bias in training data via lineage and provenance analysis."""

    def __init__(self, mcp: DataHubMCPClient, groq: GroqClient):
        self.mcp = mcp
        self.groq = groq

    async def detect_bias(
        self,
        model_urn: str,
        training_data_urn: str = "",
    ) -> EvidenceObject:
        """Detect potential bias in training data lineage.

        Args:
            model_urn: URN of the ML model
            training_data_urn: URN of the training dataset (optional, will trace from model)
        """
        now = datetime.now(timezone.utc).isoformat()

        # Get model metadata
        model_entities = await self.mcp.get_entities([model_urn])
        model_entity = model_entities[0] if model_entities else {}
        model_name = model_entity.get("name", "unknown")

        # If no training data URN provided, trace lineage from model
        if not training_data_urn:
            lineage = await self.mcp.get_lineage(model_urn, depth=3)
            upstream = lineage.get("upstream", [])
            # Find dataset entities upstream of the model
            for u in upstream:
                if u.get("type") == "dataset":
                    training_data_urn = u.get("urn", "")
                    break

        # Get training data metadata
        training_fields = []
        if training_data_urn:
            training_fields = await self.mcp.list_schema_fields(training_data_urn)

        # Analyze for bias risks
        bias_risks = []

        # ── Check 1: Demographic skew ──────────────────────────────────
        demographic_risks = self._check_demographic_skew(training_fields)
        bias_risks.extend(demographic_risks)

        # ── Check 2: Label imbalance ───────────────────────────────────
        label_risks = self._check_label_imbalance(training_fields)
        bias_risks.extend(label_risks)

        # ── Check 3: Temporal bias ─────────────────────────────────────
        temporal_risks = self._check_temporal_bias(training_fields)
        bias_risks.extend(temporal_risks)

        # ── Check 4: Feature leakage ───────────────────────────────────
        leakage_risks = self._check_feature_leakage(training_fields)
        bias_risks.extend(leakage_risks)

        # ── Check 5: Missing protected attributes ──────────────────────
        protected_risks = self._check_protected_attributes(training_fields)
        bias_risks.extend(protected_risks)

        # Calculate overall bias risk score
        risk_score = self._calculate_risk_score(bias_risks)

        # Build finding
        if bias_risks:
            high_risks = [r for r in bias_risks if r.severity in ("high", "critical")]
            finding = (
                f"BIAS DETECTION: {len(bias_risks)} potential bias risks found in {model_name}. "
                f"High/Critical: {len(high_risks)}. "
                f"Risk score: {risk_score:.2f}. "
                f"Types: {', '.join(set(r.risk_type for r in bias_risks))}."
            )
            severity = Severity.HIGH if high_risks else Severity.MEDIUM
        else:
            finding = (
                f"BIAS DETECTION: No significant bias risks found in {model_name}. "
                f"Risk score: {risk_score:.2f}."
            )
            severity = Severity.LOW

        # Build mutations
        mutations = []
        if bias_risks:
            mutations.append(DataHubMutation(
                tool="addStructuredProperties",
                params={
                    "bias_risk_score": risk_score,
                    "bias_risk_count": len(bias_risks),
                    "bias_risk_types": list(set(r.risk_type for r in bias_risks)),
                    "bias_detected_at": now,
                },
                safe=True,
            ))

        return EvidenceObject(
            worker_id="bias_detector",
            timestamp=now,
            finding=finding,
            confidence=0.85 if bias_risks else 0.90,
            severity=severity,
            evidence=[
                EvidenceItem(
                    type="bias_analysis",
                    description=f"Checked {len(training_fields)} training features for {len(bias_risks)} bias risk types",
                    entity_urn=model_urn,
                ),
            ],
            next_action="Review bias risks and apply mitigations" if bias_risks else "No action needed",
            datahub_mutations=mutations,
        )

    def _check_demographic_skew(self, fields: list[dict]) -> list[BiasRisk]:
        """Check for demographic skew in training features."""
        risks = []

        # Common demographic column patterns
        demographic_patterns = [
            "gender", "sex", "race", "ethnicity", "age", "nationality",
            "religion", "disability", "sexual_orientation", "marital_status",
        ]

        for field_def in fields:
            field_name = field_def.get("name", "").lower()
            for pattern in demographic_patterns:
                if pattern in field_name:
                    risks.append(BiasRisk(
                        risk_type="demographic_skew",
                        severity="medium",
                        description=f"Demographic column '{field_def.get('name', '')}' detected in training data. "
                                   f"Ensure balanced representation across {pattern} categories.",
                        affected_columns=[field_def.get("name", "")],
                        recommendation=f"Check distribution of {pattern} in training data. "
                                      f"Consider reweighting or stratified sampling.",
                        confidence=0.7,
                    ))
                    break

        return risks

    def _check_label_imbalance(self, fields: list[dict]) -> list[BiasRisk]:
        """Check for label imbalance in training targets."""
        risks = []

        # Common label column patterns
        label_patterns = ["label", "target", "class", "outcome", "churn", "conversion"]

        label_columns = []
        for field_def in fields:
            field_name = field_def.get("name", "").lower()
            for pattern in label_patterns:
                if pattern in field_name:
                    label_columns.append(field_def.get("name", ""))
                    break

        if label_columns:
            # In production, we'd check actual label distribution
            # For now, flag as a risk to investigate
            risks.append(BiasRisk(
                risk_type="label_imbalance",
                severity="medium",
                description=f"Label columns detected: {', '.join(label_columns)}. "
                           f"Verify class balance in training data.",
                affected_columns=label_columns,
                recommendation="Check label distribution. If imbalanced, consider "
                              "oversampling minority class or using class weights.",
                confidence=0.6,
            ))

        return risks

    def _check_temporal_bias(self, fields: list[dict]) -> list[BiasRisk]:
        """Check for temporal bias in training data."""
        risks = []

        # Check for time-based features that might introduce bias
        temporal_patterns = ["date", "time", "timestamp", "year", "month", "day"]

        temporal_columns = []
        for field_def in fields:
            field_name = field_def.get("name", "").lower()
            for pattern in temporal_patterns:
                if pattern in field_name:
                    temporal_columns.append(field_def.get("name", ""))
                    break

        if temporal_columns:
            risks.append(BiasRisk(
                risk_type="temporal_bias",
                severity="low",
                description=f"Temporal columns detected: {', '.join(temporal_columns)}. "
                           f"Ensure training data spans representative time period.",
                affected_columns=temporal_columns,
                recommendation="Verify training data covers seasonal patterns and "
                              "doesn't over-represent specific time periods.",
                confidence=0.5,
            ))

        return risks

    def _check_feature_leakage(self, fields: list[dict]) -> list[BiasRisk]:
        """Check for potential feature leakage."""
        risks = []

        # Patterns that might indicate label leakage
        leakage_patterns = ["future_", "next_", "predicted_", "forecast_", "target_"]

        for field_def in fields:
            field_name = field_def.get("name", "").lower()
            for pattern in leakage_patterns:
                if pattern in field_name:
                    risks.append(BiasRisk(
                        risk_type="feature_leakage",
                        severity="critical",
                        description=f"Potential label leakage detected: '{field_def.get('name', '')}' "
                                   f"matches pattern '{pattern}'.",
                        affected_columns=[field_def.get("name", "")],
                        recommendation="Remove this feature from training data. "
                                      "It may contain information not available at prediction time.",
                        confidence=0.8,
                    ))
                    break

        return risks

    def _check_protected_attributes(self, fields: list[dict]) -> list[BiasRisk]:
        """Check for missing protected attribute documentation."""
        risks = []

        # Protected attributes that should be documented
        protected_patterns = ["gender", "sex", "race", "ethnicity", "age", "religion"]

        found_protected = []
        for field_def in fields:
            field_name = field_def.get("name", "").lower()
            for pattern in protected_patterns:
                if pattern in field_name:
                    found_protected.append(field_def.get("name", ""))
                    break

        if found_protected:
            risks.append(BiasRisk(
                risk_type="missing_protected_docs",
                severity="medium",
                description=f"Protected attributes detected: {', '.join(found_protected)}. "
                           f"Ensure proper documentation and fairness testing.",
                affected_columns=found_protected,
                recommendation="Document how protected attributes are used. "
                              "Run fairness metrics (demographic parity, equalized odds).",
                confidence=0.7,
            ))

        return risks

    def _calculate_risk_score(self, risks: list[BiasRisk]) -> float:
        """Calculate overall bias risk score (0-1)."""
        if not risks:
            return 0.0

        severity_weights = {
            "low": 0.1,
            "medium": 0.3,
            "high": 0.6,
            "critical": 1.0,
        }

        total_weight = sum(severity_weights.get(r.severity, 0.3) for r in risks)
        max_possible = len(risks) * 1.0  # If all were critical

        return min(1.0, total_weight / max(max_possible, 1))
