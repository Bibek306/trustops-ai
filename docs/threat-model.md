# TrustOps Threat Model

## Assets
- approved organizational evidence
- generated questionnaire responses
- reviewer decisions
- audit history

## Key threats

| Threat | Control |
|---|---|
| Hallucinated answer | evidence-only prompt + abstention |
| Stale policy retrieval | approved/current/latest-version filtering |
| Expired evidence | effective/expiry validation |
| Unsupported generated claim | post-generation claim verification |
| High-impact answer released automatically | risk routing + human review |
| Prompt injection inside evidence | evidence is treated as data; agent has no release tool |
| Agent privilege escalation | least-privilege/agent tools |
| Untraceable response | chunk-level provenance + audit events |
| Reviewer decision lost | persisted review records |

## Known prototype limitations
Authentication/RBAC, durable workflow checkpoints, encryption at rest, secret management, rate limiting, and multi-tenant isolation are not yet implemented. These must be added before handling real customer data.
