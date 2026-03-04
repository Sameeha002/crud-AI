const WS_URL = "ws://127.0.0.1:8000/ws/chat";

export const sendMessageStream = async (
  thread_id,
  content,
  userId = null,
  onChunk,
  onComplete,
  onError,
  onThreadId,
  signal
) => {
  // Use thread_id if exists, otherwise 0 to create new thread
  const threadId = thread_id || 0;

  return new Promise((resolve) => {
    const ws = new WebSocket(`${WS_URL}/${threadId}`);

    // Abort support — close WebSocket if signal fires
    signal?.addEventListener("abort", () => {
      if(ws.readyState === WebSocket.OPEN){
        ws.send(JSON.stringify({type: "stop"}))
      }
      onComplete();
      resolve();
    });

    ws.onopen = () => {
      console.log("WebSocket connected!");
      ws.send(
        JSON.stringify({
          content: content,
          user_id: userId,
        })
      );
    };

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        console.log("Received:", parsed);

        if (parsed.type === "thread_id") {
          console.log("New thread created:", parsed.thread_id);
          if (onThreadId && parsed.thread_id) {
            onThreadId(parsed.thread_id);
          }
          return;
        }

        if (parsed.type === "tool_call") {
          onChunk({
            type: "tool_call",
            tool: parsed.tool,
            display_name: parsed.tool,
          });
          return;
        }

        if (parsed.type === "tool_result") {
          onChunk({
            type: "tool_result",
            tool: parsed.tool,
            content: parsed.content,
          });
          return;
        }

        if (parsed.type === "text") {
          onChunk({
            type: "text",
            content: parsed.content,
          });
          return;
        }

        if (parsed.type === "message_id") {
          onChunk({
            type: "message_id",
            message_id: parsed.message_id,
          });
          // message_id is the last event — streaming is done
          ws.close();
          onComplete();
          resolve();
          return;
        }

        if (parsed.type === "error") {
          console.error("Server error:", parsed.message);
          onError(new Error(parsed.message));
          resolve();
          return;
        }
      } catch (err) {
        console.error("Failed to parse message:", err);
        onError(err);
        resolve();
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
      onError(new Error("WebSocket connection error"));
      resolve();
    };

    ws.onclose = () => {
      console.log("WebSocket closed");
    };
  });
};