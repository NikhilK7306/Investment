"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Send, Bot, User, Brain, Sparkles, MessageSquare, Clock } from "lucide-react";
import { useState } from "react";

const agents = [
  { id: "all", name: "All Agents", active: true },
  { id: "fundamental", name: "Fundamental", active: false },
  { id: "market", name: "Market", active: false },
  { id: "risk", name: "Risk", active: false },
  { id: "sentiment", name: "Sentiment", active: false },
  { id: "decision", name: "Decision", active: false },
];

const initialMessages = [
  { id: "1", role: "system", agent: "Decision", content: "Welcome to the IPO Intelligence Agent Chat. I can help you analyze IPOs, assess risks, evaluate market conditions, and more. Select an agent or ask a general question.", timestamp: "2024-01-15 09:00" },
];

export default function ChatPage() {
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages([...messages, { id: Date.now().toString(), role: "user", agent: "You", content: input, timestamp: new Date().toISOString() }]);
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
            <Button variant="outline"><Sparkles className="h-4 w-4 mr-2" />New Conversation</Button>
            <Button><Brain className="h-4 w-4 mr-2" />Analyze IPO</Button>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">6</div>
              <p className="text-xs text-muted-foreground">All agents online</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Conversations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">12</div>
              <p className="text-xs text-muted-foreground">Active today</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Response</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-500">1.2s</div>
              <p className="text-xs text-muted-foreground">Average response time</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Queries Today</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">47</div>
              <p className="text-xs text-muted-foreground">+12 from yesterday</p>
            </CardContent>
          </Card>
        </div>

        <div className="flex flex-wrap gap-2">
          {agents.map((agent) => (
            <Badge key={agent.id} variant={agent.active ? "default" : "secondary"} className="cursor-pointer">
              {agent.name}
            </Badge>
          ))}
        </div>

        <Card className="flex flex-col h-[600px]">
          <CardHeader>
            <CardTitle>Chat</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col">
            <div className="flex-1 overflow-y-auto space-y-4 mb-4">
              {messages.map((msg) => (
                <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
                  {msg.role !== "user" && (
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <Bot className="h-4 w-4 text-primary" />
                    </div>
                  )}
                  <div className={`max-w-[70%] ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"} rounded-lg p-3`}>
                    <div className="flex items-center gap-2 mb-1">
                      {msg.role !== "user" && <Badge variant="secondary" className="text-[10px]">{msg.agent}</Badge>}
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
