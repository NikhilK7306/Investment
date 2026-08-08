"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Brain, FileText, ArrowLeft, AlertCircle } from "lucide-react";
import { analysisService } from "@/services/analysisService";
import type { ReportData } from "@/types/analysis";

export default function ReportDetailPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol: rawSymbol } = use(params);
  const symbol = rawSymbol.toUpperCase();
  const router = useRouter();
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await analysisService.getReport(symbol);
      const reportData = res.agent_results?.report as ReportData | undefined;
      if (res.status === "completed" && reportData) {
        setReport(reportData);
      } else {
        setReport(null);
      }
    } catch (err) {
      console.error("Failed to load report:", err);
      setReport(null);
      setError("No report found for this symbol.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol]);

  const generate = async () => {
    setGenerating(true);
    setError(null);
    try {
      await analysisService.generateReport(symbol);
      await load();
    } catch (err) {
      console.error("Failed to generate report:", err);
      setError("Failed to generate report. Run an analysis for this symbol first.");
    } finally {
      setGenerating(false);
    }
  };

  const sections: { label: string; key: string }[] = [
    { label: "IPO Overview", key: "ipo_overview" },
    { label: "Company Background", key: "company_background" },
    { label: "Industry Analysis", key: "industry_analysis" },
    { label: "Financial Analysis", key: "financial_analysis" },
    { label: "Valuation Analysis", key: "valuation_analysis" },
    { label: "Risk Analysis", key: "risk_analysis" },
    { label: "Management Assessment", key: "management_assessment" },
    { label: "Sentiment Analysis", key: "sentiment_analysis" },
    { label: "Recommendation", key: "recommendation" },
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => router.push("/reports")}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">{symbol} - Investment Research Report</h1>
              <p className="text-muted-foreground">
                {report?.created_at ? `Generated: ${new Date(report.created_at).toLocaleString()}` : "Research report"}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={load} disabled={loading}>
              <Brain className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button onClick={generate} disabled={generating}>
              <FileText className="h-4 w-4 mr-2" />
              {generating ? "Generating..." : "Regenerate Report"}
            </Button>
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}

        {loading ? (
          <p className="text-muted-foreground">Loading report...</p>
        ) : !report ? (
          <Card>
            <CardContent className="text-center py-16">
              <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-medium">No report available for {symbol}</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Run an analysis first, then generate the investment research report.
              </p>
              <Button onClick={generate} disabled={generating}>
                <FileText className="h-4 w-4 mr-2" />
                {generating ? "Generating..." : "Generate Report"}
              </Button>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>{report.title}</CardTitle>
            </CardHeader>
            <CardContent className="prose max-w-none space-y-6">
              <div className="text-center border-b pb-6">
                <h2 className="text-3xl font-bold">{symbol}</h2>
                <p className="text-muted-foreground">IPO Investment Research Report</p>
                <p className="text-sm text-muted-foreground">
                  Generated: {report.created_at ? new Date(report.created_at).toLocaleDateString() : "N/A"}
                </p>
              </div>

              <section>
                <h3 className="text-xl font-semibold mb-3">Executive Summary</h3>
                <div className="whitespace-pre-wrap text-sm leading-relaxed">{report.executive_summary}</div>
              </section>

              {report.investment_thesis && (
                <section>
                  <h3 className="text-xl font-semibold mb-3">Investment Thesis</h3>
                  <div className="grid gap-4 md:grid-cols-2">
                    {report.bull_case && (
                      <div className="p-4 rounded-lg bg-green-50 border border-green-200">
                        <h4 className="font-medium text-green-800 mb-2">Bull Case</h4>
                        <div className="whitespace-pre-wrap text-sm text-green-700">{report.bull_case}</div>
                      </div>
                    )}
                    {report.bear_case && (
                      <div className="p-4 rounded-lg bg-red-50 border border-red-200">
                        <h4 className="font-medium text-red-800 mb-2">Bear Case</h4>
                        <div className="whitespace-pre-wrap text-sm text-red-700">{report.bear_case}</div>
                      </div>
                    )}
                  </div>
                </section>
              )}

              {Object.keys(report.key_metrics || {}).length > 0 && (
                <section>
                  <h3 className="text-xl font-semibold mb-3">Key Metrics</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b text-left text-sm text-muted-foreground">
                          <th className="pb-2">Metric</th>
                          <th className="pb-2 text-right">Value</th>
                        </tr>
                      </thead>
                      <tbody className="text-sm">
                        {Object.entries(report.key_metrics).map(([key, value]) => (
                          <tr key={key} className="border-b last:border-0">
                            <td className="py-3 font-medium">
                              {key.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                            </td>
                            <td className="py-3 text-right font-medium">
                              {typeof value === "number" ? value.toFixed(2) : String(value)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}

              {sections.map(({ label, key }) => {
                const content = (report as unknown as Record<string, string>)[key];
                return content ? (
                  <section key={key}>
                    <h3 className="text-xl font-semibold mb-3">{label}</h3>
                    <div className="whitespace-pre-wrap text-sm leading-relaxed">{content}</div>
                  </section>
                ) : null;
              })}

              <div className="border-t pt-6">
                <p className="text-sm text-muted-foreground">
                  <strong>Disclaimer:</strong> This report is for informational purposes only and does not constitute investment advice.
                  Past performance is not indicative of future results. The AI agents generating this analysis may make errors.
                  Please consult with a qualified financial advisor before making investment decisions.
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
