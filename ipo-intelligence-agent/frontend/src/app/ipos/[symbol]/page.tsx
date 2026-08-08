"use client";

import { use, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  DollarSign,
  BarChart2,
  Target,
  Shield,
  Users,
  Clock,
  Brain,
  FileText,
  ChevronRight,
} from "lucide-react";
import { ipoService } from "@/services/ipoService";
import { analysisService } from "@/services/analysisService";
import type { IPOResponse, FinancialPeriod } from "@/types/ipo";
import type { AnalysisResponse, ReportData } from "@/types/analysis";

const compactMoney = (currency: string, value: number | null | undefined): string => {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  const abs = Math.abs(value);
  let formatted: string;
  if (abs >= 1e12) formatted = `${(value / 1e12).toFixed(2)}T`;
  else if (abs >= 1e9) formatted = `${(value / 1e9).toFixed(2)}B`;
  else if (abs >= 1e6) formatted = `${(value / 1e6).toFixed(2)}M`;
  else if (abs >= 1e3) formatted = `${(value / 1e3).toFixed(1)}K`;
  else formatted = value.toFixed(0);
  return `${currency}${formatted}`;
};

const compactPercent = (value: number | null | undefined): string => {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  return `${(value * 100).toFixed(1)}%`;
};

export default function IPODetailPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol: rawSymbol } = use(params);
  const symbol = rawSymbol.toUpperCase();
  const router = useRouter();
  const [ipo, setIpo] = useState<IPOResponse | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [financials, setFinancials] = useState<FinancialPeriod[]>([]);
  const [report, setReport] = useState<ReportData | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [generateReportLoading, setGenerateReportLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const [ipoData, analysisData, financialsData] = await Promise.all([
          ipoService.getBySymbol(symbol).catch(() => null),
          analysisService.getResult(symbol).catch(() => null),
          ipoService.getFinancials(symbol).catch(() => null),
        ]);
        setIpo(ipoData);
        setAnalysis(analysisData);
        setFinancials(financialsData?.periods || []);
      } catch (err) {
        console.error("Failed to fetch IPO:", err);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [symbol]);

  const loadReport = async () => {
    setReportLoading(true);
    try {
      const res = await analysisService.getReport(symbol);
      const reportData = res.agent_results?.report as ReportData | undefined;
      if (res.status === "completed" && reportData) {
        setReport(reportData);
      }
    } catch (err) {
      console.error("Failed to load report:", err);
      setReport(null);
    } finally {
      setReportLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "report") loadReport();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, symbol]);

  const statusBadgeVariant: Record<string, "default" | "success" | "outline" | "destructive" | "secondary"> = {
    FILED: "default",
    PRICED: "success",
    LISTED: "success",
    ANNOUNCED: "outline",
    WITHDRAWN: "destructive",
    POSTPONED: "secondary",
  };

  const ipoName = ipo?.company_name || symbol;
  const ipoExchange = ipo?.exchange || "N/A";
  const ipoStatus = ipo?.status || "N/A";
  const ipoSector = ipo?.sector || "N/A";
  const ipoIndustry = ipo?.industry || "N/A";
  const ipoExpectedDate = ipo?.expected_date ? new Date(ipo.expected_date).toLocaleDateString() : "TBD";
  const isIndian = ipo?.exchange === "NSE" || ipo?.exchange === "BSE";
  const currency = isIndian ? "₹" : "$";
  const ipoPriceRange = ipo?.price_range ? `${currency}${ipo.price_range.low} - ${currency}${ipo.price_range.high}` : "N/A";
  const overallScore = analysis?.overall_score ?? null;
  const recommendation = analysis?.recommendation ?? "N/A";
  const riskLevel = analysis?.risk_level ?? "N/A";
  const confidence = analysis?.confidence ?? null;
  const timeHorizon = analysis?.time_horizon ?? "N/A";
  const hasAnalysis = !!analysis && analysis.status === "completed";
  const breakdownItems = hasAnalysis && analysis.score_breakdown
    ? Object.entries(analysis.score_breakdown).map(([key, score]) => ({
        key,
        label: key
          .split("_")
          .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
          .join(" "),
        score,
      }))
    : [];

  const startAnalysis = async () => {
    setAnalyzing(true);
    setAnalyzeError(null);
    try {
      const result = await analysisService.analyze(symbol);
      if (result?.error) {
        setAnalyzeError(
          typeof result.error === "string" ? result.error : "Analysis failed"
        );
        return;
      }
      router.push(`/ipos/${symbol}`);
    } catch (err) {
      const message =
        typeof (err as { response?: { data?: { detail?: string } } })?.response
          ?.data?.detail === "string"
          ? (err as { response?: { data?: { detail?: string } } }).response!.data!
              .detail!
          : "Analysis failed. Check the IPO symbol and try again.";
      setAnalyzeError(message);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <Badge variant="secondary">{ipoExchange}</Badge>
              <Badge variant={statusBadgeVariant[ipoStatus] || "outline"}>
                {ipoStatus}
              </Badge>
            </div>
            <h1 className="text-3xl font-bold mt-2">{ipoName} <span className="text-muted-foreground font-normal">({symbol})</span></h1>
            <p className="text-muted-foreground">{ipoSector} / {ipoIndustry}</p>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="outline" onClick={() => setActiveTab("report")}>
              <FileText className="h-4 w-4 mr-2" />Download Report
            </Button>
            <Button onClick={startAnalysis} disabled={analyzing}>
              <Brain className="h-4 w-4 mr-2" />
              {analyzing
                ? "Analyzing…"
                : hasAnalysis
                ? "Re-run Analysis"
                : "Run Analysis"}
            </Button>
          </div>
        </div>

        {analyzeError && (
          <div className="flex items-center gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            <AlertTriangle className="h-4 w-4" />
            {analyzeError}
          </div>
        )}

        {/* Score Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Overall Score</p>
                  <p className="text-4xl font-bold">{overallScore ?? "--"}{overallScore ? "/100" : ""}</p>
                </div>
                <Target className="h-12 w-12 text-primary/20" />
              </div>
              <Progress value={overallScore ?? 0} className="mt-4 h-2" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground">Recommendation</p>
              <p className="text-3xl font-bold text-green-600">{recommendation}</p>
              <p className="text-sm text-muted-foreground mt-1">Confidence: {confidence !== null ? `${Math.round(confidence * 100)}%` : "N/A"}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground">Risk Level</p>
              <p className="text-3xl font-bold text-yellow-600">{riskLevel}</p>
              <p className="text-sm text-muted-foreground mt-1">Time Horizon: {timeHorizon}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground">IPO Date</p>
              <p className="text-3xl font-bold">{ipoExpectedDate}</p>
              <p className="text-sm text-muted-foreground mt-1">Price Range: {ipoPriceRange}</p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-7">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="financials">Financials</TabsTrigger>
            <TabsTrigger value="analysis">Analysis</TabsTrigger>
            <TabsTrigger value="risks">Risks</TabsTrigger>
            <TabsTrigger value="sentiment">Sentiment</TabsTrigger>
            <TabsTrigger value="report">Report</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><DollarSign className="h-5 w-5" /> IPO Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div><p className="text-muted-foreground">Price Range</p><p className="font-medium">{ipoPriceRange}</p></div>
                    <div><p className="text-muted-foreground">Shares Offered</p><p className="font-medium">{ipo?.shares_offered?.toLocaleString() || "N/A"}</p></div>
                    <div><p className="text-muted-foreground">Valuation</p><p className="font-medium">{ipo?.valuation?.equity_value ? `${currency}${(ipo.valuation.equity_value / 1e9).toFixed(1)}B` : "N/A"}</p></div>
                    <div><p className="text-muted-foreground">Lead Underwriters</p><p className="font-medium">{ipo?.underwriters?.length ? ipo.underwriters.join(", ") : ipo?.lead_underwriter || "N/A"}</p></div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><BarChart2 className="h-5 w-5" /> Score Breakdown</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {hasAnalysis ? (
                    <div className="space-y-2">
                      {breakdownItems.length > 0 ? (
                        breakdownItems.map((item) => (
                          <div key={item.label || item.key} className="space-y-1">
                            <div className="flex justify-between text-sm">
                              <span>{item.label}</span>
                              <span className="font-medium">{item.score}/100</span>
                            </div>
                            <Progress value={item.score} className="h-2" />
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-muted-foreground">
                          No score breakdown was produced for this analysis.
                        </p>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No analysis available yet. Click "Re-run Analysis" above to generate a breakdown.
                    </p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><Shield className="h-5 w-5" /> Key Risks</CardTitle>
                </CardHeader>
                <CardContent>
                  {hasAnalysis && analysis.key_risks.length > 0 ? (
                    <div className="space-y-2">
                      {analysis.key_risks.map((risk, i) => (
                        <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-muted/50">
                          <AlertTriangle className="h-4 w-4 text-yellow-500" />
                          <span className="text-sm">{risk}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No risk assessment available yet. Run an analysis to identify key risks.
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><TrendingUp className="h-5 w-5" /> Bull Case</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    {hasAnalysis && analysis.bull_case ? (
                      <p className="font-medium text-green-700 whitespace-pre-wrap">{analysis.bull_case}</p>
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        No bull case available yet. Run an analysis to generate one.
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><TrendingDown className="h-5 w-5" /> Bear Case</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    {hasAnalysis && analysis.bear_case ? (
                      <p className="font-medium text-red-700 whitespace-pre-wrap">{analysis.bear_case}</p>
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        No bear case available yet. Run an analysis to generate one.
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="financials" className="space-y-6">
            {financials.length === 0 ? (
              <Card>
                <CardContent className="py-16 text-center">
                  <BarChart2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <h3 className="text-lg font-medium">No financial statements available</h3>
                  <p className="text-sm text-muted-foreground max-w-md mx-auto mt-2">
                    No financial history has been collected for {symbol} yet. Financial data is
                    populated by the collection pipeline as and when it becomes available.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle>Income Statement</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b text-left text-sm text-muted-foreground">
                            <th className="pb-2">Metric</th>
                            {financials.map((p) => (
                              <th key={p.period || p.period_end || p.revenue} className="pb-2 text-right">
                                {p.period_end ? new Date(p.period_end).toLocaleDateString(undefined, { year: "numeric", month: "short" }) : p.period || "—"}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="text-sm">
                          {[
{ label: "Revenue", accessor: (p: FinancialPeriod) => compactMoney(currency, p.revenue) },
                            { label: "Revenue Growth (YoY)", accessor: (p: FinancialPeriod) => compactPercent(p.revenue_growth_yoy) },
                            { label: "Gross Profit", accessor: (p: FinancialPeriod) => compactMoney(currency, p.gross_profit) },
                            { label: "Gross Margin", accessor: (p: FinancialPeriod) => compactPercent(p.gross_margin) },
                            { label: "Operating Income", accessor: (p: FinancialPeriod) => compactMoney(currency, p.operating_income) },
                            { label: "Operating Margin", accessor: (p: FinancialPeriod) => compactPercent(p.operating_margin) },
                            { label: "EBITDA", accessor: (p: FinancialPeriod) => compactMoney(currency, p.ebitda) },
                            { label: "Net Income", accessor: (p: FinancialPeriod) => compactMoney(currency, p.net_income) },
                            { label: "Net Margin", accessor: (p: FinancialPeriod) => compactPercent(p.net_margin) },
                            { label: "Free Cash Flow", accessor: (p: FinancialPeriod) => compactMoney(currency, p.free_cash_flow) },
].map(({ label, accessor }) => (
                            <tr key={label} className="border-b last:border-0">
                              <td className="py-3 font-medium">{label}</td>
                              {financials.map((p, i) => (
                                <td key={i} className="py-3 text-right">{accessor(p)}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>

                <div className="grid gap-6 md:grid-cols-2">
                  <Card>
                    <CardHeader>
                      <CardTitle>Balance Sheet & Liquidity</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {[
                          { name: "Cash & Equivalents", fn: (p: FinancialPeriod) => compactMoney(currency, p.cash_and_equivalents) },
                          { name: "Total Debt", fn: (p: FinancialPeriod) => compactMoney(currency, p.total_debt) },
                          { name: "Total Equity", fn: (p: FinancialPeriod) => compactMoney(currency, p.total_equity) },
                          { name: "Debt / Equity", fn: (p: FinancialPeriod) => (p.debt_to_equity === null ? "N/A" : p.debt_to_equity.toFixed(2)) },
                          { name: "Current Ratio", fn: (p: FinancialPeriod) => (p.current_ratio === null ? "N/A" : p.current_ratio.toFixed(2)) },
                        ].map(({ name, fn }) => (
                          <div key={name} className="flex items-center justify-between p-2 rounded-lg bg-muted/50">
                            <span className="text-sm">{name}</span>
                            <span className="font-medium text-sm">{fn(financials[0])}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Profitability & Efficiency</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {[
                          { name: "Return on Equity (ROE)", fn: (p: FinancialPeriod) => compactPercent(p.roe) },
                          { name: "Return on Invested Capital (ROIC)", fn: (p: FinancialPeriod) => compactPercent(p.roic) },
                          { name: "Gross Margin", fn: (p: FinancialPeriod) => compactPercent(p.gross_margin) },
                          { name: "Operating Margin", fn: (p: FinancialPeriod) => compactPercent(p.operating_margin) },
                          { name: "Net Margin", fn: (p: FinancialPeriod) => compactPercent(p.net_margin) },
                        ].map(({ name, fn }) => (
                          <div key={name} className="flex items-center justify-between p-2 rounded-lg bg-muted/50">
                            <span className="text-sm">{name}</span>
                            <span className="font-medium text-sm">{fn(financials[0])}</span>
                          </div>
                        ))}
                        <p className="text-xs text-muted-foreground pt-2">
                          Latest period: {financials[0].period_end ? new Date(financials[0].period_end).toLocaleDateString() : financials[0].period || "N/A"}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </>
            )}
          </TabsContent>

          <TabsContent value="analysis" className="space-y-6">
            {hasAnalysis ? (
              <div className="grid gap-6 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Bull Case</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {analysis.bull_case ? (
                      <p className="text-sm whitespace-pre-wrap">{analysis.bull_case}</p>
                    ) : (
                      <p className="text-sm text-muted-foreground">Not produced in the latest analysis.</p>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Bear Case</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {analysis.bear_case ? (
                      <p className="text-sm whitespace-pre-wrap">{analysis.bear_case}</p>
                    ) : (
                      <p className="text-sm text-muted-foreground">Not produced in the latest analysis.</p>
                    )}
                  </CardContent>
                </Card>

                {analysis.key_catalysts.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Key Catalysts</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2 text-sm">
                        {analysis.key_catalysts.map((c, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <CheckCircle className="h-4 w-4 mt-0.5 text-green-500 shrink-0" />
                            <span>{c}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {analysis.key_risks.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Key Risks</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2 text-sm">
                        {analysis.key_risks.map((r, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <AlertTriangle className="h-4 w-4 mt-0.5 text-yellow-500 shrink-0" />
                            <span>{r}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}
              </div>
            ) : (
              <Card>
                <CardContent className="py-16 text-center">
                  <Brain className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <h3 className="text-lg font-medium">No analysis available</h3>
                  <p className="text-sm text-muted-foreground max-w-md mx-auto mt-2">
                    Run an analysis for {symbol} to see the AI's bull/bear arguments, catalysts and risks.
                  </p>
                  <Button className="mt-4" onClick={startAnalysis} disabled={analyzing}>
                    <Brain className="h-4 w-4 mr-2" />{analyzing ? "Analyzing…" : "Run Analysis"}
                  </Button>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="risks" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Risk Assessment</CardTitle>
              </CardHeader>
              <CardContent>
                {hasAnalysis && analysis.key_risks.length > 0 ? (
                  <div className="space-y-3">
                    {analysis.key_risks.map((risk, i) => (
                      <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                        <AlertTriangle className="h-4 w-4 mt-0.5 text-yellow-500 shrink-0" />
                        <span className="text-sm">{risk}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-12 text-center">
                    <Shield className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                    <h3 className="text-lg font-medium">No risk assessment available</h3>
                    <p className="text-sm text-muted-foreground max-w-md mx-auto mt-2">
                      Run an analysis for {symbol} to surface key risks and mitigations identified by the AI agents.
                    </p>
                    <Button className="mt-4" variant="outline" onClick={startAnalysis} disabled={analyzing}>
                      <Brain className="h-4 w-4 mr-2" />{analyzing ? "Analyzing…" : "Run Analysis"}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="sentiment" className="space-y-4">
            {hasAnalysis && analysis.sentiment_score !== null ? (
              <div className="grid gap-6 md:grid-cols-3">
                <Card>
                  <CardHeader>
                    <CardTitle>Composite Sentiment</CardTitle>
                  </CardHeader>
                  <CardContent className="text-center py-8">
                    <div className={`text-6xl font-bold ${analysis.sentiment_score >= 0 ? "text-green-600" : "text-red-600"}`}>
                      {analysis.sentiment_score > 0 ? "+" : ""}{analysis.sentiment_score.toFixed(2)}
                    </div>
                    <p className="text-sm text-muted-foreground mt-2">{analysis.sentiment || "Neutral"}</p>
                    {analysis.confidence !== null && (
                      <p className="text-sm text-muted-foreground mt-4">Confidence: {Math.round(analysis.confidence * 100)}%</p>
                    )}
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Sentiment Drivers</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {analysis.sentiment_drivers.length > 0 ? (
                      <ul className="space-y-3">
                        {analysis.sentiment_drivers.map((driver, i) => (
                          <li key={i} className="flex items-center gap-2 p-2 rounded-lg bg-muted/50 text-sm">
                            {driver}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-muted-foreground">Sentiment drivers were not recorded.</p>
                    )}
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Score Breakdown</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {breakdownItems.length > 0 ? (
                      breakdownItems.map((item) => (
                        <div key={item.key} className="flex items-center justify-between">
                          <span className="text-sm">{item.label}</span>
                          <span className="text-sm font-medium">{item.score}/100</span>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-muted-foreground">No score breakdown recorded.</p>
                    )}
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card>
                <CardContent className="py-16 text-center">
                  <TrendingUp className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <h3 className="text-lg font-medium">No sentiment data available</h3>
                  <p className="text-sm text-muted-foreground max-w-md mx-auto mt-2">
                    Sentiment analysis is produced by the analysis pipeline. Run an analysis for {symbol} to
                    collect news, social and analyst sentiment.
                  </p>
                  <Button className="mt-4" variant="outline" onClick={startAnalysis} disabled={analyzing}>
                    <Brain className="h-4 w-4 mr-2" />{analyzing ? "Analyzing…" : "Run Analysis"}
                  </Button>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="report" className="space-y-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Investment Research Report</CardTitle>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    disabled={generateReportLoading || reportLoading}
                    onClick={async () => {
                      setGenerateReportLoading(true);
                      try {
                        await analysisService.generateReport(symbol);
                        await loadReport();
                      } catch (err) {
                        console.error("Failed to generate report:", err);
                      } finally {
                        setGenerateReportLoading(false);
                      }
                    }}
                  >
                    <Brain className="h-4 w-4 mr-2" />
                    {generateReportLoading ? "Generating..." : "Regenerate Report"}
                  </Button>
                  <Button variant="outline"><FileText className="h-4 w-4 mr-2" />Export PDF</Button>
                </div>
              </CardHeader>
              <CardContent className="prose max-w-none space-y-6">
                {reportLoading ? (
                  <p className="text-muted-foreground">Loading report...</p>
                ) : !report ? (
                  <div className="text-center py-12">
                    <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                    <h3 className="text-lg font-medium">No report available</h3>
                    <p className="text-sm text-muted-foreground">
                      Run an analysis first, then generate the investment research report.
                    </p>
                    <Button
                      className="mt-4"
                      disabled={generateReportLoading}
                      onClick={async () => {
                        setGenerateReportLoading(true);
                        try {
                          await analysisService.generateReport(symbol);
                          await loadReport();
                        } catch (err) {
                          console.error("Failed to generate report:", err);
                        } finally {
                          setGenerateReportLoading(false);
                        }
                      }}
                    >
                      <Brain className="h-4 w-4 mr-2" />
                      {generateReportLoading ? "Generating..." : "Generate Report"}
                    </Button>
                  </div>
                ) : (
                  <>
                    <div className="text-center border-b pb-6">
                      <h2 className="text-3xl font-bold">{ipoName} ({symbol})</h2>
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

                    {[
                      { label: "IPO Overview", key: "ipo_overview" },
                      { label: "Company Background", key: "company_background" },
                      { label: "Industry Analysis", key: "industry_analysis" },
                      { label: "Financial Analysis", key: "financial_analysis" },
                      { label: "Valuation Analysis", key: "valuation_analysis" },
                      { label: "Risk Analysis", key: "risk_analysis" },
                      { label: "Management Assessment", key: "management_assessment" },
                      { label: "Sentiment Analysis", key: "sentiment_analysis" },
                      { label: "Recommendation", key: "recommendation" },
                    ].map(({ label, key }) => (
                      (report as unknown as Record<string, string>)[key] ? (
                        <section key={key}>
                          <h3 className="text-xl font-semibold mb-3">{label}</h3>
                          <div className="whitespace-pre-wrap text-sm leading-relaxed">
                            {(report as unknown as Record<string, string>)[key]}
                          </div>
                        </section>
                      ) : null
                    ))}

                    <div className="border-t pt-6">
                      <p className="text-sm text-muted-foreground">
                        <strong>Disclaimer:</strong> This report is for informational purposes only and does not constitute investment advice.
                        Past performance is not indicative of future results. The AI agents generating this analysis may make errors.
                        Please consult with a qualified financial advisor before making investment decisions.
                      </p>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
