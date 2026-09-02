import re
from typing import Iterable


# Information that should be blocked when the user is asking to obtain,
# reveal, provide, or disclose the actual secret/restricted value.
SECRET_PATTERNS = [
    r"\bpassword\b",
    r"\bpasswd\b",
    r"\bapi[\s-]?key\b",
    r"\baccess[\s-]?token\b",
    r"\bprivate[\s-]?key\b",
    r"\bdatabase credentials?\b",
    r"\bdatabase password\b",
    r"\bconnection string\b",
    r"\bencryption key\b",
    r"\bsecurity key\b",
    r"\bcredentials?\b",
]

PROTECTED_DATA_PATTERNS = [
    r"\bcustomer records?\b",
    r"\bcustomer information\b",
    r"\bcustomer data\b",
    r"\bpersonal data\b",
    r"\bemployee information\b",
    r"\bfinancial information\b",
]

DISCLOSURE_VERBS = [
    "give me",
    "show me",
    "provide",
    "reveal",
    "tell me",
    "send me",
    "share",
    "display",
    "list",
    "export",
    "retrieve",
    "get me",
    "what is",
    "what are",
]


SENSITIVE_KEYWORDS = [
    "internal network",
    "internal architecture",
    "incident details",
    "vulnerability details",
    "security incident",
    "confidential",
    "restricted",
]


def _contains_any(text: str, patterns: list[str]) -> list[str]:
    matches = []

    for pattern in patterns:
        if re.search(pattern, text):
            matches.append(pattern)

    return matches


def _is_disclosure_request(question: str) -> tuple[bool, list[str]]:
    """
    Detect whether the user is trying to obtain protected information.

    Important:
    "Is customer data encrypted?" is NOT a disclosure request.

    "Give me the customer data." IS a disclosure request.
    """

    q = question.lower().strip()

    disclosure_requested = any(
        verb in q for verb in DISCLOSURE_VERBS
    )

    secret_matches = _contains_any(q, SECRET_PATTERNS)
    protected_data_matches = _contains_any(q, PROTECTED_DATA_PATTERNS)

    # Direct requests for secrets are always treated as confidential.
    if secret_matches:
        return True, secret_matches

    # Protected data is confidential only when the question is actually
    # requesting the data rather than asking about its security/control.
    if protected_data_matches and disclosure_requested:
        return True, protected_data_matches

    return False, []


def risk_assessment(question: str, evidence: Iterable[object]) -> dict:
    evidence = list(evidence)
    q = question.lower().strip()

    confidentiality_flag, confidential_matches = _is_disclosure_request(q)

    sensitive_matches = [
        term for term in SENSITIVE_KEYWORDS
        if term in q
    ]

    compliance = any(
        x in q
        for x in [
            "iso",
            "soc 2",
            "soc2",
            "certification",
            "certified",
            "regulatory",
            "compliance",
            "attestation",
        ]
    )

    commitment = any(
        x in q
        for x in [
            "guarantee",
            "warranty",
            "contract",
            "sla",
            "promise",
            "will you",
        ]
    )

    security_impact = any(
        x in q
        for x in [
            "breach",
            "incident",
            "encryption",
            "encrypt",
            "mfa",
            "access",
            "retention",
            "delete",
            "backup",
        ]
    )

    if confidentiality_flag:
        level = "high"
    elif sensitive_matches or compliance or commitment:
        level = "high"
    elif security_impact:
        level = "medium"
    else:
        level = "low"

    if not evidence and level == "low":
        level = "high"

    score = {
        "low": 0.25,
        "medium": 0.55,
        "high": 0.85,
    }[level]

    if not evidence:
        score = min(1.0, score + 0.12)

    factors = []

    if confidentiality_flag:
        factors.append(
            "confidential_or_restricted_information_request"
        )

    if sensitive_matches:
        factors.append(
            "sensitive_internal_information_request"
        )

    if compliance:
        factors.append(
            "compliance_or_certification_claim"
        )

    if commitment:
        factors.append(
            "external_commitment_claim"
        )

    if security_impact:
        factors.append(
            "security_control_claim"
        )

    if not evidence:
        factors.append(
            "no_approved_current_evidence"
        )

    if not factors:
        factors.append(
            "general_information_request"
        )

    return {
        "risk_level": level,
        "risk_score": round(score, 2),
        "trust_score": int((1 - score) * 100),
        "factors": factors,
        "requires_human_review": level == "high",
        "confidentiality_flag": confidentiality_flag,
        "confidentiality_matches": confidential_matches,
        "evidence_count": len(evidence),
        "evidence_coverage_hint": round(
            min(len(evidence) / 3.0, 1.0),
            2,
        ),
    }