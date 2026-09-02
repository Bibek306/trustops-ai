"""Simple TrustOps evaluation: only three metrics."""
import json
from pathlib import Path

from app.main import governed_answer, retrieve_evidence

DATASET = Path(__file__).with_name("dataset.json")
ABSTAIN_TEXT = "Insufficient approved evidence to answer this safely."


def main():
    cases = json.loads(DATASET.read_text(encoding="utf-8"))
    retrieval_hits = 0
    retrieval_total = 0
    grounded_hits = 0
    grounded_total = 0
    abstain_hits = 0
    abstain_total = 0

    for case in cases:
        evidence = retrieve_evidence(case["question"], k=5)
        if case["answerable"]:
            retrieval_total += 1
            groups = {d.metadata.get("group") for d in evidence}
            if case["expected_group"] in groups:
                retrieval_hits += 1

            result = governed_answer(case["question"], f"eval-{case['id']}")
            grounded_total += 1
            if result["verification"]["status"] in {"supported", "abstained"} and result["answer"] != ABSTAIN_TEXT:
                grounded_hits += 1
        else:
            abstain_total += 1
            result = governed_answer(case["question"], f"eval-{case['id']}")
            if result["answer"] == ABSTAIN_TEXT:
                abstain_hits += 1

    def pct(hit, total):
        return round((hit / total) * 100, 1) if total else 0.0

    print("\nTrustOps Evaluation")
    print("-------------------")
    print(f"Retrieval Recall@5 : {pct(retrieval_hits, retrieval_total)}%")
    print(f"Grounded Answers   : {pct(grounded_hits, grounded_total)}%")
    print(f"Safe Abstention    : {pct(abstain_hits, abstain_total)}%")
    print(f"Answerable cases   : {retrieval_total}")
    print(f"Unanswerable cases : {abstain_total}")


if __name__ == "__main__":
    main()
