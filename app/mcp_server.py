"""MCP gateway exposing only safe evidence operations."""
from app.main import governed_answer, retrieve_evidence


def create_server():
    from fastmcp import FastMCP
    mcp = FastMCP("TrustOps Evidence Gateway")

    @mcp.tool()
    def search_approved_evidence(question: str) -> list[dict]:
        return [{"content": d.page_content, "metadata": d.metadata} for d in retrieve_evidence(question)]

    @mcp.tool()
    def create_governed_draft(question: str) -> dict:
        return governed_answer(question, "mcp")

    return mcp


if __name__ == "__main__":
    create_server().run()
