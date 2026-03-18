import { useEffect, useRef, useState } from "react";
import "./Main.css";
import { IoSend } from "react-icons/io5";
import { FaCircleStop } from "react-icons/fa6";
import {
  sendMessageStream,
  sendEditMessageStream,
  sendRegenerateStream,
} from "../Services/ChatService";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { AiOutlineLike } from "react-icons/ai";
import { AiOutlineDislike } from "react-icons/ai";
import Dislike from "../Popup/Dislike";
import FeedbackService from "../Services/FeedbackService";
import { FiEdit2 } from "react-icons/fi";
import TextArea from "../EditTextArea/TextArea";
import { CiRedo } from "react-icons/ci";
import { sendAgentMessage } from "../Services/ChatService";

const Main = ({
  messages,
  setMessages,
  activeThread,
  setActiveThread,
  userId,
  toggleSidebar,
  setSources,
  sidebarOpen,
}) => {
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState("");
  const [toolCalls, setToolCalls] = useState([]);
  const [toolResults, setToolResults] = useState([]);
  const [editingIndex, setEditingIndex] = useState(null);
  const [mode, setMode] = useState("assistant");

  const messagesEndRef = useRef(null);
  const streamingMessageRef = useRef("");
  const toolCallsRef = useRef([]);
  const toolResultsRef = useRef([]);
  const abortControllerRef = useRef(null);
  const messageIdRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    console.log("Active Thread:", activeThread);
    console.log("User ID:", userId);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const userMessage = {
      role: "user",
      content: input,
    };

    // Add user message to UI
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput("");
    setIsLoading(true);
    setStreamingMessage("");
    setToolCalls([]);
    streamingMessageRef.current = "";
    toolCallsRef.current = [];
    toolResultsRef.current = [];
    messageIdRef.current = null;

    try {
      await sendMessageStream(
        activeThread,
        currentInput,
        userId,
        // onChunk call back function
        (parsed) => {
          if (parsed.type === "tool_call") {
            toolCallsRef.current = [...toolCallsRef.current, parsed];
            setToolCalls([...toolCallsRef.current]);
            return;
          }
          if (parsed.type === "tool_result") {
            toolResultsRef.current = [...toolResultsRef.current, parsed];
            setToolResults([...toolResultsRef.current]);
            return;
          }
          if (parsed.type === "message_id") {
            messageIdRef.current = parsed.message_id;
            return;
          }
          if (parsed.type === "text") {
            streamingMessageRef.current += parsed.content;
            setStreamingMessage(streamingMessageRef.current);
          }
        },
        // onComplete
        // onComplete
        async () => {
          const structuredContent = [
            ...toolCallsRef.current,
            ...toolResultsRef.current,
            { type: "text", content: streamingMessageRef.current },
          ];
          setStreamingMessage("");
          setToolCalls([]);
          setToolResults([]);
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: JSON.stringify(structuredContent),
              message_id: messageIdRef.current,
            },
          ]);
          // }

          setStreamingMessage("");
          setToolCalls([]);
          setToolResults([]);
          toolCallsRef.current = [];
          toolResultsRef.current = [];
          streamingMessageRef.current = "";
          setIsLoading(false);
        },
        // onError
        (error) => {
          console.error("Streaming error:", error);
          // Remove the user message on error
          setMessages((prev) => prev.slice(0, -1));
          setInput(currentInput);
          alert("Failed to send message. Please try again.");
          setStreamingMessage("");
          setToolCalls([]);
          setToolResults([]);
          toolCallsRef.current = [];
          toolResultsRef.current = [];
          streamingMessageRef.current = "";
          setIsLoading(false);
        },
        // onThreadId
        (newThreadId) => {
          console.log("Received thread_id:", newThreadId);
          if (!activeThread) {
            setActiveThread(newThreadId);
          }
        },
        // pass signal to abort controller to stop streaming messages
        abortController.signal,
      );
    } catch (error) {
      console.error("Error sending message:", error);
      // Remove the user message if there was an error
      setMessages((prev) => prev.slice(0, -1));
      setInput(currentInput); // Restore the input
      alert("Failed to send message. Please try again.");
    } finally {
      setIsLoading(false);
      setStreamingMessage("");
      setToolCalls([]);
      setToolResults([]);
      toolCallsRef.current = [];
      toolResultsRef.current = [];
      streamingMessageRef.current = "";
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };
  const handleAgentSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput("");
    setIsLoading(true);

    try {
      const data = await sendAgentMessage(userId, activeThread, currentInput);
      if (!activeThread && data.thread_id) {
        setActiveThread(data.thread_id);
      }
      const structuredContent = [
        // tool calls first
        ...(data.routed_to ? [{type: "routed_to", agent: data.routed_to}] : []),
        ...(data.tool_calls || []).map((tc) => ({
          type: "tool_call",
          tool: tc.tool,
          display_name: tc.tool,
        })),
        // then tool results
        ...(data.tool_results || []).map((tr) => ({
          type: "tool_result",
          tool: tr.tool,
          content:
            typeof tr.content === "string"
              ? tr.content
              : JSON.stringify(tr.content, null, 2),
        })),
        // finally the text response
        { type: "text", content: data.response ?? "" },
      ];

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: JSON.stringify(structuredContent),
          message_id: data.message_id ?? null,
        },
      ]);
    } catch (error) {
      console.error("Agent error:", error);
      setMessages((prev) => prev.slice(0, -1));
      setInput(currentInput);
      alert("Agent failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const extractSources = (text) => {
    if (!text || typeof text !== "string") return [];

    const sources = [];
    const lines = text.split("\n");

    lines.forEach((line) => {
      // Standard markdown
      const markdownMatch = line.match(/\[(.+?)\]\((https?:\/\/[^\s)]+)\)/);
      if (markdownMatch) {
        sources.push({ title: markdownMatch[1], url: markdownMatch[2] });
        return;
      }

      // 【https://...】
      const bracketMatch = line.match(
        /^[\d\.\s]*(.+?)[【\[【](https?:\/\/[^\s】\]]+)[】\]】]/,
      );
      if (bracketMatch) {
        const title = bracketMatch[1].replace(/[-–—]+$/, "").trim(); // strip trailing dashes
        sources.push({ title, url: bracketMatch[2] });
        return;
      }

      // bare URL
      const urlMatch = line.match(/(https?:\/\/[^\s】\]]+)/);
      if (urlMatch) {
        try {
          sources.push({
            title: new URL(urlMatch[1]).hostname,
            url: urlMatch[1],
          });
        } catch {
          sources.push({ title: urlMatch[1], url: urlMatch[1] });
        }
      }
    });

    return sources;
  };

  const handleSourceClick = (parsedcontent) => {
    if (!Array.isArray(parsedcontent)) {
      toggleSidebar();
      return;
    }
    const textItem = parsedcontent.find((item) => item.type === "text");
    if (textItem) {
      const links = extractSources(textItem.content);
      setSources(links);
    }
    toggleSidebar();
  };

  const stripSources = (text) => {
    return text.replace(/\n*#{1,3}\s*Sources[\s\S]*/i, "").trim();
  };

  const handleEditSubmit = async (editedContent, messageIndex) => {
    const updatedMessages = [
      ...messages.slice(0, messageIndex),
      { role: "user", content: editedContent },
    ];
    setMessages(updatedMessages);
    setEditingIndex(null);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    setIsLoading(true);
    setStreamingMessage("");
    setToolCalls([]);
    streamingMessageRef.current = "";
    toolCallsRef.current = [];
    toolResultsRef.current = [];
    messageIdRef.current = null;

    await sendEditMessageStream(
      activeThread,
      messageIndex,
      editedContent,
      // onChunk — same as handleEditSend
      (parsed) => {
        if (parsed.type === "tool_call") {
          toolCallsRef.current = [...toolCallsRef.current, parsed];
          setToolCalls([...toolCallsRef.current]);
          return;
        }
        if (parsed.type === "tool_result") {
          toolResultsRef.current = [...toolResultsRef.current, parsed];
          setToolResults([...toolResultsRef.current]);
          return;
        }
        if (parsed.type === "message_id") {
          messageIdRef.current = parsed.message_id;
          return;
        }
        if (parsed.type === "text") {
          streamingMessageRef.current += parsed.content;
          setStreamingMessage(streamingMessageRef.current);
        }
      },
      // onComplete
      () => {
        const structuredContent = [
          ...toolCallsRef.current,
          ...toolResultsRef.current,
          { type: "text", content: streamingMessageRef.current },
        ];
        setStreamingMessage("");
        setToolCalls([]);
        setToolResults([]);
        setMessages([
          ...updatedMessages,
          {
            role: "assistant",
            content: JSON.stringify(structuredContent),
            message_id: messageIdRef.current,
          },
        ]);
        setStreamingMessage("");
        setToolCalls([]);
        setToolResults([]);
        toolResultsRef.current = [];
        streamingMessageRef.current = "";
        setIsLoading(false);
      },
      // onError
      (error) => {
        console.error("Streaming error:", error);
        setIsLoading(false);
      },
      abortController.signal,
    );
  };

  const handleRegenerate = async (msg) => {
    // Clear the existing message and mark regenerating
    setMessages((prev) =>
      prev.map((m) =>
        m.message_id === msg.message_id
          ? { ...m, content: "", isRegenerating: true }
          : m,
      ),
    );

    setIsLoading(true);
    streamingMessageRef.current = "";
    toolCallsRef.current = [];
    toolResultsRef.current = [];
    messageIdRef.current = null;

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    await sendRegenerateStream(
      activeThread,
      msg.message_id,
      (parsed) => {
        if (parsed.type === "tool_call") {
          toolCallsRef.current = [...toolCallsRef.current, parsed];
          setToolCalls([...toolCallsRef.current]);
          return;
        }
        if (parsed.type === "tool_result") {
          toolResultsRef.current = [...toolResultsRef.current, parsed];
          setToolResults([...toolResultsRef.current]);
          return;
        }
        if (parsed.type === "message_id") {
          messageIdRef.current = parsed.message_id;
          return;
        }
        if (parsed.type === "text") {
          streamingMessageRef.current += parsed.content;
          setStreamingMessage(streamingMessageRef.current);
        }
      },
      () => {
        // onComplete — replace the message in state
        const structuredContent = [
          ...toolCallsRef.current,
          ...toolResultsRef.current,
          { type: "text", content: streamingMessageRef.current },
        ];
        setStreamingMessage("");
        setToolCalls([]);
        setToolResults([]);
        setMessages((prev) =>
          prev.map((m) =>
            m.message_id === msg.message_id
              ? {
                  ...m,
                  content: JSON.stringify(structuredContent),
                  isRegenerating: false,
                }
              : m,
          ),
        );
        setStreamingMessage("");
        setIsLoading(false);
        streamingMessageRef.current = "";
      },
      (err) => {
        console.error(err);
        setIsLoading(false);
      },
      abortController.signal,
    );
  };

  return (
    <div className={`main-container ${sidebarOpen ? "shifted" : ""}`}>
      {messages.length === 0 && (
        <div className="greeting-message">
          <h2>Hey! How can I help you today</h2>
        </div>
      )}

      <div className="chat-window">
        <div className="message-wrapper">
          {messages.map((msg, index) => {
            if (msg.role === "user") {
              return (
                <div key={index} className="user-message-wrapper">
                  <div className="message user-message">{msg.content}</div>
                  <div className="edit">
                    <FiEdit2
                      onClick={() =>
                        setEditingIndex(editingIndex === index ? null : index)
                      }
                    />
                  </div>
                  {editingIndex == index && (
                    <TextArea
                      content={msg.content}
                      onCancel={() => setEditingIndex(null)}
                      onSubmit={(editedContent) =>
                        handleEditSubmit(editedContent, index)
                      }
                    />
                  )}
                </div>
              );
            }
            let parsedContent = [];
            try {
              parsedContent =
                typeof msg.content === "string"
                  ? JSON.parse(msg.content)
                  : msg.content;

              // console.log("Parsed Content:", parsedContent);
            } catch (error) {
              return (
                <div key={index} className="message assistant-message">
                  {msg.content}
                </div>
              );
            }
            return (
              <div className="message assistant-message" key={index}>
                {parsedContent.map((item, i) => {
                  if (item.type === "routed_to") {
                    const agentLabels = {
                      music_agent: "Music Agent",
                      sales_agent: "Sales Agent",
                    };
                    return (
                      <div key={i} className="  ">
                        <span>Supervisor routed to: </span>
                        <strong>{agentLabels[item.agent] || item.agent}</strong>
                      </div>
                    );
                  }
                  if (item.type === "tool_call") {
                    return (
                      <div key={i} className="tool-call-back">
                        <b>Tool called:</b> {item.display_name || item.tool}
                      </div>
                    );
                  }

                  if (item.type === "tool_result") {
                    return (
                      <div key={i} className="tool-result">
                        <b>Result:</b> {item.content}
                      </div>
                    );
                  }

                  if (item.type === "text") {
                    return (
                      <div key={i}>
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {stripSources(item.content)}
                        </ReactMarkdown>

                        <div className="feedback-actions">
                          <div>
                            <AiOutlineLike
                              className="like-button"
                              onClick={() =>
                                FeedbackService(
                                  activeThread,
                                  msg.message_id,
                                  "like",
                                  null,
                                )
                              }
                            />
                          </div>
                          <div>
                            <AiOutlineDislike
                              className="dislike-button"
                              role="button"
                              data-bs-toggle="modal"
                              data-bs-target={`#dislikeModal-${msg.message_id}`}
                              data-bs-focus="false"
                            />
                            <Dislike
                              threadId={activeThread}
                              messageId={msg.message_id}
                              modalId={`dislikeModal-${msg.message_id}`}
                            />
                          </div>
                          <div>
                            <CiRedo
                              className="regenerate-button"
                              onClick={() => handleRegenerate(msg)}
                            />
                          </div>
                          {parsedContent.some(
                            (c) =>
                              c.type === "tool_call" &&
                              (c.tool === "web_search" ||
                                c.display_name
                                  ?.toLowerCase()
                                  .includes("search")),
                          ) && (
                            <div>
                              <p
                                className="sources"
                                onClick={() => handleSourceClick(parsedContent)}
                              >
                                Sources
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  }
                  return null;
                })}
              </div>
            );
          })}

          {(toolCalls.length > 0 ||
            toolResults.length > 0 ||
            streamingMessage) && (
            <div className="message assistant-message">
              {toolCalls.map((tool, index) => (
                <div className="tool-call-back" key={`tr-${index}`}>
                  Tool Called: {tool.display_name || tool.tool}
                </div>
              ))}

              {toolResults.map((result, index) => (
                <div key={`tr-${index}`} className="tool-result">
                  <b>Result:</b> {result.content}
                </div>
              ))}

              {streamingMessage && (
                <div className="message assistant-message">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {streamingMessage}
                  </ReactMarkdown>
                  <span className="cursor">▋</span>
                </div>
              )}
            </div>
          )}

          {isLoading && !streamingMessage && (
            <div className="message assistant-message">
              <span className="typing-indicator">Thinking...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="chat-input">
        <div className="chat-input-card">
          {/* Mode toggle toolbar at top */}
          <div className="chat-input-toolbar">
            <button
              className={mode === "assistant" ? "mode-btn active" : "mode-btn"}
              onClick={() => setMode("assistant")}
            >
              Assistant
            </button>
            <button
              className={mode === "agent" ? "mode-btn active" : "mode-btn"}
              onClick={() => setMode("agent")}
            >
              Multi-Agent
            </button>
          </div>

          {/* Textarea + send button row below */}
          <div className="chat-input-bottom">
            <textarea
              placeholder={
                mode === "agent"
                  ? "Ask the multi-agent..."
                  : "Enter Message Here . . ."
              }
              className="chat-input-field"
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                e.target.style.height = "auto";
                e.target.style.height = e.target.scrollHeight + "px";
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  mode === "agent" ? handleAgentSend() : handleSend();
                }
              }}
              disabled={isLoading}
              rows={1}
            />

            {isLoading ? (
              <FaCircleStop className="stop-btn" onClick={handleStop} />
            ) : (
              <IoSend
                className="send-btn"
                onClick={mode === "agent" ? handleAgentSend : handleSend}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Main;