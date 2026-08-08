"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BookOpen, Search, CheckCircle, AlertCircle, Loader2, Brain } from "lucide-react";
import { memoryService } from "@/services/memoryService";
import type { KnowledgeResponse, LessonResponse, BestPracticeResponse } from "@/types/memory";

export default function KnowledgePage() {
  const [knowledge, setKnowledge] = useState<KnowledgeResponse[]>([]);
  const [lessons, setLessons] = useState<LessonResponse[]>([]);
  const [practices, setPractices] = useState<BestPracticeResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const [k, l, p] = await Promise.all([
          memoryService.getKnowledge({ limit: 100 }).catch(() => []),
          memoryService.getLessons({ limit: 100 }).catch(() => []),
          memoryService.getBestPractices({ limit: 100 }).catch(() => []),
        ]);
        setKnowledge(k);
        setLessons(l);
        setPractices(p);
      } catch (err) {
        console.error("Failed to load knowledge base:", err);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Knowledge Base</h1>
            <p className="text-muted-foreground">Verified financial knowledge, best practices, and learned lessons</p>
          </div>
        </div>

        <Tabs defaultValue="knowledge" className="space-y-4">
          <TabsList>
            <TabsTrigger value="knowledge">Knowledge ({knowledge.length})</TabsTrigger>
            <TabsTrigger value="lessons">Lessons ({lessons.length})</TabsTrigger>
            <TabsTrigger value="best-practices">Best Practices ({practices.length})</TabsTrigger>
          </TabsList>

          {loading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading knowledge base...
            </div>
          )}

          <TabsContent value="knowledge" className="space-y-4">
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search knowledge..." className="pl-10" />
            </div>

            {knowledge.length === 0 ? (
              <Card>
                <CardContent className="py-16 text-center">
                  <Brain className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <h3 className="text-lg font-medium">No knowledge stored yet</h3>
                  <p className="text-sm text-muted-foreground max-w-md mx-auto mt-2">
                    Knowledge concepts are written by the analysis agents after each IPO analysis.
                    Run an analysis to start building this library.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {knowledge.map((item, index) => (
                  <Card key={index} className="hover:border-primary/50 transition-colors">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-base">
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
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="lessons" className="space-y-4">
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search lessons..." className="pl-10" />
            </div>

            {lessons.length === 0 ? (
              <Card>
                <CardContent className="py-16 text-center">
                  <AlertCircle className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <h3 className="text-lg font-medium">No lessons learned yet</h3>
                  <p className="text-sm text-muted-foreground max-w-md mx-auto mt-2">
                    Lessons are extracted automatically from outcome verification and agent reflections.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {lessons.map((lesson, index) => (
                  <div key={index} className="border rounded-lg p-4 hover:border-primary/50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <Badge variant={lesson.lesson_type === "BEST_PRACTICE" ? "success" : lesson.lesson_type === "ANTI_PATTERN" ? "destructive" : "default"}>
                          {lesson.lesson_type}
                        </Badge>
                        <h3 className="font-semibold text-lg">{lesson.title}</h3>
                        <Badge variant="outline" className="text-xs">{Math.round(lesson.confidence * 100)}% confidence</Badge>
                      </div>
                    </div>
                    {lesson.description && (
                      <p className="mt-2 text-sm text-muted-foreground">{lesson.description}</p>
                    )}
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
                          <AlertCircle className="h-3 w-3" /> Don&apos;t
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
            )}
          </TabsContent>

          <TabsContent value="best-practices" className="space-y-4">
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search best practices..." className="pl-10" />
            </div>

            {practices.length === 0 ? (
              <Card>
                <CardContent className="py-16 text-center">
                  <Brain className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <h3 className="text-lg font-medium">No best practices recorded yet</h3>
                  <p className="text-sm text-muted-foreground max-w-md mx-auto mt-2">
                    Best practices are recorded by the agents when they discover techniques that
                    consistently produce accurate analyses.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {practices.map((practice, i) => (
                  <Card key={i}>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-base">
                        <BookOpen className="h-5 w-5" />
                        {practice.practice_name}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <p className="text-sm text-muted-foreground">{practice.description}</p>
                      <div className="flex flex-wrap gap-2">
                        {practice.tags.map((tag, i) => (
                          <Badge key={i} variant="outline" className="text-xs">{tag}</Badge>
                        ))}
                      </div>
                      <div className="flex items-center justify-between pt-2 border-t">
                        <Badge variant="success">{Math.round(practice.success_rate * 100)}% success</Badge>
                        <Badge variant="outline">{practice.usage_count} uses</Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}