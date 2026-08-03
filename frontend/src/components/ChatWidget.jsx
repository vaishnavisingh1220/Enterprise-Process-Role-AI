import { useEffect, useRef, useState } from "react";
import { askChat, ApiError } from "../api/client";

const SUGGESTED_QUESTIONS = [
  "How does AI affect the Procurement Manager?",
  "Compare Warehouse Manager and Inventory Analyst",
  "Which roles work across multiple processes?",
  "What activities will be automated?",
];

let nextId = 1;

/**
 * A chat interface over the /chat/ask endpoint. Every answer is grounded
 * in the deterministic query router + reasoning engine — this widget just
 * displays the result, including which intent/entities were matched, so
 * the traceability story stays visible even in free-text conversation.
 */
export default function ChatWidget() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function send(text) {
    const question = text.trim();
    if (!question || sending) return;

    setMessages((prev) => [...prev, { id: nextId++, role: "user", content: question }]);
    setInput("");
    setSending(true);

    try {
      const result = await askChat(question);
      setMessages((prev) => [
        ...prev,
        {
          id: nextId++,
          role: "assistant",
          content: result.answer,
          intent: result.matched_intent,
          matchedRoles: result.matched_roles,
          matchedProcesses: result.matched_processes,
          analysisId: result.analysis_id,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: nextId++,
          role: "error",
          content: err instanceof ApiError ? err.message : "Something went wrong.",
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    send(input);
  }

  return (
    <div className="flex h-[600px] flex-col rounded-lg border border-border bg-surface">
      <div className="border-b border-border px-4 py-3">
        <h2 className="font-display text-sm font-semibold text-text-primary">
          Ask about AI impact
        </h2>
        <p className="mt-0.5 text-xs text-text-muted">
          Grounded in the same reasoning engine as the rest of this app — every answer traces
          back to real activity data.
        </p>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
        {messages.length === 0 && (
          <div className="space-y-2">
            <p className="text-xs text-text-muted">Try asking:</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => send(q)}
                  className="rounded-full border border-border bg-ink px-3 py-1.5 text-left text-xs text-text-secondary transition-colors hover:border-accent/50 hover:text-text-primary"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <ChatBubble key={msg.id} message={msg} />
        ))}

        {sending && (
          <div className="flex items-center gap-2 text-xs text-text-muted">
            <span className="flex gap-1">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-text-muted [animation-delay:-0.3s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-text-muted [animation-delay:-0.15s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-text-muted" />
            </span>
            thinking
          </div>
        )}

        <div ref={scrollRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t border-border p-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about roles, processes, or AI impact…"
            disabled={sending}
            className="flex-1 rounded-lg border border-border bg-ink px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-60"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}

const INTENT_LABELS = {
  role_impact: "Role impact",
  compare_roles: "Comparison",
  multi_process_roles: "Multi-process roles",
  activities_by_impact: "Activities by impact",
  process_detail: "Process detail",
  role_list: "Role list",
  process_list: "Process list",
  unknown: "Out of scope",
};

function ChatBubble({ message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-lg rounded-br-sm bg-accent px-3.5 py-2 text-sm text-white">
          {message.content}
        </div>
      </div>
    );
  }

  if (message.role === "error") {
    return (
      <div className="flex justify-start">
        <div className="max-w-[80%] rounded-lg rounded-bl-sm border border-impact-eliminate/40 bg-impact-eliminate/10 px-3.5 py-2 text-sm text-impact-eliminate">
          {message.content}
        </div>
      </div>
    );
  }

  // assistant
  const matched = [...(message.matchedRoles || []), ...(message.matchedProcesses || [])];
  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] space-y-2">
        <div className="rounded-lg rounded-bl-sm bg-ink px-3.5 py-2.5 text-sm leading-relaxed text-text-primary">
          <p className="whitespace-pre-line">{message.content}</p>
        </div>
        <div className="flex flex-wrap items-center gap-1.5 px-1">
          <span className="rounded-full border border-border px-2 py-0.5 font-mono text-[10px] text-text-muted">
            {INTENT_LABELS[message.intent] || message.intent}
          </span>
          {matched.map((name) => (
            <span
              key={name}
              className="rounded-full border border-accent/30 bg-accent/10 px-2 py-0.5 font-mono text-[10px] text-accent"
            >
              {name}
            </span>
          ))}
          {message.analysisId && (
            <span className="font-mono text-[10px] text-text-muted">#{message.analysisId}</span>
          )}
        </div>
      </div>
    </div>
  );
}
