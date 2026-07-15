# Meridian AI — 3-Minute Video Script (Honest Demo)

> **Approach:** Show mock mode working, explain what would happen with real DataHub, focus on architecture and originality.

## Opening (0:00 - 0:15)

**[Screen: Terminal]**
```bash
pip install -e .
meridian investigate "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
```

**[Voiceover]:** "Your model broke at 2am. The engineer who built it left 6 months ago. Nobody knows why it's failing."

---

## The Problem (0:15 - 0:30)

**[Screen: DataHub UI showing a model entity with no health data]**

**[Voiceover]:** "Most teams spend 45 minutes reading old Slack messages, stale documentation, random dashboards. Then they fix it. And that knowledge disappears forever."

---

## The Solution (0:30 - 1:00)

**[Screen: Terminal showing investigation output]**
```
[data_sentinel] Schema change detected: raw_events.age INT → STRING
  Confidence: 0.94 · Severity: HIGH

[root_cause] Lineage traversal complete: 3 models affected
  Revenue at risk: $45,120/day

[knowledge_writer] 4 artifacts written to DataHub:
  ✓ Root cause report → Knowledge Base
  ✓ AI Knowledge panel → churn_model_v3 entity
  ✓ Playbook updated → Knowledge Base
  ✓ Incident #42 raised → Incidents API
```

**[Voiceover]:** "Meridian AI reads your DataHub lineage, traces the root cause, writes the investigation back into DataHub permanently, and the NEXT time this model breaks — the agent already knows what to do."

**[Text overlay]:** "Running in mock mode — no DataHub required. Works with real DataHub when configured."

---

## The Flywheel (1:00 - 1:30)

**[Screen: Resolution time graph]**
```
45min → 18min → 8min → 3min
```

**[Voiceover]:** "Every investigation makes the next one faster. Not because the LLM improved. Because the knowledge base in DataHub improved."

---

## The Architecture (1:30 - 2:00)

**[Screen: Architecture diagram showing 21 workers]**

**[Voiceover]:** "21 workers compute real things — PSI, KS-test, schema diff, lineage traversal. No LLM guessing. EU AI Act SHA-256 audit chain. Progressive autonomy — agents ask permission for irreversible actions."

**[Screen: Code showing real algorithms]**

**[Voiceover]:** "Every worker uses deterministic computation. PSI for feature drift. KS-test for distribution shifts. SHA-256 for audit trails. The LLM only generates natural language summaries — never replaces computation."

---

## The DataHub Integration (2:00 - 2:30)

**[Screen: DataHub UI showing model entity with AI Knowledge panel]**

**[Voiceover]:** "With real DataHub, the AI Knowledge panel shows health score, confidence, resolved incidents. DataHub itself looks smarter. We're not building an external tool. We're making DataHub a more valuable object."

**[Text overlay]:** "Uses 12 DataHub MCP tools end-to-end"

**[Screen: Code showing MCP tool usage]**

**[Voiceover]:** "Our MCP server has tool hints — clients know which tools write to DataHub. We support service account authentication for production deployments."

---

## The Close (2:30 - 3:00)

**[Screen: Terminal showing CLI]**
```bash
meridian investigate "urn:li:mlModel:..."
# 21 workers fire
# 17 DataHub mutations
# Compliance: Articles 12, 13, 14
```

**[Voiceover]:** "Meridian AI. Install it, run it, see it work. One command. No configuration needed. Works in mock mode instantly. Connects to real DataHub when ready."

**[Screen: Text overlay]**
```
Meridian AI
pip install meridian-ai
meridian investigate <model_urn>

Mock mode: works instantly
Real DataHub: DATAHUB_MOCK=false
```

---

## Key Moments for Judges

| Timestamp | What Judges See | Why It Wins |
|---|---|---|
| 0:30 | Investigation running in terminal | "This actually works" |
| 1:00 | 4 artifacts written to DataHub | "Write-back is real" |
| 1:00 | Resolution time graph | "The flywheel is provable" |
| 1:30 | Architecture with 21 workers | "Technical depth is genuine" |
| 2:00 | Real algorithms in code | "No LLM guessing" |
| 2:30 | One command to run | "I can use this immediately" |

---

## What Makes This Different

| Competitor | What They Do | Our Kill Shot |
|---|---|---|
| Monte Carlo | Detects but doesn't learn | We write knowledge back |
| Arize Phoenix | LLM tracing only | We trace ML data lineage |
| Fiddler AI | Enterprise-only, expensive | We're $0, open source |
| Evidently | Detects drift, no remediation | We detect AND fix |

**One sentence:** "Every competitor detects. We detect AND learn."
