"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Brain, Zap, BarChart2, AlertTriangle } from "lucide-react";
import { memoryService } from "@/services/memoryService";
import type { MemoryEntry, FailureResponse, SuccessResponse, KnowledgeResponse, BestPracticeResponse, ReflectionItem, LessonResponse } from "@/types/memory";

export default function MemoryPage() {
  const router = useRouter();
  const [reflections, setReflections] = useState<ReflectionItem[]>([]);
  const [shortTermEntries, setShortTermEntries] = useState<MemoryEntry[]>([]);
  const [longTermEntries, setLongTermEntries] = useState<MemoryEntry[]>([]);
  const [failures, setFailures] = useState<FailureResponse[]>([]);
  const [unresolvedFailures, setUnresolvedFailures] = useState<FailureResponse[]>([]);
  const [successes, setSuccesses] = useState<SuccessResponse[]>([]);
  const [knowledgeEntries, setKnowledgeEntries] = useState<KnowledgeResponse[]>([]);
  const [bestPractices, setBestPractices] = useState<BestPracticeResponse[]>([]);
  const [lessons, setLessons] = useState<LessonResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [
        reflectionsData,
        shortTermData,
        longTermData,
        failuresData,
        unresolvedData,
        successesData,
        knowledgeData,
        practicesData,
        lessonsData,
      ] = await Promise.all([
        memoryService.getReflections(),
        memoryService.getRecent({ memory_type: "short_term" }),
        memoryService.getRecent({ memory_type: "long_term" }),
        memoryService.getFailures(),
        memoryService.getUnresolvedFailures(),
        memoryService.getSuccesses(),
        memoryService.getKnowledge(),
        memoryService.getBestPractices(),
        memoryService.getLessons(),
      ]);
      setReflections(reflectionsData);
      setShortTermEntries(shortTermData);
      setLongTermEntries(longTermData);
      setFailures(failuresData);
      setUnresolvedFailures(unresolvedData);
      setSuccesses(successesData);
      setKnowledgeEntries(knowledgeData);
      setBestPractices(practicesData);
      setLessons(lessonsData);
    } catch (err) {
      console.error("Failed to load memory data", err);
      setError("Failed to load memory data. Please retry.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const avgSuccessRate = successes.length > 0
    ? Math.round((successes.reduce((sum, s) => sum + s.success_rate, 0) / successes.length) * 100)
    : 0;

  const totalEntries = shortTermEntries.length + longTermEntries.length + reflections.length + lessons.length + failures.length + successes.length + knowledgeEntries.length + bestPractices.length;

  const distributionData = [
    { name: "Short-term", value: shortTermEntries.length, color: "blue" },
    { name: "Long-term", value: longTermEntries.length, color: "green" },
    { name: "Failure", value: failures.length, color: "red" },
    { name: "Success", value: successes.length, color: "green" },
    { name: "Knowledge", value: knowledgeEntries.length, color: "blue" },
    { name: "Best Practice", value: bestPractices.length, color: "yellow" },
    { name: "Reflection", value: reflections.length, color: "orange" },
    { name: "Lesson", value: lessons.length, color: "purple" },
  ];

  const maxDistValue = Math.max(...distributionData.map((d) => d.value), 1);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <p className="text-muted-foreground">Loading memory data...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Memory Management</h1>
            <p className="text-muted-foreground">
              Manage and monitor all memory systems across the agent pipeline
            </p>
          </div>
          <Button variant="outline" onClick={fetchData}><BarChart3 className="h-4 w-4 mr-2" />Refresh</Button>
        </div>

        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="p-4 text-sm text-red-700 flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />{error}
            </CardContent>
          </Card>
        )}

        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Short-term</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{shortTermEntries.length.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">Active entries</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Long-term</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{longTermEntries.length.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">Stored analyses</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Memory</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalEntries.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">Across all stores</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Unresolved Failures</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-500">{unresolvedFailures.length.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">Recording errors</p>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="short-term">Short-term</TabsTrigger>
            <TabsTrigger value="long-term">Long-term</TabsTrigger>
            <TabsTrigger value="experience">Experience</TabsTrigger>
            <TabsTrigger value="reflection">Reflection</TabsTrigger>
            <TabsTrigger value="cleanup">Cleanup</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Failure Memory</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-red-500">{failures.length}</div>
                  <p className="text-xs text-muted-foreground">{unresolvedFailures.length} unresolved</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Success Memory</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-500">{successes.length}</div>
                  <p className="text-xs text-muted-foreground">{avgSuccessRate}% avg success rate</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Knowledge Base</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{knowledgeEntries.length}</div>
                  <p className="text-xs text-muted-foreground">Concepts stored</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Best Practices</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{bestPractices.length}</div>
                  <p className="text-xs text-muted-foreground">Active practices</p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Memory Type Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {distributionData.map((item) => (
                    <div key={item.name} className="flex items-center justify-between">
                      <span className="text-sm">{item.name}</span>
                      <div className="flex items-center gap-2 flex-1 justify-end">
                        <div className={`w-32 h-2 bg-${item.color}-500/20 rounded-full overflow-hidden`}>
                          <div className={`h-full bg-${item.color}-500 rounded-full`} style={{ width: `${Math.min(100, (item.value / maxDistValue) * 100)}%` }} />
                        </div>
                        <span className="text-sm font-mono w-16 text-right">{item.value.toLocaleString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="short-term" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Short-term Memory</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">Active session context and temporary analysis data</p>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Key</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Size</TableHead>
                        <TableHead>Created</TableHead>
                        <TableHead>Expires</TableHead>
                        <TableHead>Access Count</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {shortTermEntries.map((item, i) => (
                        <TableRow key={item.id || i}>
                          <TableCell className="font-mono text-sm">{item.id}</TableCell>
                          <TableCell><Badge variant="secondary">{item.memory_type}</Badge></TableCell>
                          <TableCell>{(JSON.stringify(item.content).length / 1024).toFixed(1)} KB</TableCell>
                          <TableCell>{item.created_at && new Date(item.created_at).toLocaleString()}</TableCell>
                          <TableCell>{item.ttl_days ? new Date(new Date(item.created_at).getTime() + item.ttl_days * 86400000).toISOString().split("T")[0] : "N/A"}</TableCell>
                          <TableCell className="font-mono">{item.access_count}</TableCell>
                        </TableRow>
                      ))}
                      {shortTermEntries.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                            No short-term memory entries recorded yet.
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="long-term" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Long-term Memory</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">Persisted analyses and learned knowledge</p>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Key</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Created</TableHead>
                        <TableHead>Access Count</TableHead>
                        <TableHead>Last Accessed</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {longTermEntries.map((item, i) => (
                        <TableRow key={item.id || i}>
                          <TableCell className="font-mono text-sm">{item.id}</TableCell>
                          <TableCell><Badge variant="secondary">{item.memory_type}</Badge></TableCell>
                          <TableCell>{item.created_at && new Date(item.created_at).toLocaleString()}</TableCell>
                          <TableCell className="font-mono">{item.access_count}</TableCell>
                          <TableCell>{item.last_accessed ? new Date(item.last_accessed).toLocaleString() : "N/A"}</TableCell>
                        </TableRow>
                      ))}
                      {longTermEntries.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                            No long-term memory entries recorded yet.
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="experience" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Experience Memory</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">Past analyses linked to actual outcomes for learning</p>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>IPO</TableHead>
                        <TableHead>Situation</TableHead>
                        <TableHead>Success Rate</TableHead>
                        <TableHead>Reuses</TableHead>
                        <TableHead>Created</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {successes.map((item, i) => (
                        <TableRow key={item.success_id || i}>
                          <TableCell className="font-mono font-medium">{item.ipo_symbol || "N/A"}</TableCell>
                          <TableCell className="max-w-[300px] truncate">{item.strategy_description}</TableCell>
                          <TableCell>
                            <Badge variant={item.success_rate > 0.8 ? "success" : item.success_rate > 0.5 ? "default" : "destructive"}>
                              {Math.round(item.success_rate * 100)}%
                            </Badge>
                          </TableCell>
                          <TableCell>{item.reuse_count}</TableCell>
                          <TableCell>{item.success_id ? "N/A" : "N/A"}</TableCell>
                        </TableRow>
                      ))}
                      {successes.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                            No experience memory entries recorded yet.
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="reflection" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Reflection Memory</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">Lessons extracted from prediction vs reality comparisons</p>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>IPO</TableHead>
                        <TableHead>Prediction Type</TableHead>
                        <TableHead>Predicted</TableHead>
                        <TableHead>Actual</TableHead>
                        <TableHead>Accuracy</TableHead>
                        <TableHead>Mistakes</TableHead>
                        <TableHead>Lessons</TableHead>
                        <TableHead>Created</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {reflections.map((item, i) => (
                        <TableRow key={item.prediction_id || i}>
                          <TableCell className="font-mono font-medium">{item.ipo_symbol}</TableCell>
                          <TableCell><Badge variant="secondary">{item.prediction_type}</Badge></TableCell>
                          <TableCell>{item.predicted_value > 0 ? "+" : ""}{Math.round(item.predicted_value * 100)}%</TableCell>
                          <TableCell>{item.actual_value > 0 ? "+" : ""}{Math.round(item.actual_value * 100)}%</TableCell>
                          <TableCell>
                            <Badge variant={item.accuracy > 0.7 ? "success" : item.accuracy > 0.5 ? "default" : "destructive"}>
                              {Math.round(item.accuracy * 100)}%
                            </Badge>
                          </TableCell>
                          <TableCell className="max-w-[200px] truncate">{item.mistakes_identified.join(", ") || "N/A"}</TableCell>
                          <TableCell className="max-w-[200px] truncate">{item.lessons_extracted?.join(", ") || "N/A"}</TableCell>
                          <TableCell>{item.created_at?.split("T")[0]}</TableCell>
                        </TableRow>
                      ))}
                      {reflections.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={8} className="text-center text-muted-foreground py-8">
                            No reflection entries recorded yet.
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="cleanup" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Memory Cleanup</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Cleanup runs automatically on a schedule. Pending counts are reported by the memory service.
                </p>
                <div className="grid gap-4 md:grid-cols-4">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Expired Short-term</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold">{shortTermEntries.length}</div>
                      <p className="text-xs text-muted-foreground">Current entries</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Failures</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold">{failures.length}</div>
                      <p className="text-xs text-muted-foreground">Recorded failures</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Lessons</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold">{lessons.length}</div>
                      <p className="text-xs text-muted-foreground">Extracted lessons</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Reflections</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold">{reflections.length}</div>
                      <p className="text-xs text-muted-foreground">Unverified learnings</p>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}