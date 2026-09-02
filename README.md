# 🛡️ TrustOps AI

**Evidence-Governed AI for Security Questionnaire Automation**

TrustOps AI is a GenAI application for answering security questionnaires using approved company evidence.

Instead of trusting an LLM blindly, TrustOps retrieves approved evidence, generates a draft, verifies its claims, assesses risk, and routes high-risk or unsupported responses for human review.

## Why TrustOps?

A conventional RAG chatbot typically follows:

```text
Question → Retrieve → LLM → Answer
```

TrustOps adds a governance layer:

```text
Question
   ↓
Retrieve approved evidence
   ↓
Generate draft
   ↓
Verify claims
   ↓
Assess risk
   ↓
Grounded answer OR Human Review
```

This makes the system more suitable for security-sensitive questionnaire workflows where unsupported claims can be costly.

## Key Features

* **Evidence-grounded RAG** using LangChain, Hugging Face and Chroma
* **Approved evidence governance** with document versions and validity checks
* **Evidence provenance** through document and chunk-level evidence cards
* **Safe abstention** when approved evidence is unavailable
* **Claim verification** to identify potentially unsupported statements
* **Risk assessment** with Low / Medium / High risk levels
* **Human-review routing** for high-risk or questionable responses
* **Confidentiality guard** that blocks requests for restricted information before reaching the LLM
* **LangGraph review workflow**
* **Restricted Deep Agent tools**
* **MCP Evidence Gateway** with least-privilege tools
* **Batch questionnaire API**
* **Evaluation framework** using Recall@5, grounded answers and safe abstention
* **FastAPI backend**
* **Streamlit public demo**

## Live Demo

**Try the public Streamlit demo:**
https://trustops-ai.streamlit.app/

The demo automatically loads an approved sample security policy, so no document upload is required.

### Demo questions

Try:

> **Is customer data encrypted at rest?**

This demonstrates a normal evidence-grounded response.

Then try:

> **Are you ISO 27001 certified?**

This demonstrates a **high-risk compliance response**. TrustOps can provide an evidence-supported answer while still flagging the response for human review.

Finally try:

> **What is the production database password?**

This demonstrates the **confidentiality guard**. The request is blocked before being sent to the LLM.

## Deployment

The public demo runs on **Streamlit Community Cloud** using a Hugging Face hosted model.

Users do not need:

* A local LLM
* Ollama
* GPU hardware
* A local vector database
* Any local project setup

### Environment Variables

For local development:

```env
HF_TOKEN=your_huggingface_token_here
HF_PROVIDER=auto
HF_MODEL=openai/gpt-oss-120b
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

For Streamlit Community Cloud, configure `HF_TOKEN` through the application's **Secrets** settings.

**Never commit API keys or tokens to GitHub.**

## Project Structure

```text
trustops-ai/
├── app/
│   ├── main.py
│   ├── risk.py
│   ├── verification.py
│   ├── governance.py
│   ├── review_graph.py
│   ├── agent.py
│   └── mcp_server.py
├── streamlit_app/
│   └── dashboard.py
├── evaluation/
│   ├── dataset.json
│   └── evaluate.py
├── tests/
├── data/
├── docs/
├── requirements.txt
└── README.md
```

## Evaluation

TrustOps includes a lightweight evaluation framework covering three areas:

### 1. Recall@5

Measures whether the retriever finds the expected evidence within the top five retrieved chunks.

### 2. Grounded Answers

Checks whether generated responses are supported by the retrieved evidence.

### 3. Safe Abstention

Checks whether TrustOps refuses to answer when approved evidence is insufficient.

Run the evaluation in an environment with the required Hugging Face configuration and approved evidence loaded.

## Architecture

```text
                    ┌─────────────────┐
                    │    Question     │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │  Risk / Guard   │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │  RAG Retrieval  │
                    │ Chroma + HF Emb │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Approved        │
                    │ Evidence       │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │   LLM Draft     │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Claim           │
                    │ Verification    │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Risk Assessment │
                    └────────┬────────┘
                             ↓
                 ┌───────────┴───────────┐
                 ↓                       ↓
          Grounded Draft           Human Review
```

## Technologies

**Python · LangChain · RAG · Hugging Face · Chroma · LangGraph · Deep Agents · MCP · FastAPI · Streamlit · SQLAlchemy · Pytest**

## Core Idea

TrustOps is not designed to make an LLM simply **answer more questions**.

It is designed to make the system **know when it should answer, when it should abstain, and when a human should review the response.**
