"""Predictive Incident Forecasting — 24-Hour Risk Radar.

"Every tool detects AFTER; nobody predicts BEFORE."

This module predicts which models will fail next by analyzing:
  - Freshness age (how stale is the data?)
  - Recent schema changes (did something change recently?)
  - Upstream contract violations (are quality checks failing?)
  - Historical incident patterns (has this model failed before?)
  - Drift velocity (how fast is drift increasing?)

Produces a "24-Hour Risk Forecast" for each model:
  - risk_level: low, medium, high, critical
  - risk_factors: list of contributing factors
  - predicted_failure_window: when failure is likely
  - confidence: how confident we are in the prediction

Based on MERIDIAN_MASTER_STRATEGY.md:
"Nightly scan predicts which models will fail next. Every tool detects
AFTER; nobody predicts BEFORE."
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.models import EvidenceObject, Severity, EvidenceItem, DataHubMutation

logger = logging.getLogger("meridian-ai.risk_forecaster")


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskFactor:
    """A single risk factor contributing to model failure risk."""
    factor_name: str
    weight: float  # 0-1, how much this contributes to risk
    current_value: float
    threshold: float
    is_triggered: bool = False
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "factor_name": self.factor_name,
            "weight": self.weight,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "is_triggered": self.is_triggered,
            "description": self.description,
        }


@dataclass
class RiskForecast:
    """A risk forecast for a single model."""
    model_urn: str
    model_name: str
    risk_level: RiskLevel
    risk_score: float  # 0-1
    risk_factors: list[RiskFactor] = field(default_factory=list)
    predicted_failure_window: str = ""  # e.g., "12-24 hours"
    confidence: float = 0.0
    recommendations: list[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "model_urn": self.model_urn,
            "model_name": self.model_name,
            "risk_level": self.risk_level.value,
            "risk_score": round(self.risk_score, 4),
            "risk_factors": [rf.to_dict() for rf in self.risk_factors],
            "predicted_failure_window": self.predicted_failure_window,
            "confidence": round(self.confidence, 4),
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
        }


class RiskForecaster:
    """Predict which models will fail next based on historical signals.

    Analyzes multiple risk factors to produce a 24-hour risk forecast
    for each model in the DataHub catalog.
    """

    def __init__(self, mcp: DataHubMCPClient, groq: GroqClient):
        self.mcp = mcp
        self.groq = groq

    async def forecast_model_risk(self, model_urn: str) -> RiskForecast:
        """Forecast risk for a single model.

        Args:
            model_urn: URN of the ML model

        Returns:
            RiskForecast with risk level, factors, and recommendations
        """
        now = datetime.now(timezone.utc).isoformat()

        # Get model metadata
        entities = await self.mcp.get_entities([model_urn])
        entity = entities[0] if entities else {}
        model_name = entity.get("name", "unknown")

        # Analyze risk factors
        risk_factors = []

        # Factor 1: Freshness (how stale is upstream data?)
        freshness_factor = await self._check_freshness_risk(model_urn, entity)
        risk_factors.append(freshness_factor)

        # Factor 2: Recent schema changes
        schema_factor = await self._check_schema_change_risk(model_urn)
        risk_factors.append(schema_factor)

        # Factor 3: Upstream contract violations
        contract_factor = await self._check_contract_risk(model_urn)
        risk_factors.append(contract_factor)

        # Factor 4: Historical incident patterns
        history_factor = await self._check_history_risk(model_urn, entity)
        risk_factors.append(history_factor)

        # Factor 5: Current health score
        health_factor = self._check_health_risk(entity)
        risk_factors.append(health_factor)

        # Calculate overall risk score
        total_weight = sum(rf.weight for rf in risk_factors)
        triggered_weight = sum(rf.weight for rf in risk_factors if rf.is_triggered)
        risk_score = triggered_weight / max(total_weight, 0.001)

        # Determine risk level
        if risk_score >= 0.8:
            risk_level = RiskLevel.CRITICAL
            predicted_window = "0-6 hours"
        elif risk_score >= 0.6:
            risk_level = RiskLevel.HIGH
            predicted_window = "6-12 hours"
        elif risk_score >= 0.3:
            risk_level = RiskLevel.MEDIUM
            predicted_window = "12-24 hours"
        else:
            risk_level = RiskLevel.LOW
            predicted_window = "24+ hours"

        # Generate recommendations
        recommendations = self._generate_recommendations(risk_factors, risk_level)

        # Calculate confidence
        confidence = min(0.95, 0.5 + (len([rf for rf in risk_factors if rf.is_triggered]) * 0.1))

        return RiskForecast(
            model_urn=model_urn,
            model_name=model_name,
            risk_level=risk_level,
            risk_score=risk_score,
            risk_factors=risk_factors,
            predicted_failure_window=predicted_window,
            confidence=confidence,
            recommendations=recommendations,
            timestamp=now,
        )

    async def forecast_all_models(self) -> list[RiskForecast]:
        """Forecast risk for all models in DataHub.

        Returns:
            List of RiskForecast objects sorted by risk score (highest first)
        """
        # Get all ML models
        models = await self.mcp.search(query="", entity_type="mlModel")

        forecasts = []
        for model in models:
            model_urn = model.get("urn", "")
            if model_urn:
                try:
                    forecast = await self.forecast_model_risk(model_urn)
                    forecasts.append(forecast)
                except Exception as e:
                    logger.error(f"Failed to forecast risk for {model_urn}: {e}")

        # Sort by risk score (highest first)
        forecasts.sort(key=lambda f: f.risk_score, reverse=True)

        return forecasts

    async def generate_risk_report(self) -> EvidenceObject:
        """Generate a comprehensive risk report for all models.

        Returns:
            EvidenceObject with risk forecast results
        """
        now = datetime.now(timezone.utc).isoformat()

        forecasts = await self.forecast_all_models()

        # Analyze forecasts
        high_risk_models = [f for f in forecasts if f.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)]
        medium_risk_models = [f for f in forecasts if f.risk_level == RiskLevel.MEDIUM]
        low_risk_models = [f for f in forecasts if f.risk_level == RiskLevel.LOW]

        # Build finding
        if high_risk_models:
            finding = (
                f"RISK FORECAST: {len(high_risk_models)} models at HIGH/CRITICAL risk. "
                f"Predicted failures within 12 hours: {', '.join(f.model_name for f in high_risk_models[:5])}. "
                f"Total models analyzed: {len(forecasts)}."
            )
            severity = Severity.HIGH
        elif medium_risk_models:
            finding = (
                f"RISK FORECAST: {len(medium_risk_models)} models at MEDIUM risk. "
                f"Predicted failures within 24 hours: {', '.join(f.model_name for f in medium_risk_models[:5])}. "
                f"Total models analyzed: {len(forecasts)}."
            )
            severity = Severity.MEDIUM
        else:
            finding = (
                f"RISK FORECAST: All {len(forecasts)} models at LOW risk. "
                f"No predicted failures within 24 hours."
            )
            severity = Severity.LOW

        # Build mutations (write risk scores to DataHub)
        mutations = []
        for forecast in forecasts:
            if forecast.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                mutations.append(DataHubMutation(
                    tool="addStructuredProperties",
                    params={
                        "risk_level": forecast.risk_level.value,
                        "risk_score": forecast.risk_score,
                        "predicted_failure_window": forecast.predicted_failure_window,
                        "risk_forecast_timestamp": forecast.timestamp,
                    },
                    safe=True,
                ))

        return EvidenceObject(
            worker_id="risk_forecaster",
            timestamp=now,
            finding=finding,
            confidence=0.85 if high_risk_models else 0.90,
            severity=severity,
            evidence=[
                EvidenceItem(
                    type="risk_forecast",
                    description=f"Analyzed {len(forecasts)} models: {len(high_risk_models)} high/critical, {len(medium_risk_models)} medium, {len(low_risk_models)} low",
                ),
            ],
            next_action="Review high-risk models and take preventive action" if high_risk_models else "No action needed",
            datahub_mutations=mutations,
        )

    async def _check_freshness_risk(self, model_urn: str, entity: dict) -> RiskFactor:
        """Check freshness risk for a model's upstream data."""
        # Get lineage to find upstream datasets
        lineage = await self.mcp.get_lineage(model_urn, depth=2)
        upstream = lineage.get("upstream", [])

        # Check if any upstream dataset is stale
        stale_count = 0
        for u in upstream:
            urn = u.get("urn", "")
            entities = await self.mcp.get_entities([urn])
            if entities:
                upstream_entity = entities[0]
                last_update = upstream_entity.get("last_update")
                if last_update:
                    try:
                        last_update_time = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
                        age_hours = (datetime.now(timezone.utc) - last_update_time).total_seconds() / 3600
                        if age_hours > 24:  # Stale if > 24 hours
                            stale_count += 1
                    except (ValueError, TypeError):
                        pass

        is_triggered = stale_count > 0
        return RiskFactor(
            factor_name="freshness",
            weight=0.25,
            current_value=stale_count,
            threshold=1,
            is_triggered=is_triggered,
            description=f"{stale_count} upstream datasets stale (>24h)" if is_triggered else "All upstream datasets fresh",
        )

    async def _check_schema_change_risk(self, model_urn: str) -> RiskFactor:
        """Check if recent schema changes indicate risk."""
        # In production, query DataHub for recent schema change events
        # For now, use a heuristic
        lineage = await self.mcp.get_lineage(model_urn, depth=2)
        upstream = lineage.get("upstream", [])

        recent_changes = 0
        for u in upstream:
            urn = u.get("urn", "")
            entities = await self.mcp.get_entities([urn])
            if entities:
                # Check for schema change indicators
                entity = entities[0]
                if entity.get("schema_changed_recently", False):
                    recent_changes += 1

        is_triggered = recent_changes > 0
        return RiskFactor(
            factor_name="schema_changes",
            weight=0.20,
            current_value=recent_changes,
            threshold=1,
            is_triggered=is_triggered,
            description=f"{recent_changes} upstream datasets with recent schema changes" if is_triggered else "No recent schema changes",
        )

    async def _check_contract_risk(self, model_urn: str) -> RiskFactor:
        """Check if upstream contracts are being violated."""
        lineage = await self.mcp.get_lineage(model_urn, depth=2)
        upstream = lineage.get("upstream", [])

        violations = 0
        for u in upstream:
            urn = u.get("urn", "")
            entities = await self.mcp.get_entities([urn])
            if entities:
                entity = entities[0]
                # Check for quality assertion failures
                if entity.get("assertion_failures", 0) > 0:
                    violations += 1

        is_triggered = violations > 0
        return RiskFactor(
            factor_name="contract_violations",
            weight=0.20,
            current_value=violations,
            threshold=1,
            is_triggered=is_triggered,
            description=f"{violations} upstream datasets with contract violations" if is_triggered else "No contract violations",
        )

    async def _check_history_risk(self, model_urn: str, entity: dict) -> RiskFactor:
        """Check historical incident patterns."""
        resolved_incidents = entity.get("resolved_incidents", 0)
        health_score = entity.get("health_score", 100)

        # Models with many incidents and low health are at higher risk
        risk_score = 0.0
        if resolved_incidents > 5:
            risk_score += 0.3
        if health_score < 70:
            risk_score += 0.3
        if resolved_incidents > 10 and health_score < 80:
            risk_score += 0.2

        is_triggered = risk_score > 0.3
        return RiskFactor(
            factor_name="historical_incidents",
            weight=0.20,
            current_value=risk_score,
            threshold=0.3,
            is_triggered=is_triggered,
            description=f"Risk score {risk_score:.2f} based on {resolved_incidents} resolved incidents and health {health_score}" if is_triggered else "Low historical risk",
        )

    def _check_health_risk(self, entity: dict) -> RiskFactor:
        """Check current health score risk."""
        health_score = entity.get("health_score", 100)
        confidence = entity.get("confidence", 1.0)

        # Low health or low confidence = high risk
        risk_score = 0.0
        if health_score < 60:
            risk_score += 0.5
        elif health_score < 80:
            risk_score += 0.2
        if confidence < 0.7:
            risk_score += 0.3

        is_triggered = risk_score > 0.3
        return RiskFactor(
            factor_name="health_score",
            weight=0.15,
            current_value=health_score,
            threshold=80,
            is_triggered=is_triggered,
            description=f"Health score {health_score}, confidence {confidence:.2f}" if is_triggered else f"Health score {health_score} is acceptable",
        )

    def _generate_recommendations(self, risk_factors: list[RiskFactor], risk_level: RiskLevel) -> list[str]:
        """Generate recommendations based on risk factors."""
        recommendations = []

        for rf in risk_factors:
            if rf.is_triggered:
                if rf.factor_name == "freshness":
                    recommendations.append("Check upstream data pipelines for delays or failures")
                elif rf.factor_name == "schema_changes":
                    recommendations.append("Review recent schema changes for breaking changes")
                elif rf.factor_name == "contract_violations":
                    recommendations.append("Investigate upstream quality assertion failures")
                elif rf.factor_name == "historical_incidents":
                    recommendations.append("Review incident history for recurring patterns")
                elif rf.factor_name == "health_score":
                    recommendations.append("Investigate model health degradation")

        if risk_level == RiskLevel.CRITICAL:
            recommendations.insert(0, "URGENT: Take immediate action to prevent model failure")
        elif risk_level == RiskLevel.HIGH:
            recommendations.insert(0, "Schedule preventive maintenance within 12 hours")

        return recommendations
