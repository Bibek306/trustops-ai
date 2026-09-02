"""Small Deep Agent with deliberately limited tools."""
from langchain_core.tools import tool
from app.main import governed_answer, retrieve_evidence


@tool
def search_approved_evidence(question: str) -> list[dict]:
    """Read-only search of approved evidence."""
    return [{"content": d.page_content, "metadata": d.metadata} for d in retrieve_evidence(question)]


@tool
def create_draft(question: str) -> dict:
    """Create a governed draft. The agent cannot approve or release it."""
    return governed_answer(question, "agent")


def build_agent():
    from deepagents import create_deep_agent
    from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
    from app.main import MODEL, hf_token
    if not hf_token():
        raise RuntimeError("HF_TOKEN is missing")
    llm = ChatHuggingFace(llm=HuggingFaceEndpoint(
        repo_id=MODEL, task="text-generation", provider="auto", temperature=0,
        max_new_tokens=300, huggingfacehub_api_token=hf_token()))
    return create_deep_agent(
        model=llm,
        tools=[search_approved_evidence, create_draft],
        system_prompt="Use approved evidence only. You may search and create drafts. Never approve or release answers.",
    )
