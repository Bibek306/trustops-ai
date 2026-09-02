# TrustOps AI

**Evidence-Governed AI for Security Questionnaire Automation**

TrustOps is a GenAI application that helps answer security questionnaires using approved company evidence. Instead of trusting the LLM blindly, TrustOps retrieves evidence, generates a draft, verifies the answer, assigns risk, and flags unsupported or high-risk responses for human review.

## Why TrustOps stands out

A normal RAG chatbot mainly does:

```text
Question → Retrieve → LLM → Answer
```

TrustOps adds a simple trust layer:

```text
Question
   ↓
RAG retrieves approved evidence
   ↓
LLM creates a draft
   ↓
Claim verification
   ↓
Risk assessment
   ↓
Safe answer OR human review
```

### Key features

- RAG with LangChain, Hugging Face hosted models, embeddings and Chroma
- Approved/current evidence governance
- Evidence cards with document and chunk provenance
- Safe abstention when evidence is missing
- Simple claim verification
- Explainable low/medium/high risk assessment
- LangGraph human-review workflow
- Restricted Deep Agent tools
- MCP Evidence Gateway with least-privilege tools
- Batch questionnaire API
- Simple evaluation: Recall@5, Grounded Answers, Safe Abstention
- FastAPI backend and Streamlit public demo

## Public demo deployment

The recommended deployment is **Streamlit Community Cloud**. The public demo uses a hosted LLM, so users do not need Hugging Face Inference Providers, a local model, or any local setup.

### Environment variables

For local development or testing, fill the included `.env` file:

```env
HF_TOKEN=your_huggingface_token_here
HF_PROVIDER=auto
HF_MODEL=openai/gpt-oss-120b
HF_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

For Streamlit Community Cloud, add the same `HF_TOKEN` in **Secrets** instead of committing it. Hugging Face Inference Providers require a token with the `Make calls to Inference Providers` permission.

Hugging Face currently provides a small monthly free credit for free accounts, subject to change; usage beyond included credits requires additional billing.

Do not commit API keys to GitHub.

### Deploy

1. Push this repository to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new app and select `streamlit_app/dashboard.py`.
4. Add `HF_TOKEN` in the app Secrets settings.
5. Deploy.

The app automatically loads the bundled sample security policy, so anyone opening the public URL can try it immediately.

## Demo questions

Try:

> Is customer data encrypted at rest?

Then try:

> Are you ISO 27001 certified?

The first should be answered from the sample policy. The second demonstrates safe abstention because the sample evidence does not establish certification.

## Project structure

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

Keep evaluation simple. TrustOps measures only three things:

1. **Recall@5** — did the retriever find the expected evidence?
2. **Grounded Answers** — did the generated answer pass evidence-based verification?
3. **Safe Abstention** — did the system refuse to answer when evidence was missing?

Run the evaluation in an environment with the required API configuration and approved evidence loaded.

## Technologies

Python · LangChain · RAG · Hugging Face · Chroma · LangGraph · Deep Agents · MCP · FastAPI · Streamlit · SQLAlchemy · Pytest
