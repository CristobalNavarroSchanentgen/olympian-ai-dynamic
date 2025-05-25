"""Chat API Routes - Divine Dialogue Management"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
from loguru import logger

from ..core.service_manager import get_ollama_service, get_project_service
from ..core.websocket import ws_manager
from ..core.config import settings

router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # user, assistant, system
    content: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    model: str
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = True


class ConversationCreate(BaseModel):
    """Conversation creation model"""
    title: Optional[str] = None
    project_id: Optional[str] = None
    model: str
    system_prompt: Optional[str] = None


class StopRequest(BaseModel):
    """Stop generation request model"""
    client_id: str


# In-memory conversation storage (would use database in production)
conversations: Dict[str, Dict[str, Any]] = {}


@router.post("/message")
async def send_chat_message(request: ChatRequest):
    """Send a chat message and get response"""
    ollama_service = get_ollama_service()
    if not ollama_service:
        raise HTTPException(status_code=503, detail="Ollama service not available")
    
    # Create or get conversation
    if request.conversation_id:
        if request.conversation_id not in conversations:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conversation = conversations[request.conversation_id]
    else:
        # Create new conversation
        conversation_id = str(uuid.uuid4())
        conversation = {
            "id": conversation_id,
            "created_at": datetime.now(),
            "model": request.model,
            "project_id": request.project_id,
            "messages": [],
            "system_prompt": request.system_prompt
        }
        conversations[conversation_id] = conversation
        request.conversation_id = conversation_id
    
    # Add user message
    user_message = ChatMessage(
        role="user",
        content=request.message,
        timestamp=datetime.now()
    )
    conversation["messages"].append(user_message.dict())
    
    # Get context from project if applicable
    context = []
    project_service = get_project_service()
    if request.project_id and project_service:
        project = await project_service.get_project(request.project_id)
        if project and project.get("context"):
            context = project["context"]
    
    # Add conversation history as context
    for msg in conversation["messages"][-10:]:  # Last 10 messages
        context.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Generate response
    if not request.stream:
        # Non-streaming response
        response_text = ""
        async for chunk in ollama_service.stream_chat(
            model=request.model,
            message=request.message,
            system_prompt=request.system_prompt or conversation.get("system_prompt"),
            context=context,
            temperature=request.temperature,
            project_id=request.project_id
        ):
            response_text += chunk
        
        # Add assistant message
        assistant_message = ChatMessage(
            role="assistant",
            content=response_text,
            timestamp=datetime.now(),
            metadata={"model": request.model}
        )
        conversation["messages"].append(assistant_message.dict())
        
        return {
            "conversation_id": request.conversation_id,
            "message": assistant_message.dict(),
            "model": request.model
        }
    else:
        # For streaming, return conversation ID and let WebSocket handle it
        return {
            "conversation_id": request.conversation_id,
            "streaming": True,
            "message": "Use WebSocket connection for streaming response"
        }


@router.post("/stop")
async def stop_generation(request: StopRequest):
    """Stop ongoing generation for a client"""
    client_status = ws_manager.get_client_stream_status(request.client_id)
    
    if not client_status["has_active_stream"]:
        raise HTTPException(status_code=400, detail="No active generation to stop")
    
    # Send stop message via WebSocket manager
    await ws_manager._handle_stop_generation(request.client_id, {"type": "stop_generation"})
    
    return {
        "status": "stopped",
        "client_id": request.client_id,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/status/{client_id}")
async def get_chat_status(client_id: str):
    """Get chat status for a client"""
    status = ws_manager.get_client_stream_status(client_id)
    
    return {
        "client_id": client_id,
        "is_streaming": status["is_streaming"],
        "has_active_stream": status["has_active_stream"],
        "can_stop": status["has_active_stream"],
        "timestamp": datetime.now().isoformat()
    }


@router.post("/conversations")
async def create_conversation(conversation: ConversationCreate):
    """Create a new conversation"""
    conversation_id = str(uuid.uuid4())
    
    new_conversation = {
        "id": conversation_id,
        "title": conversation.title or f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "model": conversation.model,
        "project_id": conversation.project_id,
        "system_prompt": conversation.system_prompt,
        "messages": []
    }
    
    conversations[conversation_id] = new_conversation
    
    return new_conversation


@router.get("/conversations")
async def list_conversations(
    project_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """List all conversations, optionally filtered by project"""
    # Filter conversations
    filtered_conversations = [
        conv for conv in conversations.values()
        if not project_id or conv.get("project_id") == project_id
    ]
    
    # Sort by updated_at (most recent first)
    sorted_conversations = sorted(
        filtered_conversations,
        key=lambda x: x.get("updated_at", x["created_at"]),
        reverse=True
    )
    
    # Paginate
    total = len(sorted_conversations)
    paginated = sorted_conversations[offset:offset + limit]
    
    return {
        "conversations": paginated,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all messages"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversations[conversation_id]


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    del conversations[conversation_id]
    
    return {
        "status": "deleted",
        "conversation_id": conversation_id
    }


@router.put("/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    title: Optional[str] = None,
    system_prompt: Optional[str] = None
):
    """Update conversation metadata"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation = conversations[conversation_id]
    
    if title is not None:
        conversation["title"] = title
    
    if system_prompt is not None:
        conversation["system_prompt"] = system_prompt
    
    conversation["updated_at"] = datetime.now()
    
    return conversation


@router.post("/conversations/{conversation_id}/clear")
async def clear_conversation(conversation_id: str):
    """Clear all messages from a conversation"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation = conversations[conversation_id]
    conversation["messages"] = []
    conversation["updated_at"] = datetime.now()
    
    return {
        "status": "cleared",
        "conversation_id": conversation_id
    }


@router.post("/conversations/{conversation_id}/fork")
async def fork_conversation(conversation_id: str, from_message_index: Optional[int] = None):
    """Fork a conversation from a specific point"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    original = conversations[conversation_id]
    new_id = str(uuid.uuid4())
    
    # Create forked conversation
    forked = {
        "id": new_id,
        "title": f"{original.get('title', 'Conversation')} (Fork)",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "model": original["model"],
        "project_id": original.get("project_id"),
        "system_prompt": original.get("system_prompt"),
        "messages": original["messages"][:from_message_index] if from_message_index else original["messages"].copy(),
        "forked_from": conversation_id
    }
    
    conversations[new_id] = forked
    
    return forked


@router.get("/models/recommended")
async def get_recommended_models():
    """Get recommended models based on system capacity"""
    # Get system recommendations
    import psutil
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    recommendations = {
        "fast": [],
        "balanced": [],
        "powerful": []
    }
    
    # Get available models from discovered services
    available_models = []
    if "ollama" in settings.discovered_services:
        ollama_data = settings.discovered_services["ollama"]
        available_models = ollama_data.get("models", [])
    
    model_names = [m.get("name", "") for m in available_models if isinstance(m, dict)]
    
    # Categorize based on system resources
    if memory_gb >= 32:
        recommendations["fast"] = [m for m in model_names if any(size in m for size in ["3b", "7b"])]
        recommendations["balanced"] = [m for m in model_names if "13b" in m]
        recommendations["powerful"] = [m for m in model_names if any(size in m for size in ["70b", "8x"])]
    elif memory_gb >= 16:
        recommendations["fast"] = [m for m in model_names if any(size in m for size in ["phi", "3b"])]
        recommendations["balanced"] = [m for m in model_names if "7b" in m]
        recommendations["powerful"] = [m for m in model_names if "13b" in m]
    else:
        recommendations["fast"] = [m for m in model_names if any(small in m for small in ["phi", "tinyllama"])]
        recommendations["balanced"] = [m for m in model_names if "7b" in m]
        recommendations["powerful"] = recommendations["balanced"]  # Same as balanced for low memory
    
    return {
        "recommendations": recommendations,
        "system_memory_gb": round(memory_gb, 2),
        "total_available_models": len(model_names)
    }


@router.post("/regenerate/{conversation_id}")
async def regenerate_last_response(conversation_id: str):
    """Regenerate the last assistant response in a conversation"""
    ollama_service = get_ollama_service()
    if not ollama_service:
        raise HTTPException(status_code=503, detail="Ollama service not available")
    
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation = conversations[conversation_id]
    messages = conversation["messages"]
    
    # Find last user message
    last_user_idx = None
    for i in range(len(messages) - 1, -1, -1):
        if messages[i]["role"] == "user":
            last_user_idx = i
            break
    
    if last_user_idx is None:
        raise HTTPException(status_code=400, detail="No user message found to regenerate from")
    
    # Remove messages after last user message
    conversation["messages"] = messages[:last_user_idx + 1]
    
    # Regenerate response
    last_user_message = messages[last_user_idx]["content"]
    
    response_text = ""
    async for chunk in ollama_service.stream_chat(
        model=conversation["model"],
        message=last_user_message,
        system_prompt=conversation.get("system_prompt"),
        context=[{"role": m["role"], "content": m["content"]} for m in messages[:last_user_idx]],
        temperature=0.8,  # Slightly higher for variation
        project_id=conversation.get("project_id")
    ):
        response_text += chunk
    
    # Add new assistant message
    assistant_message = ChatMessage(
        role="assistant",
        content=response_text,
        timestamp=datetime.now(),
        metadata={"model": conversation["model"], "regenerated": True}
    )
    conversation["messages"].append(assistant_message.dict())
    conversation["updated_at"] = datetime.now()
    
    return {
        "conversation_id": conversation_id,
        "message": assistant_message.dict(),
        "status": "regenerated"
    }