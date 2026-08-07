"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { AlertTriangle, Search, CheckCircle as CheckCircleIcon, AlertCircle as AlertCircleIcon, Clock, Filter, Zap } from "lucide-react";
import { memoryService } from "@/services/memoryService";
import type { FailureResponse } from "@/types/memory";

export default function FailuresPage() {
  const router = useRouter();
  const [failures, setFailures] = useState<FailureResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFailures();
  }, []);

  async function loadFailures() {
    try {
      setLoading(true);
      const data = await memoryService.getFailures();
      setFailures(data);
    } catch (err) {
      console.error("Failed to load failures:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleResolve(failureId: string) {
    try {
      await memoryService.resolveFailure(failureId);
      setFailures(prev => prev.map(f => f.failure_id === failureId ? { ...f, resolved: true } : f));
    } catch (err) {
      console.error("Failed to resolve failure:", err);
    }
  }

  const unresolvedFailures = failures.filter(f => !f.resolved);
  const resolvedCount = failures.filter(f => f.resolved).length;
  const categoryCount = new Set(failures.map(f => f.category)).size;
  const recurrenceRate = failures.length > 0 ? Math.round((failures.filter(f => f.occurrences > 1).length / failures.length) * 100) : 0;

  function getTopAgent(): { name: string; count: number } {
    const counts: Record<string, number> = {};
    failures.forEach(f => {
      counts[f.agent_name] = (counts[f.agent_name] || 0) + 1;
    });
    let top = { name: "N/A", count: 0 };
    for (const [name, count] of Object.entries(counts)) {
      if (count > top.count) top = { name, count };
    }
    return top;
  }

  function getTopCategory(): { name: string; count: number } {
    const counts: Record<string, number> = {};
    failures.forEach(f => {
      counts[f.category] = (counts[f.category] || 0) + 1;
    });
    let top = { name: "N/A", count: 0 };
    for (const [name, count] of Object.entries(counts)) {
      if (count > top.count) top = { name, count };
    }
    return top;
  }

  function getCategories(): { name: string; count: number; resolved: number; color: string }[] {
    const counts: Record<string, { total: number; resolved: number }> = {};
    failures.forEach(f => {
      if (!counts[f.category]) counts[f.category] = { total: 0, resolved: 0 };
      counts[f.category].total++;
      if (f.resolved) counts[f.category].resolved++;
    });
    return Object.entries(counts).map(([name, data]) => ({
      name,
      count: data.total,
      resolved: data.resolved,
      color: data.total > 10 ? "red" : data.total > 5 ? "orange" : "yellow",
    }));
  }

  const topAgent = getTopAgent();
  const topCategory = getTopCategory();
  const categories = getCategories();

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <p className="text-muted-foreground">Loading failures...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Failure Memory</h1>
            <p className="text-muted-foreground">Track, analyze, and learn from agent failures to prevent recurrence</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/failures")}><AlertTriangle className="h-4 w-4 mr-2" />Run Cleanup</Button>
            <Button onClick={() => router.push("/failures/record")}><AlertCircleIcon className="h-4 w-4 mr-2" />Record Failure</Button>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Failures</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{failures.length}</div>
              <p className="text-xs text-muted-foreground">+{unresolvedFailures.length} unresolved</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Unresolved</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-500">{unresolvedFailures.length}</div>
              <p className="text-xs text-muted-foreground">Need attention</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Resolved</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-500">{resolvedCount}</div>
              <p className="text-xs text-muted-foreground">{failures.length > 0 ? Math.round(resolvedCount / failures.length * 100) : 0}% resolved</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Categories</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{categoryCount}</div>
              <p className="text-xs text-muted-foreground">Categories tracked</p>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="list" className="space-y-4">
          <TabsList>
            <TabsTrigger value="list">All Failures ({failures.length})</TabsTrigger>
            <TabsTrigger value="unresolved">Unresolved ({unresolvedFailures.length})</TabsTrigger>
            <TabsTrigger value="categories">By Category</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          <TabsContent value="list" className="space-y-4">
            <div className="flex gap-4 mb-4">
              <Input placeholder="Search failures..." className="w-80" />
              <Select defaultValue="all">
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="All Agents" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Agents</SelectItem>
                  <SelectItem value="Fundamental">Fundamental</SelectItem>
                  <SelectItem value="Market">Market</SelectItem>
                  <SelectItem value="Risk">Risk</SelectItem>
                  <SelectItem value="Sentiment">Sentiment</SelectItem>
                  <SelectItem value="Decision">Decision</SelectItem>
                </SelectContent>
              </Select>
              <Select defaultValue="all">
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  <SelectItem value="Parsing Failure">Parsing Failure</SelectItem>
                  <SelectItem value="Rate Limit">Rate Limit</SelectItem>
                  <SelectItem value="Calculation">Calculation</SelectItem>
                  <SelectItem value="Missing Data">Missing Data</SelectItem>
                  <SelectItem value="Model Error">Model Error</SelectItem>
                </SelectContent>
              </Select>
              <Select defaultValue="all">
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="All Severity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Severity</SelectItem>
                  <SelectItem value="Critical">Critical</SelectItem>
                  <SelectItem value="High">High</SelectItem>
                  <SelectItem value="Medium">Medium</SelectItem>
                  <SelectItem value="Low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-10">ID</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead>Agent</TableHead>
                        <TableHead>Category</TableHead>
                        <TableHead>Error</TableHead>
                        <TableHead className="max-w-[200px]">Message</TableHead>
                        <TableHead>Severity</TableHead>
                        <TableHead>Resolved</TableHead>
                        <TableHead>Occurrences</TableHead>
                        <TableHead className="w-24">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {failures.map((failure) => (
                        <TableRow key={failure.failure_id} className="hover:bg-accent/50 cursor-pointer" onClick={() => router.push(`/failures/${failure.failure_id}`)}>
                          <TableCell className="font-mono text-sm">{failure.failure_id}</TableCell>
                          <TableCell>{failure.last_occurrence?.split("T")[0]}</TableCell>
                          <TableCell><Badge variant="secondary">{failure.agent_name}</Badge></TableCell>
                          <TableCell><Badge variant="outline">{failure.category}</Badge></TableCell>
                          <TableCell className="font-medium">{failure.error_type}</TableCell>
                          <TableCell className="max-w-[200px] truncate text-muted-foreground">{failure.error_message}</TableCell>
                          <TableCell>
                            <Badge variant={failure.severity === "High" ? "destructive" : failure.severity === "Medium" ? "default" : "secondary"}>
                              {failure.severity}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {failure.resolved ? (
                              <Badge variant="success"><CheckCircleIcon className="h-3 w-3 mr-1" />Resolved</Badge>
                            ) : (
                              <Badge variant="destructive"><AlertCircleIcon className="h-3 w-3 mr-1" />Open</Badge>
                            )}
                          </TableCell>
                          <TableCell className="font-mono">{failure.occurrences}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={(e) => { e.stopPropagation(); router.push(`/failures/${failure.failure_id}`); }}><AlertTriangle className="h-4 w-4" /></Button>
                              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={(e) => { e.stopPropagation(); handleResolve(failure.failure_id); }}><CheckCircleIcon className="h-4 w-4" /></Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="unresolved" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Unresolved Failures</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {unresolvedFailures.map((failure) => (
                    <div key={failure.failure_id} className="p-4 border rounded-lg bg-red-50 border-red-200">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-mono font-medium">{failure.failure_id}</span>
                            <Badge variant="destructive">{failure.severity}</Badge>
                            <Badge variant="secondary">{failure.agent_name}</Badge>
                            <Badge variant="outline">{failure.category}</Badge>
                          </div>
                          <p className="font-medium">{failure.error_type}</p>
                          <p className="text-sm text-muted-foreground">{failure.error_message}</p>
                          <div className="mt-2 flex flex-wrap gap-2 text-sm">
                            <span className="text-muted-foreground">Root cause: </span>
                            <span className="font-mono text-red-600">{failure.root_cause}</span>
                          </div>
                          <div className="mt-1 flex flex-wrap gap-2 text-sm">
                            <span className="text-muted-foreground">Attempted fix: </span>
                            <span className="font-mono text-blue-600">{failure.attempted_fix || "None"}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button variant="default" size="sm" onClick={() => handleResolve(failure.failure_id)}><CheckCircleIcon className="h-4 w-4 mr-1" />Mark Resolved</Button>
                          <Button variant="outline" size="sm" onClick={() => router.push(`/failures/${failure.failure_id}/fix`)}><AlertTriangle className="h-4 w-4 mr-1" />Add Fix</Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="categories" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {categories.map((cat, i) => (
                <Card key={i}>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle>{cat.name}</CardTitle>
                    <Badge variant={cat.color === "red" ? "destructive" : cat.color === "orange" ? "secondary" : cat.color === "yellow" ? "warning" : "default"}>
                      {cat.count}
                    </Badge>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Resolved</span>
                      <span className="font-medium">{cat.resolved}/{cat.count}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Resolution Rate</span>
                      <span className="font-medium text-green-600">{cat.count > 0 ? Math.round(cat.resolved / cat.count * 100) : 0}%</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Avg Time to Resolve</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-green-500">2.3 days</div>
                  <p className="text-xs text-muted-foreground">Median resolution time</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Recurrence Rate</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-red-500">{recurrenceRate}%</div>
                  <p className="text-xs text-muted-foreground">Failures with {'>'}1 occurrence</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Top Agent</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{topAgent.name}</div>
                  <p className="text-xs text-muted-foreground">{topAgent.count} failures ({failures.length > 0 ? Math.round(topAgent.count / failures.length * 100) : 0}%)</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Top Category</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-red-500">{topCategory.name}</div>
                  <p className="text-xs text-muted-foreground">{topCategory.count} failures ({failures.length > 0 ? Math.round(topCategory.count / failures.length * 100) : 0}%)</p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Failure Trend (Last 30 Days)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {failures.length > 0 ? (
                    (() => {
                      const now = new Date();
                      const buckets: Record<string, number> = {};
                      const weekFormat = (d: Date) => {
                        const start = new Date(d);
                        start.setDate(start.getDate() - start.getDay());
                        return start.toISOString().split("T")[0];
                      };
                      failures.forEach(f => {
                        const d = new Date(f.last_occurrence);
                        const key = weekFormat(d);
                        buckets[key] = (buckets[key] || 0) + 1;
                      });
                      const sorted = Object.entries(buckets).sort(([a], [b]) => a.localeCompare(b)).slice(-5);
                      const maxCount = Math.max(...sorted.map(([, c]) => c), 1);
                      return sorted.map(([date, count], i) => (
                        <div key={i} className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className="w-24 text-sm text-muted-foreground">{date}</span>
                            <div className="w-48 bg-muted rounded-full h-2">
                              <div className={`h-2 rounded-full transition-all ${count > 2 ? 'bg-red-500' : count > 1 ? 'bg-yellow-500' : 'bg-green-500'}`} style={{ width: `${(count / maxCount) * 100}%` }} />
                            </div>
                          </div>
                          <span className="text-sm font-mono">{count} failures</span>
                        </div>
                      ));
                    })()
                  ) : (
                    <p className="text-sm text-muted-foreground">No failure data available</p>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Failure Patterns</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {failures.length > 0 ? (
                    (() => {
                      const patterns: Record<string, { count: number; agents: Set<string>; fixes: Set<string> }> = {};
                      failures.forEach(f => {
                        const key = `${f.error_type}: ${f.root_cause}`;
                        if (!patterns[key]) patterns[key] = { count: 0, agents: new Set(), fixes: new Set() };
                        patterns[key].count++;
                        patterns[key].agents.add(f.agent_name);
                        patterns[key].fixes.add(f.attempted_fix || "None");
                      });
                      return Object.entries(patterns).sort(([, a], [, b]) => b.count - a.count).slice(0, 8).map(([pattern, data], i) => (
                        <div key={i} className="p-3 border rounded-lg flex items-center justify-between">
                          <div className="flex-1">
                            <p className="font-medium">{pattern}</p>
                            <p className="text-sm text-muted-foreground">{data.count} occurrences · {Array.from(data.agents).join(", ")} agent</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary">{data.count}x</Badge>
                            <Badge variant="success">{Array.from(data.fixes)[0]}</Badge>
                          </div>
                        </div>
                      ));
                    })()
                  ) : (
                    <p className="text-sm text-muted-foreground">No failure patterns available</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
