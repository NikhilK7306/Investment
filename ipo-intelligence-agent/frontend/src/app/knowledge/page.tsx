"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Brain, Search, AlertTriangle, CheckCircle, BookOpen, Sparkles, Zap, TrendingUp, AlertCircle, Plus, Edit, Trash2, Globe, Settings, History, Lightbulb } from "lucide-react";

const mockPractices = [
  { name: "DCF with conservative growth assumptions", category: "Valuation", successRate: 0.89, usage: 12, tags: ["DCF", "Valuation", "Conservative"] },
  { name: "Peer-based EV/Revenue with 20% discount", category: "Valuation", successRate: 0.85, usage: 8, tags: ["Comps", "Valuation", "Discount"] },
  { name: "Scenario analysis with Monte Carlo simulation", category: "Risk", successRate: 0.87, usage: 6, tags: ["Risk", "Monte Carlo", "Scenarios"] },
  { name: "TAM/SAM/SOM with platform business adjustment", category: "Market", successRate: 0.84, usage: 9, tags: ["Market Sizing", "Platform", "TAM"] },
  { name: "Sentiment-weighted scoring with news divergence detection", category: "Sentiment", successRate: 0.82, usage: 15, tags: ["Sentiment", "NLP", "Scoring"] },
  { name: "Scenario analysis with Monte Carlo simulation", category: "Risk", successRate: 0.87, usage: 6, tags: ["Risk", "Monte Carlo", "Scenarios"] },
];

const mockKnowledge = [
  { id: "1", concept: "DCF Valuation", domain: "Valuation", confidence: 0.95, tags: ["DCF", "Valuation", "Cash Flow"], evidence: ["Damodaran", "McKinsey"], description: "Discounted cash flow analysis for IPO valuation" },
  { id: "2", concept: "Comparable Company Analysis", domain: "Valuation", confidence: 0.93, tags: ["Comps", "Valuation", "Multiples"], evidence: ["IBISWorld", "Bloomberg"], description: "Peer-based valuation using EV/Revenue, P/E multiples" },
  { id: "3", concept: "Market Sizing", domain: "Market Analysis", confidence: 0.90, tags: ["TAM", "SAM", "SOM", "Market Size"], evidence: ["Gartner", "IDC"], description: "Total addressable market estimation frameworks" },
  { id: "4", concept: "Risk Factors", domain: "Risk Assessment", confidence: 0.88, tags: ["Risk", "IPO", "SEC Filing"], evidence: ["SEC Filings", "Prospectus"], description: "Common risk factors in IPO prospectuses" },
];

const mockLessons = [
  { id: "1", type: "Best Practice", title: "Always validate financial data before analysis", do: ["Cross-reference multiple sources", "Check for data anomalies", "Verify units and currencies"], dont: ["Trust single source blindly", "Ignore outliers without investigation"], confidence: 0.92, tags: ["Data Quality", "Fundamental Analysis"] },
  { id: "2", type: "Prompt Improvement", title: "Add explicit validation steps in prompts", do: ["Ask agent to verify assumptions", "Request source citations", "Require confidence scores"], dont: ["Accept first answer without verification"], confidence: 0.88, tags: ["Prompt Engineering", "Validation"] },
  { id: "3", type: "Anti Pattern", title: "Assuming linear growth in mature markets", do: ["Model saturation effects", "Consider market maturity", "Use logistic growth models"], dont: ["Extrapolate linear growth indefinitely"], confidence: 0.85, tags: ["Market Analysis", "Growth Modeling"] },
];

export default function KnowledgePage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Knowledge Base</h1>
            <p className="text-muted-foreground">Verified financial knowledge, best practices, and learned lessons</p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Knowledge
          </Button>
        </div>

        <Tabs defaultValue="knowledge" className="space-y-4">
          <TabsList>
            <TabsTrigger value="knowledge">Knowledge ({mockKnowledge.length})</TabsTrigger>
            <TabsTrigger value="lessons">Lessons ({mockLessons.length})</TabsTrigger>
            <TabsTrigger value="best-practices">Best Practices</TabsTrigger>
          </TabsList>

          <TabsContent value="knowledge" className="space-y-4">
            <div className="flex gap-4 mb-4">
              <Input placeholder="Search knowledge..." className="w-80" />
              <Select defaultValue="all">
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="All Domains" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Domains</SelectItem>
                  <SelectItem value="SaaS Metrics">SaaS Metrics</SelectItem>
                  <SelectItem value="Unit Economics">Unit Economics</SelectItem>
                  <SelectItem value="Finance">Finance</SelectItem>
                  <SelectItem value="Valuation">Valuation</SelectItem>
                  <SelectItem value="Competitive Advantage">Competitive Advantage</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {mockKnowledge.map((item, index) => (
                <Card key={index} className="hover:border-primary/50 transition-colors">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BookOpen className="h-5 w-5" />
                      {item.concept}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="text-sm text-muted-foreground">{item.domain}</p>
                    <p className="text-sm text-muted-foreground">{item.description}</p>
                    <div className="flex flex-wrap gap-2">
                      {item.tags.map((tag, i) => (
                        <Badge key={i} variant="outline" className="text-xs">{tag}</Badge>
                      ))}
                    </div>
                    <div className="flex items-center justify-between pt-2 border-t">
                      <Badge variant={item.confidence > 0.9 ? "success" : "default"}>
                        {Math.round(item.confidence * 100)}% confidence
                      </Badge>
                      <div className="flex gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8"><Edit className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8"><Trash2 className="h-4 w-4" /></Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="lessons" className="space-y-4">
            <div className="flex gap-4 mb-4">
              <Input placeholder="Search lessons..." className="w-80" />
              <Select defaultValue="all">
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="All Types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="Best Practice">Best Practice</SelectItem>
                  <SelectItem value="Prompt Improvement">Prompt Improvement</SelectItem>
                  <SelectItem value="Anti Pattern">Anti Pattern</SelectItem>
                  <SelectItem value="Risk Factor">Risk Factor</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-4">
              {mockLessons.map((lesson, index) => (
                <div key={index} className="border rounded-lg p-4 hover:border-primary/50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <Badge variant={lesson.type === "Best Practice" ? "success" : lesson.type === "Anti Pattern" ? "destructive" : "default"}>
                        {lesson.type}
                      </Badge>
                      <h3 className="font-semibold text-lg">{lesson.title}</h3>
                      <Badge variant="outline" className="text-xs">{Math.round(lesson.confidence * 100)}% confidence</Badge>
                    </div>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">Confidence: {Math.round(lesson.confidence * 100)}%</p>
                  <div className="mt-3 grid gap-4 md:grid-cols-2">
                    <div>
                      <h4 className="font-medium text-sm text-green-600 flex items-center gap-1">
                        <CheckCircle className="h-3 w-3" /> Do
                      </h4>
                      <ul className="mt-1 space-y-1 text-sm text-green-700">
                        {lesson.do.map((item, i) => (
                          <li key={i} className="flex items-center gap-1">
                            <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-sm text-red-600 flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" /> Don't
                      </h4>
                      <ul className="mt-1 space-y-1 text-sm text-red-700">
                        {lesson.dont.map((item, i) => (
                          <li key={i} className="flex items-center gap-1">
                            <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {lesson.tags.map((tag, i) => (
                      <Badge key={i} variant="outline" className="text-xs">{tag}</Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="best-practices" className="space-y-4">
            <div className="flex gap-4 mb-4">
              <Input placeholder="Search best practices..." className="w-80" />
              <Button variant="outline"><Plus className="h-4 w-4 mr-2" />Add Practice</Button>
            </div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {mockPractices.map((practice, i) => (
                <Card key={i}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BookOpen className="h-5 w-5" />
                      {practice.name}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex-4 text-sm text-muted-foreground">
                      <p className="font-medium text-muted-foreground">Category: </p>
                      <span>{practice.category}</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {practice.tags.map((tag, i) => (
                        <Badge key={i} variant="outline" className="text-xs">{tag}</Badge>
                      ))}
                    </div>
                    <div className="flex items-center justify-between pt-2 border-t">
                      <Badge variant="success">{Math.round(practice.successRate * 100)}% success</Badge>
                      <Badge variant="outline">{practice.usage} uses</Badge>
                    </div>
                    <Button className="w-full">Use Template</Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}