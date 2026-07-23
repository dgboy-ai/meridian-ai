# Meridian AI — Security & Compliance

> Security architecture, EU AI Act compliance, and audit trail implementation.

## Security Architecture

### Authentication

| Component | Implementation | Details |
|-----------|---------------|---------|
| JWT Tokens | HS256 signing | Auto-generated secret key via `secrets.token_hex(32)` |
| Password Storage | SHA-256 hashing | Demo users hashed, production should use bcrypt |
| Password Policy | Minimum 8 characters | Enforced on registration |
| Token Expiry | 30 minutes | Configurable via `AUTH_ACCESS_TOKEN_EXPIRE_MINUTES` |
| Auth Toggle | Opt-in via `AUTH_ENABLED=true` | Disabled by default for zero-friction demo |

### Input Validation

| Check | Implementation | Location |
|-------|---------------|----------|
| Pydantic Schemas | All API inputs validated | `backend/schemas.py` |
| Body Size Limit | 10MB max on POST/PUT/PATCH | `backend/main.py` middleware |
| Rate Limiting | 60 req/min per process | `backend/main.py` RateLimiter |
| Path Validation | Incident IDs max 50 chars | `backend/main.py` endpoints |

### CORS Configuration

| Setting | Default | Production |
|---------|---------|-----------|
| Origins | `*` | Specific domains |
| Credentials | `false` | `true` with specific origins |
| Methods | GET, POST, PUT, PATCH, DELETE | Restrict as needed |
| Headers | Authorization, Content-Type | Restrict as needed |

### Data Protection

| Measure | Implementation |
|---------|---------------|
| Secrets | Environment variables, never in code |
| `.env.secrets` | Gitignored |
| Docker | Non-root user, resource limits |
| Audit Trail | SHA-256 hash chain for all AI decisions |

## EU AI Act Compliance

### Articles Covered

| Article | Name | What Meridian Does |
|---------|------|-------------------|
| **Article 12** | Record-Keeping | Automatic logging of all AI decisions with timestamps, confidence scores, reasoning chains |
| **Article 13** | Transparency | Investigation Timeline shows what AI found, why it concluded, what it did next |
| **Article 14** | Human Oversight | Progressive Autonomy ensures humans approve irreversible actions |

### SHA-256 Audit Chain

Every AI decision is logged with a SHA-256 hash. Each hash includes the previous hash, creating a blockchain-like chain that's cryptographically verifiable.

```json
{
  "record_id": "audit-2026-07-12T14:32:00Z",
  "timestamp": "2026-07-12T14:32:00Z",
  "article": "12",
  "system_name": "Meridian AI",
  "decision_type": "ROOT_CAUSE_ANALYSIS",
  "confidence": 0.96,
  "reasoning_chain": [
    "Schema change detected in raw_events.age",
    "Lineage traversal: raw_events → feature_pipeline → churn_model_v3",
    "Blast radius: 3 models, 12 dashboards"
  ],
  "hash_sha256": "a1b2c3d4...",
  "previous_hash": "e5f6g7h8..."
}
```

### Technical File Generation

Per investigation, Meridian generates a Technical File containing:
- All audit records for the investigation
- Chain integrity verification (hash linkage)
- Article coverage summary
- Confidence scores across all decisions

## Deterministic Validation Layer

Before any write-back to DataHub, Meridian runs 4 deterministic checks:

| Check | What It Does | On Failure |
|-------|-------------|-----------|
| **Confidence Threshold** | Worker confidence must be > 0.7 | Reject, request more evidence |
| **Entity Exists** | DataHub URN verified before mutation | Reject, log error |
| **Action Safety** | Destructive actions queued for human approval | Warning (soft check) |
| **Duplicate Check** | Prevents raising duplicate incidents | Skip, update existing |

### Maker-Checker Verification

The VerifierAgent challenges RootCause conclusions before write-back:
- If verification confidence < 0.5: knowledge write-back skipped entirely
- If verification confidence >= 0.5: proceed with write-back
- Full reasoning chain preserved for audit

## Progressive Autonomy

| Level | Name | Behavior | Applied To |
|-------|------|----------|-----------|
| **0** | Advisory | Suggests only; human executes | Root Cause, Explanation Drift |
| **1** | Supervised | Executes with pre-approval | Model Health |
| **2** | Monitored | Executes; human reviews post-hoc | Data Sentinel, Feature Drift |
| **3** | Autonomous | Executes without human involvement | Contract Enforcement, Knowledge Writing |
| **4** | Self-improving | Refines its own procedures via reflexion | After sufficient incident history |

## Agentic Circuit Breaker

Monitors agent reasoning health in real-time:
- **Loop detection**: Repeated identical reasoning
- **Semantic drift**: Conclusions diverging from evidence
- **Confidence degradation**: Declining worker confidence
- **Timeout enforcement**: Max investigation duration

## Provenance Tracking

Every worker tracks which context sources were used:
- Source trust scoring (verified vs unverified)
- Freshness scoring (how recent is the data)
- Full audit trail for compliance and debugging
- Which LLM calls were made and their inputs

## Security Checklist for Production

- [ ] Set `AUTH_ENABLED=true`
- [ ] Generate strong `AUTH_SECRET_KEY`
- [ ] Use bcrypt for password hashing (replace SHA-256 demo)
- [ ] Restrict CORS origins to specific domains
- [ ] Enable Elasticsearch authentication
- [ ] Use Docker secrets for database passwords
- [ ] Set up per-IP rate limiting
- [ ] Add security headers (CSP, HSTS, X-Frame-Options)
- [ ] Enable audit trail persistence
- [ ] Configure token revocation mechanism
