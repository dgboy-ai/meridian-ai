# Meridian AI — Claude's Gap Analysis for Winning Grand Prize
## Written by: Claude Sonnet 4.6 (Thinking)
## Date: July 19, 2026
## Purpose: Raw, unfiltered assessment of what's missing to beat 1051 participants

---

> **The brutal truth:** You have an exceptional architecture and a genuinely novel idea. But right now you are building a story about a product rather than building the product. Judges will notice the gap between the claims and the reality within 3 minutes of looking at the code.
>
> The path to Grand Prize is not more features. It is making the existing 7 core features undeniably, verifiably real — and then presenting them with the clarity and confidence of someone who knows they built something genuinely good.

---

## The Judge Test (The Real Stakes)

Five judges. Here is what each one will do before voting:

**Tim Bossenmaier (Data Architect @ Cloudflight):**
- Will check if the DataHub integration is real, not just claimed
- Will look at the audit trail for EU AI Act and ask "would this pass an actual audit?"
- Will ask: "Would I deploy this at a client?" — if the answer is "it's demo mode," he will rank it below a simpler project that actually works

**Aman Gairola (Engineering Manager @ Pinterest):**
- Runs production ML at scale. Will immediately see through mock data
- Cares about the flywheel claim: does resolution time actually decrease?
- Will ask: "What does this cost to operate? Is the ROI real?"
- Will check if PSI/KS-test math is correct AND if the inputs are real (they are not)

**Maggie Hays (Founding PM @ DataHub):**
- Knows DataHub's capabilities better than anyone in that room
- Will test the write-back claims in DataHub's actual entity model
- Cares deeply about the "DataHub becomes smarter" narrative — is it actually smarter, or is it a demo?
- Will read the Devpost description and check every claim against the code

**Alyssa Lee (Chief of Staff @ DataHub):**
- Focused on the DataHub ecosystem story — does this make DataHub more valuable?
- Will check if the open-source contribution is real (PR submitted) or just "coming soon"
- Will care about submission quality: video, README, can someone set this up?

**Nick Adams (DataHub):**
- Knows the MCP Server API better than anyone
- Will test the MCP tool calls and check if they match the actual API spec
- Will notice immediately if the `datahub-meridian-ai` skill PR was actually submitted or just mentioned in docs

---

## Part 1: The Five Highest-Impact Gaps

### GAP-1: The Core Demo Is Mock-Only (Score Impact: -3 pts on Technical Execution)

**What exists:** A beautiful mock mode that runs `meridian investigate` and prints impressive output — all from hardcoded data.

**What judges see when they look carefully:**
- `backend/clients/datahub_client.py` — `MOCK_ENTITIES` with 6 hardcoded entities
- `backend/workers/feature_drift.py:47-56` — PSI/KS math is real but input arrays are hardcoded
- `backend/workers/root_cause.py:68` — root cause is always the source node you pointed at
- `replay_data.json` — 3 pre-recorded incidents that never change

**The gap nobody in your documents has solved:**
You have a `DATAHUB_MOCK=false` flag but assessment.md honestly admits: "It will probably fail because we haven't tested against real DataHub." This is the most critical gap. If ONE judge flips that flag and the system crashes, the Technical Execution score collapses.

**What to actually do:**
1. Spin up DataHub locally via docker-compose (you have it)
2. Seed the demo data (`python scripts/seed_meridian.py`)
3. Run ONE real investigation against it with `DATAHUB_MOCK=false`
4. Fix whatever breaks
5. Record a screen capture of this working as your demo video — not mock mode
6. In the README, the **first** option should be the real DataHub demo, not mock mode

**Why this alone could win:** Every other submission will also demo in mock mode. The one team that demos against a real DataHub instance — even a local one — wins the Technical Execution criterion by default.

---

### GAP-2: The Demo Video Is a Submission Blocker (Score Impact: -2 pts on Submission Quality)

**Current state:** `VIDEO_SCRIPT.md` exists but says "[recording pending]" in the Devpost submission. This is a disqualification-level issue. Judges cannot evaluate a project without a video.

**What the existing video script misses:**
1. It shows terminal output — this is the WORST medium for judges. Text scrolling in a terminal communicates nothing to non-technical judges (Alyssa Lee, Maggie Hays)
2. It does not show the DataHub entity page changing — the single most powerful proof moment in the whole strategy doc is absent from the script
3. It does not show the frontend dashboard at all — 6 months of frontend work is invisible
4. The "emotional payoff" moment (opening churn_model_v3 in DataHub after investigation) is described in HACKATHON_STRATEGY.md but cut from the video script

**The 3-minute video structure that wins:**

| Timestamp | Screen | Audio | Why It Wins |
|-----------|--------|-------|-------------|
| 0:00-0:08 | Blank DataHub entity page for churn_model_v3 — NO AI Knowledge panel | "This model broke at 2am. 32,000 predictions failed. $45,000 in revenue at risk." | Establishes the problem visually |
| 0:08-0:30 | Frontend Mission Control — run investigation live | "Watch Meridian read DataHub, trace the lineage, and investigate." | Shows the product |
| 0:30-1:00 | Investigation Timeline — workers firing in real-time | Narrate the evidence chain — "confidence 0.94...lineage traversed...3 models affected" | Shows depth |
| 1:00-1:20 | D3 blast radius visualization — nodes lighting up | "Blast radius: 3 models, 12 dashboards, $45K/day" | The wow moment |
| 1:20-1:45 | SWITCH TO DATAHUB — churn_model_v3 entity page NOW WITH AI Knowledge panel | "30 seconds later, DataHub itself has changed. The AI wrote this. Let's look." | The payoff — nothing else in this hackathon does this |
| 1:45-2:15 | DataHub Knowledge Base — show the root cause report and reflexion playbook | "Incident #1 took 45 minutes. Incident #42 took 3 minutes. Because knowledge compounds." | The flywheel proof |
| 2:15-2:45 | Resolution time graph in frontend — count-up animation | "Every team using Meridian gets faster. Not because AI improved. Because knowledge in DataHub improves." | The long-term value |
| 2:45-3:00 | CLI: `pip install meridian-ai && meridian investigate <urn>` | "One command. No login. Apache 2.0. Start in 60 seconds." | Call to action |

**Critical rule:** Every second of the video must show something on SCREEN that proves a claim. No more "what WOULD happen with real DataHub" narration. Show it happening.

---

### GAP-3: The Frontend Is Architecturally Disconnected (Score Impact: -2 pts on Originality)

**Current state:** The landing page is beautiful (ParticleField, glassmorphism, aurora effects) but it is a marketing page, not an investigation tool. The judges' "3 ways to verify" in the README sends them to the CLI, not the frontend.

**The missing frontend screens that the strategy correctly identifies but don't exist:**
1. **Resolution Time Graph** — The strategy calls this "Hero Screen 1" and says "judges see this before anything else." It does not exist as a dedicated page.
2. **DataHub Entity Preview** — When the investigation writes back to DataHub, the frontend should show what changed on the DataHub entity page. Right now there is no screen that shows this.
3. **Live Investigation Trigger** — gap.md F6: "No 'Run Investigation' button." Judges cannot trigger an investigation from the frontend. They have to use the CLI or curl.
4. **Blast Radius screen** — The D3 `LineageGraph3D.tsx` exists but is it wired to real investigation data? Is it accessible from the main flow?

**The product flow that should exist (and currently does not):**
```
Landing Page → "Enter Investigation" → Select a model → 
Trigger investigation → Watch real-time SSE stream → 
See investigation timeline → Blast radius visualization → 
DataHub write-back proof panel → Resolution time comparison
```

Right now steps 3–7 are either broken, behind a URL judges won't find, or not connected to each other.

**What to actually do:**
1. Create a `/dashboard` page that is the actual product — not the landing page
2. Add a model selector (churn_model_v3, ltv_model_v2, etc.)
3. "Investigate" button that calls `POST /api/investigate` and streams via SSE
4. Wire the existing `LineageGraph3D.tsx` to the blast radius data from the investigation
5. Show a "DataHub Artifacts Written" panel after investigation completes
6. The landing page CTA button should go to this dashboard, not to docs

---

### GAP-4: The Open-Source Contribution Is Phantom (Score Impact: -2 pts on Bonus Criteria)

**Current state:** The README and strategy mention "contributed `datahub-meridian-ai` skill to `datahub-project/datahub-skills`" as a key differentiator to win with Nick Adams. The HACKATHON_STRATEGY.md says this is how you "capture the bonus criteria."

**Reality:** No PR has been submitted. The contribution is described as a future plan in every document.

**Why this matters:** Nick Adams is a judge. If he goes to `github.com/datahub-project/datahub-skills` and finds no PR from your team, the "meaningful open-source contribution" bonus criteria gets a zero. If there IS a PR — even a draft PR — he will find it and it will resonate deeply because he built the system you're contributing to.

**What to actually do (3 hours of work):**
1. Read the existing `datahub-skills` repo structure (it's public on GitHub)
2. Create a `meridian_ai/` skill directory following their pattern
3. Write a `SKILL.md` that documents how to use Meridian AI as a DataHub skill
4. Open a PR — a real PR, not a draft
5. Link the PR in your Devpost submission and README
6. Mention Nick Adams' name in the PR description: "Built for the DataHub Agent Hackathon, extends DataHub Skills with ML incident investigation capabilities"

This is the highest ROI action available to you right now. 3 hours → +2 bonus points → directly visible to the judge who built the system.

---

### GAP-5: The Flywheel Claim Is Unverifiable (Score Impact: -1 pt on Real-World Usefulness)

**Current state:** The flywheel is the core narrative: "18min → 8min → 3min." But `examples/resolution_times.json` shows fabricated numbers, and judges know it because the reflexion loop that should generate these improvements is never actually called between investigations in the demo.

**The actual problem:** The reflexion loop reads past playbooks from DataHub and updates them after each investigation. But in mock mode, there is no persistent Knowledge Base. Every investigation starts from zero. The flywheel cannot actually spin in the demo.

**What to actually do:**
1. Seed the DataHub Knowledge Base with 2-3 historical playbooks before the demo
2. Run investigation #1 in real DataHub — measure actual resolution time with `time.perf_counter()`
3. The knowledge_writer writes the root cause report and playbook
4. Run investigation #42 (same incident type) — the reflexion loop retrieves the playbook from Knowledge Base
5. Show that investigation #42 is faster because the playbook existed
6. This creates a REAL flywheel that judges can verify

If real DataHub isn't achievable: mock this correctly by making the reflexion loop actually read from the mock Knowledge Base between investigations. Right now mock data is stateless — each investigation is isolated. Make the mock Knowledge Base persistent across investigations in the same session.

---

## Part 2: Per-Judging-Criterion Analysis

### Criterion 1: Use of DataHub

**Current strength:** Strong on paper. 12+ MCP tool calls are documented.

**Hidden gap:** The Devpost says "24 capabilities" but assessment.md admits "12." The README says "9 tools." Pick ONE number and make sure every file says the same thing. Judges will cross-reference.

**Deeper gap:** Reading from DataHub is easy. Writing back is the differentiator. The write-back is the product. But judges cannot currently verify that writes actually happen in DataHub — they can only see it in mock mode output. The `examples/ai-knowledge/churn_model_v3.json` exists but judges need to see this IN DataHub's actual UI.

**Recommendation:** Record one 30-second clip of:
1. DataHub's churn_model_v3 entity page BEFORE investigation — no AI Knowledge panel
2. Run investigation (30 seconds)
3. Refresh DataHub — AI Knowledge panel NOW EXISTS with `resolved_incidents`, `health_score`, etc.

This clip is the entire Use of DataHub criterion in 30 seconds.

---

### Criterion 2: Technical Execution

**Current strength:** 21 workers, PSI/KS-test math, SHA-256, deterministic validation — all genuinely impressive.

**Critical gap from prgaps.md (Status unknown — are these actually fixed?):**
- BUG 2: Verification result is ignored (planner always proceeds regardless of verifier)
- BUG 3: Root cause = source node always (no actual causal inference)
- BUG 4: Feature drift uses hardcoded arrays (PSI math is real, inputs are fake)
- BUG 6: EU AI Act chain is in-memory (restart = chain lost)

These bugs exist in your own gap analysis from July 15. prgaps.md says they are fixed. **Are they?** The self_healing_assertions.py file you have open right now — is it wired into the planner? Is it actually called?

**Recommendation:** Run `meridian investigate` and trace every worker output:
- What does root_cause.py actually return? Is it the source node or a computed score?
- Does the verifier check result gate write-back? Add a log line to verify.
- Does feature_drift.py use entity metadata or hardcoded arrays?

If these bugs are not fixed, fix them before anything else. This is the difference between 7/10 and 9/10 on Technical Execution.

**Also missing:** The tests badge says "559 tests" but assessment.md says 359 and prgaps.md says 511. Standardize this. Judges will check `pytest tests/ -v` and count.

---

### Criterion 3: Originality

**Current strength:** The flywheel/reflexion loop is genuinely original. EU AI Act compliance is genuinely timely. The write-back pattern differentiates from every monitoring tool.

**The gap no document mentions:** The DataHub AI Tool Audit Dashboard (July 2026 Public Beta). MERIDIAN_ECOSYSTEM_EXPANSION.md identifies this as "Feature 3: Agent-to-Agent Audit Trail" and says "Nick Adams will recognize we are the ONLY team that used their newest feature." 

**Is this implemented?** The ECOSYSTEM doc calls it Critical Tier 1 but there is zero evidence in the backend/ directory that it's built. This is a "mentioned but phantom" feature — like the Skills PR.

**What to do:** Either implement it (legitimate 4-6 hours if DataHub's beta API is accessible) OR remove all mentions of it from every document. Phantom features hurt you when judges look for them and don't find them.

**The genuine originality anchor:** Your strongest originality claim — the one nobody else has — is that **DataHub's entity pages look smarter after every investigation.** This is a new use of DataHub's structured properties API that transforms a passive catalog into an active knowledge base. This has never been demonstrated in any hackathon or product before. Lead with this.

---

### Criterion 4: Real-World Usefulness

**The gap that kills this criterion:** The README "Run in 5 minutes" section leads with mock mode. Judges who follow Option 1 get a terminal that prints mock data. That does not demonstrate real-world usefulness.

**What makes something "real-world useful" to the judges:**
- Tim: "Would I recommend this to a Cloudflight client? Is it deployable?"
- Aman: "Would Pinterest's ML platform team use this? Does it plug into existing workflows?"
- Maggie: "Does this make DataHub's value proposition stronger to our customers?"

**Current answer:** Maybe, theoretically, with configuration. Not demonstrated.

**What to do:**
1. Add a "Real-World Deployment" section to the README that shows what happens at a company that uses DataHub in production
2. Create a `docs/production-deployment.md` that shows: "If you use DataHub Cloud + Groq API, here's how this deploys in 20 minutes"
3. The Quickstart should lead with: `docker-compose up && python scripts/seed_meridian.py && meridian investigate <real_urn>`

**Also:** The `$45,000/day` revenue at risk claim needs a cleaner citation. "32K predictions × $1.41/prediction" — where does $1.41 come from? Judges from ML-heavy companies (Aman at Pinterest) will ask this. Either cite a source or make it configurable (users input their own revenue-per-prediction).

---

### Criterion 5: Submission Quality

**This is your current weakest criterion (honest assessment from gaps.md: "5/10").**

**The blockers:**
1. **No demo video** — absolute requirement, currently "[recording pending]"
2. **No live URL** — all judges must run it locally; many won't
3. **Devpost description inconsistencies** — "24 capabilities" vs "12" vs "9" across different files

**What a 10/10 Devpost looks like:**
- Video embedded at the top (YouTube link, unlisted)
- Live demo URL that works (Vercel for frontend + Railway for backend)
- README that opens with ONE clear "how to see this working in 60 seconds" instruction
- Screenshots embedded in the README (NOT ascii art — actual PNG screenshots)
- Clear link to the DataHub Skills PR

**Minimum viable submission quality to win:**
- Video recorded (even screen recording with OBS — 3 minutes, 1 take)
- `docker-compose up && python scripts/seed_meridian.py && open http://localhost:3000` works end-to-end
- README has 2-3 screenshots of the actual frontend UI (not mockups)
- Devpost description has consistent numbers

---

## Part 3: The Five Things Nobody Else Has (Keep These — They Are Your Moat)

1. **Write-back to DataHub as structured properties on entity pages** — nobody else changes the DataHub entity model. Every other tool is external.

2. **Reflexion loop that writes improved playbooks back to DataHub Knowledge Base** — the cumulative intelligence story is unique. No competitor does this.

3. **Deterministic validation layer gating LLM writes** — "LLMs reason, code verifies, then write" — this is the production safety pattern that enterprise judges (Tim) will immediately recognize as correct.

4. **EU AI Act Article 12 SHA-256 audit chain stored in DataHub** — this is 29 days from enforcement. Every enterprise judge will react to this.

5. **Progressive Autonomy (5 levels) with human-in-the-loop for irreversible actions** — Maggie Hays and Tim Bossenmaier will both care deeply about this. It demonstrates you understand production deployment concerns.

---

## Part 4: The 12 Things That Are Hurting You That Nobody Has Said Clearly

### 4.1 Document Inconsistency (Judge Killer)

You have 10+ strategy documents that contradict each other:
- README says "9 DataHub tools" / Devpost says "24 capabilities" / assessment says "12"
- README says "559 tests" / assessment says "359" / prgaps says "511"
- README says "14 workers" / title says "21 workers" / badge says "21"

Judges will notice. It looks like a team that doesn't know their own product. Pick one set of numbers, make them true (run the tests, count the tools), and use them everywhere.

### 4.2 The Strategy Docs Are Not Your Product

HACKATHON_STRATEGY.md is 2,850 lines. MERIDIAN_ECOSYSTEM_EXPANSION.md is 455 lines. These are planning documents, not a product. The danger: you have spent enormous time documenting what to build and not enough time building it. Every hour spent on a strategy doc is an hour not spent making `DATAHUB_MOCK=false` actually work.

### 4.3 The Frontend Doesn't Tell the Story

The landing page is beautiful but it sells features. Judges need to USE the tool, not read about it. The 4 hero screens from HACKATHON_STRATEGY.md (Resolution Time Graph, Investigation Timeline, DataHub Model Page, Blast Radius) should be 4 real, working pages that judges can navigate. Currently, they are described in 2,850 lines of strategy but 2 of them don't exist as pages.

### 4.4 No Live URL Is a Major Handicap

Every submission with a live Vercel/Railway/Render URL will beat every submission that requires docker-compose to demo. Judges are reviewing 50+ submissions. The ones they spend 5 minutes with are the ones they can click a URL and see working. Deploy. This alone moves you from bottom 10 to top 10 in submission quality.

### 4.5 The Video Script Doesn't Use the Frontend

The VIDEO_SCRIPT.md shows terminal output and architecture diagrams. A judge who watched that video would not know you have a beautiful Next.js dashboard with particle effects, glassmorphism, and real-time SSE streaming. The frontend is your most visible differentiator and the video script hides it entirely.

### 4.6 The "21 Workers" Badge Is Confusing

"21 workers" is a lot to communicate. But judges care about which workers actually demonstrate the core value proposition, not the total count. Lead with 4 workers that create the narrative: DataSentinel → RootCause → KnowledgeWriter → ReflexionLoop. The other 17 are supporting cast. In the video, name 4. In the demo, show 4. In the README, lead with 4. After judges are convinced, they can read the full list.

### 4.7 The Replay Mode and Demo Mode Aren't Clearly Separated

The strategy mentions a "Replay Mode" and a "Playback Driver" for zero-friction judge experience. But assessment.md admits the demo is pre-recorded mock data. If the replay mode is your judge experience strategy, make it crystal clear: "Click this button to see a pre-recorded investigation replay — all events are real investigation outputs, replayed at 2x speed." That is honest and still impressive. What you can't do is present a replay as a live investigation.

### 4.8 The `datahub-meridian-ai` Skill PR Is Mentioned Everywhere but Doesn't Exist

This is referenced in: HACKATHON_STRATEGY.md, DEVPOST_SUBMISSION.md, README.md, DataHub Integration table. Nick Adams is a judge. He will check GitHub. Either submit the PR or remove every mention.

### 4.9 The EU AI Act Claim Has a Credibility Problem

The SHA-256 audit chain is real. But assessment.md says "the audit chain lives in a Python list. Server restart = chain lost." If the EU AI Act chain is in-memory, it fails the first test of a real audit. DataHub is specifically mentioned as the persistence layer, but the current implementation doesn't write the chain to DataHub — it stores it locally.

**Fix:** Write the SHA-256 chain to DataHub's Knowledge Base as a document after every investigation. One `save_document()` call. This turns a demo feature into a real one.

### 4.10 The Business Impact Numbers Are All the Same

Every scenario: "$45,000/day," "32,000 predictions," "churn_model_v3." The demo looks like one incident on infinite repeat. Judges want to see the system generalize. Seed at least 3 different model types with different revenue impacts:
- `churn_model_v3`: $45K/day
- `ltv_model_v2`: $12K/day  
- `fraud_detection_v1`: $200K/day

This makes the blast radius calculation look like it actually computed something, not just printed a constant.

### 4.11 The `knowledge_mimo.md` File (89,636 bytes) Should Not Be In the Root

Judges who look at the repo structure will see a 90KB file called `knowledge_mimo.md` in the project root. This looks like a personal notes file accidentally committed. Either move it to a `docs/internal/` directory or remove it from the repo.

Similarly: `HACKATHON_STRATEGY.md` (140KB), `MERIDIAN_ECOSYSTEM_EXPANSION.md`, `MERIDIAN_MASTER_STRATEGY.md`, `mimo_newidea.md`, `prgaps.md`, `assessment.md`, `gaps.md` — these are all internal planning documents that should NOT be in the public repo. They contain admissions like "root cause is always the source node" and "probably will fail with real DataHub" that will hurt you if judges read them. Move them to a `planning/` directory and add it to `.gitignore`.

### 4.12 The SSE Stream Has No Error Recovery

gap.md F5 and S1 both identify this. The EventSource in the frontend closes on error with no retry. During the live demo at the hackathon, if the stream drops once, the investigation UI becomes a blank screen. This is a demo-killing bug that is 30 lines of code to fix. It should be the first code fix after the video is recorded.

---

## Part 5: The 3-Day Sprint to Maximize Score

### Day 1: Make It Real

**Morning (4 hours):**
- [ ] Spin up DataHub via docker-compose
- [ ] Run `python scripts/seed_meridian.py`
- [ ] Set `DATAHUB_MOCK=false` and run `meridian investigate`
- [ ] Fix every error until it works
- [ ] Verify the 4 DataHub writes actually appear in the DataHub UI

**Afternoon (4 hours):**
- [ ] Fix BUG 2: Make verification result gate write-back
- [ ] Fix BUG 3: Root cause should use `compute_root_cause_score`, not source node
- [ ] Fix BUG 4: Feature drift should use entity schema fields, not hardcoded arrays
- [ ] Fix EU AI Act chain: write to DataHub Knowledge Base, not in-memory list

### Day 2: Record the Video and Deploy

**Morning (3 hours):**
- [ ] Standardize ALL numbers across ALL documents (one source of truth)
- [ ] Move planning docs (`gaps.md`, `prgaps.md`, `assessment.md`, `knowledge_mimo.md`, etc.) to `planning/` and gitignore
- [ ] Add 3 different model scenarios with different revenue impacts

**Afternoon (3 hours):**
- [ ] Deploy frontend to Vercel
- [ ] Deploy backend to Railway or Render
- [ ] Verify live URL works end-to-end

**Evening (2 hours):**
- [ ] Record the 3-minute video following the structure in GAP-2 above
- [ ] Use OBS or Loom — real DataHub UI visible, real writes happening
- [ ] Upload to YouTube (unlisted)
- [ ] Update Devpost with video link and live URL

### Day 3: The Open-Source PR and Final Polish

**Morning (3 hours):**
- [ ] Submit the `datahub-meridian-ai` skill PR to `datahub-project/datahub-skills`
- [ ] Add README screenshots (real screenshots, not ASCII art)
- [ ] Add SSE reconnection logic to frontend (30-line fix from gap.md S1)
- [ ] Add "Run Investigation" button to the dashboard

**Afternoon (3 hours):**
- [ ] Fix frontend: add loading skeletons (F3), error handling (F1)
- [ ] Create the 4 hero screens as real pages: dashboard with resolution time graph, investigation timeline, blast radius, write-back proof
- [ ] Final pass: read Devpost submission aloud, check every claim against the code

---

## Part 6: The Winning Narrative (What to Say When)

### The 30-Second Hook (First words of the video):

> "Every ML incident at most companies creates tribal knowledge that disappears forever. Meridian AI changes that — permanently. In 8 seconds, it reads your DataHub lineage, traces the root cause, and writes everything it learned into DataHub. So the next time the same model breaks, the AI already knows what to do. Watch."

Then immediately show the investigation running. No architecture slides. No problem definition. Show the thing working.

### The Emotional Payoff (1:20 in the video):

> "This is the moment. Let's open DataHub. Here is churn_model_v3 — before the investigation, no AI Knowledge panel. Now — 30 seconds later — look at this. Resolved incidents: 14. Known failure patterns: 3. Health score: 81. The AI wrote this. DataHub itself became smarter. This is not external monitoring. This is DataHub as an organizational brain."

This moment will be referenced in every judge's notes. It is the unforgettable proof that you did something nobody else did.

### The Close (2:45 in the video):

> "pip install meridian-ai. One command. Apache 2.0. No login. If your team runs DataHub in production, you have everything you need to stop losing money to silent ML failures that your team didn't even know were happening. The next incident — your AI already knows what to do."

---

## Part 7: What This Project Actually Is (And Why It Can Win)

The strategy documents describe Meridian AI as "the only system that makes DataHub smarter every time an ML incident occurs." This is true. And it is enough to win.

You do not need 21 workers. You do not need to address all 4 challenges. You do not need EU AI Act compliance AND FinOps attribution AND Shadow AI discovery AND LLM hallucination tracing.

You need 4 workers that work correctly against a real DataHub instance, a frontend that shows the investigation in real-time, a DataHub entity page that visibly changes after the investigation, and a 3-minute video that shows all three of these things happening live.

The team that wins Grand Prize will not have the most features. They will have the most clearly demonstrated value, delivered with the most confidence, to judges who can verify it themselves in 5 minutes.

**That can be you. But only if you stop writing documents about what to build and start making what you have actually work.**

---

## Appendix: Specific Files That Need Attention Before Submission

| File | Issue | Priority |
|------|-------|----------|
| `knowledge_mimo.md` (89KB) | Personal notes in root dir, should be removed from public repo | HIGH |
| `HACKATHON_STRATEGY.md` (140KB) | Internal planning doc, should be in `planning/` + gitignored | HIGH |
| `assessment.md` | Contains "probably will fail with real DataHub" — remove before judges see | HIGH |
| `prgaps.md` | Admits "root cause is always source node" — remove before judges see | HIGH |
| `gaps.md` | Admits "Frontend: 4/10" — remove before judges see | HIGH |
| `DEVPOST_SUBMISSION.md` | Has "[recording pending]" — update with real video link | CRITICAL |
| `backend/workers/root_cause.py` | Root cause = source node always | CRITICAL |
| `backend/workers/feature_drift.py` | Hardcoded arrays for PSI inputs | CRITICAL |
| `backend/workers/eu_ai_act_compliance.py` | Chain is in-memory, not persisted to DataHub | CRITICAL |
| `frontend/app/incidents/[id]/page.tsx` | No SSE reconnection on error | HIGH |
| `README.md` | Inconsistent numbers (9/12/24 tools, 14/21 workers, 359/511/559 tests) | HIGH |

---

*Written: July 19, 2026*
*Analyzed: All major project files including README.md, gaps.md, prgaps.md, assessment.md, HACKATHON_STRATEGY.md (lines 1-800), MERIDIAN_ECOSYSTEM_EXPANSION.md, DEVPOST_SUBMISSION.md, VIDEO_SCRIPT.md, frontend/app/page.tsx, backend/ directory structure (40 files)*
