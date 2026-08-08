"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { MetricCard } from "@/components/ui/metric-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Target,
  AlertTriangle,
  CheckCircle,
  Clock,
  Brain,
  BarChart2,
  FileText,
  RefreshCw,
} from "lucide-react";
import { ipoService } from "@/services/ipoService";
import { analysisService } from "@/services/analysisService";
import { memoryService } from "@/services/memoryService";
import type { IPOResponse } from "@/types/ipo";
import type { JobStatsResponse } from "@/types/analysis";

export default function DashboardPage() {
  const router = useRouter();
  const [ipos, setIpos] = useState<IPOResponse[]>([]);
  const [jobStats, setJobStats] = useState<JobStatsResponse | null>(null);
  const [memoryCounts, setMemoryCounts] = useState<{ failures: number; successes: number; lessons: number; reflections: number }>({ failures: 0, successes: 0, lessons: 0, reflections: 0 });
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [iposData, statsData, failures, successes, lessons, reflections] = await Promise.all([
        ipoService.listUpcoming({ limit: 5 }),
        analysisService.getJobStats(),
        memoryService.getFailures(),
        memoryService.getSuccesses(),
        memoryService.getLessons(),
        memoryService.getReflections(),
      ]);
      setIpos(iposData);
      setJobStats(statsData);
      setMemoryCounts({
        failures: failures.length,
        successes: successes.length,
        lessons: lessons.length,
        reflections: reflections.length,
      });
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const metrics = [
    {
      title: "Upcoming IPOs",
      value: String(ipos.length),
      change: `${ipos.length} tracked`,
      changeType: "positive" as const,
      icon: "calendar",
    },
    {
      title: "Active Analyses",
      value: String(jobStats?.total_running ?? 0),
      change: `${jobStats?.total_pending ?? 0} pending`,
      changeType: "positive" as const,
      icon: "bar-chart",
    },
    {
      title: "Total Completed",
      value: String(jobStats?.total_completed ?? 0),
      change: jobStats && jobStats.total_failed > 0 ? `${jobStats.total_failed} failed` : "0 failed",
      changeType: jobStats && jobStats.total_failed > 0 ? "negative" as const : "positive" as const,
      icon: "target",
    },
    {
      title: "Task Success Rate",
      value: jobStats && jobStats.total_completed + jobStats.total_failed > 0
        ? `${Math.round((jobStats.total_completed / (jobStats.total_completed + jobStats.total_failed)) * 100)}%`
        : "—",
      change: "completed jobs only",
      changeType: "neutral" as const,
      icon: "check-circle",
    },
  ];

  const agentStatusEntries = [
    { name: "Discovery", status: ipos.length > 0 ? "completed" as const : "idle" as const, lastRun: "via API" },
    { name: "Collection", status: "idle" as const, lastRun: "awaiting trigger" },
    { name: "Fundamental", status: jobStats?.total_running && jobStats.total_running > 0 ? "running" as const : "idle" as const, lastRun: jobStats ? `${jobStats.total_completed} completed` : "N/A" },
    { name: "Market", status: "idle" as const, lastRun: "N/A" },
    { name: "Risk", status: "idle" as const, lastRun: "N/A" },
    { name: "Sentiment", status: "idle" as const, lastRun: "N/A" },
    { name: "Decision", status: "idle" as const, lastRun: "N/A" },
    { name: "Report", status: "idle" as const, lastRun: "N/A" },
    { name: "Memory", status: "idle" as const, lastRun: "N/A" },
    { name: "Reflection", status: "idle" as const, lastRun: "N/A" },
  ];

  const systemStats = {
    totalIPOs: ipos.length,
    completedAnalyses: jobStats?.total_completed ?? 0,
    avgProcessingTime: "N/A",
    failures: memoryCounts.failures,
    successes: memoryCounts.successes,
    lessons: memoryCounts.lessons,
    reflections: memoryCounts.reflections,
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
            <p className="text-muted-foreground">
              Overview of your IPO intelligence pipeline
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
              {loading ? "Loading..." : "Refresh Data"}
            </Button>
            <Button size="sm" onClick={() => router.push("/analysis")}>
              <BarChart2 className="h-4 w-4 mr-2" />
              New Analysis
            </Button>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {metrics.map((metric, index) => (
            <MetricCard key={index} {...metric} />
          ))}
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-lg">Upcoming IPOs</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => router.push("/ipos")}>
                View All
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {ipos.length === 0 && !loading && (
                  <p className="text-muted-foreground text-sm">No upcoming IPOs found.</p>
                )}
                {ipos.map((ipo, index) => (
                  <div
                    key={ipo.symbol}
                    className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent transition-colors cursor-pointer"
                    onClick={() => router.push(`/ipos/${ipo.symbol}`)}
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-primary/10">
                        <Brain className="h-4 w-4 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium">{ipo.symbol}</p>
                        <p className="text-sm text-muted-foreground">{ipo.company_name}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge
                        variant={
                          ipo.status === "FILED" ? "default" : ipo.status === "PRICED" ? "success" : "outline"
                        }
                      >
                        {ipo.status}
                      </Badge>
                      {ipo.expected_date && (
                        <span className="text-sm text-muted-foreground">
                          {new Date(ipo.expected_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-lg">Agent Status</CardTitle>
              <Badge variant="success">All Healthy</Badge>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {agentStatusEntries.map((agent, index) => (
                  <div key={index} className="flex items-center justify-between text-sm">
                    <span className="capitalize">{agent.name}</span>
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          "w-2 h-2 rounded-full",
                          agent.status === "running" && "bg-blue-500 animate-pulse",
                          agent.status === "completed" && "bg-green-500",
                          agent.status === "idle" && "bg-gray-400",
                          agent.status === "error" && "bg-red-500"
                        )}
                      />
                      <span className="text-muted-foreground">{agent.lastRun}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-4 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-lg">System Statistics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Upcoming IPOs</span>
                <span className="font-bold text-2xl">{systemStats.totalIPOs.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Completed Analyses</span>
                <span className="font-bold text-2xl">{systemStats.completedAnalyses.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Failures</span>
                <span className="font-bold text-2xl">{systemStats.failures}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Successes</span>
                <span className="font-bold text-2xl">{systemStats.successes}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Lessons Learned</span>
                <span className="font-bold text-2xl">{systemStats.lessons}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Reflections</span>
                <span className="font-bold text-2xl">{systemStats.reflections}</span>
              </div>
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-lg">Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {ipos.length === 0 && !loading && (
                  <p className="text-muted-foreground text-sm">No recent activity.</p>
                )}
                {ipos.slice(0, 5).map((ipo, index) => (
                  <div key={index} className="flex items-center justify-between p-3 rounded-lg border">
                    <div className="flex items-center gap-3">
                      <div className="p-1.5 rounded bg-blue-100">
                        <FileText className="h-4 w-4 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">IPO discovered</p>
                        <p className="text-xs text-muted-foreground">{ipo.symbol} - {ipo.company_name}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {ipo.expected_date && (
                        <span className="text-xs text-muted-foreground">
                          {new Date(ipo.expected_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-lg">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-start" onClick={() => router.push("/ipos")}>
                <BarChart2 className="h-4 w-4 mr-2" />
                Analyze New IPO
              </Button>
              <Button variant="outline" className="w-full justify-start" onClick={() => router.push("/reflection")}>
                <Brain className="h-4 w-4 mr-2" />
                Run Reflection Cycle
              </Button>
              <Button variant="outline" className="w-full justify-start" onClick={() => router.push("/reports")}>
                <FileText className="h-4 w-4 mr-2" />
                Generate Report
              </Button>
              <Button variant="outline" className="w-full justify-start" onClick={() => router.push("/analysis")}>
                <Target className="h-4 w-4 mr-2" />
                View Predictions
              </Button>
              <Button variant="outline" className="w-full justify-start" onClick={() => router.push("/failures")}>
                <AlertTriangle className="h-4 w-4 mr-2" />
                Review Failures
              </Button>
              <Button variant="outline" className="w-full justify-start" onClick={() => router.push("/successes")}>
                <CheckCircle className="h-4 w-4 mr-2" />
                Review Successes
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
