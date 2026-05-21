import axios from "axios";

const API_URL = "https://crud-ai.onrender.com";

const parseSSEChunks = async (reader, onChunk, onComplete, onError, onThreadId, signal) => {
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      if (signal?.aborted) {
        onComplete();
        break;
      }

      const { done, value } = await reader.read();
      if (done) {
        onComplete();
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop(); // keep incomplete line in buffer

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith("data:")) continue;

        const jsonStr = trimmed.slice(5).trim();
        if (!jsonStr) continue;

        try {
          const parsed = JSON.parse(jsonStr);

          if (parsed.type === "thread_id") {
            if (onThreadId && parsed.thread_id) {
              onThreadId(parsed.thread_id);
            }
            continue;
          }

          if (parsed.type === "tool_call") {
            onChunk({ type: "tool_call", tool: parsed.tool, display_name: parsed.display_name || parsed.tool });
            continue;
          }

          if (parsed.type === "tool_result") {
            onChunk({ type: "tool_result", tool: parsed.tool, content: parsed.content });
            continue;
          }

          if (parsed.type === "text") {
            onChunk({ type: "text", content: parsed.content });
            continue;
          }

          if (parsed.type === "message_id") {
            onChunk({ type: "message_id", message_id: parsed.message_id });
            onComplete();
            return;
          }

          if (parsed.type === "error") {
            onError(new Error(parsed.message));
            return;
          }
        } catch (err) {
          console.error("Failed to parse SSE line:", line, err);
        }
      }
    }
  } catch (err) {
    if (signal?.aborted) {
      onComplete();
    } else {
      console.error("Stream reading error:", err);
      onError(err);
    }
  }
};

export const sendMessageStream = async (
  thread_id,
  content,
  userId = null,
  onChunk,
  onComplete,
  onError,
  onThreadId,
  signal,
) => {
  try {
    const response = await fetch(`${API_URL}/assistant/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        thread_id: thread_id || null,
        content,
        user_id: userId,
      }),
      signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }

    const reader = response.body.getReader();
    await parseSSEChunks(reader, onChunk, onComplete, onError, onThreadId, signal);
  } catch (err) {
    if (err.name === "AbortError") {
      onComplete();
    } else {
      console.error("SSE error:", err);
      onError(err);
    }
  }
};

export const sendEditMessageStream = async (
  thread_id,
  from_index,
  content,
  onChunk,
  onComplete,
  onError,
  onThreadId,
  signal,
) => {
  try {
    const response = await fetch(`${API_URL}/assistant/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        thread_id: thread_id || null,
        content,
        type: "edit_message",
        from_index,
      }),
      signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }

    const reader = response.body.getReader();
    await parseSSEChunks(reader, onChunk, onComplete, onError, onThreadId, signal);
  } catch (err) {
    if (err.name === "AbortError") {
      onComplete();
    } else {
      console.error("SSE error:", err);
      onError(err);
    }
  }
};

export const sendRegenerateStream = async (
  thread_id,
  message_id,
  onChunk,
  onComplete,
  onError,
  signal,
  onThreadId,
) => {
  try {
    const response = await fetch(`${API_URL}/assistant/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        thread_id: thread_id || null,
        type: "regenerate",
        message_id,
      }),
      signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }

    const reader = response.body.getReader();
    await parseSSEChunks(reader, onChunk, onComplete, onError, onThreadId, signal);
  } catch (err) {
    if (err.name === "AbortError") {
      onComplete();
    } else {
      console.error("SSE error:", err);
      onError(err);
    }
  }
};

export const sendAgentMessage = async (user_id, thread_id, input) => {
  const response = await axios.post(`${API_URL}/api/v1/agents/run`, {
    user_id,
    thread_id: thread_id ? Number(thread_id) : 0,
    input,
  });
  return response.data;
};