"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { chatWithAI } from "@/lib/api";
import { AIChatMessage, AIExplanationResponse } from "@/types/stock";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface AIChatPanelProps {
  symbol: string | null;
  initialInsight: AIExplanationResponse | null;
}

export default function AIChatPanel({ symbol, initialInsight }: AIChatPanelProps) {
  const [messages, setMessages] = useState<AIChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [conversationSummary, setConversationSummary] = useState<string | null>(null);
  const [provider, setProvider] = useState<"gemini" | "fallback" | null>(null);
  const [model, setModel] = useState<string>("-");

  useEffect(() => {
    setMessages([]);
    setInput("");
    setChatError(null);
    setConversationSummary(null);
    setProvider(initialInsight?.provider ?? null);
    setModel(initialInsight?.model ?? "-");
  }, [symbol, initialInsight]);

  const canSend = useMemo(() => !!symbol && input.trim().length > 0 && !loading, [symbol, input, loading]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!symbol || !input.trim() || loading) {
      return;
    }

    const userMessage: AIChatMessage = { role: "user", content: input.trim() };
    const nextHistory = [...messages, userMessage];
    setMessages(nextHistory);
    setInput("");
    setLoading(true);
    setChatError(null);

    try {
      const res = await chatWithAI(symbol, {
        message: userMessage.content,
        history: messages,
        conversation_summary: conversationSummary,
      });

      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
      setProvider(res.provider);
      setModel(res.model);
      setConversationSummary(res.conversation_summary ?? null);
      if (res.fallback_used && res.fallback_reason) {
        setChatError(`Fallback: ${res.fallback_reason}`);
      }
    } catch (err) {
      setChatError(err instanceof Error ? err.message : "Chat request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm uppercase tracking-[0.2em] text-slate-500">AI Chat</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between rounded-md bg-slate-100 px-3 py-2 text-xs dark:bg-slate-900">
          <span>{symbol ?? "No symbol selected"}</span>
          <Badge variant={provider === "gemini" ? "success" : "secondary"}>
            {provider ?? "N/A"} / {model}
          </Badge>
        </div>

        <div className="max-h-64 space-y-2 overflow-y-auto rounded-md border border-slate-200 bg-white p-2 dark:border-slate-700 dark:bg-slate-950">
          {messages.length === 0 ? (
            <p className="text-xs text-slate-500 dark:text-slate-300">
              Ask about trend, risk, entry levels, or compare momentum for this symbol.
            </p>
          ) : null}
          {messages.map((message, idx) => (
            <div
              key={`${message.role}-${idx}`}
              className={
                message.role === "user"
                  ? "ml-auto max-w-[90%] rounded-md bg-cyan-500 px-3 py-2 text-sm text-white"
                  : "mr-auto max-w-[90%] rounded-md bg-slate-100 px-3 py-2 text-sm text-slate-700 dark:bg-slate-900 dark:text-slate-200"
              }
            >
              {message.content}
            </div>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask follow-up questions..."
            rows={3}
            className="w-full resize-none rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none ring-cyan-400 focus:ring-2 dark:border-slate-700 dark:bg-slate-950"
          />
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500 dark:text-slate-300">
              Context-aware chat with history summarization.
            </span>
            <Button type="submit" size="sm" disabled={!canSend}>
              {loading ? "Thinking..." : "Send"}
            </Button>
          </div>
        </form>

        {chatError ? <p className="text-xs text-amber-600 dark:text-amber-300">{chatError}</p> : null}
      </CardContent>
    </Card>
  );
}
