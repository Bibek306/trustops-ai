"""TrustOps AI: a small, explainable RAG application.

Flow: approved evidence -> retrieval -> answer -> verification -> risk.
FastAPI exposes the same core features used by the Streamlit demo.
"""
import csv
import io
import json
import os
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import chromadb

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, create_engine, delete, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from langchain_chroma import Chroma
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.documents import Document as LCDocument
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint, HuggingFaceEndpointEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.governance import is_currently_valid, version_key
from app.risk import risk_assessment
from app.verification import claim_check

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "trustops.db"
CHROMA_PATH = ROOT / "data" / "chroma_db"
UPLOAD_PATH = ROOT / "uploads"
MODEL = os.getenv("HF_MODEL", "openai/gpt-oss-120b")
EMBED_MODEL = os.getenv(
    "HF_EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2"
)
ABSTAIN = "Insufficient approved evidence to answer this safely."

# Shared persistent Chroma database.
CHROMA_PATH.mkdir(parents=True, exist_ok=True)
chroma_client = chromadb.EphemeralClient()


def hf_token():
    return os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")


engine = create_engine(f"sqlite:///{DB_PATH.as_posix()}", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)



class Base(DeclarativeBase):
    pass

Base.metadata.create_all(engine)

def now():
    return datetime.now(timezone.utc)

class Doc(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    group: Mapped[str] = mapped_column(String(100), index=True)
    version: Mapped[str] = mapped_column(String(50))
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="uploaded", index=True)
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[str | None] = mapped_column(String(100))
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Chunk(Base):
    __tablename__ = "chunks"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    idx: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)


class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    question: Mapped[str] = mapped_column(Text)
    draft_answer: Mapped[str] = mapped_column(Text)
    final_answer: Mapped[str | None] = mapped_column(Text)
    decision: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    reviewer: Mapped[str | None] = mapped_column(String(100))
    reason: Mapped[str | None] = mapped_column(Text)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    reviewed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Audit(Base):
    __tablename__ = "audit"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    event: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(64))
    payload: Mapped[str] = mapped_column(Text)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    session_id: str = "default"


class ReviewRequest(BaseModel):
    decision: str = Field(pattern="^(approved|edited|rejected)$")
    reviewer: str = "human-reviewer"
    final_answer: str | None = None
    reason: str | None = None


class BatchRequest(BaseModel):
    questions: list[str] = Field(min_length=1, max_length=100)


HISTORY = defaultdict(InMemoryChatMessageHistory)


def get_session_history(session_id: str):
    return HISTORY[session_id]


def audit(event, entity_id, payload):
    with Session() as db:
        db.add(Audit(id=uuid4().hex, event=event, entity_id=entity_id, payload=json.dumps(payload)))
        db.commit()


def get_vectorstore():
    if not hf_token():
        raise RuntimeError("HF_TOKEN is missing. Add it to .env or Streamlit Secrets.")

    embeddings = HuggingFaceEndpointEmbeddings(
        model=EMBED_MODEL,
        task="feature-extraction",
        huggingfacehub_api_token=hf_token(),
    )

    return Chroma(
        client=chroma_client,
        collection_name="trustops_evidence",
        embedding_function=embeddings,
    )


# Kept as this function name because the rest of the project uses it.
vectorstore = get_vectorstore


def approved_ids():
    with Session() as db:
        docs = db.scalars(select(Doc).where(Doc.status == "approved")).all()
    groups = defaultdict(list)
    for doc in docs:
        if is_currently_valid(doc):
            groups[doc.group].append(doc)
    return {max(items, key=lambda d: version_key(d.version)).id for items in groups.values()}


def retrieve_evidence(question, k=5):
    allowed = approved_ids()
    if not allowed:
        return []
    retriever = get_vectorstore().as_retriever(
        search_type="mmr", search_kwargs={"k": k, "fetch_k": max(12, k * 3)}
    )
    docs = retriever.invoke(question)
    return [doc for doc in docs if doc.metadata.get("document_id") in allowed][:k]


def make_citations(docs):
    return [
        {
            "filename": d.metadata.get("filename"),
            "version": d.metadata.get("version"),
            "chunk_index": d.metadata.get("chunk_index"),
            "quote": d.page_content[:500],
        }
        for d in docs
    ]


def generate_answer(question, session_id, evidence):
    llm = ChatHuggingFace(
        llm=HuggingFaceEndpoint(
            repo_id=MODEL,
            task="text-generation",
            provider=os.getenv("HF_PROVIDER", "auto"),
            max_new_tokens=300,
            temperature=0,
            huggingfacehub_api_token=hf_token(),
        )
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are TrustOps. Answer only from the approved evidence below.
Never invent facts. Do not infer certifications, contracts, exact retention periods,
encryption algorithms, or security controls unless the evidence explicitly supports them.
If the evidence is insufficient, respond exactly: Insufficient approved evidence to answer this safely.
Keep the answer concise.

Approved evidence:\n{context}"""),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    context = "\n\n".join(
        f"[{d.metadata.get('filename')} {d.metadata.get('version')} | chunk {d.metadata.get('chunk_index')}]\n{d.page_content}"
        for d in evidence
    )
    chain = prompt | llm
    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    answer = chain_with_history.invoke(
        {"context": context, "input": question},
        config={"configurable": {"session_id": session_id}},
    )
    text = answer.content if hasattr(answer, "content") else str(answer)
    return text.strip()


def governed_answer(question, session_id="default"):
    evidence = retrieve_evidence(question)
    risk = risk_assessment(question, evidence)

    # Never allow restricted/confidential requests to reach the LLM.
    if risk.get("confidentiality_flag"):
        result = {
            "answer": (
                "This request involves confidential or restricted information "
                "and cannot be answered automatically."
            ),
            "risk": risk,
            "trust_status": "needs_review",
            "citations": make_citations(evidence),
            "verification": {
                "status": "abstained",
                "unsupported_claims": [],
                "claim_count": 0,
            },
        }

        audit(
            "answer_blocked_confidential",
            session_id,
            {
                "question": question,
                "risk": risk,
            },
        )

        return result

    if not evidence:
        result = {
            "answer": ABSTAIN,
            "risk": risk,
            "trust_status": "blocked_no_evidence",
            "citations": [],
            "verification": {
                "status": "abstained",
                "unsupported_claims": [],
                "claim_count": 0,
            },
        }

        audit(
            "answer_blocked",
            session_id,
            {"question": question},
        )

        return result

    answer = generate_answer(question, session_id, evidence)
    verification = claim_check(answer, evidence)

    needs_review = (
        answer == ABSTAIN
        or verification["status"] == "needs_review"
        or risk["requires_human_review"]
    )

    result = {
        "answer": answer,
        "risk": risk,
        "trust_status": "needs_review" if needs_review else "grounded_draft",
        "citations": make_citations(evidence),
        "verification": verification,
    }

    audit(
        "answer_generated",
        session_id,
        {
            "question": question,
            "risk": risk,
            "status": result["trust_status"],
        },
    )

    return result


app = FastAPI(title="TrustOps AI", version="2.0")


@app.on_event("startup")
def startup():
    UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)


@app.get("/health")
def health():
    return {"status": "ok", "service": "TrustOps AI"}


@app.post("/documents/upload", status_code=201)
async def upload(file: UploadFile = File(...), document_group: str = Form("general"), version: str = Form("v1")):
    name = Path(file.filename or "document.txt").name
    if Path(name).suffix.lower() not in {".txt", ".md", ".pdf"}:
        raise HTTPException(400, "Only PDF, TXT and Markdown files are allowed")
    body = await file.read()
    did = uuid4().hex
    path = UPLOAD_PATH / f"{did}{Path(name).suffix.lower()}"
    path.write_bytes(body)
    try:
        if path.suffix == ".pdf":
            from pypdf import PdfReader
            text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        raise HTTPException(422, f"Text extraction failed: {exc}") from exc
    with Session() as db:
        db.add(Doc(id=did, filename=name, group=document_group, version=version, text=text))
        db.commit()
    return {"document_id": did, "status": "uploaded", "next": f"POST /documents/{did}/process then approve"}


@app.post("/documents/{document_id}/process")
def process(document_id: str):
    with Session() as db:
        doc = db.get(Doc, document_id)
        if not doc:
            raise HTTPException(404, "Document not found")
        pieces = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120).create_documents([doc.text])
        db.execute(delete(Chunk).where(Chunk.document_id == document_id))
        chunks = [Chunk(id=uuid4().hex, document_id=document_id, idx=i, content=p.page_content) for i, p in enumerate(pieces)]
        db.add_all(chunks)
        db.commit()
        vs = get_vectorstore()
        vs.delete(where={"document_id": document_id})
        vs.add_documents([
            LCDocument(page_content=c.content, metadata={"chunk_id": c.id, "document_id": doc.id,
                "filename": doc.filename, "version": doc.version, "group": doc.group, "chunk_index": c.idx})
            for c in chunks
        ], ids=[c.id for c in chunks])
        doc.status = "indexed"
        db.commit()
    audit("document_indexed", document_id, {"chunks": len(chunks)})
    return {"document_id": document_id, "status": "indexed", "chunks": len(chunks), "next": "approve"}


@app.post("/documents/{document_id}/approve")
def approve(document_id: str, reviewer: str = Form("evidence-owner")):
    with Session() as db:
        doc = db.get(Doc, document_id)
        if not doc:
            raise HTTPException(404, "Document not found")
        if doc.status != "indexed":
            raise HTTPException(409, "Document must be indexed first")
        doc.status, doc.approved_at, doc.approved_by = "approved", now(), reviewer
        db.commit()
    audit("document_approved", document_id, {"reviewer": reviewer})
    return {"document_id": document_id, "status": "approved"}


@app.post("/ask")
def ask(payload: AskRequest):
    try:
        return governed_answer(payload.question, payload.session_id)
    except Exception as exc:
        raise HTTPException(503, f"TrustOps is unavailable: {exc}") from exc


@app.post("/batch")
def batch(payload: BatchRequest):
    results = [governed_answer(q, f"batch-{uuid4().hex}") | {"question": q} for q in payload.questions]
    return {"count": len(results), "results": results}


@app.post("/reviews")
def create_review(payload: AskRequest):
    result = governed_answer(payload.question, payload.session_id)
    if result["trust_status"] != "needs_review":
        raise HTTPException(409, "This response does not require review")
    rid = uuid4().hex
    with Session() as db:
        db.add(Review(id=rid, question=payload.question, draft_answer=result["answer"]))
        db.commit()
    return {"review_id": rid, "draft": result}


@app.get("/reviews")
def reviews():
    with Session() as db:
        rows = db.scalars(select(Review).order_by(Review.created.desc())).all()
        return [{"review_id": r.id, "question": r.question, "draft_answer": r.draft_answer,
                 "final_answer": r.final_answer, "decision": r.decision, "reviewer": r.reviewer,
                 "reason": r.reason} for r in rows]


@app.post("/reviews/{review_id}/decision")
def decide_review(review_id: str, payload: ReviewRequest):
    if payload.decision == "edited" and not payload.final_answer:
        raise HTTPException(400, "final_answer is required for an edited decision")
    with Session() as db:
        review = db.get(Review, review_id)
        if not review:
            raise HTTPException(404, "Review not found")
        review.decision = payload.decision
        review.reviewer = payload.reviewer
        review.final_answer = payload.final_answer if payload.decision == "edited" else (review.draft_answer if payload.decision == "approved" else None)
        review.reason, review.reviewed = payload.reason, now()
        db.commit()
        return {"review_id": review_id, "decision": review.decision, "final_answer": review.final_answer}


@app.get("/report")
def report():
    with Session() as db:
        docs = db.scalars(select(Doc)).all()
        reviews = db.scalars(select(Review)).all()
    return {"documents": len(docs), "approved_documents": sum(d.status == "approved" for d in docs),
            "pending_reviews": sum(r.decision == "pending" for r in reviews),
            "approved_reviews": sum(r.decision == "approved" for r in reviews),
            "edited_reviews": sum(r.decision == "edited" for r in reviews),
            "rejected_reviews": sum(r.decision == "rejected" for r in reviews)}


@app.get("/audit")
def audit_log(limit: int = 100):
    with Session() as db:
        rows = db.scalars(select(Audit).order_by(Audit.created.desc()).limit(min(max(limit, 1), 500))).all()
        return [{"event": a.event, "entity_id": a.entity_id, "payload": json.loads(a.payload), "created": a.created} for a in rows]


@app.get("/batch/csv")
def batch_csv_export():
    with Session() as db:
        rows = db.scalars(select(Review).order_by(Review.created)).all()
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["question", "answer", "decision", "reviewer", "reason"])
    for r in rows:
        writer.writerow([r.question, r.final_answer or r.draft_answer, r.decision, r.reviewer or "", r.reason or ""])
    return StreamingResponse(iter([out.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=trustops_reviews.csv"})
