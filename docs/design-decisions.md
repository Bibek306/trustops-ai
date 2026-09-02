# Design Decisions

## Why the LLM is not the authority
LLMs are useful for language generation but can produce unsupported claims. TrustOps therefore separates drafting from evidence governance and release.

## Why approval precedes retrieval
An indexed document is not automatically trusted. Explicit approval creates a governance boundary between ingestion and usable evidence.

## Why version filtering is deterministic
Document recency and validity are policy decisions, not generation tasks. They should be enforced outside the model.

## Why human review is a release gate
Compliance claims, commitments, and unsupported security claims can have business consequences. The model can draft but cannot approve or release them.

## Why the agent has no release tool
Giving an LLM an irreversible or high-impact tool creates unnecessary blast radius. TrustOps uses least privilege: read evidence and create drafts, nothing more.
