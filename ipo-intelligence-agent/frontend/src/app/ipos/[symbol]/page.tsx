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
import type { IPOResponse } from "@/types/ipo";
import type { AnalysisResponse } from "@/types/analysis";

export default function IPODetailPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol: rawSymbol } = use(params);
  const symbol = rawSymbol.toUpperCase();
  const router = useRouter();
  const [ipo, setIpo] = useState<IPOResponse | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const [ipoData, analysisData] = await Promise.all([
          ipoService.getBySymbol(symbol).catch(() => null),
          analysisService.getResult(symbol).catch(() => null),
        ]);
        setIpo(ipoData);
        setAnalysis(analysisData);
      } catch (err) {
        console.error("Failed to fetch IPO:", err);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [symbol]);

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
  const ipoPriceRange = ipo?.price_range ? `$${ipo.price_range.low} - $${ipo.price_range.high}` : "N/A";
  const overallScore = analysis?.overall_score ?? 78;
  const recommendation = analysis?.recommendation ?? "N/A";
  const riskLevel = analysis?.risk_level ?? "MODERATE";
  const confidence = analysis?.confidence ?? 0.75;

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
            <Button variant="outline" onClick={() => router.push(`/reports/${symbol}`)}>
              <FileText className="h-4 w-4 mr-2" />Download Report
            </Button>
            <Button onClick={async () => {
              try {
                await analysisService.analyze(symbol);
                router.push(`/analysis?symbol=${symbol}`);
              } catch (err) {
                console.error("Failed to start analysis:", err);
              }
            }}>
              <Brain className="h-4 w-4 mr-2" />Re-run Analysis
            </Button>
          </div>
        </div>

        {/* Score Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Overall Score</p>
                  <p className="text-4xl font-bold">{overallScore}/100</p>
                </div>
                <Target className="h-12 w-12 text-primary/20" />
              </div>
              <Progress value={overallScore} className="mt-4 h-2" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground">Recommendation</p>
              <p className="text-3xl font-bold text-green-600">{recommendation}</p>
              <p className="text-sm text-muted-foreground mt-1">Confidence: {Math.round(confidence * 100)}%</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground">Risk Level</p>
              <p className="text-3xl font-bold text-yellow-600">{riskLevel}</p>
              <p className="text-sm text-muted-foreground mt-1">Time Horizon: Medium Term</p>
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
        <Tabs defaultValue="overview" className="w-full">
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
                    <div><p className="text-muted-foreground">Valuation</p><p className="font-medium">{ipo?.valuation?.equity_value ? `$${(ipo.valuation.equity_value / 1e9).toFixed(1)}B` : "N/A"}</p></div>
                    <div><p className="text-muted-foreground">Lead Underwriters</p><p className="font-medium">Goldman Sachs, Morgan Stanley</p></div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><BarChart2 className="h-5 w-5" /> Score Breakdown</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    {[
                      { label: "Financial Strength", score: 85, weight: 25 },
                      { label: "Growth Potential", score: 78, weight: 25 },
                      { label: "Market Opportunity", score: 82, weight: 20 },
                      { label: "Management Quality", score: 88, weight: 15 },
                      { label: "Risk Level (inv.)", score: 75, weight: 15 },
                    ].map((item) => (
                      <div key={item.label} className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>{item.label}</span>
                          <span className="font-medium">{item.score}/100</span>
                        </div>
                        <Progress value={item.score} className="h-2" />
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><Shield className="h-5 w-5" /> Key Risks</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {[
                      { risk: "High customer concentration (top 3 = 45% revenue)", severity: "high" },
                      { risk: "Intense competition from MSFT, GOOGL", severity: "moderate" },
                      { risk: "Key person dependency on CEO", severity: "moderate" },
                      { risk: "Regulatory uncertainty in data privacy", severity: "low" },
                    ].map((r, i) => (
                      <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-muted/50">
                        <AlertTriangle className={`h-4 w-4 ${r.severity === "high" ? "text-red-500" : r.severity === "moderate" ? "text-yellow-500" : "text-green-500"}`} />
                        <span className="text-sm">{r.risk}</span>
                        <Badge variant={r.severity === "high" ? "destructive" : r.severity === "moderate" ? "secondary" : "outline"} className="ml-auto">
                          {r.severity}
                        </Badge>
                      </div>
                    ))}
                  </div>
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
                    <p className="font-medium text-green-700">✓ Strong recurring revenue model (92% ARR)</p>
                    <p className="font-medium text-green-700">✓ Expanding TAM with 35% CAGR</p>
                    <p className="font-medium text-green-700">✓ Best-in-class net revenue retention (130%)</p>
                    <p className="font-medium text-green-700">✓ Experienced management with prior exits</p>
                    <p className="font-medium text-green-700">✓ Clear path to profitability by Q4 2025</p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><TrendingDown className="h-5 w-5" /> Bear Case</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <p className="font-medium text-red-700">✗ High valuation at 15x forward revenue</p>
                    <p className="font-medium text-red-700">✗ Customer concentration risk</p>
                    <p className="font-medium text-red-700">✗ Increasing competition from well-funded rivals</p>
                    <p className="font-medium text-red-700">✗ Path to profitability not yet proven</p>
                    <p className="font-medium text-red-700">✗ Lockup expiration in 180 days</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="financials" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Financial Statements</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b text-left text-sm text-muted-foreground">
                        <th className="pb-2">Metric</th>
                        <th className="pb-2 text-right">FY2023</th>
                        <th className="pb-2 text-right">FY2022</th>
                        <th className="pb-2 text-right">FY2021</th>
                        <th className="pb-2 text-right">YoY Change</th>
                      </tr>
                    </thead>
                    <tbody className="text-sm">
                      {[
                        { metric: "Revenue", fy23: "$245.6M", fy22: "$189.2M", fy21: "$142.1M", change: "+29.8%" },
                        { metric: "Gross Profit", fy23: "$198.7M", fy22: "$148.5M", fy21: "$108.3M", change: "+33.8%" },
                        { metric: "Gross Margin", fy23: "81.0%", fy22: "78.5%", fy21: "76.2%", change: "+250bps" },
                        { metric: "Operating Income", fy23: "-$12.4M", fy22: "-$28.7M", fy21: "-$35.2M", change: "Improving" },
                        { metric: "Net Income", fy23: "-$15.8M", fy22: "-$31.2M", fy21: "-$38.9M", change: "Improving" },
                        { metric: "Free Cash Flow", fy23: "$8.2M", fy22: "-$5.4M", fy21: "-$12.1M", change: "Turnaround" },
                        { metric: "Cash & Equivalents", fy23: "$185.4M", fy22: "$92.1M", fy21: "$45.3M", change: "+101%" },
                      ].map((row, i) => (
                        <tr key={i} className="border-b last:border-0">
                          <td className="py-3 font-medium">{row.metric}</td>
                          <td className="py-3 text-right font-medium">{row.fy23}</td>
                          <td className="py-3 text-right">{row.fy22}</td>
                          <td className="py-3 text-right">{row.fy21}</td>
                          <td className="py-3 text-right text-green-600 font-medium">{row.change}</td>
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
                  <CardTitle>Key Ratios</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {[
                    { name: "Revenue Growth (YoY)", value: "29.8%", trend: "up" },
                    { name: "Gross Margin", value: "81.0%", trend: "up" },
                    { name: "Operating Margin", value: "-5.1%", trend: "up" },
                    { name: "Net Margin", value: "-6.4%", trend: "up" },
                    { name: "FCF Margin", value: "3.3%", trend: "up" },
                    { name: "Rule of 40", value: "24.7%", trend: "up" },
                    { name: "Net Revenue Retention", value: "130%", trend: "up" },
                    { name: "CAC Payback Period", value: "14 months", trend: "down" },
                  ].map((r, i) => (
                    <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-muted/50">
                      <span className="text-sm">{r.name}</span>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{r.value}</span>
                        {r.trend === "up" ? <TrendingUp className="h-4 w-4 text-green-600" /> : <TrendingDown className="h-4 w-4 text-red-600" />}
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Valuation Metrics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {[
                    { name: "IPO Price (Mid)", value: "$20.00" },
                    { name: "Implied Market Cap", value: "$2.1B" },
                    { name: "EV/Revenue (FY23)", value: "8.6x" },
                    { name: "EV/Revenue (FY24E)", value: "6.2x" },
                    { name: "EV/Gross Profit", value: "10.6x" },
                    { name: "Price/FCF", value: "256x" },
                    { name: "Peer Median EV/Rev", value: "9.2x" },
                    { name: "Discount/Premium to Peers", value: "-6.5%", trend: "down" },
                  ].map((m, i) => (
                    <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-muted/50">
                      <span className="text-sm">{m.name}</span>
                      <span className="font-medium">{m.value}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="analysis" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Fundamental Analysis</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 rounded-lg bg-green-50 border border-green-200">
                    <p className="font-medium text-green-800">Strengths</p>
                    <ul className="mt-2 space-y-1 text-sm text-green-700">
                      <li>• Exceptional gross margins (81%) with improving trend</li>
                      <li>• Strong net revenue retention (130%)</li>
                      <li>• Accelerating revenue growth (29.8% YoY)</li>
                      <li>• Improving FCF trajectory, turning positive</li>
                    </ul>
                  </div>
                  <div className="p-4 rounded-lg bg-yellow-50 border border-yellow-200">
                    <p className="font-medium text-yellow-800">Concerns</p>
                    <ul className="mt-2 space-y-1 text-sm text-yellow-700">
                      <li>• Still operating at a net loss</li>
                      <li>• High S&M spend (65% of revenue)</li>
                      <li>• Customer concentration risk</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Market Analysis</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 rounded-lg bg-blue-50 border border-blue-200">
                    <p className="font-medium text-blue-800">Market Opportunity</p>
                    <ul className="mt-2 space-y-1 text-sm text-blue-700">
                      <li>• TAM: $45B (Enterprise Software)</li>
                      <li>• SAM: $12B (Vertical SaaS)</li>
                      <li>• SOM: $800M (5-year target)</li>
                      <li>• Market growing at 35% CAGR</li>
                    </ul>
                  </div>
                  <div className="p-4 rounded-lg bg-purple-50 border border-purple-200">
                    <p className="font-medium text-purple-800">Competitive Position</p>
                    <ul className="mt-2 space-y-1 text-sm text-purple-700">
                      <li>• #3 player in niche vertical</li>
                      <li>• Strong differentiation via AI/ML</li>
                      <li>• High switching costs (130% NRR)</li>
                      <li>• Patent portfolio: 47 granted</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="risks" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Risk Assessment</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b text-left text-sm text-muted-foreground">
                        <th className="pb-2">Risk Factor</th>
                        <th className="pb-2">Category</th>
                        <th className="pb-2">Severity</th>
                        <th className="pb-2">Probability</th>
                        <th className="pb-2">Impact</th>
                        <th className="pb-2">Mitigation</th>
                      </tr>
                    </thead>
                    <tbody className="text-sm">
                      {[
                        { risk: "Customer Concentration", cat: "Financial", sev: "HIGH", prob: "70%", impact: "80%", mit: "Diversify customer base" },
                        { risk: "Competitive Threat", cat: "Market", sev: "HIGH", prob: "65%", impact: "75%", mit: "Invest in differentiation" },
                        { risk: "Key Person Risk", cat: "Operational", sev: "MODERATE", prob: "40%", impact: "70%", mit: "Succession planning" },
                        { risk: "Regulatory Changes", cat: "Regulatory", sev: "MODERATE", prob: "35%", impact: "60%", mit: "Compliance monitoring" },
                        { risk: "Lockup Expiration", cat: "Post-IPO", sev: "MODERATE", prob: "90%", impact: "50%", mit: "Staggered release" },
                      ].map((r, i) => (
                        <tr key={i} className="border-b last:border-0">
                          <td className="py-3 font-medium">{r.risk}</td>
                          <td className="py-3">{r.cat}</td>
                          <td className="py-3"><Badge variant={r.sev === "HIGH" ? "destructive" : "secondary"}>{r.sev}</Badge></td>
                          <td className="py-3">{r.prob}</td>
                          <td className="py-3">{r.impact}</td>
                          <td className="py-3 text-sm text-muted-foreground">{r.mit}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="sentiment" className="space-y-4">
            <div className="grid gap-6 md:grid-cols-3">
              <Card>
                <CardHeader>
                  <CardTitle>Composite Sentiment</CardTitle>
                </CardHeader>
                <CardContent className="text-center py-8">
                  <div className="text-6xl font-bold text-green-600">+0.34</div>
                  <p className="text-sm text-muted-foreground mt-2">Moderately Positive</p>
                  <div className="mt-4 flex justify-center gap-4 text-sm">
                    <span>Confidence: 82%</span>
                    <span>Articles: 147</span>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Source Breakdown</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {[
                    { source: "Financial News", score: 0.42, count: 52, weight: 30 },
                    { source: "Analyst Reports", score: 0.58, count: 18, weight: 25 },
                    { source: "Social Media", score: 0.15, count: 89, weight: 20 },
                    { source: "Alternative Data", score: 0.38, count: 12, weight: 15 },
                    { source: "Institutional", score: 0.65, count: 8, weight: 10 },
                  ].map((s, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <span className="text-sm">{s.source}</span>
                      <div className="flex items-center gap-2">
                        <Progress value={(s.score + 1) * 50} className="w-32 h-2" />
                        <span className="text-sm font-medium">{s.score > 0 ? "+" : ""}{s.score.toFixed(2)}</span>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Key Themes</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="p-3 rounded-lg bg-green-50">
                    <p className="font-medium text-green-800">Positive</p>
                    <ul className="mt-1 space-y-1 text-sm text-green-700">
                      <li>• Strong earnings momentum</li>
                      <li>• AI/ML differentiation praised</li>
                      <li>• Management credibility high</li>
                    </ul>
                  </div>
                  <div className="p-3 rounded-lg bg-red-50">
                    <p className="font-medium text-red-800">Negative</p>
                    <ul className="mt-1 space-y-1 text-sm text-red-700">
                      <li>• Valuation concerns</li>
                      <li>• Competitive intensity</li>
                      <li>• Lockup overhang</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="report" className="space-y-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Investment Research Report</CardTitle>
                <Button variant="outline"><FileText className="h-4 w-4 mr-2" />Export PDF</Button>
              </CardHeader>
              <CardContent className="prose max-w-none space-y-6">
                <div className="text-center border-b pb-6">
                  <h2 className="text-3xl font-bold">{ipoName} ({symbol})</h2>
                  <p className="text-muted-foreground">IPO Investment Research Report</p>
                  <p className="text-sm text-muted-foreground">Generated: {new Date().toLocaleDateString()}</p>
                </div>

                <section>
                  <h3 className="text-xl font-semibold mb-3">Executive Summary</h3>
                  <p>TechCorp Inc (TECH) is a leading enterprise software provider targeting the $45B enterprise workflow automation market. The company demonstrates strong fundamentals with 29.8% YoY revenue growth, 81% gross margins, and improving free cash flow trajectory. We assign a <strong>BUY</strong> recommendation with an overall score of 82/100.</p>
                </section>

                <section>
                  <h3 className="text-xl font-semibold mb-3">Investment Thesis</h3>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="p-4 rounded-lg bg-green-50 border border-green-200">
                      <h4 className="font-medium text-green-800 mb-2">Bull Case</h4>
                      <ul className="space-y-1 text-sm text-green-700">
                        <li>• Market leader in high-growth vertical (35% CAGR)</li>
                        <li>• Best-in-class net revenue retention (130%)</li>
                        <li>• AI/ML differentiation creating moat</li>
                        <li>• Clear path to profitability by Q4 2025</li>
                      </ul>
                    </div>
                    <div className="p-4 rounded-lg bg-red-50 border border-red-200">
                      <h4 className="font-medium text-red-800 mb-2">Bear Case</h4>
                      <ul className="space-y-1 text-sm text-red-700">
                        <li>• Trading at premium to peers (8.6x vs 6.2x median)</li>
                        <li>• Customer concentration (top 3 = 45% revenue)</li>
                        <li>• Intense competition from MSFT, GOOGL</li>
                        <li>• Lockup expiration creates overhang</li>
                      </ul>
                    </div>
                  </div>
                </section>

                <section>
                  <h3 className="text-xl font-semibold mb-3">Key Metrics</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b text-left text-sm text-muted-foreground">
                          <th className="pb-2">Metric</th>
                          <th className="pb-2 text-right">Value</th>
                          <th className="pb-2 text-right">Peer Median</th>
                          <th className="pb-2">Assessment</th>
                        </tr>
                      </thead>
                      <tbody className="text-sm">
                        {[
                          { metric: "Revenue Growth (YoY)", value: "29.8%", peer: "22.1%", assessment: "Above Average" },
                          { metric: "Gross Margin", value: "81.0%", peer: "74.5%", assessment: "Best-in-Class" },
                          { metric: "FCF Margin", value: "3.3%", peer: "-1.2%", assessment: "Above Average" },
                          { metric: "Net Revenue Retention", value: "130%", peer: "115%", assessment: "Best-in-Class" },
                          { metric: "Rule of 40", value: "24.7%", peer: "28.3%", assessment: "Below Average" },
                        ].map((m, i) => (
                          <tr key={i} className="border-b last:border-0">
                            <td className="py-3 font-medium">{m.metric}</td>
                            <td className="py-3 text-right font-medium">{m.value}</td>
                            <td className="py-3 text-right">{m.peer}</td>
                            <td className="py-3"><Badge variant="default">{m.assessment}</Badge></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>

                <section>
                  <h3 className="text-xl font-semibold mb-3">Valuation</h3>
                  <div className="grid gap-4 md:grid-cols-3">
                    <Card>
                      <CardHeader>
                        <CardTitle>DCF Valuation</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-2xl font-bold">$24.50</p>
                        <p className="text-sm text-muted-foreground">Fair Value Estimate</p>
                        <p className="text-sm text-green-600 mt-1">+22.5% upside to mid-point</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader>
                        <CardTitle>Comparable Companies</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-2xl font-bold">$22.80</p>
                        <p className="text-sm text-muted-foreground">EV/Rev Multiple</p>
                        <p className="text-sm text-green-600 mt-1">+14% upside</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader>
                        <CardTitle>Precedent Transactions</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-2xl font-bold">$26.20</p>
                        <p className="text-sm text-muted-foreground">M&A Comps</p>
                        <p className="text-sm text-green-600 mt-1">+31% upside</p>
                      </CardContent>
                    </Card>
                  </div>
                </section>

                <div className="border-t pt-6">
                  <p className="text-sm text-muted-foreground">
                    <strong>Disclaimer:</strong> This report is for informational purposes only and does not constitute investment advice.
                    Past performance is not indicative of future results. The AI agents generating this analysis may make errors.
                    Please consult with a qualified financial advisor before making investment decisions.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
