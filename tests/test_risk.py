from types import SimpleNamespace
from app.risk import risk_assessment
from app.verification import claim_check


def doc(text):
    return SimpleNamespace(page_content=text, metadata={"document_id": "d1"})


def test_compliance_claim_is_high_risk():
    result = risk_assessment("Are you ISO 27001 certified?", [doc("Certification evidence")])
    assert result["risk_level"] == "high"
    assert result["requires_human_review"] is True


def test_security_control_is_medium_risk():
    result = risk_assessment("Is customer data encrypted at rest?", [doc("Customer data is encrypted at rest.")])
    assert result["risk_level"] == "medium"


def test_no_evidence_escalates_low_risk_question():
    result = risk_assessment("Do you have an office in Berlin?", [])
    assert result["risk_level"] == "high"
    assert result["requires_human_review"] is True


def test_supported_claim_passes():
    result = claim_check("Customer data is encrypted at rest.", [doc("Customer data is encrypted at rest using managed encryption.")])
    assert result["status"] == "supported"


def test_unsupported_claim_is_flagged():
    result = claim_check("We guarantee 99.99% uptime.", [doc("We monitor service availability.")])
    assert result["status"] == "needs_review"
    assert result["unsupported_claims"]


def test_missing_evidence_is_abstention():
    result = claim_check("Insufficient approved evidence to answer this safely.", [])
    assert result["status"] == "abstained"
