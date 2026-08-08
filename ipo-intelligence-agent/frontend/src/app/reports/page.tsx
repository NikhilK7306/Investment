"use client";

import { use, useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Brain, FileText, ExternalLink, AlertCircle } from "lucide-react";
import Link from "next/link";
import { analysisService } from "@/services/analysisService";
import type { AnalysisResponse, ReportData } from "@/types/analysis";

export default function ReportsPage() {
  const [reports, setReports] = useState<AnalysisResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await analysisService.listReports(50);
      setReports(data);
    } catch (err) {
      console.error("Failed to load reports:", err);
      setError("Failed to load reports. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getReportData = (r: AnalysisResponse): ReportData | undefined =>
    r.agent_results?.report as ReportData | undefined;

  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Investment Reports</h1>
            <p className="text-muted-foreground">View and manage generated investment research reports</p>
          </div>
        </div>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle>Completed Reports ({reports.length})</CardTitle>
            <Button variant="outline" onClick={load} disabled={loading}>
              <Brain className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-muted-foreground">Loading reports...</p>
            ) : error ? (
              <div className="flex items-center gap-2 text-sm text-destructive">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            ) : reports.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium">No reports generated yet</h3>
                <p className="text-sm text-muted-foreground">
                  Run an analysis on an IPO, then generate its research report.
                </p>
                <Link href="/analysis">
                  <Button className="mt-4">
                    <Brain className="h-4 w-4 mr-2" />
                    Go to Analysis
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Company</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Score</TableHead>
                      <TableHead>Recommendation</TableHead>
                      <TableHead className="w-20">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {reports.map((report, index) => {
                      const reportData = getReportData(report);
                      const score = report.overall_score ?? reportData?.key_metrics?.overall_score ?? 0;
                      const recommendation = report.recommendation ?? reportData?.key_metrics?.recommendation ?? "N/A";
                      const date = reportData?.created_at ? new Date(reportData.created_at).toLocaleDateString() : "N/A";
                      return (
                        <TableRow key={index} className="hover:bg-accent/50 cursor-pointer">
                          <TableCell>
                            <Link href={`/reports/${report.symbol}`}>
                              <div>
                                <p className="font-medium">{report.symbol}</p>
                                <p className="text-sm text-muted-foreground">{reportData?.title ?? "Investment Research Report"}</p>
                              </div>
                            </Link>
                          </TableCell>
                          <TableCell>{date}</TableCell>
                          <TableCell>
                            <span className={cn(
                              "font-bold px-2 py-1 rounded text-sm",
                              score >= 80 ? "bg-green-100 text-green-700" :
                              score >= 70 ? "bg-blue-100 text-blue-700" :
                              score >= 60 ? "bg-yellow-100 text-yellow-700" :
                              "bg-red-100 text-red-700"
                            )}>
                              {typeof score === "number" ? score.toFixed(1) : score}
                            </span>
                          </TableCell>
                          <TableCell>
                            <Badge variant={["BUY", "AGGRESSIVE_BUY"].includes(recommendation.toUpperCase()) ? "success" :
                              recommendation.toUpperCase() === "ACCUMULATE" ? "default" :
                              ["WATCH", "HOLD"].includes(recommendation.toUpperCase()) ? "secondary" : "outline"}>
                              {recommendation.toUpperCase()}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Link href={`/reports/${report.symbol}`}>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <ExternalLink className="h-4 w-4" />
                              </Button>
                            </Link>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
