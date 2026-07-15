# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Meridian AI, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email security concerns to: [maintainer email]
3. Include: description, steps to reproduce, potential impact

We will respond within 48 hours and work with you on a fix.

## Security Measures

### Authentication
- JWT authentication (opt-in via `AUTH_ENABLED=true`)
- Tokens expire after configurable duration (default: 30 minutes)
- Public paths bypass auth: `/health`, `/docs`, `/openapi.json`

### Input Validation
- Pydantic schemas validate all API inputs
- Request body size limit: 10MB (configurable via `MAX_BODY_SIZE`)
- Rate limiting: 60 req/min (configurable via `MAX_RPM`)

### Data Protection
- Secrets stored in environment variables, never in code
- `.env.secrets` is gitignored
- CORS origins configurable (default: `*` for dev, restrict in production)

### Audit Trail
- EU AI Act compliant SHA-256 hash chain
- All AI decisions logged with full context
- Chain persisted to `data/audit_chain.json`

### Infrastructure
- Docker images use non-root user (when configured)
- Health checks enabled in Dockerfile
- Resource limits enforced in docker-compose

## Dependencies

Run `pip audit` regularly to check for known vulnerabilities:

```bash
pip install pip-audit
pip-audit
```

## Configuration Security

| Setting | Default | Production Recommendation |
|---------|---------|---------------------------|
| `AUTH_ENABLED` | `false` | `true` |
| `JWT_SECRET_KEY` | random | Strong random string |
| `CORS_ORIGINS` | `*` | Specific domains |
| `DATAHUB_MOCK` | `true` | `false` with real DataHub |
