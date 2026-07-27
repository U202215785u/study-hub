"""对话管道 — 处理聊天消息"""
from datetime import datetime

from memory_store import insert_entry
from capture_gate import should_capture, classify_content, extract_summary
from self_engine import load_self_layer, run_decision_engine, retrieve_memories
from agent_loop import chat_completion, build_system_prompt


def process_dialogue(message: str, session_id: str = "default") -> dict:
    """处理单条对话消息。"""
    # 1. 加载 Self 层
    snapshot = load_self_layer()
    
    # 2. 检索记忆
    memories_result = retrieve_memories(message, k=5, snapshot=snapshot, message_text=message)
    memories = memories_result.get("candidates", memories_result.get("results", []))
    
    # 3. 决策引擎
    decision = run_decision_engine(message, snapshot, memories)
    
    # 4. 构建 prompt
    system_prompt = build_system_prompt(snapshot, memories)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message},
    ]
    
    # 5. 调用 LLM
    response = chat_completion(messages)
    
    # 6. 自动捕获
    capture_result = None
    if decision.get("should_capture_memory"):
        capture_ok, reason = should_capture(message)
        if capture_ok:
            entry_id = insert_entry(
                source="chat",
                type=classify_content(message),
                content=extract_summary(message),
                context={
                    "priority": decision.get("priority"),
                    "linked_project": decision.get("linked_project"),
                    "session_id": session_id,
                },
            )
            capture_result = {"captured": True, "entry_id": entry_id, "reason": reason}
    
    return {
        "message": message,
        "response": response,
        "decision": decision,
        "memories": memories[:5],
        "capture": capture_result,
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }
