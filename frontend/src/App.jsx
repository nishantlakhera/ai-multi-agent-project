import React, { useState } from "react";
import { chat } from "./api/client";
import "./App.css";

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
    <div className="app">
      <div className="app__shell">
        <header className="app__header">
          <div>
            <p className="app__eyebrow">Multi-Agent Control Room</p>
            <h1 className="app__title">Ask, Route, Synthesize</h1>
            <p className="app__subtitle">
              A multi-source assistant that blends docs, data, and web context.
            </p>
          </div>
          <div className="app__status">
            <span className="app__pulse" />
            Live pipeline
          </div>
        </header>
        <div className="app__hero">
          <div className="app__hero-copy">
            <p className="app__hero-title">Intelligence stitched from three planes.</p>
            <p className="app__hero-body">
              Ask a question and watch the router choose the right specialist. The
              system blends internal docs, live data, and web context into one reply.
              Trigger async test runs with the Test Agent while you keep chatting.
            </p>
          </div>
          <div className="app__hero-art" aria-hidden="true">
            <svg viewBox="0 0 260 180" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="beam" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0" stopColor="#1e7a6d" stopOpacity="0.9" />
                  <stop offset="1" stopColor="#f2a654" stopOpacity="0.85" />
                </linearGradient>
              </defs>
              <rect x="12" y="18" width="96" height="62" rx="14" fill="#ffffff" opacity="0.8" />
              <rect x="148" y="12" width="96" height="62" rx="14" fill="#ffffff" opacity="0.65" />
              <rect x="78" y="104" width="120" height="64" rx="16" fill="#ffffff" opacity="0.7" />
              <circle cx="64" cy="49" r="20" fill="url(#beam)" />
              <circle cx="196" cy="42" r="18" fill="url(#beam)" opacity="0.8" />
              <path d="M64 70 C88 96, 120 104, 138 120" stroke="#1e7a6d" strokeWidth="4" fill="none" />
              <path d="M196 60 C176 92, 150 104, 130 120" stroke="#f2a654" strokeWidth="4" fill="none" />
              <circle cx="130" cy="126" r="14" fill="#1d2426" opacity="0.15" />
            </svg>
          </div>
        </div>

        <section className="chat">
          <div className="chat__header">
            <span>Conversation</span>
            <span className="chat__hint">Shift + Enter for a new line</span>
          </div>
          <div className="chat__stream">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`chat__row ${
                  m.role === "user" ? "chat__row--user" : "chat__row--assistant"
                }`}
                style={{ animationDelay: `${idx * 40}ms` }}
              >
                <div
                  className={`chat__bubble ${
                    m.role === "user" ? "chat__bubble--user" : "chat__bubble--assistant"
                  }`}
                >
                  <div className="chat__content">{m.content}</div>
                  {m.meta?.route && (
                    <div className="chat__meta">
                      route: {m.meta.route} | sources:{" "}
                      {m.meta.sources?.map((s) => s.type).join(", ") || "none"}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="chat__typing">
                <span />
                <span />
                <span />
              </div>
            )}
          </div>
        </section>

        <section className="composer">
          <textarea
            rows={3}
            className="composer__input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask about DB, docs, web, or run a test case..."
          />
          <div className="composer__actions">
            <button onClick={sendMessage} disabled={loading} className="composer__send">
              Send
            </button>
            <span className="composer__note">Responses stream from the route selected.</span>
          </div>
        </section>
      </div>
    </div>
  );
}
