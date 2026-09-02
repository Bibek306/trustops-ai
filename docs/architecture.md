# TrustOps Architecture

## Purpose
TrustOps is designed around a simple rule: **the LLM is a drafting component, not the source of truth and not the final release authority.**

## Pipeline
1. Evidence ingestion extracts text and records document provenance.
2. Documents are chunked and indexed into Chroma.
3. An evidence owner explicitly approves a version before retrieval can use it.
4. Retrieval uses MMR and filters to the latest currently valid approved version in each evidence group.
5. The LLM drafts an answer only from retrieved evidence.
6. A deterministic claim verifier flags poorly supported generated claims.
7. A risk engine considers compliance, commitment, security-control, and evidence-availability factors.
8. High-risk, unsupported, or evidence-free responses are routed to human review.
9. Audit events record ingestion, approval, generation, blocking, and review decisions.

## Agent boundary
The Deep Agent:
- `search_approved_evidence`
- `draft_governed_answer`

They do **not** expose approval, release, deletion, evidence modification, or sending tools. This is a least-privilege boundary.

## Version governance
Each evidence group can have multiple versions. Retrieval considers only approved, currently valid documents and chooses the newest version in the group. Expired or future-effective evidence is excluded.

## Production hardening roadmap
- Replace SQLite with PostgreSQL.
- Add authentication/RBAC around evidence owners and reviewers.
- Replace in-memory LangGraph checkpointing with a durable checkpointer.
- Add a dedicated reranker and benchmark retrieval recall/MRR.
- Expand claim verification to an LLM-as-judge plus deterministic checks, with a human-audited test set.
- Add rate limits, structured logging, secrets management, and object storage for uploaded files.
