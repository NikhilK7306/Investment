"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Progress } from "@/components/ui/progress";
import { Brain, TrendingUp, TrendingDown, CheckCircle, AlertTriangle, Target, Shield, BarChart2, FileText, Sparkles, Zap, Activity, RefreshCw } from "lucide-react";
import { analysisService } from "@/services/analysisService";
import type { JobResponse, JobStatsResponse } from "@/types/analysis";

export default function AnalysisPage() {
  const router = useRouter();
  const [analyses, setAnalyses] = useState<AnalysisEntry[]>([]);
  const [runningJobs, setRunningJobs] = useState<JobResponse[]>([]);
  const [loading, setLoading] = useState(true);

  interface AnalysisEntry {
    symbol: string;
    name: string;
    date: string;
    score: number;
    recommendation: string;
    risk: string;
    status: string;
  }

  const fetchData = async () => {
    setLoading(true);
    try {
      const [pendingJobs] = await Promise.all([
        analysisService.getPendingJobs({ limit: 10 }),
      ]);
      setRunningJobs(pendingJobs.filter((j) => j.status === "RUNNING"));
      const completed = pendingJobs.filter((j) => j.status === "COMPLETED");
      setAnalyses(
        completed.map((j) => ({
          symbol: (j.payload?.symbol as string) || "N/A",
          name: (j.payload?.symbol as string) || "Unknown",
          date: j.completed_at ? new Date(j.completed_at).toLocaleDateString() : "N/A",
          score: (j.result?.overall_score as number) || 0,
          recommendation: (j.result?.recommendation as string) || "N/A",
          risk: (j.result?.risk_level as string) || "N/A",
          status: "COMPLETED",
        }))
      );
    } catch (err) {
      console.error("Failed to fetch analyses:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Analysis Center</h1>
            <p className="text-muted-foreground">View and manage IPO analyses</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
              {loading ? "Loading..." : "Refresh"}
            </Button>
            <Button onClick={() => router.push("/ipos")}>
              <Brain className="h-4 w-4 mr-2" />
              New Analysis
            </Button>
          </div>
        </div>

        <Tabs defaultValue="recent" className="space-y-4">
          <TabsList>
            <TabsTrigger value="recent">Recent Analyses</TabsTrigger>
            <TabsTrigger value="running">Running ({runningJobs.length})</TabsTrigger>
            <TabsTrigger value="templates">Templates</TabsTrigger>
          </TabsList>

          <TabsContent value="recent" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle>Completed Analyses</CardTitle>
                <Button variant="outline" size="sm">Export CSV</Button>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Company</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead>Score</TableHead>
                        <TableHead>Recommendation</TableHead>
                        <TableHead>Risk</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="w-48">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {loading && (
                        <TableRow>
                          <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                            Loading analyses...
                          </TableCell>
                        </TableRow>
                      )}
                      {!loading && analyses.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                            No completed analyses yet.
                          </TableCell>
                        </TableRow>
                      )}
                      {analyses.map((analysis, index) => (
                        <TableRow key={index} className="hover:bg-accent/50 cursor-pointer">
                          <TableCell>
                            <Link href={`/analysis/${analysis.symbol}`}>
                              <div>
                                <p className="font-medium">{analysis.symbol}</p>
                                <p className="text-sm text-muted-foreground">{analysis.name}</p>
                              </div>
                            </Link>
                          </TableCell>
                          <TableCell>{analysis.date}</TableCell>
                          <TableCell>
                            <span className={cn(
                              "font-bold px-2 py-1 rounded text-sm",
                              analysis.score >= 80 ? "bg-green-100 text-green-700" :
                              analysis.score >= 70 ? "bg-blue-100 text-blue-700" :
                              analysis.score >= 60 ? "bg-yellow-100 text-yellow-700" :
                              "bg-red-100 text-red-700"
                            )}>
                              {analysis.score}
                            </span>
                          </TableCell>
                          <TableCell>
                            <Badge variant={analysis.recommendation === "BUY" || analysis.recommendation === "AGGRESSIVE_BUY" ? "success" :
                              analysis.recommendation === "ACCUMULATE" ? "default" :
                              analysis.recommendation === "WATCH" ? "secondary" : "outline"}>
                              {analysis.recommendation}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant={analysis.risk === "LOW" ? "success" :
                              analysis.risk === "MODERATE" ? "default" : "destructive"}>
                              {analysis.risk}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant="success">{analysis.status}</Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Link href={`/analysis/${analysis.symbol}`}>
                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                  <FileText className="h-4 w-4" />
                                </Button>
                              </Link>
                              <Link href={`/reports/${analysis.symbol}`}>
                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                  <FileText className="h-4 w-4" />
                                </Button>
                              </Link>
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

          <TabsContent value="running" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Running Analyses</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {runningJobs.length === 0 && (
                    <p className="text-muted-foreground text-sm py-4">No running analyses.</p>
                  )}
                  {runningJobs.map((job) => (
                    <div key={job.id} className="p-4 rounded-lg border">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <Brain className="h-5 w-5 text-primary" />
                          <div>
                            <p className="font-medium">{(job.payload?.symbol as string) || "N/A"}</p>
                            <p className="text-sm text-muted-foreground">{job.job_type} Analysis</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-sm text-muted-foreground">
                            Started: {job.started_at ? new Date(job.started_at).toLocaleTimeString() : "N/A"}
                          </span>
                        </div>
                      </div>
                      <Progress value={50} className="h-2" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="templates" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[
                { name: "Standard IPO Analysis", agents: 8, duration: "~8 min", description: "Full analysis pipeline for standard IPOs" },
                { name: "Quick Screen", agents: 4, duration: "~3 min", description: "Rapid screening for initial evaluation" },
                { name: "Deep Dive", agents: 10, duration: "~15 min", description: "Comprehensive analysis with extended research" },
                { name: "Sector Focus", agents: 6, duration: "~6 min", description: "Sector-specific analysis template" },
                { name: "Risk Assessment", agents: 5, duration: "~5 min", description: "Focused risk analysis template" },
                { name: "Sentiment Deep Dive", agents: 4, duration: "~4 min", description: "Extended sentiment and alternative data" },
              ].map((template, i) => (
                <Card key={i} className="hover:border-primary/50 transition-colors">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Zap className="h-5 w-5 text-yellow-500" />
                      {template.name}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="text-sm text-muted-foreground">{template.description}</p>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>{template.agents} agents</span>
                      <span>{template.duration}</span>
                    </div>
                    <Button className="w-full" onClick={() => router.push("/ipos")}>
                      Run Template
                    </Button>
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
