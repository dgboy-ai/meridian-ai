"""Seed Meridian Commerce demo dataset into DataHub.

Works in both modes:
  - mock: Seeds in-memory data structures
  - real: Creates entities via DataHub Python SDK (GraphQL)

Usage:
  DATAHUB_MOCK=true python scripts/seed_meridian.py   # mock mode
  DATAHUB_MOCK=false python scripts/seed_meridian.py  # real DataHub
"""
import asyncio
import json
import sys
import os
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")


# ── Entity Definitions ────────────────────────────────────────────────────────

DATASETS = [
    {
        "urn": "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
        "name": "raw_events",
        "platform": "snowflake",
        "type": "dataset",
        "description": "Raw user events from Snowflake — clickstream, purchases, signups",
        "owner": "data-engineering",
        "tags": ["meridian-commerce", "production"],
        "fields": [
            {"name": "event_id", "type": "STRING"},
            {"name": "user_id", "type": "STRING"},
            {"name": "user_age", "type": "STRING"},
            {"name": "timestamp", "type": "TIMESTAMP"},
        ],
    },
    {
        "urn": "urn:li:dataset:(urn:li:dataPlatform:dbt,meridian.feature_pipeline,PROD)",
        "name": "feature_pipeline",
        "platform": "dbt",
        "type": "dataset",
        "description": "dbt feature pipeline — transforms raw events into ML features",
        "owner": "data-engineering",
        "tags": ["meridian-commerce", "production"],
        "fields": [
            {"name": "user_id", "type": "STRING"},
            {"name": "age_bucket", "type": "STRING"},
            {"name": "event_frequency", "type": "INT"},
            {"name": "session_duration", "type": "INT"},
        ],
    },
    {
        "urn": "urn:li:dataset:(urn:li:dataPlatform:feast,meridian.feature_store,PROD)",
        "name": "feature_store",
        "platform": "feast",
        "type": "dataset",
        "description": "Feast feature store — serving features for ML models",
        "owner": "ml-platform-team",
        "tags": ["meridian-commerce", "production", "golden"],
        "fields": [
            {"name": "user_id", "type": "STRING"},
            {"name": "age_bucket", "type": "STRING"},
            {"name": "event_frequency", "type": "INT"},
            {"name": "session_duration", "type": "INT"},
        ],
    },
]

MODELS = [
    {
        "urn": "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
        "name": "churn_model_v3",
        "platform": "mlflow",
        "type": "mlModel",
        "description": "XGBoost model predicting 30-day customer churn probability",
        "owner": "ml-platform-team",
        "tags": ["meridian-commerce", "production", "churn"],
        "hyperparameters": {"algorithm": "XGBoost", "max_depth": 6, "n_estimators": 200},
    },
    {
        "urn": "urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
        "name": "ltv_model_v2",
        "platform": "mlflow",
        "type": "mlModel",
        "description": "Customer lifetime value prediction model",
        "owner": "ml-platform-team",
        "tags": ["meridian-commerce", "production", "ltv"],
        "hyperparameters": {"algorithm": "LightGBM", "max_depth": 8},
    },
    {
        "urn": "urn:li:mlModel:(urn:li:dataPlatform:mlflow,segment_model_v1,PROD)",
        "name": "segment_model_v1",
        "platform": "mlflow",
        "type": "mlModel",
        "description": "Customer segmentation model using K-means clustering",
        "owner": "ml-platform-team",
        "tags": ["meridian-commerce", "production", "segmentation"],
        "hyperparameters": {"algorithm": "KMeans", "n_clusters": 5},
    },
]

LINEAGE = [
    # (downstream, upstream) — data flows from upstream to downstream
    ("urn:li:dataset:(urn:li:dataPlatform:dbt,meridian.feature_pipeline,PROD)",
     "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)"),
    ("urn:li:dataset:(urn:li:dataPlatform:feast,meridian.feature_store,PROD)",
     "urn:li:dataset:(urn:li:dataPlatform:dbt,meridian.feature_pipeline,PROD)"),
    ("urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
     "urn:li:dataset:(urn:li:dataPlatform:feast,meridian.feature_store,PROD)"),
    ("urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
     "urn:li:dataset:(urn:li:dataPlatform:feast,meridian.feature_store,PROD)"),
    ("urn:li:mlModel:(urn:li:dataPlatform:mlflow,segment_model_v1,PROD)",
     "urn:li:dataset:(urn:li:dataPlatform:feast,meridian.feature_store,PROD)"),
]

KNOWLEDGE_DOCS = [
    {
        "title": "Incident #12 — Root Cause Report",
        "content": "# Incident #12 — Root Cause Report\nAuto-generated: 2026-03-10 10:33 UTC\n\n## Summary\nSchema change in raw_events.age (INT to STRING) caused churn_model_v3 to degrade from 89% to 71% accuracy.\n\n## Root Cause\nColumn type change broke the age_bucket feature transformation.\n\n## Resolution\nRollback to churn_model_v3 v2.1. Feature pipeline patched. Time to resolve: 18 minutes.",
        "tags": ["incident", "root-cause", "schema-change"],
    },
    {
        "title": "Incident #28 — Root Cause Report",
        "content": "# Incident #28 — Root Cause Report\nAuto-generated: 2026-05-15 14:30 UTC\n\n## Summary\nFeature pipeline freshness violation caused churn_model_v3 to use stale features.\n\n## Root Cause\nAirflow DAG delay of 4 hours due to upstream dependency failure.\n\n## Resolution\nManual pipeline trigger. Added freshness assertion. Time to resolve: 8 minutes.",
        "tags": ["incident", "root-cause", "freshness"],
    },
    {
        "title": "Playbook: Schema Change to Model Degradation",
        "content": "# Playbook: Schema Change to Model Degradation\nPattern ID: schema-change-type-mismatch\nConfidence: 0.96 · Based on: incidents #12, #28, #42\n\n## Detection signals\n- Column type change in upstream dataset\n- Feature pipeline success with silent type coercion\n- Model accuracy drop 2-4 hours after pipeline run\n\n## Fastest resolution (learned from 3 incidents)\n1. Identify changed column via list_schema_fields diff (2 min)\n2. Trace to affected feature via get_lineage (3 min)\n3. Roll back model to last known-good version (2 min)\n4. Patch feature pipeline type casting (5 min)\nTotal: ~12 min first occurrence. ~3 min with this playbook.",
        "tags": ["playbook", "schema-change", "auto-generated"],
    },
]


async def seed_real():
    """Seed entities into a real DataHub instance via Python SDK."""
    try:
        from datahub.ingestion.run.pipeline import Pipeline
        from datahub.emitter.mce_builder import DatasetMCEMetadataBuilder
        from datahub.metadata.schema_classes import (
            DatasetPropertiesClass, SchemaMetadataClass, SchemaFieldClass,
            OwnershipClass, OwnerClass, GlobalTagsClass, TagAssociationClass,
            MLModelPropertiesClass, UpstreamLineageClass, DownstreamLineageClass,
            FineGrainedLineageClass, Upstream, Downstream,
        )
    except ImportError:
        logger.error("DataHub Python SDK not installed. Run: pip install acryl-datahub")
        return False

    gms_url = os.getenv("DATAHUB_GMS_URL", "http://localhost:8080/api/gms")
    logger.info(f"Seeding real DataHub at {gms_url}")

    # Wait for GMS to be ready
    from urllib.request import urlopen
    for attempt in range(30):
        try:
            resp = urlopen(f"{gms_url.replace('/api/gms', '')}/health", timeout=3)
            if resp.status == 200:
                logger.info("DataHub GMS is ready")
                break
        except Exception:
            pass
        logger.info(f"Waiting for DataHub GMS... (attempt {attempt + 1}/30)")
        await asyncio.sleep(3)
    else:
        logger.error("DataHub GMS did not become ready in 90 seconds")
        return False

    # Create datasets using GraphQL
    from urllib.request import Request, urlopen

    for ds in DATASETS:
        mutation = """
        mutation createDataset($input: CreateDatasetInput!) {
            createDataset(input: $input)
        }
        """
        variables = {
            "input": {
                "urn": ds["urn"],
                "datasetProperties": {
                    "name": ds["name"],
                    "description": ds["description"],
                    "platform": ds["platform"],
                },
            }
        }
        body = json.dumps({"query": mutation, "variables": variables}).encode()
        req = Request(
            f"{gms_url.replace('/api/gms', '')}/api/graphql",
            data=body,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        try:
            resp = urlopen(req, timeout=10)
            result = json.loads(resp.read().decode())
            if "errors" not in result:
                logger.info(f"  Created dataset: {ds['name']}")
            else:
                logger.warning(f"  Dataset {ds['name']}: {result.get('errors', [])}")
        except Exception as e:
            logger.warning(f"  Failed to create dataset {ds['name']}: {e}")

    # Create ML models
    for model in MODELS:
        mutation = """
        mutation createMLModel($input: CreateMLModelInput!) {
            createMLModel(input: $input)
        }
        """
        variables = {
            "input": {
                "urn": model["urn"],
                "mlModelProperties": {
                    "name": model["name"],
                    "description": model["description"],
                    "platform": model["platform"],
                    "hyperParameters": model["hyperparameters"],
                },
            }
        }
        body = json.dumps({"query": mutation, "variables": variables}).encode()
        req = Request(
            f"{gms_url.replace('/api/gms', '')}/api/graphql",
            data=body,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        try:
            resp = urlopen(req, timeout=10)
            result = json.loads(resp.read().decode())
            if "errors" not in result:
                logger.info(f"  Created model: {model['name']}")
            else:
                logger.warning(f"  Model {model['name']}: {result.get('errors', [])}")
        except Exception as e:
            logger.warning(f"  Failed to create model {model['name']}: {e}")

    # Create lineage
    for downstream_urn, upstream_urn in LINEAGE:
        mutation = """
        mutation updateLineage($input: UpdateLineageInput!) {
            updateLineage(input: $input)
        }
        """
        variables = {
            "input": {
                "downstreamUrn": downstream_urn,
                "upstreamUrn": upstream_urn,
            }
        }
        body = json.dumps({"query": mutation, "variables": variables}).encode()
        req = Request(
            f"{gms_url.replace('/api/gms', '')}/api/graphql",
            data=body,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        try:
            resp = urlopen(req, timeout=10)
            logger.info(f"  Created lineage: {upstream_urn.split(',')[-2]} -> {downstream_urn.split(',')[-2]}")
        except Exception as e:
            logger.warning(f"  Failed to create lineage: {e}")

    # Create knowledge documents
    for doc in KNOWLEDGE_DOCS:
        mutation = """
        mutation createDocument($input: CreateDocumentInput!) {
            createDocument(input: $input)
        }
        """
        variables = {
            "input": {
                "title": doc["title"],
                "content": doc["content"],
                "tags": doc["tags"],
            }
        }
        body = json.dumps({"query": mutation, "variables": variables}).encode()
        req = Request(
            f"{gms_url.replace('/api/gms', '')}/api/graphql",
            data=body,
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        try:
            resp = urlopen(req, timeout=10)
            logger.info(f"  Created document: {doc['title']}")
        except Exception as e:
            logger.warning(f"  Failed to create document {doc['title']}: {e}")

    logger.info(f"\nSeeded {len(DATASETS)} datasets, {len(MODELS)} models, {len(KNOWLEDGE_DOCS)} documents")
    return True


async def seed_mock():
    """Seed mock data (in-memory)."""
    from backend.clients.datahub_client import DataHubMCPClient
    mcp = DataHubMCPClient(mock=True)

    logger.info("Seeding mock DataHub...")

    for doc in KNOWLEDGE_DOCS:
        await mcp.save_document(**doc)
        logger.info(f"  Created: {doc['title']}")

    logger.info(f"Seeded {len(KNOWLEDGE_DOCS)} documents to mock DataHub")


async def main():
    mock_mode = os.getenv("DATAHUB_MOCK", "true").lower() == "true"

    if mock_mode:
        await seed_mock()
    else:
        success = await seed_real()
        if not success:
            logger.error("Failed to seed real DataHub. Is it running?")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
