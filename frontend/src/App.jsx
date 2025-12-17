import React, { useState } from "react";
import { chat } from "./api/client";

const USER_ID = "demo-user";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = { role: "user", content: input };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await chat(USER_ID, userMsg.content);
      const assistantMsg = {
        role: "assistant",
        content: res.answer,
        meta: { route: res.route, sources: res.sources }
      };
      setMessages((m) => [...m, assistantMsg]);
    } catch (e) {
      console.error(e);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Error calling backend." }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto", padding: 24 }}>
      <h1>Multi-Agent AI Chat</h1>
      <div
        style={{
          border: "1px solid #ccc",
          borderRadius: 8,
          padding: 16,
          minHeight: 300,
          marginBottom: 16,
          overflowY: "auto"
        }}
      >
        {messages.map((m, idx) => (
          <div
            key={idx}
            style={{
              marginBottom: 12,
              textAlign: m.role === "user" ? "right" : "left"
            }}
          >
            <div
              style={{
                display: "inline-block",
                padding: "8px 12px",
                borderRadius: 12,
                background: m.role === "user" ? "#e0f7fa" : "#f1f1f1"
              }}
            >
              <div>{m.content}</div>
              {m.meta?.route && (
                <div style={{ fontSize: 10, marginTop: 4, opacity: 0.7 }}>
                  route: {m.meta.route} | sources:{" "}
                  {m.meta.sources?.map((s) => s.type).join(", ") || "none"}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && <div>Thinking...</div>}
      </div>
      <textarea
        rows={3}
        style={{ width: "100%", padding: 8 }}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder="Ask anything about DB, docs, or web..."
      />
      <button onClick={sendMessage} disabled={loading} style={{ marginTop: 8 }}>
        Send
      </button>
    </div>
  );
}
