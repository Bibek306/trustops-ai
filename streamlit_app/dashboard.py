import os
import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Streamlit Cloud secret -> environment variable before importing app.main.
try:
    if not os.getenv("HF_TOKEN") and "HF_TOKEN" in st.secrets:
        os.environ["HF_TOKEN"] = st.secrets["HF_TOKEN"]
except Exception:
    pass

from app.main import Base, Session, Doc, engine, now, governed_answer, get_vectorstore
from app.main import LCDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import select
from uuid import uuid4

st.set_page_config(page_title="TrustOps AI", page_icon="🛡️", layout="wide")
st.title("🛡️ TrustOps AI")
st.caption("Evidence-governed AI for security questionnaire automation")

if not os.getenv("HF_TOKEN"):
    st.error("Add HF_TOKEN to .env or Streamlit Secrets.")
    st.stop()

@st.cache_resource
def setup_demo():
    Base.metadata.create_all(engine)

    text = (ROOT / "data" / "acmecloud_security_policy.txt").read_text(
        encoding="utf-8"
    )

    with Session() as db:
        doc = db.scalars(
            select(Doc).where(
                Doc.group == "demo-policy",
                Doc.version == "v1",
            )
        ).first()

        if not doc:
            doc = Doc(
                id=uuid4().hex,
                filename="acmecloud_security_policy.txt",
                group="demo-policy",
                version="v1",
                text=text,
                status="indexed",
                effective_at=now(),
            )
            db.add(doc)
            db.commit()
        else:
            # Refresh the demo document from the current TXT file.
            doc.text = text
            doc.status = "indexed"
            doc.approved_at = None
            doc.approved_by = None
            db.commit()

        pieces = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=120,
        ).create_documents([doc.text])

        vs = get_vectorstore()

        # Remove old chunks for this demo document.
        existing = vs.get(where={"document_id": doc.id})

        if existing.get("ids"):
            vs.delete(ids=existing["ids"])

        # Add the complete, refreshed document.
        vs.add_documents(
            [
                LCDocument(
                    page_content=p.page_content,
                    metadata={
                        "document_id": doc.id,
                        "filename": doc.filename,
                        "version": doc.version,
                        "group": doc.group,
                        "chunk_index": i,
                    },
                )
                for i, p in enumerate(pieces)
            ]
        )

        doc.status = "approved"
        doc.approved_at = now()
        doc.approved_by = "TrustOps Demo"
        db.commit()


try:
    setup_demo()
except Exception as exc:
    st.error(f"Could not initialize the demo evidence: {exc}")
    st.stop()

with st.sidebar:
    st.header("Try it")
    st.write("The demo uses one approved sample security policy.")
    st.write("Good question: Is customer data encrypted at rest?")
    st.write("Challenge: Are you ISO 27001 certified?")

question = st.text_area("Security question", "Is customer data encrypted at rest?")
if st.button("Generate governed answer", type="primary"):
    with st.spinner("Retrieving evidence and verifying the answer..."):
        try:
            result = governed_answer(question, "public-demo")
        except Exception as exc:
            st.error(f"TrustOps could not process the question: {exc}")
            st.stop()

    a, b, c = st.columns(3)
    a.metric("Risk", result["risk"]["risk_level"].upper())
    b.metric("Trust score", f"{result['risk']['trust_score']}/100")
    c.metric("Status", result["trust_status"].replace("_", " ").title())

    st.subheader("Answer")
    st.info(result["answer"])

    st.subheader("Verification")
    if result["verification"]["status"] == "supported":
        st.success("✓ Answer is supported by retrieved evidence.")
    elif result["verification"]["status"] == "abstained":
        st.warning("⚠ TrustOps abstained because evidence was insufficient.")
    else:
        st.warning("⚠ Some claims need human review.")

    st.subheader("Evidence cards")
    seen = set()

    for card in result["citations"]:
        key = (
            card["filename"],
            card["version"],
            card["chunk_index"],
        )

        if key in seen:
            continue

        seen.add(key)

        with st.expander(
            f"{card['filename']} · {card['version']} · chunk {card['chunk_index']}"
        ):
            st.write(card["quote"])

st.divider()
st.markdown("**Flow:** Question → RAG → Approved Evidence → Draft → Verification → Risk → Human Review")
st.caption("LangChain • RAG • Chroma • LangGraph • Deep Agents")
