"""Training Data Provenance — records which training data version produced the model.

"Reproducing a model's training run six months later is harder than most teams assume.
The source data shifted, the transformation logic evolved, the feature definitions drifted."

This module:
  - Records training dataset version (which snapshot was used)
  - Records transformation logic (which dbt model, which version)
  - Records feature definitions (which columns, which transformations)
  - Records model version (which MLflow run)
  - Links to upstream lineage (which source tables, which dbt models)
  - Enables "reproduce this model" workflow
"""
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger("meridian-ai.training_provenance")


@dataclass
class TrainingDataVersion:
    """Version information for training data."""
    dataset_urn: str
    dataset_name: str
    version: str = ""  # e.g., snapshot ID, git commit, Airflow run ID
    snapshot_time: str = ""
    row_count: int = 0
    schema_hash: str = ""  # Hash of schema fields for change detection
    lineage_urns: list[str] = field(default_factory=list)  # Upstream lineage

    def to_dict(self) -> dict:
        return {
            "dataset_urn": self.dataset_urn,
            "dataset_name": self.dataset_name,
            "version": self.version,
            "snapshot_time": self.snapshot_time,
            "row_count": self.row_count,
            "schema_hash": self.schema_hash,
            "lineage_urns": self.lineage_urns,
        }


@dataclass
class TransformationVersion:
    """Version information for a transformation (dbt model, Spark job, etc.)."""
    transformation_urn: str
    transformation_name: str
    transformation_type: str  # "dbt", "spark", "airflow", "custom"
    version: str = ""  # e.g., git commit, Airflow run ID
    sql_hash: str = ""  # Hash of transformation logic
    inputs: list[str] = field(default_factory=list)  # Input dataset URNs
    outputs: list[str] = field(default_factory=list)  # Output dataset URNs

    def to_dict(self) -> dict:
        return {
            "transformation_urn": self.transformation_urn,
            "transformation_name": self.transformation_name,
            "transformation_type": self.transformation_type,
            "version": self.version,
            "sql_hash": self.sql_hash,
            "inputs": self.inputs,
            "outputs": self.outputs,
        }


@dataclass
class FeatureDefinition:
    """Definition of a feature used in training."""
    feature_name: str
    source_column: str
    source_dataset: str
    transformation: str = ""  # e.g., "CAST(age AS INT)", "BUCKET(session_duration, 30)"
    data_type: str = ""
    is_derived: bool = False  # True if this feature is computed from other features

    def to_dict(self) -> dict:
        return {
            "feature_name": self.feature_name,
            "source_column": self.source_column,
            "source_dataset": self.source_dataset,
            "transformation": self.transformation,
            "data_type": self.data_type,
            "is_derived": self.is_derived,
        }


@dataclass
class ModelTrainingVersion:
    """Complete training provenance for a model."""
    model_urn: str
    model_name: str
    training_run_id: str = ""
    training_time: str = ""
    framework: str = ""  # "mlflow", "sagemaker", "custom"
    # Training data
    training_datasets: list[TrainingDataVersion] = field(default_factory=list)
    # Transformations
    transformations: list[TransformationVersion] = field(default_factory=list)
    # Features
    features: list[FeatureDefinition] = field(default_factory=list)
    # Model metadata
    algorithm: str = ""
    hyperparameters: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    # Lineage
    upstream_lineage: list[str] = field(default_factory=list)
    # Hashes for change detection
    training_data_hash: str = ""
    feature_hash: str = ""

    def to_dict(self) -> dict:
        return {
            "model_urn": self.model_urn,
            "model_name": self.model_name,
            "training_run_id": self.training_run_id,
            "training_time": self.training_time,
            "framework": self.framework,
            "training_datasets": [td.to_dict() for td in self.training_datasets],
            "transformations": [t.to_dict() for t in self.transformations],
            "features": [f.to_dict() for f in self.features],
            "algorithm": self.algorithm,
            "hyperparameters": self.hyperparameters,
            "metrics": self.metrics,
            "upstream_lineage": self.upstream_lineage,
            "training_data_hash": self.training_data_hash,
            "feature_hash": self.feature_hash,
            "reproducibility_score": self.calculate_reproducibility_score(),
        }

    def calculate_reproducibility_score(self) -> float:
        """Calculate how reproducible this model is (0-1)."""
        score = 0.0
        # Has training data version?
        if self.training_datasets:
            score += 0.3
        # Has transformation versions?
        if self.transformations:
            score += 0.2
        # Has feature definitions?
        if self.features:
            score += 0.2
        # Has hyperparameters?
        if self.hyperparameters:
            score += 0.15
        # Has metrics?
        if self.metrics:
            score += 0.15
        return round(score, 2)


class TrainingProvenanceManager:
    """Manage training provenance for ML models."""

    def __init__(self):
        self._provenance: dict[str, ModelTrainingVersion] = {}

    def record_training(
        self,
        model_urn: str,
        model_name: str,
        training_run_id: str = "",
        framework: str = "mlflow",
        algorithm: str = "",
        hyperparameters: dict | None = None,
        metrics: dict | None = None,
        training_datasets: list[dict] | None = None,
        transformations: list[dict] | None = None,
        features: list[dict] | None = None,
        upstream_lineage: list[str] | None = None,
    ) -> ModelTrainingVersion:
        """Record training provenance for a model."""
        now = datetime.now(timezone.utc).isoformat()

        # Parse training datasets
        td_versions = []
        if training_datasets:
            for td in training_datasets:
                td_versions.append(TrainingDataVersion(
                    dataset_urn=td.get("urn", ""),
                    dataset_name=td.get("name", ""),
                    version=td.get("version", ""),
                    snapshot_time=td.get("snapshot_time", now),
                    row_count=td.get("row_count", 0),
                    schema_hash=td.get("schema_hash", ""),
                    lineage_urns=td.get("lineage_urns", []),
                ))

        # Parse transformations
        t_versions = []
        if transformations:
            for t in transformations:
                t_versions.append(TransformationVersion(
                    transformation_urn=t.get("urn", ""),
                    transformation_name=t.get("name", ""),
                    transformation_type=t.get("type", "custom"),
                    version=t.get("version", ""),
                    sql_hash=t.get("sql_hash", ""),
                    inputs=t.get("inputs", []),
                    outputs=t.get("outputs", []),
                ))

        # Parse features
        feature_defs = []
        if features:
            for f in features:
                feature_defs.append(FeatureDefinition(
                    feature_name=f.get("name", ""),
                    source_column=f.get("source_column", ""),
                    source_dataset=f.get("source_dataset", ""),
                    transformation=f.get("transformation", ""),
                    data_type=f.get("data_type", ""),
                    is_derived=f.get("is_derived", False),
                ))

        # Compute hashes for change detection
        training_data_str = json.dumps([td.get("urn", "") for td in (training_datasets or [])], sort_keys=True)
        training_data_hash = hashlib.sha256(training_data_str.encode()).hexdigest()[:16]

        feature_str = json.dumps([f.get("name", "") for f in (features or [])], sort_keys=True)
        feature_hash = hashlib.sha256(feature_str.encode()).hexdigest()[:16]

        provenance = ModelTrainingVersion(
            model_urn=model_urn,
            model_name=model_name,
            training_run_id=training_run_id,
            training_time=now,
            framework=framework,
            training_datasets=td_versions,
            transformations=t_versions,
            features=feature_defs,
            algorithm=algorithm,
            hyperparameters=hyperparameters or {},
            metrics=metrics or {},
            upstream_lineage=upstream_lineage or [],
            training_data_hash=training_data_hash,
            feature_hash=feature_hash,
        )

        self._provenance[model_urn] = provenance
        return provenance

    def get_provenance(self, model_urn: str) -> ModelTrainingVersion | None:
        """Get training provenance for a model."""
        return self._provenance.get(model_urn)

    def has_data_changed(self, model_urn: str, new_data_hash: str) -> bool:
        """Check if training data has changed since last training."""
        provenance = self._provenance.get(model_urn)
        if not provenance:
            return True  # Unknown = assume changed
        return provenance.training_data_hash != new_data_hash

    def has_features_changed(self, model_urn: str, new_feature_hash: str) -> bool:
        """Check if features have changed since last training."""
        provenance = self._provenance.get(model_urn)
        if not provenance:
            return True  # Unknown = assume changed
        return provenance.feature_hash != new_feature_hash

    def get_reproducibility_report(self, model_urn: str) -> dict:
        """Generate a reproducibility report for a model."""
        provenance = self._provenance.get(model_urn)
        if not provenance:
            return {
                "model_urn": model_urn,
                "reproducible": False,
                "reason": "No training provenance recorded",
                "score": 0.0,
            }

        score = provenance.calculate_reproducibility_score()
        missing = []
        if not provenance.training_datasets:
            missing.append("training_datasets")
        if not provenance.transformations:
            missing.append("transformations")
        if not provenance.features:
            missing.append("feature_definitions")
        if not provenance.hyperparameters:
            missing.append("hyperparameters")

        return {
            "model_urn": model_urn,
            "model_name": provenance.model_name,
            "reproducible": score >= 0.7,
            "score": score,
            "missing": missing,
            "training_data_hash": provenance.training_data_hash,
            "feature_hash": provenance.feature_hash,
            "training_time": provenance.training_time,
            "framework": provenance.framework,
        }

    def to_dict(self) -> dict:
        """Export all provenance data."""
        return {
            model_urn: prov.to_dict()
            for model_urn, prov in self._provenance.items()
        }
