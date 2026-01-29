"""
Enhanced LangGraph Workflow - V2.0
Multi-agent system with supervisor routing and conditional edges
"""
from typing import Literal
from langgraph.graph import StateGraph, END

from .state import AgentState
from .agents import (
    supervisor_agent,
    teacher_agent,
    coder_agent,
    examiner_agent,
    visionary_agent,
    empath_agent
)


def create_workflow() -> StateGraph:
    """
    Create LangGraph workflow with enhanced supervisor routing.
    
    Workflow:
    1. START -> supervisor_agent (V2.0 with SetFit + cache)
    2. supervisor -> specialist agent (teacher/coder/examiner/visionary/empath)
    3. specialist -> END
    
    Future enhancements (Phase 2):
    - Multi-agent parallel routing for complex queries
    - Response fusion for collaborative answers
    - Feedback loop for RL policy training
    """
    # Initialize StateGraph
    workflow = StateGraph(AgentState)
    
    # Add nodes (agents)
    workflow.add_node("supervisor", supervisor_agent)
    workflow.add_node("teacher", teacher_agent)
    workflow.add_node("coder", coder_agent)
    workflow.add_node("examiner", examiner_agent)
    workflow.add_node("visionary", visionary_agent)
    workflow.add_node("empath", empath_agent)
    
    # Define routing logic
    def route_after_supervisor(state: AgentState) -> Literal["teacher", "coder", "examiner", "visionary", "empath"]:
        """
        Route to specialist agent based on supervisor's intent prediction.
        
        Args:
            state: Current agent state with intent field
        
        Returns:
            Next agent name
        """
        intent = state.get("intent", "teacher")
        
        # Map intent to agent
        intent_to_agent = {
            "teacher": "teacher",
            "coder": "coder",
            "examiner": "examiner",
            "visionary": "visionary",
            "empath": "empath"
        }
        
        next_agent = intent_to_agent.get(intent, "teacher")  # Default to teacher
        
        print(f"[Graph] Routing to: {next_agent}")
        
        return next_agent
    
    # Set entry point
    workflow.set_entry_point("supervisor")
    
    # Add conditional edges (supervisor -> specialist agents)
    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "teacher": "teacher",
            "coder": "coder",
            "examiner": "examiner",
            "visionary": "visionary",
            "empath": "empath"
        }
    )
    
    # Add edges from specialist agents to END
    workflow.add_edge("teacher", END)
    workflow.add_edge("coder", END)
    workflow.add_edge("examiner", END)
    workflow.add_edge("visionary", END)
    workflow.add_edge("empath", END)
    
    return workflow


def compile_graph():
    """
    Compile workflow into executable graph.
    
    Returns:
        Compiled LangGraph app
    """
    workflow = create_workflow()
    app = workflow.compile()
    
    print("[Graph] Workflow compiled successfully")
    print("[Graph] Available nodes: supervisor, teacher, coder, examiner, visionary, empath")
    
    return app


# Create singleton graph instance
graph_app = None


def get_graph():
    """Get or create compiled graph (singleton)."""
    global graph_app
    
    if graph_app is None:
        graph_app = compile_graph()
    
    return graph_app


def visualize_graph(output_path: str = "workflow_graph.png"):
    """
    Generate visual representation of workflow graph.
    
    Args:
        output_path: Path to save PNG image
    """
    try:
        from IPython.display import Image, display
        
        app = get_graph()
        
        # Generate mermaid diagram
        graph_image = app.get_graph().draw_mermaid_png()
        
        with open(output_path, 'wb') as f:
            f.write(graph_image)
        
        print(f"[Graph] Visualization saved to: {output_path}")
        
        return graph_image
    
    except Exception as e:
        print(f"[Graph] Visualization failed: {e}")
        return None


if __name__ == "__main__":
    # Test graph creation
    print("=" * 80)
    print("LangGraph Workflow - V2.0")
    print("=" * 80)
    
    app = compile_graph()
    
    # Test query
    test_state = {
        "messages": [],
        "user_id": "test_user",
        "session_id": "test_session",
        "query": "Explain binary search algorithm",
        "user_emotion": "neutral",
        "current_topic": "",
        "next_step": "",
        "intent": "",
        "confidence": 0.0,
        "method": "",
        "latency_ms": 0.0,
        "complexity_score": None,
        "next_agent": None,
        "response": "",
        "mastery_state": None
    }
    
    print("\nTest Query: 'Explain binary search algorithm'")
    print("-" * 80)
    
    # NOTE: Cannot execute without trained model
    # Uncomment after training SetFit classifier
    result = app.invoke(test_state)
    print(f"Final Response: {result['response']}")
    
    print("\n[Graph] Ready for integration")
    # print("[Graph] Train SetFit classifier before first use:")
    # print("  python -m ai_engine.supervisor.classifier")
