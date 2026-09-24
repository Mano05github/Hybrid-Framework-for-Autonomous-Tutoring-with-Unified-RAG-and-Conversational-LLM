"""
LangGraph Workflow — Teaching-Only
supervisor → teacher / examiner / visionary / empath / general
"""
from typing import Literal
from langgraph.graph import StateGraph, END

from .state import AgentState
from .agents import (
    supervisor_agent,
    teacher_agent,
    examiner_agent,
    visionary_agent,
    empath_agent,
    general_agent,
)


def create_workflow() -> StateGraph:
    """
    Workflow:
    1. START -> supervisor
    2. supervisor -> teacher / examiner / visionary / empath / general
    3. specialist -> END   (empath -> teacher -> END)
    """
    workflow = StateGraph(AgentState)

    workflow.add_node("supervisor", supervisor_agent)
    workflow.add_node("teacher",   teacher_agent)
    workflow.add_node("examiner",  examiner_agent)
    workflow.add_node("visionary", visionary_agent)
    workflow.add_node("empath",    empath_agent)
    workflow.add_node("general",   general_agent)

    def route_after_supervisor(
        state: AgentState,
    ) -> Literal["teacher", "examiner", "visionary", "empath", "general"]:
        """Route to specialist agent based on supervisor intent."""
        intent = state.get("intent", "general")
        intent_to_agent = {
            "teacher":   "teacher",
            "coder":     "teacher",   # coder falls back to teacher until coder node is restored
            "examiner":  "examiner",  # now routed to real examiner node
            "visionary": "visionary",
            "empath":    "empath",
            "general":   "general",
        }
        next_agent = intent_to_agent.get(intent, "general")
        print(f"[Graph] Routing intent='{intent}' → node='{next_agent}'")
        return next_agent

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "teacher":   "teacher",
            "examiner":  "examiner",
            "visionary": "visionary",
            "empath":    "empath",
            "general":   "general",
        }
    )

    workflow.add_edge("teacher",   END)
    workflow.add_edge("examiner",  END)
    workflow.add_edge("visionary", END)
    workflow.add_edge("empath",    "teacher")   # empath is silent — teacher replies
    workflow.add_edge("general",   END)

    return workflow


def compile_graph():
    """Compile workflow into executable graph."""
    workflow = create_workflow()
    app = workflow.compile()
    print("[Graph] Compiled — nodes: supervisor, teacher, visionary, empath, general")
    return app


graph_app = None


def get_graph():
    """Get or create compiled graph (singleton)."""
    global graph_app
    if graph_app is None:
        graph_app = compile_graph()
    return graph_app


# Backwards-compatible alias
app = get_graph
