from langgraph.graph import StateGraph, END
from .state import AgentState
from .state import AgentState
from .agents import SupervisorAgent, TeacherAgent, CoderAgent, EmpathAgent
from .examiner import ExaminerAgent # Fixed Import
from .analyst import AnalystAgent
from .visionary import VisionaryAgent

# Initialize Agents
supervisor = SupervisorAgent()
teacher = TeacherAgent()
coder = CoderAgent()
empath = EmpathAgent()
examiner = ExaminerAgent()
analyst = AnalystAgent()
visionary = VisionaryAgent()

# Define the Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("supervisor", supervisor.invoke)
workflow.add_node("teacher", teacher.invoke)
workflow.add_node("coder", coder.invoke)
workflow.add_node("empath", empath.invoke)
workflow.add_node("examiner", examiner.invoke) # New Node
workflow.add_node("examiner", examiner.invoke)
workflow.add_node("analyst", analyst.invoke)
workflow.add_node("visionary", visionary.invoke)

# Define Routing Logic
def route_next(state: AgentState):
    return state["next_step"]

# Add Edges
workflow.set_entry_point("supervisor")

workflow.add_conditional_edges(
    "supervisor",
    route_next,
    {
        "teacher": "teacher",
        "coder": "coder",
        "examiner": "examiner",
        "teacher": "teacher",
        "coder": "coder",
        "examiner": "examiner",
        "empath": "empath",
        "visionary": "visionary",
        "analyst": "analyst"
    }
)

# All agents route to Analyst for "Logging/Grading" before Ending
workflow.add_edge("teacher", "analyst")
workflow.add_edge("coder", "analyst")
workflow.add_edge("empath", "analyst")
workflow.add_edge("examiner", "analyst")
workflow.add_edge("visionary", "analyst")

# Analyst ends the turn
workflow.add_edge("analyst", END)

# Compile
app = workflow.compile()
