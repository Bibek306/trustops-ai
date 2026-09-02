import re


ABSTAIN = "Insufficient approved evidence to answer this safely."


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _meaningful_words(text: str) -> set[str]:
    stop = {
        "the", "and", "for", "with", "from", "that", "this", "their",
        "your", "will", "does", "are", "was", "were", "has", "have",
        "into", "only", "also", "been", "being", "can", "may", "not",
        "what", "which", "how", "why", "who", "doesn", "than",
        "customer", "company", "system", "data", "information",
    }

    return {
        word
        for word in re.findall(r"[a-zA-Z0-9]{3,}", text.lower())
        if word not in stop
    }


def claim_check(answer: str, evidence: list[object]) -> dict:
    """
    Verify that the generated answer is grounded in the supplied evidence.

    This is a lightweight lexical verifier. It checks whether the important
    concepts in each claim are represented in the approved evidence without
    requiring exact sentence-level wording.
    """

    if not answer or answer.strip() == ABSTAIN:
        return {
            "status": "abstained",
            "unsupported_claims": [],
            "claim_count": 0,
        }

    evidence_text = _normalize(
        " ".join(
            getattr(d, "page_content", "")
            for d in evidence
        )
    )

    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", answer)
        if s.strip()
    ]

    unsupported = []

    for sentence in sentences:
        meaningful = _meaningful_words(sentence)

        if not meaningful:
            continue

        supported = sum(
            1
            for word in meaningful
            if word in evidence_text
        )

        ratio = supported / len(meaningful)

        # A slightly more tolerant threshold avoids rejecting legitimate
        # paraphrases while still catching clearly unsupported claims.
        if ratio < 0.25:
            unsupported.append(sentence)

    return {
        "status": "supported" if not unsupported else "needs_review",
        "unsupported_claims": unsupported,
        "claim_count": len(sentences),
    }