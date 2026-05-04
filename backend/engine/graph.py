# backend/engine/graph.py
# Generic AI conversation graph - works with any vertical/industry

import json
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from engine.personas import UserRole, get_system_prompt_for_role, get_persona, PersonaConfig

import os
import httpx
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the LLM
llm = ChatOpenAI(
    api_key=os.getenv("VLLM_API_KEY", "EMPTY"),
    base_url=os.getenv("VLLM_API_BASE", "http://localhost:8000/v1"),
    model=os.getenv("VLLM_MODEL", "default-model"),
    max_tokens=1024,
    temperature=0.7,
)

# ==========================================
# STATE MANAGEMENT
# ==========================================

class AppState(TypedDict):
    messages: Annotated[list, add_messages]
    role: UserRole
    persona_id: Optional[str]
    # Other state variables
    extracted_entities: Dict[str, Any]
    conversation_context: Dict[str, Any]

# ==========================================
# AI NODES
# ==========================================

async def analyze_intent(state: AppState) -> dict:
    """
    Node 1: Analyze the user's input to understand intent.
    """
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    
    return {
        "extracted_entities": {
            "last_input_length": len(last_message),
            "intent": "query"  # Could be expanded with actual intent classification
        }
    }

async def fetch_knowledge_context(query: str) -> str:
    """Fetches RAG context from the knowledge base if available."""
    brain_url = os.getenv("BRAIN_API_URL", "")
    
    # Skip if no knowledge base configured
    if not brain_url or brain_url == "http://localhost:8000":
        return ""
    
    endpoint = f"{brain_url}/api/v1/ai/enhanced/semantic/search/"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(endpoint, json={
                "query": query,
                "top_k": 3,
                "language": "en"
            })
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if not results:
                    return ""
                
                context_str = "<knowledge_context>\n"
                for i, res in enumerate(results, 1):
                    title = res.get("title") or "Document"
                    content = res.get("content", "").strip()
                    context_str += f"Document {i} ({title}):\n{content}\n\n"
                context_str += "</knowledge_context>\n"
                return context_str
    except Exception as e:
        # Silently fail - knowledge base is optional
        pass
    return ""

async def generate_ai_response(state: AppState) -> dict:
    """
    Node 2: Generate the AI response using the appropriate persona.
    """
    role = state.get("role", UserRole.CLIENT)
    persona_id = state.get("persona_id")
    messages = state["messages"]
    
    # Get the latest user message
    latest_message = messages[-1].content if messages else ""
    
    # Get system prompt for the persona/role
    system_prompt = get_system_prompt_for_role(role, persona_id)
    
    # Get persona info for the name
    persona_name = "AI Assistant"
    if persona_id:
        persona = get_persona(persona_id)
        if persona:
            persona_name = persona.name
    
    # Inject RAG context if available
    if latest_message:
        rag_context = await fetch_knowledge_context(latest_message)
        if rag_context:
            system_prompt += f"\n\nHere is relevant background information:\n{rag_context}"

    # Format messages for the API
    formatted_messages = [SystemMessage(content=system_prompt)] + messages

    try:
        response = await llm.ainvoke(formatted_messages)
        reply = response.content
    except Exception as e:
        print(f"LLM Error: {e}")
        reply = f"I apologize, but I am unable to process your request at this moment due to a connection issue. (Error: {str(e)})"
    
    return {"messages": [AIMessage(content=reply.strip())]}

# ==========================================
# GRAPH DEFINITION
# ==========================================

workflow = StateGraph(AppState)

# Add our nodes
workflow.add_node("intent_analyzer", analyze_intent)
workflow.add_node("response_generator", generate_ai_response)

# Define the edges (workflow progression)
workflow.set_entry_point("intent_analyzer")
workflow.add_edge("intent_analyzer", "response_generator")
workflow.add_edge("response_generator", END)

# Compile the graph
ai_conversation_graph = workflow.compile()

# Backward compatibility
anya_graph = ai_conversation_graph
