"""Simple LangGraph workflow: draft -> review if needed -> final answer."""
from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from langgraph.checkpoint.memory import InMemorySaver
from app.main import governed_answer


class State(TypedDict, total=False):
    question: str
    result: dict
    final_answer: str


def draft(state):
    return {**state, "result": governed_answer(state["question"], "graph")}


def route(state):
    return "review" if state["result"]["trust_status"] == "needs_review" else "final"


def review(state):
    decision = interrupt({"draft": state["result"]["answer"], "message": "Human review required"})
    if decision.get("decision") == "rejected":
        answer = "Response rejected by reviewer."
    else:
        answer = decision.get("final_answer") or state["result"]["answer"]
    return {**state, "final_answer": answer}


def final(state):
    return {**state, "final_answer": state.get("final_answer", state["result"]["answer"])}


g = StateGraph(State)
g.add_node("draft", draft)
g.add_node("review", review)
g.add_node("final", final)
g.add_edge(START, "draft")
g.add_conditional_edges("draft", route, {"review": "review", "final": "final"})
g.add_edge("review", "final")
g.add_edge("final", END)
review_graph = g.compile(checkpointer=InMemorySaver())
