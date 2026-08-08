"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Send, Bot, User, Clock } from "lucide-react";
import { useState } from "react";

const agents = [
  { id: "discovery", name: "Discovery" },
  { id: "fundamental", name: "Fundamental" },
  { id: "market", name: "Market" },
  { id: "risk", name: "Risk" },
  { id: "sentiment", name: "Sentiment" },
  { id: "decision", name: "Decision" },
];

interface ChatMessage {
  id: string;
  role: "user" | "system";
  agent?: string;
  content: string;
  timestamp: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages([
      ...messages,
      { id: Date.now().toString(), role: "user", content: input, timestamp: new Date().toISOString() },
    ]);
    setInput("");
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Agent Chat</h1>
            <p className="text-muted-foreground">Interact with IPO intelligence agents in real-time</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setMessages([])}>New Conversation</Button>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {agents.map((agent) => (
            <Badge key={agent.id} variant="secondary">{agent.name}</Badge>
          ))}
        </div>

        <Card className="flex flex-col h-[600px]">
          <CardHeader>
            <CardTitle>Chat</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col">
            <div className="flex-1 overflow-y-auto space-y-4 mb-4">
              {messages.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-center">
                  <Bot className="h-12 w-12 mb-4 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground max-w-sm">
                    Ask about an IPO, its valuation, market conditions, or risks. Messages are handled
                    by the agent pipeline and routed to the relevant specialist agent.
                  </p>
                </div>
              )}
              {messages.map((msg) => (
                <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
                  {msg.role !== "user" && (
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <Bot className="h-4 w-4 text-primary" />
                    </div>
                  )}
                  <div className={`max-w-[70%] ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"} rounded-lg p-3`}>
                    <div className="flex items-center gap-2 mb-1">
                      {msg.role !== "user" && msg.agent && <Badge variant="secondary" className="text-[10px]">{msg.agent}</Badge>}
                      {msg.role === "user" && <span className="text-xs font-medium">You</span>}
                    </div>
                    <p className="text-sm">{msg.content}</p>
                    <div className="flex items-center gap-1 mt-1">
                      <Clock className="h-3 w-3 opacity-50" />
                      <span className="text-[10px] opacity-50">{msg.timestamp}</span>
                    </div>
                  </div>
                  {msg.role === "user" && (
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <User className="h-4 w-4 text-primary" />
                    </div>
                  )}
                </div>
              ))}
            </div>
            <Separator className="mb-4" />
            <div className="flex gap-2">
              <Input
                placeholder="Ask about an IPO, company, or market condition..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                className="flex-1"
              />
              <Button onClick={handleSend}><Send className="h-4 w-4" /></Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}