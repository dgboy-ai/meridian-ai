# How to Win the DataHub Agent Hackathon

> 1,902 participants. 16 days left. $20,500 in prizes. Here's the complete strategy.

---

## The Competition

| Metric | Number |
|--------|--------|
| Participants | 1,902 |
| Days left | 16 (deadline: August 10, 2026) |
| Prizes | $20,500 total |
| Grand Prize | $6,000 + DataHub Townhall presentation |
| Challenge Winners | $3,000 × 4 (one per challenge) |
| Judges | 7 (Tim, Aman, Maggie, Alyssa, Nick, Wenjia, Mike) |

## What We're Competing Against

Most of the 1,902 participants will build:
- Simple text-to-SQL agents (Analytics Agent already exists)
- Basic data quality monitors (Assertions already exist)
- Simple MCP wrappers (too shallow)
- Data steward agents (Skills already do this)

**What almost nobody will build:**
- A closed-loop autonomous agent that WRITES BACK to DataHub
- A system that gets FASTER with every incident (flywheel)
- EU AI Act compliance (SHA-256 audit chain)
- Production-grade with 552 tests

---

## The 5 Judging Criteria (Equally Weighted)

### 1. Use of DataHub (25%)

**What judges want:** "Go beyond reading metadata and contribute back to the graph."

| We Claim | Evidence | File |
|----------|----------|------|
| 15 DataHub capabilities | 7 read + 5 write + 2 governance + Actions Framework | `backend/clients/datahub_client.py` |
| 5 artifacts per investigation | Root cause, playbook, AI Knowledge, incident, compliance | `backend/workers/knowledge_writer.py` |
| Actions Framework auto-trigger | YAML pipeline fires on schema changes | `config/actions/meridian_auto_trigger.yaml` |
| MCP Server as MCP tool | Meridian exposes itself for other agents | `backend/mcp_server.py` |

### 2. Technical Execution (25%)

**What judges want:** "Does the code do what the submission claims?"

| We Claim | Evidence | File |
|----------|----------|------|
| 552 tests passing | `python -m pytest tests/` | `tests/` |
| Deterministic Validation | 4 checks before any write | `backend/validation.py` |
| Progressive Autonomy | 5 levels from Advisory to Self-improving | `backend/autonomy.py` |
| Maker-Checker | VerifierAgent challenges RootCause | `backend/workers/verifier_agent.py` |
| Circuit Breaker | Monitors agent health | `backend/resilience.py` |
| Context-aware mock | Responses derived from investigation data | `backend/clients/groq_client.py` |

### 3. Originality (25%)

**What judges want:** "Go beyond features DataHub already provides."

| We Claim | Why It's Novel | Evidence |
|----------|---------------|----------|
| Cumulative intelligence flywheel | No other tool compounds knowledge | `examples/resolution_times.json` (18→8→3 min) |
| AI Knowledge Panel | DataHub entity pages gain intelligence | `examples/ai-knowledge/churn_model_v3.json` |
| EU AI Act compliance | SHA-256 audit chain, no one else has this | `backend/workers/eu_ai_act_compliance.py` |
| Self-healing assertions | Generates preventive checks from patterns | `backend/workers/self_healing_assertions.py` |
| Custom agent framework | Built our own, not just LangGraph wrapper | `backend/workers/planner.py` |

### 4. Real-World Usefulness (25%)

**What judges want:** "Would a real team see clear value?"

| We Claim | Evidence | Impact |
|----------|----------|--------|
| $45K/day problem | 32K predictions × $1.41/prediction | Silent ML degradation |
| 4 personas | ML Platform Engineer, Data Engineer, MLOps Lead, Enterprise Architect | Clear workflows |
| EU AI Act timing | Enforcement August 2, 2026 | 22 days before deadline |
| Lineage-based drift | Training data → features → models → deployments | Production ML traceability |

### 5. Submission Quality (25%)

**What judges want:** "Understand what it does, why it matters, try it themselves."

| We Claim | Evidence | Status |
|----------|----------|--------|
| Clear README | Problem → Solution → Architecture → Setup | DONE |
| 3 verification methods | CLI (30s), Examples (10s), Full Stack (5min) | DONE |
| Sample outputs | 7 files in examples/ folder | DONE |
| Demo video | 3-min walkthrough | TODO |
| 6 documentation files | Features, Security, Architecture, API, Deployment, DataHub Integration | DONE |

---

## The 3 Winning Signals

These are what separate winners from the other 1,900 projects:

### Signal 1: "Solve, Don't Just Alert"

> "A winning submission identifies a problem and provides an automated solution, rather than just reporting the error."

**We DO this:**
- Detect schema change → TRACE root cause through lineage → PROPOSE rollback → WRITE fix back to DataHub
- Not just monitoring. Not just alerting. FIXING.

### Signal 2: Closed-Loop Autonomous Agent

> "The most successful submissions demonstrate a 'read-write' loop."

**Our loop:**
```
READ (7 MCP tools) → ANALYZE (18 workers) → FIX (5 artifacts) → WRITE BACK (DataHub)
```

This is the #1 winning signal.

### Signal 3: Changes Visible in DataHub UI

> "The changes are reflected directly in the DataHub UI."

**After our investigation, judges see:**
- AI Knowledge panel appears on model entity page
- Root cause report in Knowledge Base
- Incident record linked to affected assets
- Tags on all affected datasets
- EU AI Act audit trail

---

## What to Do in the Next 16 Days

### Week 1 (Days 1-7): Deploy & Record

| Day | Task | Time | Why |
|-----|------|------|-----|
| 1 | Deploy backend on Render | 1 hour | Judges need real data |
| 1 | Connect Vercel to Render | 30 min | Frontend shows real investigations |
| 2 | Record demo video (3 min) | 2 hours | Submission requirement |
| 3 | Upload video to YouTube | 30 min | Submission requirement |
| 3 | Final README polish | 1 hour | Submission quality |
| 4 | Submit to Devpost | 30 min | Get it in early |
| 5-7 | Join #agent-hackathon, answer questions | 30 min/day | Community engagement |

### Week 2 (Days 8-14): Polish & Promote

| Day | Task | Time | Why |
|-----|------|------|-----|
| 8-10 | Fix any issues found by early reviewers | 1 hour/day | Iterate before deadline |
| 11-12 | Share on LinkedIn/Twitter | 30 min | Visibility |
| 13 | Final check: all links work, video plays | 30 min | Last chance to fix |
| 14 | Submit feedback survey | 15 min | $50 bonus prize |

### Week 3 (Days 15-16): Final Push

| Day | Task | Time | Why |
|-----|------|------|-----|
| 15 | Last review of submission | 30 min | Final polish |
| 16 | Deadline: August 10, 5:00 PM ET | — | Submit before cutoff |

---

## The Video Script (3 Minutes)

### 0:00-0:15 — The Hook
**Screen:** DataHub entity page for churn_model_v3 — NO AI Knowledge panel
**Voice:** "This model serves 32,000 predictions a day. Last Tuesday, it silently degraded from 89% to 71% accuracy. Nobody noticed for 3 days. That's $45,000 in revenue at risk."

### 0:15-0:45 — The Investigation
**Screen:** Click "Run Investigation" → timeline streaming events
**Voice:** "Meridian AI reads DataHub's lineage graph, traces root cause through column-level lineage, and writes the fix back — a closed-loop autonomous agent."

### 0:45-1:15 — The Write-Back (Wow Moment)
**Screen:** Switch to DataHub UI → AI Knowledge panel appeared
**Voice:** "Look at DataHub. The AI Knowledge panel is there. Health score: 89. Resolved incidents: 15. The AI wrote this. DataHub itself became smarter."

### 1:15-1:45 — The Flywheel
**Screen:** Resolution time graph: 18→8→3 min
**Voice:** "Every investigation improves the next one. 18 minutes first time. 8 minutes second. 3 minutes third. The knowledge base compounds."

### 1:45-2:15 — Compliance
**Screen:** SHA-256 audit trail
**Voice:** "EU AI Act enforcement starts August 2nd. Meridian generates a Technical File for every investigation. Cryptographically proven."

### 2:15-2:45 — Architecture
**Screen:** 18 workers firing
**Voice:** "18 workers compute real things — PSI, KS-test, lineage traversal. 552 tests. Production-grade."

### 2:45-3:00 — The Close
**Screen:** Terminal
```bash
pip install -e .
meridian investigate "urn:li:mlModel:..."
```
**Voice:** "One command. Apache 2.0. No login required."

---

## Devpost Submission Checklist

### Required
- [ ] Project URL (Vercel frontend)
- [ ] GitHub repo URL (public, Apache 2.0)
- [ ] Text description (from DEVPOST_SUBMISSION.md)
- [ ] Demo video (YouTube, <3 min)
- [ ] Challenge: Production ML Agents

### Recommended
- [ ] Sample outputs in examples/ folder
- [ ] Link to DataHub Slack #agent-hackathon
- [ ] Link to Analytics Agent repo (reference)

### Bonus
- [ ] Feedback survey ($50 × 10 prizes)
- [ ] DataHub Skill contribution (skill/datahub-meridian-ai/)
- [ ] Actions Framework YAML (config/actions/)

---

## Key Phrases for Every Piece of Documentation

1. **"Meridian AI is a closed-loop autonomous agent that reads DataHub, investigates the problem, and writes the fix back."**
2. **"Every investigation makes DataHub smarter."**
3. **"83% faster from first to third occurrence."**
4. **"15 DataHub capabilities, 5 artifacts per investigation."**
5. **"EU AI Act enforcement August 2, 2026 — 22 days before deadline."**
6. **"We solve, don't just alert."**
7. **"552 tests, validation layer, production-grade."**

---

## Files That Matter Most

| File | Why Judges Look At It |
|------|----------------------|
| `README.md` | First impression — problem, solution, setup |
| `examples/` | Provable outputs — 7 generated files |
| `backend/workers/planner.py` | Core orchestration — 18 workers |
| `backend/clients/datahub_client.py` | DataHub integration — 15 tools |
| `backend/validation.py` | Safety — deterministic validation |
| `backend/workers/eu_ai_act_compliance.py` | EU AI Act — SHA-256 audit chain |
| `config/actions/meridian_auto_trigger.yaml` | Actions Framework — auto-trigger |
| `skill/datahub-meridian-ai/` | Open-source contribution bonus |
