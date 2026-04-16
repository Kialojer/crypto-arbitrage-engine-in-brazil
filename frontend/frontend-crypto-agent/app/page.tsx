"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";

interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [threadId] = useState(() =>
    Math.random().toString(36).substring(7)
  );

  const { getToken } = useAuth();

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const token = await getToken();

    if (!token) {
      alert("Please sign in first to use the AI Agent!");
      return;
    }

    const userMessage = input;
    const aiMessageId = Date.now().toString();

    setInput("");
    setIsLoading(true);

    // ✅ یک setState تمیز (بدون race condition)
    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString() + "_user", role: "user", content: userMessage },
      { id: aiMessageId, role: "ai", content: "" },
    ]);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          question: userMessage,
          thread_id: threadId,
        }),
      });

      if (!response.ok) throw new Error(`Server Error: ${response.status}`);
      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const part of parts) {
          if (part.startsWith("data: ")) {
            const dataStr = part.replace("data: ", "");

            if (dataStr === "[DONE]") {
              setIsLoading(false);
              return;
            }

            try {
              const parsed = JSON.parse(dataStr);

              // ✅ آپدیت پایدار بر اساس id
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === aiMessageId
                    ? { ...msg, content: msg.content + parsed.text }
                    : msg
                )
              );
            } catch (err) {
              console.error("Stream parse error:", err);
            }
          }
        }
      }

      setIsLoading(false);
    } catch (error) {
      console.error("Fetch error:", error);

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === aiMessageId
            ? {
                ...msg,
                content: "❌ Authentication Error or Server Offline.",
              }
            : msg
        )
      );

      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#f9fafb] p-8 font-sans">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-[#062147] tracking-tight">
            Crypto Intelligence
          </h1>
          <p className="text-sm text-gray-500 mt-2">
            Secure Autonomous Auditing & Market Analysis
          </p>
        </header>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col h-[70vh]">
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center p-8 bg-[#209DD7]/5 rounded-lg border border-dashed border-[#209DD7]/20">
                <div className="w-12 h-12 rounded-full bg-[#209DD7]/10 flex items-center justify-center mb-4">
                  <span className="text-[#209DD7] text-xl">📊</span>
                </div>
                <h3 className="text-[#062147] font-medium">
                  Ready for Analysis
                </h3>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${
                    msg.role === "user"
                      ? "justify-end"
                      : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[80%] p-4 rounded-lg text-sm leading-relaxed ${
                      msg.role === "user"
                        ? "bg-[#209DD7] text-white rounded-br-none"
                        : "bg-gray-50 text-[#062147] border border-gray-100 rounded-bl-none"
                    }`}
                  >
                    {msg.role === "ai" && (
                      <strong className="block text-[#753991] mb-1 text-xs uppercase tracking-wider">
                        AI Agent
                      </strong>
                    )}
                    {msg.content}
                  </div>
                </div>
              ))
            )}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-50 border border-gray-100 p-4 rounded-lg rounded-bl-none flex items-center space-x-3">
                  <div className="w-2.5 h-2.5 bg-[#753991] rounded-full animate-glow-pulse"></div>
                  <div
                    className="w-2.5 h-2.5 bg-[#753991] rounded-full animate-glow-pulse"
                    style={{ animationDelay: "0.2s" }}
                  ></div>
                  <div
                    className="w-2.5 h-2.5 bg-[#753991] rounded-full animate-glow-pulse"
                    style={{ animationDelay: "0.4s" }}
                  ></div>
                </div>
              </div>
            )}
          </div>

          <div className="p-4 bg-gray-50 border-t border-gray-100">
            <form onSubmit={sendMessage} className="flex space-x-4">
              <input
                suppressHydrationWarning
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about Bitcoin price or calculate 15% tax..."
                className="flex-1 bg-white border border-gray-200 text-[#062147] rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-[#209DD7]/50"
                disabled={isLoading}
              />
              <button
                suppressHydrationWarning
                type="submit"
                disabled={isLoading || !input.trim()}
                className="bg-[#209DD7] text-white px-6 py-3 rounded-lg font-medium disabled:opacity-50"
              >
                Analyze
              </button>
            </form>
          </div>
        </div>
      </div>
    </main>
  );
}