# Meridian AI — Quick Start for DataHub Users

> **One command to see it work.** No configuration needed for demo mode.

## For Judges (5 Minutes)

### Option A: Zero Setup (Mock Mode)

```bash
git clone https://github.com/trueboy1123/meridian-ai
cd meridian-ai
pip install -e .
python -m backend.main
```

Open http://localhost:8000/docs — run the investigation endpoint. See 17 workers fire, see DataHub mutations happen.

### Option B: With Real DataHub (Docker)

```bash
docker compose up -d
# Wait 90 seconds
python scripts/seed_meridian.py
python -m backend.main
```

Open http://localhost:9002 — see real entities in DataHub UI.
Open http://localhost:8000/docs — run investigation.
Switch back to DataHub — see the entity page changed.

### Option C: Just Read the Output

```bash
python scripts/regenerate_examples.py
cat examples/ai-knowledge/churn_model_v3.json
# Shows resolved_incidents: 15 (increments each investigation)
```

---

## For DataHub Admins (Your Real Workflow)

### What Problem Does This Solve?

You have ML models in production. When they break:
1. You don't know for 3 days
2. Investigation takes 30+ minutes
3. The knowledge disappears after the fix
4. Next time, you start from zero

Meridian AI fixes all 4:
1. Schema change → auto-investigation in 8 seconds
2. Investigation completes in 8 minutes (first time), 3 minutes (with playbook)
3. Everything written back to DataHub permanently
4. Playbooks improve after every incident

### How It Fits Your DataHub Stack

```
Your DataHub                    Meridian AI
─────────────                   ────────────
Entities (MLModel, Dataset)  ←  Reads schema, lineage, ownership
Ingestion (Airflow, dbt)     ←  Monitors for changes
Assertions (quality checks)  ←  Triggers on failures
Incidents (lifecycle)        →  Auto-raises incidents
Knowledge Base               →  Writes root cause reports
Structured Properties        →  Updates AI Knowledge panel
Tags                         →  Tags affected assets
```

### Day 1: Install and Try

```bash
pip install datahub-meridian-ai
```

### Day 2: Configure for Your Models

```bash
export DATAHUB_GMS_URL=http://your-datahub:8080/api/gms
export DATAHUB_GMS_TOKEN=your-token
```

### Production: Use Service Accounts (Not PATs)

For production deployments and autonomous agents, **always use service accounts** instead of personal access tokens (PATs).

**Why service accounts?**
- PATs belong to individual humans — they expire when the employee leaves
- Service accounts belong to systems — they persist and can be audited
- Service accounts support **Default Views** (DataHub v1.0.0+) — scope agent visibility to specific domains

**How to set up:**

1. Create a service account in DataHub:
   - Go to Settings → Users & Groups → Service Accounts
   - Create a new service account (e.g., `meridian-ai-agent`)

2. Generate an access token for the service account

3. Configure Meridian AI:
   ```bash
   export DATAHUB_GMS_URL=http://your-datahub:8080/api/gms
   export DATAHUB_GMS_TOKEN=<service-account-token>
   ```

4. (Optional) Scope with Default Views:
   - In DataHub, create a Default View for the service account
   - The agent will only see assets in that view
   - Useful for limiting visibility to specific domains or teams

**Production checklist:**
- [ ] Service account created (not PAT)
- [ ] Access token generated
- [ ] Default View configured (recommended)
- [ ] Token stored securely (not in code)

### Day 3: Set Up Auto-Investigation

```bash
datahub actions -c config/actions/meridian_auto_trigger.yaml
```

Now when someone changes a schema in DataHub, Meridian automatically:
1. Detects the change
2. Traverses lineage to find affected models
3. Writes root cause report to Knowledge Base
4. Updates AI Knowledge panel on affected entities
5. Raises incident linked to all affected assets

### Day 4: Review the Knowledge Base

Open DataHub → Knowledge Base → Search "Meridian":
- Root cause reports for every investigation
- Playbooks that improve after each incident
- EU AI Act Technical Files for compliance

### Day 5: Share with Your Team

```bash
# Your team can now run:
/datahub-meridian-ai:investigate-model urn:li:mlModel:...
/datahub-meridian-ai:check-health urn:li:mlModel:...
/datahub-meridian-ai:view-playbook schema-change-type-mismatch
```

---

## What Gets Written Back to DataHub

After every investigation, these artifacts exist in DataHub:

| Artifact | Location | What It Shows |
|---|---|---|
| Root Cause Report | Knowledge Base | Full investigation with evidence chain |
| Reflexion Playbook | Knowledge Base | Improved after every incident |
| AI Knowledge Panel | Model entity page | Health score, confidence, resolved incidents |
| Incident Record | Incidents API | Linked to all affected entities |
| EU AI Act Technical File | Knowledge Base | SHA-256 audit trail for compliance |

**The key insight:** DataHub itself looks smarter. You're not building an external tool. You're making DataHub a more valuable object.

---

## Adapting to Your Environment

### Different DataHub Version?

Meridian AI works with DataHub v0.14.0+. The MCP client auto-detects your version.

### Different LLM Provider?

Replace Groq with OpenAI, Anthropic, or any OpenAI-compatible API:

```python
from backend.clients.groq_client import GroqClient
# Just set GROQ_API_KEY to your provider's key
# The client uses standard OpenAI-compatible API
```

### No LLM at All?

Run in mock mode. All statistical computation (PSI, KS-test, schema diff) works without any LLM. The LLM only generates natural language summaries.

### Different Data Sources?

Meridian AI works with any data source in DataHub — Snowflake, BigQuery, Redshift, dbt, Airflow, Spark. It reads from DataHub's metadata, not from your data directly.

---

## The Flywheel (Why This Matters)

```
Incident #12:  18 min  (first occurrence — playbook created)
Incident #28:   8 min  (same pattern — playbook retrieved)
Incident #42:   3 min  (pattern matched instantly — knowledge applied)
```

Every incident makes the next one faster. Not because the LLM improved. Because the knowledge base in DataHub improved. And it's stored where every future engineer and agent can access it.
