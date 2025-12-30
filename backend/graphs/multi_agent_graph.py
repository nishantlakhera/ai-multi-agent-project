from langgraph.graph import StateGraph, END
from graphs.state_schema import GraphState
from agents.router_agent import router_agent
from agents.rag_agent import rag_agent
from agents.db_agent import db_agent
from agents.web_agent import web_agent
from agents.fusion_agent import fusion_agent
from agents.final_answer_agent import final_answer_agent
from agents.general_agent import general_agent
from agents.test_agent import test_agent

def build_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("router", router_agent)
    workflow.add_node("rag", rag_agent)
    workflow.add_node("db", db_agent)
    workflow.add_node("web", web_agent)
    workflow.add_node("general", general_agent)
    workflow.add_node("fusion", fusion_agent)
    workflow.add_node("final", final_answer_agent)
    workflow.add_node("test", test_agent)

    workflow.set_entry_point("router")

    def route_decider(state: GraphState):
        route = state.get("route")
        if route == "rag":
            return "rag"
        elif route == "db":
            return "db"
        elif route == "web":
            return "web"
        elif route == "test":
            return "test"
        elif route == "multi":
            return "rag"
        elif route == "general":
            return "general"
        else:
            return "final"

    workflow.add_conditional_edges(
        "router",
        route_decider,
        {
            "rag": "rag",
            "db": "db",
            "web": "web",
            "test": "test",
            "multi": "rag",
            "general": "general",
            "final": "final",
        },
    )

    def after_rag(state: GraphState):
        if state.get("route") == "multi":
            return "db"
        return "fusion"

    def after_db(state: GraphState):
        if state.get("route") == "multi":
            return "web"
        return "fusion"

    def after_web(state: GraphState):
        return "fusion"

    workflow.add_conditional_edges("rag", after_rag, {"db": "db", "fusion": "fusion"})
    workflow.add_conditional_edges("db", after_db, {"web": "web", "fusion": "fusion"})
    workflow.add_edge("web", "fusion")
    workflow.add_edge("general", "final")  # General goes directly to final
    workflow.add_edge("test", "final")  # Test runs go directly to final

    workflow.add_edge("fusion", "final")
    workflow.add_edge("final", END)

    app = workflow.compile()
    return app

graph_app = build_graph()
