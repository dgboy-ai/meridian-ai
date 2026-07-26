# DataHub Hackathon — Insights from Build Session

> Source: Lakshay Nasa (DataHub) build session video
> Saved: 2026-07-26

---

## Key Insight 1: What Judges Actually Want

**"Don't just build a demo — solve a genuine problem from your own data stack."**

This is the single most important quote. Judges don't want another text-to-SQL agent. They want something that solves a REAL problem.

**What this means for Meridian:**
- We solve a REAL problem: silent ML failures costing $45K/day
- We don't just detect — we investigate, diagnose, remediate, and learn
- This IS the "genuine problem" judges want to see

## Key Insight 2: Agent Architecture (3 Building Blocks)

The speaker says a robust agent needs:
1. **Framework** (e.g., LangGraph)
2. **DataHub Tools** (10 read / 12 write operations)
3. **LLM/Brain**

**What this means for Meridian:**
- We have all 3: Planner Agent (framework), 15 DataHub tools (more than the 10/12 baseline), Groq LLM
- We exceed the baseline — we have 15 capabilities, not just 10 read + 12 write

## Key Insight 3: The 71-Line Agent Demo

The speaker demonstrated a 71-line Python agent that:
- Identifies data quality issues (missing owners, descriptions)
- Writes updates back to DataHub

**What this means for Meridian:**
- Our agent is MUCH more complex — 18 workers, 552 tests, full investigation pipeline
- But we should make sure our agent is EASY to understand (not just big)
- The 71-line agent is a good benchmark: judges should understand our architecture quickly

## Key Insight 4: DataHub Tools (10 Read / 12 Write)

The speaker mentions 10 read and 12 write operations as the baseline.

**What this means for Meridian:**
- We have 15 total (7 read + 5 write + 2 governance + Actions Framework)
- We're above baseline — this is good
- But we should make sure judges SEE these tools being used, not just listed

## Key Insight 5: Analytics Agent as Reference

The speaker points to the Analytics Agent repo as a "production-ready implementation" reference.

**What this means for Meridian:**
- We should reference the Analytics Agent in our submission
- Show that we're building on the same foundation but solving a DIFFERENT problem
- Analytics Agent = text-to-SQL. Meridian AI = ML incident investigation

## Key Insight 6: Real-World Application

The speaker says: "solve a genuine problem from your own data stack — automating governance, tagging, or flagging broken pipelines."

**What this means for Meridian:**
- "Flagging broken pipelines" = EXACTLY what we do (Pipeline Circuit Breaker)
- "Automating governance" = EXACTLY what we do (Lifecycle Governance, Shadow AI Discovery)
- "Tagging" = EXACTLY what we do (batch_add_tags on affected assets)
- We hit ALL three examples the speaker gave

## Key Insight 7: Write-Back is Critical

The 71-line agent WRITES BACK to DataHub. The speaker emphasizes this.

**What this means for Meridian:**
- We write back 5 artifacts per investigation
- This is our strongest differentiator
- We should HIGHLIGHT this in every piece of documentation

## Immediate Actions

| Priority | Action | Why |
|----------|--------|-----|
| 1 | Make sure the Vercel demo shows REAL investigation data | Judges need to SEE the system work |
| 2 | Highlight write-back in README and Devpost description | Speaker says write-back is critical |
| 3 | Reference Analytics Agent as foundation we build on | Speaker points to it as reference |
| 4 | Show we solve "genuine problems" (governance, tagging, broken pipelines) | Speaker's exact advice |
| 5 | Make the agent architecture easy to understand (3 blocks: Framework + Tools + LLM) | Speaker's architecture model |

---

## Build Session Part 2: Detailed Guidance

### Insight 8: Solve Real Pain Points, Not Demos

**"Don't just build a demo. Judges look for agents that address actual pain points in a data engineering workflow."**

Three specific pain points mentioned:
- **Governance Automation** — detect tables missing owners, assign based on lineage
- **Quality Flagging** — tag deprecated tables, alert owners via Slack/Discord
- **Pipeline Reliability** — monitor for drift in ML models or broken downstream dependencies

**What this means for Meridian:**
- We hit ALL THREE:
  - Governance: Lifecycle Governance, Shadow AI Discovery, Deprecation Advisor
  - Quality Flagging: Contract Enforcer, Self-Healing Assertions, batch_add_tags
  - Pipeline Reliability: Pipeline Circuit Breaker, Feature Drift, Training-Serving Skew
- **Action:** List these 3 pain points explicitly in our submission description

### Insight 9: Write-Back = Agentic Capabilities

**"A high-scoring submission demonstrates write-back capabilities."**

22 DataHub tools (10 read, 12 write) — the speaker's baseline.

**What this means for Meridian:**
- We have 15 tools (7 read + 5 write + 2 governance + Actions Framework)
- We're above the 10/12 baseline
- **Action:** In the submission, explicitly list every read and write tool and what it does

### Insight 10: State Management = LangGraph Pattern

**"Utilize frameworks like LangGraph to enable your agent to think, act, and loop through multiple steps effectively."**

**What this means for Meridian:**
- Our Planner Agent IS a state machine (detection → diagnosis → enforcement → learning)
- Our Reflexion Loop IS the "think, act, loop" pattern
- We don't use LangGraph, but our architecture achieves the same thing
- **Action:** Describe our planner as a "state-driven investigation pipeline" in the submission

### Insight 11: Grounded Context Prevents Hallucination

**"An agent is only as good as its context. A superior submission ensures the LLM is not hallucinating."**

Three grounding mechanisms:
- **Real Data Context** — Agent Context Kit or DataHub Skills for live schemas, ownership, lineage
- **Architecture Transparency** — Clear 3-component model (Framework + Tools + LLM)
- **No hallucination** — LLM interprets statistical results, never replaces computation

**What this means for Meridian:**
- We ground every worker in real DataHub data (lineage, schema, ownership)
- Our statistical computation (PSI, KS-test) is REAL — LLM interprets after
- **Action:** Emphasize "LLM interprets, code computes" in the submission

### Insight 12: Production-Grade Signals

**"Even though you are building a hackathon prototype, showing an understanding of production-ready architecture will impress judges."**

Four production signals:
- **Error Handling** — graceful handling of unexpected metadata states
- **Scalability** — modular design, can extend from one table to full catalog
- **Example** — Analytics Agent repo as production reference
- **Testing** — comprehensive test suite

**What this means for Meridian:**
- We have 552 tests, validation layer, circuit breaker, progressive autonomy
- Our architecture IS modular (18 independent workers)
- **Action:** Add a "Production Readiness" section to the README

---

## Build Session Part 3: Agent Pattern Details

### Insight 13: The Closed-Loop Agent Pattern (READ → ACT → WRITE)

The 71-line agent follows a specific pattern:
1. **READ** — Identify quality issues (missing owners, lack of documentation)
2. **ACT** — Automatically assign owners, flag tables for review
3. **WRITE** — Update DataHub catalog, demonstrating closed-loop agentic workflow

**What this means for Meridian:**
- Our pipeline follows the SAME pattern but at scale:
  - READ: 7 MCP tools (search, get_entities, get_lineage, list_schema_fields, etc.)
  - ACT: 18 workers analyze, diagnose, remediate
  - WRITE: 5 artifacts back to DataHub (root cause, playbook, AI Knowledge, incident, compliance)
- **Action:** Describe our pipeline as "READ → ACT → WRITE at scale" in the submission

### Insight 14: Agent Context Kit = Custom Agent Building

The Agent Context Kit is specifically for building custom agents with LangChain/LangGraph.

**What this means for Meridian:**
- We built our own agent framework (Planner Agent) instead of using Agent Context Kit
- This shows MORE originality — we didn't just use the provided toolkit
- **Action:** Mention we built a custom agent framework, not just wrapped Agent Context Kit

---

## Build Session Part 4: Challenge Categories Deep Dive

### Insight 15: "Agents That Do Real Work" = Write-Back is Non-Negotiable

**"High-scoring agents move beyond passive metadata querying. They perform 'real work' by actively writing back to the data ecosystem."**

Specific examples given:
- Automatically assign owners to tables
- Update missing documentation
- Tag deprecated assets based on lineage

**What this means for Meridian:**
- We do ALL of this: assign tags, update AI Knowledge panels, write root cause reports, create incidents
- **Action:** In Devpost description, lead with: "Meridian AI doesn't just detect problems — it writes 5 artifacts back to DataHub after every investigation"

### Insight 16: "Production ML" = Traceability + Reliability

**"Build agents that can trace the entire lifecycle of a machine learning model, from training data and features to deployment."**

**"If a component in the feature stage or deployment phase breaks, the agent should catch the issue or suggest improvements."**

**What this means for Meridian:**
- We trace lineage from training data → features → models → deployments
- We detect schema changes, feature drift, training-serving skew
- We propose fixes (rollback, pipeline patch, preventive assertions)
- **Action:** Emphasize "end-to-end ML lineage" in submission — this is what makes us Production ML

### Insight 17: Closed-Loop Autonomy = The #1 Signal

**"The most successful submissions demonstrate a 'read-write' loop where the agent uses DataHub as a source of truth to identify problems and then executes fixes directly."**

This is THE winning signal. Not just detection. Not just analysis. FIXING.

**What this means for Meridian:**
- READ: 7 MCP tools pull context from DataHub
- ANALYZE: 18 workers compute real things (PSI, KS-test, lineage traversal)
- FIX: 5 artifacts written back to DataHub (root cause, playbook, AI Knowledge, incident, compliance)
- **Action:** The submission description should open with: "Meridian AI reads DataHub, investigates the problem, and writes the fix back — a closed-loop autonomous agent."

### Insight 18: 22 Tools = The Baseline Judges Expect

The speaker mentions 22 DataHub tools (10 read, 12 write) as the expected baseline.

**What this means for Meridian:**
- We have 15 tools — below the 22 baseline
- But we have Actions Framework YAML (auto-trigger) which most submissions won't have
- And we have governance tools (propose_lifecycle_stage, list_pending_proposals) which are rare
- **Action:** Don't apologize for having 15 instead of 22. Instead, emphasize that we use them DEEPLY (5 artifacts per investigation) rather than broadly

---

## Build Session Part 5: Final Strategy

### Insight 19: "Solve, Don't Just Alert"

**"A winning submission identifies a problem and provides an automated solution, rather than just reporting the error."**

**What this means for Meridian:**
- We don't just detect schema changes — we TRACE root cause through lineage
- We don't just report drift — we PROPOSE rollback and generate preventive assertions
- We don't just log incidents — we WRITE the fix back to DataHub
- **Action:** Every feature description should say what we DO, not what we DETECT

### Insight 20: Autonomous Remediation = Production Maturity

**"Show that the agent can make decisions—like marking a table as 'deprecated' or 'needs review'—based on the context it retrieves."**

**What this means for Meridian:**
- We already do this: Lifecycle Governance proposes DEPRECATED for failing models
- We already do this: Contract Enforcer quarantines bad datasets
- We already do this: Deprecation Advisor identifies unused assets
- **Action:** Highlight these autonomous decisions in the submission

### Insight 21: Don't Build from Scratch — Combine Tools

**"You do not need to build everything from scratch. Focus on combining these tools to solve a real-world problem."**

**What this means for Meridian:**
- We combine: MCP Server + DataHub Skills + Agent Context Kit + Actions Framework
- We don't rebuild what DataHub already provides — we EXTEND it
- **Action:** In submission, say: "Built on DataHub's MCP Server and Skills, extended with custom investigation pipeline"

### Insight 22: Framework Stack = LangChain + LangGraph + Agent Context Kit

The speaker recommends:
- **LangChain** — broader toolkit for LLM apps
- **LangGraph** — for agents that need to loop, maintain state, handle complex tasks
- **Agent Context Kit** — dedicated toolkit for DataHub agents
- **DataHub Skills** — 10 read + 12 write pre-built tools
- **MCP Server** — protocol for translating DataHub context

**What this means for Meridian:**
- We built our own framework instead of using LangGraph — MORE originality
- But we should mention we're compatible with these frameworks
- **Action:** Add "Compatible with LangChain/LangGraph/Agent Context Kit" in README

---

## Build Session Part 6: Integration Details

### Insight 23: MCP Configuration = GMS URL + Access Token

The MCP Server connection requires:
- **GMS URL**: `http://localhost:8080/api/gms` (local) or `https://<tenant>.acryl.io/api/gms` (cloud)
- **Access Token**: Generated from DataHub settings menu
- **Mutations**: Disabled by default for security — must generate token to unlock

**What this means for Meridian:**
- Our `DataHubMCPClient` already handles this (dual-mode: real + mock)
- We should document the exact setup steps in our README
- **Action:** Add "Prerequisites" section with exact GMS URL and token generation steps

### Insight 24: 22 Tools = Agent Context Kit Baseline

The Agent Context Kit provides:
- **10 read tools**: search, get_entities, get_lineage, list_schema_fields, get_dataset_queries, search_documents, grep_documents, get_me, list_lifecycle_stages, get_glossary_term_versions
- **12 write tools**: add/remove tags, add/remove terms, add/remove owners, set/remove domains, update_description, add/remove structured_properties, save_document

**What this means for Meridian:**
- We use 15 of these tools — 7 read + 5 write + 2 governance + Actions Framework
- We're close to the full baseline
- **Action:** List every tool we use with its specific purpose in the submission

### Insight 25: The "Agentic Loop" Pattern

The speaker demonstrates a specific loop:
1. **Query** DataHub API to find missing documentation/tags/ownership
2. **Identify** issues (e.g., dataset without owner)
3. **Push updates** back to DataHub (add owner, add tags, add descriptions)
4. **Verify** changes reflected in DataHub UI

**What this means for Meridian:**
- Our pipeline IS this loop at scale: detect → diagnose → remediate → learn
- But we do it for ML incidents, not just governance
- **Action:** Describe our pipeline as "agentic loop for ML incident response"

### Insight 26: Changes Must Be Visible in DataHub UI

**"The changes are reflected directly in the DataHub UI, which he refreshes to show that the new metadata has been successfully applied."**

**What this means for Meridian:**
- Our write-back creates visible artifacts in DataHub:
  - AI Knowledge panel appears on model entity pages
  - Root cause reports appear in Knowledge Base
  - Incidents appear in Incidents tab
  - Tags appear on affected assets
- **Action:** In the video, show DataHub UI BEFORE and AFTER the investigation

---

## Reference URLs

### DataHub Documentation
- **Quickstart**: https://docs.datahub.com/docs/quickstart
- **Agent Context Kit**: https://docs.datahub.com/docs/dev-guides/agent-context/agent-context
- **DataHub Skills**: https://docs.datahub.com/docs/dev-guides/agent-context/skills
- **MCP Server**: https://docs.datahub.com/docs/features/feature-guides/mcp
- **Analytics Agent**: https://docs.datahub.com/docs/features/feature-guides/analytics-agent
- **Incidents**: https://docs.datahub.com/docs/incidents/incidents
- **Lineage**: https://docs.datahub.com/docs/features/feature-guides/lineage
- **Assertions**: https://docs.datahub.com/docs/managed-datahub/observe/assertions

### GitHub Repos
- **Analytics Agent** (35 stars, 16 forks): https://github.com/datahub-project/analytics-agent
  - Uses LangGraph, FastAPI, React
  - Apache 2.0 license
  - Has "context quality score" (1-5) feature
  - Has "/improve-context" write-back command
- **DataHub Skills** (34 stars, 31 forks): https://github.com/datahub-project/datahub-skills
  - 5 catalog interaction skills (search, enrich, lineage, quality, setup)
  - 3 connector development skills
  - 22 connector standards
- **MCP Server** (78 stars): https://github.com/acryldata/mcp-server-datahub
- **DataHub Core**: https://github.com/datahub-project/datahub

### Community
- **DataHub Slack**: https://datahub.com/slack (#agent-hackathon channel)
- **Hackathon**: https://datahub.devpost.com

---

## Final Summary: How to Win

### The 5 Things Judges Care About (Equally Weighted)

| Criterion | What They Want | What We Have | Score |
|-----------|---------------|-------------|-------|
| **Use of DataHub** | Read + write, contribute back to graph | 15 tools, 5 artifacts per investigation, Actions Framework | Strong |
| **Technical Execution** | Works end-to-end, quality code | 552 tests, validation layer, production patterns | Strong |
| **Originality** | Beyond out-of-box features | Flywheel, EU AI Act, cumulative intelligence, custom framework | Strong |
| **Real-World Usefulness** | Solves a real problem | $45K/day ML failures, 4 personas, EU AI Act timing | Strong |
| **Submission Quality** | Video, README, setup instructions | 6 docs, clear setup, 3 verification methods | Strong |

### The 3 Winning Signals

1. **"Solve, don't just alert"** — We FIX problems (write 5 artifacts back), not just detect them
2. **Closed-loop autonomous agent** — READ → ANALYZE → FIX → WRITE BACK
3. **Changes visible in DataHub UI** — AI Knowledge panel, incidents, tags appear after investigation

### What to Do in the Next 15 Days

| Priority | Task | Effort |
|----------|------|--------|
| 1 | Record demo video (3 min, show flywheel + DataHub write-back) | 2 hours |
| 2 | Deploy backend on Render (real investigation data) | 1 hour |
| 3 | Connect Vercel to Render backend | 30 min |
| 4 | Final README polish | 1 hour |
| 5 | Submit to Devpost | 30 min |

**Total: ~5 hours of work to be submission-ready.**

---

## Build Session Part 7: Lineage-Based Drift & Final Notes

### Insight 27: Lineage-Based Drift = The Production ML Story

**"Build production machine learning agents capable of tracing the path from training data to features, models, and deployments."**

The agent must:
1. **Read** — Query DataHub to check if upstream source feeding model features has been modified
2. **Examine** — Use LLM to evaluate if metadata changes imply drift risk
3. **Act** — Write-back to flag model, notify owners, trigger remediation

**What this means for Meridian:**
- This is EXACTLY what our system does:
  - Read: `get_lineage` traces from dataset → features → models
  - Examine: Feature Drift worker computes PSI/KS-test on actual data
  - Act: Writes root cause report, raises incident, proposes rollback
- **Action:** In submission, describe this as "lineage-based drift detection and automated remediation"

### Insight 28: The Orchestrator Pattern

**"Build an orchestrator that detects, remediates, and scales."**

Three capabilities:
- **Detects** — Proactively checks for breakage using DataHub lineage tools
- **Remediates** — Automates resolution, not just reporting
- **Scales** — Production-grade reliability

**What this means for Meridian:**
- Our Planner Agent IS this orchestrator
- 18 workers = modular, scalable design
- Production-grade: 552 tests, validation layer, circuit breaker
- **Action:** Describe our system as "an orchestrator for ML incident response"

### Insight 29: URNs = Unique Asset IDs

**"URNs are unique IDs for every asset in your data catalog (datasets, columns, dashboards)."**

**What this means for Meridian:**
- We handle URNs throughout: `urn:li:mlModel:...`, `urn:li:dataset:...`
- Our validation layer verifies URNs before any mutation
- **Action:** Mention URN handling in the submission to show DataHub expertise

### Insight 30: Use AI to Build (Don't Hand-Type)

**"Let an AI assistant help draft your code."**

**What this means for Meridian:**
- We used AI coding assistants during development (this is expected and allowed)
- The result is what matters, not how it was built
- **Action:** No action needed — this is standard practice

### Insight 31: Community Support

**"#agent-hackathon channel in DataHub Slack is the primary place to get direct help."**

**What this means for Meridian:**
- We should join the channel and ask questions if needed
- We can also help others — this shows community engagement
- **Action:** Join #agent-hackathon, ask about our architecture approach

---

## Build Session Part 8: Final Strategy — Lineage-Based Drift

### Insight 32: Detection → Remediation = The Gap Most Submissions Miss

**"Don't just alert the user that drift is occurring. Use DataHub's write-back capabilities to automatically trigger workflows."**

Most submissions DETECT. Very few REMEDIATE. This is the gap.

**What this means for Meridian:**
- We DON'T just detect — we:
  - Propose rollback (Lifecycle Governance)
  - Quarantine bad datasets (Contract Enforcer)
  - Generate preventive assertions (Self-Healing)
  - Write root cause reports (Knowledge Writer)
  - Tag all affected assets (batch_add_tags)
- **Action:** In submission, explicitly list every remediation action we take

### Insight 33: The "Data Reliability Guardian" Framing

**"Build a 'Data Reliability Guardian' that specifically monitors critical features used in a production ML model."**

**What this means for Meridian:**
- This IS our product name: "AI Reliability Engineer"
- But "Guardian" is a stronger word for judges
- **Action:** Consider using "Data Reliability Guardian" or "ML Reliability Guardian" in the submission

### Insight 34: The 3-Step Technical Pattern

1. **Read** — Agent Context Kit pulls lineage and metadata
2. **Examine** — LLM compares current data against historical baselines
3. **Act** — 12 write-back tools document findings, alert owners, pause pipelines

**What this means for Meridian:**
- We follow this EXACTLY:
  - Read: 7 MCP tools (search, get_lineage, list_schema_fields, etc.)
  - Examine: 18 workers compute real things (PSI, KS-test, schema diff)
  - Act: 5 artifacts written back to DataHub
- **Action:** Describe our pipeline as "Read → Examine → Act" in the submission

### Insight 35: Submission Checklist (Final)

| Item | Status | Notes |
|------|--------|-------|
| Clear value proposition | TODO | "Reducing ML downtime by 50% through automated lineage-aware drift remediation" |
| High-quality demo video | TODO | Show: drift detected → lineage traced → root cause found → remediation applied |
| Community engagement | TODO | Join #agent-hackathon on DataHub Slack |
| Production-grade signals | DONE | 552 tests, validation layer, circuit breaker |
| Write-back to DataHub | DONE | 5 artifacts per investigation |
| Real-world pain point | DONE | Silent ML failures, $45K/day, EU AI Act compliance |

---

## Build Session Part 9: Datasets, Licensing & Final Checklist

### Insight 36: Dataset Licensing = Apache 2.0 Required

**"Ensure datasets are openly shareable — compatible with Apache 2.0."**

**What this means for Meridian:**
- Our replay data (`replay_data.json`) is original — no licensing issues
- Our example models (`churn_model_v3`, etc.) are fictional — no licensing issues
- Our DSA algorithms are original implementations — no licensing issues
- **Action:** Verify all example data is Apache 2.0 compatible before submission

### Insight 37: Public Availability = No Proprietary Data

**"Avoid commercial or proprietary datasets that cannot be legally shared."**

**What this means for Meridian:**
- We use no external datasets — all data is generated by our workers
- Our repo is public with Apache 2.0 license
- **Action:** Already compliant — no changes needed

### Insight 38: Planted Problems = Better Demos

**"Use datasets with built-in data quality issues or missing ownership information to demonstrate real-world remediation."**

**What this means for Meridian:**
- Our replay data has planted problems (schema changes, freshness violations)
- Our `seed_meridian.py` creates realistic DataHub entities with issues
- **Action:** Emphasize that our demo data has planted problems for judges to see

### Insight 39: "Plumbing" vs "Value" = The Winning Distinction

**"Judges want to see that you have moved past the 'plumbing' and created a tool that provides tangible value within a data stack."**

"Plumbing" = connecting tools together (easy)
"Value" = solving a real problem (hard)

**What this means for Meridian:**
- We've moved PAST plumbing — we have 18 workers, 552 tests, validation layer
- Our VALUE is: silent ML failures detected in 8 minutes instead of 3 days
- **Action:** In every piece of documentation, lead with VALUE, not plumbing

### Insight 40: Final Submission Checklist (Complete)

| Item | Status | Evidence |
|------|--------|----------|
| **Open-source license** | DONE | Apache 2.0 in LICENSE file |
| **Public repo** | DONE | github.com/dgboy-ai/meridian-ai |
| **Clear setup instructions** | DONE | README has 3 verification methods |
| **Working demo** | DONE | CLI, API server, full stack, examples |
| **High-quality video** | TODO | Record 3-min demo showing flywheel |
| **Sample outputs** | DONE | 7 files in examples/ folder |
| **Text description** | DONE | Devpost description written |
| **DataHub integration** | DONE | 15 tools, 5 artifacts per investigation |
| **Production-grade** | DONE | 552 tests, validation, circuit breaker |
| **Solves real problem** | DONE | Silent ML failures, $45K/day |
| **Open-source contribution** | DONE | DataHub Skill + Actions Framework YAML |

