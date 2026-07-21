'use client'

import DocsLayout from '../../../components/docs/DocsLayout'
import { DocH1, DocP, DocBadge, DocH2, DocH3, DocCode, DocInfo, DocTable, DocDivider } from '../../../components/docs/DocElements'

export default function GettingStartedPage() {
  return (
    <DocsLayout>
      <DocBadge color="#10b981">Getting Started</DocBadge>
      <DocH1>Quick Start</DocH1>
      <DocP>
        Get Meridian AI running in 30 seconds with zero dependencies, or 5 minutes with real DataHub.
      </DocP>

      <DocH2>Option 1: Mock Mode (30 seconds)</DocH2>
      <DocP>No Docker, no DataHub, no API keys needed. See the full investigation flow instantly.</DocP>
      <DocCode>{`git clone https://github.com/trueboy1123/meridian-ai
cd meridian-ai
pip install -e .
meridian investigate "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"`}</DocCode>
      <DocInfo type="tip">
        This fires 17 workers, generates 17 DataHub mutations, and produces a full investigation
        timeline — all in mock mode. Perfect for judges who want to verify quickly.
      </DocInfo>

      <DocH2>Option 2: API Server (Mock Mode)</DocH2>
      <DocP>Start the FastAPI server and explore via interactive docs.</DocP>
      <DocCode>{`pip install -e .
python -m backend.main
# Open http://localhost:8000/docs`}</DocCode>

      <DocH2>Option 3: Full Stack with Real DataHub (5 minutes)</DocH2>
      <DocP>Run the complete stack with real DataHub, MySQL, Kafka, and Elasticsearch.</DocP>
      <DocCode>{`# Requires Docker Desktop running
docker compose up -d

# Wait ~90s for DataHub
python scripts/seed_meridian.py

# Switch to real mode
export DATAHUB_MOCK=false
export DATAHUB_GMS_URL=http://localhost:8080/api/gms
python -m backend.main`}</DocCode>

      <DocTable
        headers={['URL', 'What It Shows']}
        rows={[
          ['http://localhost:3000', 'Meridian AI — Investigation Dashboard'],
          ['http://localhost:9002', 'DataHub UI — Entity pages, AI Knowledge panel'],
          ['http://localhost:8000/docs', 'FastAPI — Interactive API documentation'],
        ]}
      />

      <DocH2>Option 4: CLI Commands</DocH2>
      <DocP>Meridian provides a full CLI for terminal-based workflows.</DocP>

      <DocH3>Investigate a model</DocH3>
      <DocCode>{`meridian investigate "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"`}</DocCode>

      <DocH3>Check model health</DocH3>
      <DocCode>{`meridian health "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"`}</DocCode>

      <DocH3>View a playbook</DocH3>
      <DocCode>{`meridian playbook schema-change-type-mismatch`}</DocCode>

      <DocH3>Seed demo data</DocH3>
      <DocCode>{`meridian seed`}</DocCode>

      <DocH2>Verify Examples (No Running Needed)</DocH2>
      <DocP>
        Regenerate all example outputs from real worker output. Judges can verify the
        system works without running anything.
      </DocP>
      <DocCode>{`python scripts/regenerate_examples.py
# Check examples/ folder for generated output
cat examples/ai-knowledge/churn_model_v3.json`}</DocCode>

      <DocH2>Environment Variables</DocH2>
      <DocTable
        headers={['Variable', 'Default', 'Description']}
        rows={[
          ['DATAHUB_MOCK', 'true', 'Set to false for real DataHub'],
          ['DATAHUB_GMS_URL', 'http://localhost:8080/api/gms', 'DataHub GMS endpoint'],
          ['GROQ_API_KEY', '(empty)', 'Groq API key for LLM inference'],
          ['LOG_LEVEL', 'INFO', 'Logging level'],
          ['AUTH_ENABLED', 'false', 'Enable JWT authentication'],
          ['MAX_RPM', '60', 'Rate limit: requests per minute'],
        ]}
      />

      <DocDivider />

      <DocH2>What Happens When You Run It</DocH2>
      <DocP>Here&apos;s the investigation flow step by step:</DocP>
      <ol style={{ fontSize: '14px', lineHeight: 2, color: 'rgba(255,255,255,0.6)', paddingLeft: '20px' }}>
        <li><strong style={{ color: '#f43f5e' }}>Data Sentinel</strong> detects schema change in upstream dataset</li>
        <li><strong style={{ color: '#f43f5e' }}>Feature Drift</strong> computes PSI scores per feature</li>
        <li><strong style={{ color: '#f43f5e' }}>Training-Serving Skew</strong> compares schema and distributions</li>
        <li><strong style={{ color: '#f43f5e' }}>Data Leakage</strong> checks for temporal pattern violations</li>
        <li><strong style={{ color: '#8b5cf6' }}>Root Cause</strong> traverses column-level lineage to find why</li>
        <li><strong style={{ color: '#ec4899' }}>VerifierAgent</strong> challenges the root cause conclusion</li>
        <li><strong style={{ color: '#6366f1' }}>Knowledge Writer</strong> writes 5 artifacts back to DataHub</li>
        <li><strong style={{ color: '#10b981' }}>Reflexion Loop</strong> improves playbook for next time</li>
        <li><strong style={{ color: '#06b6d4' }}>EU AI Act</strong> generates SHA-256 audit chain</li>
      </ol>
    </DocsLayout>
  )
}
