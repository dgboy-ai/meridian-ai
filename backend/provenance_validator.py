"""Agent Provenance Validation — validates context before LLM calls.

"Agents without provenance are hallucination factories."

This module validates that every piece of context delivered to an agent has:
  1. Clear source metadata (where did this come from?)
  2. Freshness verification (is it from today or last year?)
  3. Source trust scoring (is it from DataHub or a stale wiki?)
  4. Reliability scoring (source trust + freshness)
  5. Rejection of low-reliability context before it reaches the model

Based on DataHub's context management pattern:
"Every piece of context delivered to an agent should carry metadata about
its source, freshness, and the policies that permitted access."
"""
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger("meridian-ai.provenance_validator")


@dataclass
class ContextSource:
    """A source of context for an agent."""
    source_id: str
    source_type: str  # "datahub_metadata", "datahub_lineage", "datahub_document", etc.
    source_urn: str = ""
    source_name: str = ""
    retrieved_at: float = 0.0
    freshness_seconds: float = 0.0
    confidence: float = 1.0
    verified: bool = True
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "source_urn": self.source_urn,
            "source_name": self.source_name,
            "retrieved_at": self.retrieved_at,
            "freshness_seconds": round(self.freshness_seconds, 2),
            "confidence": self.confidence,
            "verified": self.verified,
        }


@dataclass
class ValidationResult:
    """Result of validating a context source."""
    source_id: str
    is_valid: bool
    reliability_score: float
    issues: list[str] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "is_valid": self.is_valid,
            "reliability_score": round(self.reliability_score, 4),
            "issues": self.issues,
            "recommendation": self.recommendation,
        }


class ProvenanceValidator:
    """Validate context sources before delivering to LLM agents.

    Prevents hallucinations by ensuring context is:
    - Fresh (not stale)
    - Sourced (from trusted systems)
    - Verified (validated against DataHub)
    """

    # Source trust scores (0-1)
    SOURCE_TRUST = {
        "datahub_metadata": 0.95,
        "datahub_lineage": 0.95,
        "datahub_document": 0.90,
        "datahub_playbook": 0.85,
        "schema_diff": 0.99,
        "statistical_computation": 0.99,
        "llm_inference": 0.60,
        "user_input": 0.70,
        "hardcoded_config": 0.80,
    }

    # Freshness thresholds (seconds)
    FRESHNESS_THRESHOLDS = {
        "datahub_metadata": 3600,      # 1 hour
        "datahub_lineage": 3600,       # 1 hour
        "datahub_document": 86400,     # 24 hours
        "datahub_playbook": 604800,    # 7 days
        "schema_diff": 300,            # 5 minutes
        "statistical_computation": 300, # 5 minutes
        "llm_inference": 3600,         # 1 hour
        "user_input": 0,               # Always fresh
        "hardcoded_config": 86400,     # 24 hours
    }

    def __init__(self):
        self._validation_cache: dict[str, ValidationResult] = {}

    def validate_source(self, source: ContextSource) -> ValidationResult:
        """Validate a single context source.

        Args:
            source: The context source to validate

        Returns:
            ValidationResult with reliability score and issues
        """
        issues = []

        # Check 1: Source trust
        trust_score = self.SOURCE_TRUST.get(source.source_type, 0.5)
        if trust_score < 0.7:
            issues.append(f"Low trust source: {source.source_type} (trust={trust_score})")

        # Check 2: Freshness
        freshness_threshold = self.FRESHNESS_THRESHOLDS.get(source.source_type, 3600)
        if source.freshness_seconds > freshness_threshold:
            issues.append(
                f"Stale context: {source.freshness_seconds:.0f}s old "
                f"(threshold: {freshness_threshold}s)"
            )

        # Check 3: Verification status
        if not source.verified:
            issues.append("Context not verified against DataHub")

        # Check 4: Confidence
        if source.confidence < 0.7:
            issues.append(f"Low confidence: {source.confidence:.2f}")

        # Calculate reliability score
        freshness_factor = max(0, 1.0 - (source.freshness_seconds / (freshness_threshold * 2)))
        verification_factor = 1.0 if source.verified else 0.5
        confidence_factor = source.confidence

        reliability_score = (
            trust_score * 0.3 +
            freshness_factor * 0.3 +
            verification_factor * 0.2 +
            confidence_factor * 0.2
        )

        # Determine if valid
        is_valid = reliability_score >= 0.6 and len(issues) == 0

        # Generate recommendation
        if not is_valid:
            if issues:
                recommendation = f"Reject context: {'; '.join(issues)}"
            else:
                recommendation = "Context reliability too low"
        else:
            recommendation = "Context validated — safe to deliver to agent"

        return ValidationResult(
            source_id=source.source_id,
            is_valid=is_valid,
            reliability_score=reliability_score,
            issues=issues,
            recommendation=recommendation,
        )

    def validate_context_batch(self, sources: list[ContextSource]) -> dict:
        """Validate a batch of context sources.

        Args:
            sources: List of context sources to validate

        Returns:
            Summary of validation results
        """
        results = []
        valid_count = 0
        invalid_count = 0
        total_reliability = 0.0

        for source in sources:
            result = self.validate_source(source)
            results.append(result)
            total_reliability += result.reliability_score

            if result.is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                logger.warning(
                    f"Invalid context source: {source.source_id} "
                    f"({source.source_type}): {'; '.join(result.issues)}"
                )

        avg_reliability = total_reliability / max(len(sources), 1)

        return {
            "total_sources": len(sources),
            "valid_sources": valid_count,
            "invalid_sources": invalid_count,
            "average_reliability": round(avg_reliability, 4),
            "overall_valid": invalid_count == 0,
            "results": [r.to_dict() for r in results],
        }

    def should_reject_context(self, sources: list[ContextSource]) -> tuple[bool, list[str]]:
        """Determine if context should be rejected before reaching LLM.

        Args:
            sources: List of context sources to check

        Returns:
            Tuple of (should_reject, reasons)
        """
        validation = self.validate_context_batch(sources)

        if validation["invalid_sources"] > 0:
            reasons = [
                f"{r['source_id']}: {'; '.join(r['issues'])}"
                for r in validation["results"]
                if not r["is_valid"]
            ]
            return True, reasons

        if validation["average_reliability"] < 0.5:
            return True, [f"Average reliability too low: {validation['average_reliability']:.2f}"]

        return False, []

    def get_source_trust(self, source_type: str) -> float:
        """Get trust score for a source type."""
        return self.SOURCE_TRUST.get(source_type, 0.5)

    def get_freshness_threshold(self, source_type: str) -> float:
        """Get freshness threshold for a source type."""
        return self.FRESHNESS_THRESHOLDS.get(source_type, 3600)
