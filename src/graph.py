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
    route_evaluation,
    route_from_critic
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
    """Level 3: Adaptive Multi-Agent with LATS Branching"""
    workflow = StateGraph(AgenticResearchState)
    
    workflow.add_node("manager", manager_node)
    workflow.add_node("sub_agent", sub_agent_node)
    workflow.add_node("integrator", integrator_node)
    workflow.add_node("evaluator", evaluator_node)
    workflow.add_node("critic", critic_node)
    
    workflow.add_edge(START, "manager")
    workflow.add_conditional_edges("manager", route_sub_tasks, {"continue_coding": "sub_agent", "integrate": "integrator"})
    workflow.add_conditional_edges("sub_agent", route_sub_tasks, {"continue_coding": "sub_agent", "integrate": "integrator"})
    workflow.add_edge("integrator", "evaluator")
    
    workflow.add_conditional_edges(
        "evaluator", 
        route_evaluation, 
        {"end_success": END, "end_failure": END, "critic": "critic"}
    )
    
    # NEW: Architectural Branching conditional edge
    workflow.add_conditional_edges(
        "critic",
        route_from_critic,
        {
            "manager": "manager",
            "integrator": "integrator"
        }
    )
    
    return workflow.compile()