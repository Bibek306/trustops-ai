# Simple Evaluation

TrustOps uses only three evaluation metrics. This keeps the project easy to understand while still showing that the RAG system was tested.

## 1. Retrieval Recall@5

For answerable questions, the test dataset specifies the expected evidence group. We check whether that group appears in the top 5 retrieved chunks.

## 2. Grounded Answers

For answerable questions, we check whether the generated answer passes TrustOps' evidence-based claim verification.

## 3. Safe Abstention

For questions deliberately not covered by the evidence, we check whether TrustOps refuses to give a definitive answer.

## Run

From the project root:

```powershell
python -m evaluation.evaluate
```

Do not put benchmark numbers on your resume until you have run this against your own approved evidence set.
