"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Brain, Sparkles, BookOpen, Zap, BarChart2, Settings, History, AlertCircle, AlertTriangle } from "lucide-react";
import { memoryService } from "@/services/memoryService";
import type { MemoryEntry, FailureResponse, SuccessResponse, KnowledgeResponse, BestPracticeResponse, ReflectionItem } from "@/types/memory";

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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
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
        ] = await Promise.all([
          memoryService.getReflections(),
          memoryService.getRecent({ memory_type: "short_term" }),
          memoryService.getRecent({ memory_type: "long_term" }),
          memoryService.getFailures(),
          memoryService.getUnresolvedFailures(),
          memoryService.getSuccesses(),
          memoryService.getKnowledge(),
          memoryService.getBestPractices(),
        ]);
        setReflections(reflectionsData);
        setShortTermEntries(shortTermData);
        setLongTermEntries(longTermData);
        setFailures(failuresData);
        setUnresolvedFailures(unresolvedData);
        setSuccesses(successesData);
        setKnowledgeEntries(knowledgeData);
        setBestPractices(practicesData);
      } catch (error) {
        console.error("Failed to load memory data", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const avgSuccessRate = successes.length > 0
    ? Math.round((successes.reduce((sum, s) => sum + s.success_rate, 0) / successes.length) * 100)
    : 0;

  const distributionData = [
    { name: "Short-term", value: shortTermEntries.length, color: "blue" },
    { name: "Long-term", value: longTermEntries.length, color: "green" },
    { name: "Vector", value: 45231, color: "purple" },
    { name: "Failure", value: failures.length, color: "red" },
    { name: "Success", value: successes.length, color: "green" },
    { name: "Knowledge", value: knowledgeEntries.length, color: "blue" },
    { name: "Best Practice", value: bestPractices.length, color: "yellow" },
    { name: "Reflection", value: reflections.length, color: "orange" },
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
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/memory/consolidate")}><Zap className="h-4 w-4 mr-2" />Run Consolidation</Button>
            <Button onClick={() => router.push("/memory/optimize")}><Brain className="h-4 w-4 mr-2" />Optimize</Button>
          </div>
        </div>

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
              <CardTitle className="text-sm font-medium">Vector Store</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">45,231</div>
              <p className="text-xs text-muted-foreground">Embeddings</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Hit Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-500">87%</div>
              <p className="text-xs text-muted-foreground">Cache efficiency</p>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="short-term">Short-term</TabsTrigger>
            <TabsTrigger value="long-term">Long-term</TabsTrigger>
            <TabsTrigger value="vector">Vector Store</TabsTrigger>
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
                      <div className="flex items-center gap-2">
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
                <p className="text-muted-foreground mb-4">Active session context and temporary analysis data (TTL: 24 hours)</p>
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
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {shortTermEntries.map((item, i) => (
                        <TableRow key={item.id || i}>
                          <TableCell className="font-mono text-sm">{item.id}</TableCell>
                          <TableCell><Badge variant="secondary">{item.memory_type}</Badge></TableCell>
                          <TableCell>{(JSON.stringify(item.content).length / 1024).toFixed(1)} KB</TableCell>
                          <TableCell>{item.created_at}</TableCell>
                          <TableCell>{item.ttl_days ? new Date(new Date(item.created_at).getTime() + item.ttl_days * 86400000).toISOString().split("T")[0] : "N/A"}</TableCell>
                          <TableCell className="font-mono">{item.access_count}</TableCell>
                          <TableCell><Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => router.push(`/memory/short-term/${item.id}`)}><AlertCircle className="h-4 w-4" /></Button></TableCell>
                        </TableRow>
                      ))}
                      {shortTermEntries.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={7} className="text-center text-muted-foreground">No short-term memory entries</TableCell>
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
                <p className="text-muted-foreground mb-4">Persisted analyses and learned knowledge (Retention: 365 days)</p>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Key</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Created</TableHead>
                        <TableHead>Access Count</TableHead>
                        <TableHead>Last Accessed</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {longTermEntries.map((item, i) => (
                        <TableRow key={item.id || i}>
                          <TableCell className="font-mono text-sm">{item.id}</TableCell>
                          <TableCell><Badge variant="secondary">{item.memory_type}</Badge></TableCell>
                          <TableCell>{item.created_at}</TableCell>
                          <TableCell className="font-mono">{item.access_count}</TableCell>
                          <TableCell>{item.last_accessed || "N/A"}</TableCell>
                          <TableCell><Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => router.push(`/memory/long-term/${item.id}`)}><AlertCircle className="h-4 w-4" /></Button></TableCell>
                        </TableRow>
                      ))}
                      {longTermEntries.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={6} className="text-center text-muted-foreground">No long-term memory entries</TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="vector" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Vector Store (pgvector)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-4">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Total Vectors</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold">45,231</div>
                      <p className="text-xs text-muted-foreground">Total embeddings stored</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Dimensions</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold">1024</div>
                      <p className="text-xs text-muted-foreground">BAAI/bge-m3 model</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Index Size</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold">2.4 GB</div>
                      <p className="text-xs text-muted-foreground">HNSW index</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Avg Query Time</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-green-500">12ms</div>
                      <p className="text-xs text-muted-foreground">ANN search</p>
                    </CardContent>
                  </Card>
                </div>

                <Card className="mt-4">
                  <CardHeader>
                    <CardTitle>Collections</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Collection</TableHead>
                            <TableHead>Vectors</TableHead>
                            <TableHead>Dimensions</TableHead>
                            <TableHead>Index Type</TableHead>
                            <TableHead>Size</TableHead>
                            <TableHead>Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {[
                            { name: "ipo_analyses", vectors: 12450, dim: 1024, index: "HNSW", size: "850 MB" },
                            { name: "company_profiles", vectors: 8920, dim: 1024, index: "HNSW", size: "620 MB" },
                            { name: "knowledge_base", vectors: 12340, dim: 1024, index: "HNSW", size: "580 MB" },
                            { name: "best_practices", vectors: 18, dim: 1024, index: "FLAT", size: "2 MB" },
                            { name: "failure_patterns", vectors: 127, dim: 1024, index: "HNSW", size: "15 MB" },
                            { name: "success_patterns", vectors: 24, dim: 1024, index: "FLAT", size: "1 MB" },
                          ].map((item, i) => (
                            <TableRow key={i}>
                              <TableCell className="font-medium">{item.name}</TableCell>
                              <TableCell className="font-mono">{item.vectors.toLocaleString()}</TableCell>
                              <TableCell>{item.dim}</TableCell>
                              <TableCell><Badge variant="secondary">{item.index}</Badge></TableCell>
                              <TableCell>{item.size}</TableCell>
                              <TableCell><Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => router.push(`/memory/vector/${item.name}`)}><AlertCircle className="h-4 w-4" /></Button></TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </CardContent>
                </Card>
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
                        <TableHead>Prediction</TableHead>
                        <TableHead>Outcome</TableHead>
                        <TableHead>Accuracy</TableHead>
                        <TableHead>Learning</TableHead>
                        <TableHead>Created</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {successes.map((item, i) => {
                        const accuracy = item.success_rate;
                        const prediction = item.confidence ? `Confidence: ${Math.round(item.confidence * 100)}%` : "N/A";
                        const outcome = accuracy ? `${Math.round(accuracy * 100)}% rate` : "N/A";
                        return (
                          <TableRow key={item.success_id || i}>
                            <TableCell className="font-mono font-medium">{item.ipo_symbol || "N/A"}</TableCell>
                            <TableCell className="max-w-[200px] truncate">{item.strategy_description}</TableCell>
                            <TableCell>{prediction}</TableCell>
                            <TableCell>{outcome}</TableCell>
                            <TableCell>
                              <Badge variant={accuracy > 0.8 ? "success" : accuracy > 0.5 ? "default" : "destructive"}>
                                {Math.round(accuracy * 100)}%
                              </Badge>
                            </TableCell>
                            <TableCell className="max-w-[200px] truncate">{item.strategy_description}</TableCell>
                            <TableCell>{"N/A"}</TableCell>
                          </TableRow>
                        );
                      })}
                      {successes.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={7} className="text-center text-muted-foreground">No experience memory entries</TableCell>
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
                          <TableCell className="max-w-[200px] truncate">{item.mistakes_identified.join(", ")}</TableCell>
                          <TableCell className="max-w-[200px] truncate">{item.lessons_extracted?.join(", ") || "N/A"}</TableCell>
                          <TableCell>{item.created_at?.split("T")[0]}</TableCell>
                        </TableRow>
                      ))}
                      {reflections.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={8} className="text-center text-muted-foreground">No reflection entries</TableCell>
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
                <div className="grid gap-4 md:grid-cols-4">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Expired Short-term</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-red-500">42</div>
                      <p className="text-xs text-muted-foreground">Ready for cleanup</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Old Long-term</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-yellow-500">15</div>
                      <p className="text-xs text-muted-foreground">Older than 365 days</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Orphaned Vectors</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-orange-500">8</div>
                      <p className="text-xs text-muted-foreground">No references</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Duplicate Vectors</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-blue-500">3</div>
                      <p className="text-xs text-muted-foreground">Near-duplicates</p>
                    </CardContent>
                  </Card>
                </div>

                <div className="border-t pt-4">
                  <Button variant="destructive" onClick={() => router.push("/memory/cleanup/expired")}><AlertTriangle className="h-4 w-4 mr-2" />Cleanup Expired Short-term</Button>
                  <Button variant="outline" className="ml-2" onClick={() => router.push("/memory/cleanup/archive")}><AlertTriangle className="h-4 w-4 mr-2" />Archive Old Long-term</Button>
                  <Button variant="outline" className="ml-2" onClick={() => router.push("/memory/cleanup/deduplicate")}><Zap className="h-4 w-4 mr-2" />Deduplicate Vectors</Button>
                  <Button variant="outline" className="ml-2" onClick={() => router.push("/memory/cleanup/optimize")}><Zap className="h-4 w-4 mr-2" />Optimize Index</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
