"""Graph definitions for Level 1, Level 2, and Level 3 Architectures."""

from langgraph.graph import StateGraph, START, END
from src.state import AgenticResearchState
from src.nodes import (
    single_agent_node,
    manager_node, 
    sub_agent_node, 
    integrator_node, 
    evaluator_node, 
    critic_node, 
    route_sub_tasks, 
    route_evaluation
)

def build_level_1_graph():
    """Level 1: Single-Agent Baseline (Zero-Shot)"""
    workflow = StateGraph(AgenticResearchState)
    workflow.add_node("single_agent", single_agent_node)
    workflow.add_node("evaluator", evaluator_node)
    
    workflow.add_edge(START, "single_agent")
    workflow.add_edge("single_agent", "evaluator")
    workflow.add_edge("evaluator", END)
    
    return workflow.compile()

def build_level_2_graph():
    """Level 2: Multi-Agent Map-Reduce (NO Critic/Reflection)"""
    workflow = StateGraph(AgenticResearchState)
    workflow.add_node("manager", manager_node)
    workflow.add_node("sub_agent", sub_agent_node)
    workflow.add_node("integrator", integrator_node)
    workflow.add_node("evaluator", evaluator_node)
    
    workflow.add_edge(START, "manager")
    workflow.add_conditional_edges("manager", route_sub_tasks, {"continue_coding": "sub_agent", "integrate": "integrator"})
    workflow.add_conditional_edges("sub_agent", route_sub_tasks, {"continue_coding": "sub_agent", "integrate": "integrator"})
    workflow.add_edge("integrator", "evaluator")
    workflow.add_edge("evaluator", END)
    
    return workflow.compile()

def build_level_3_graph():
    """Builds and compiles the StateGraph for the Level 3 architecture."""
    
    # 1. Initialize the graph with our state schema
    workflow = StateGraph(AgenticResearchState)

    # 2. Add all nodes to the graph
    workflow.add_node("manager", manager_node)
    workflow.add_node("sub_agent", sub_agent_node)
    workflow.add_node("integrator", integrator_node)
    workflow.add_node("evaluator", evaluator_node)
    workflow.add_node("critic", critic_node)

    # 3. Define the entry point
    workflow.add_edge(START, "manager")

    # 4. Define the routing from the manager (sub-tasks loop setup)
    workflow.add_conditional_edges(
        "manager",
        route_sub_tasks,
        {
            "continue_coding": "sub_agent",
            "integrate": "integrator"
        }
    )

    # 5. Define the sub-agent loop
    workflow.add_conditional_edges(
        "sub_agent",
        route_sub_tasks,
        {
            "continue_coding": "sub_agent",
            "integrate": "integrator"
        }
    )

    # 6. Proceed to evaluation after integration
    workflow.add_edge("integrator", "evaluator")

    # 7. Define the evaluation and reflection loop (Critic)
    workflow.add_conditional_edges(
        "evaluator",
        route_evaluation,
        {
            "end_success": END,
            "end_failure": END,
            "critic": "critic"
        }
    )

    # 8. The critic always sends the fixed code back to the evaluator
    workflow.add_edge("critic", "manager")

    # 9. Compile and return the executable application
    return workflow.compile()