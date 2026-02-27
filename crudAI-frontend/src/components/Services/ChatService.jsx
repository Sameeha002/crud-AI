import axios from "axios";

const API_URL = "http://127.0.0.1:8000/assistant/";

// export const sendMessage = async (thread_id, content, userId = null) => {
//   const data = {
//     content: content,
//   };

//   if (thread_id) {
//     data.thread_id = thread_id;
//   }

//   if (userId) {
//     data.user_id = userId;
//   }
//   console.log("Sending payload:", data);
//   const response = await axios.post(API_URL, data, {
//     headers: {
//       "Content-Type": "application/json",
//     },
//   });

//   return response.data;
// };

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
  const data = {
    content: content,
  };

  if (thread_id) data.thread_id = thread_id;
  if (userId) data.user_id = userId;

  try {
    const response = await fetch(API_URL, { 
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {

      if(signal?.aborted){
        await reader.cancel();
        onComplete();
        return;
      }

      const { done, value } = await reader.read();
      
      if (done) {
        console.log(" Stream reading completed");
        break;
      }

      // Decode the chunk
      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;
      // Process all complete lines in the buffer
      let newlineIndex;
      while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
        const line = buffer.substring(0, newlineIndex).trim();
        console.log('line: ',line)
        buffer = buffer.substring(newlineIndex + 1);


        
        if (line.startsWith('data: ')) {
          const token = line.substring(6); // Remove "data: " prefix
          console.log('Extracted token:', token);

          if (token === '[DONE]') {
            console.log('Received [DONE] - completing stream');
            onComplete();
            return;
          } else if (token === 'ERROR') {
            console.error('Received ERROR from server');
            onError(new Error('Server error during streaming'));
            return;
          } else if (token) {
            console.log('Calling onChunk with token:', token);
            try {
              const parsed = JSON.parse(token)
              console.log('Parsed data', parsed)
              if(parsed.type === "thread_id"){
                console.log("Received Thread Id: ", parsed.thread_id)
                if(onThreadId && parsed.thread_id){
                  onThreadId(parsed.thread_id)
                }
                continue;
                
              }
              if(parsed.type === 'tool_call'){
                onChunk({
                  type: "tool_call",
                  tool: parsed.tool,
                  display_name: parsed.display_name
                  
                })
              }
              else if(parsed.type === 'tool_result'){
                onChunk({
                  type: "tool_result",
                  tool: parsed.tool,
                  content: parsed.content
                })
              }
              else if(parsed.type === 'text'){
                onChunk({
                  type: "text",
                  content: parsed.content
                })
                
              }
            } catch (error) {
              onChunk({ type: 'text', content: token })
            }
            
          } 
          else if(line.startsWith('thread_id: '))  {
            const newThreadId = line.substring(11).trim();
            if(onThreadId && newThreadId){
              onThreadId(newThreadId)
            }

          } 
        } 
      }
    }

    console.log('Stream ended without [DONE] signal, calling onComplete anyway');
    onComplete();

  } catch (error) {

    if(error.name === 'AbortError'){
      console.log('Stream aborted by user')
      onComplete();
      return;
    }

    console.error('Stream error:', error);
    onError(error);
  }
};
