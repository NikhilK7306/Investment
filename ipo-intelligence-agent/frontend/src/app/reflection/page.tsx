"use client";

import { useState, useEffect, useMemo } from "react";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Brain, TrendingUp, CheckCircle, Target, Zap, Loader2 } from "lucide-react";
import { memoryService } from "@/services/memoryService";
import { analysisService } from "@/services/analysisService";
import type { ReflectionItem } from "@/types/memory";

type TimeRange = "all" | "30d" | "90d" | "1y";

const TIME_LABELS: Record<TimeRange, string> = {
  all: "All Time",
  "30d": "Last 30 Days",
  "90d": "Last 90 Days",
  "1y": "Last Year",
};

export default function ReflectionPage() {
  const [reflections, setReflections] = useState<ReflectionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [cycleRunning, setCycleRunning] = useState(false);
  const [search, setSearch] = useState("");
  const [symbolFilter, setSymbolFilter] = useState("all");
  const [timeRange, setTimeRange] = useState<TimeRange>("all");

  useEffect(() => {
    memoryService
      .getReflections({ limit: 100 })
      .then(setReflections)
      .catch(() => setReflections([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const now = Date.now();
    const rangeMs: Record<Exclude<TimeRange, "all">, number> = {
      "30d": 30 * 86400000,
      "90d": 90 * 86400000,
      "1y": 365 * 86400000,
    };
    const q = search.toLowerCase();
    return reflections.filter((r) => {
      if (symbolFilter !== "all" && r.ipo_symbol !== symbolFilter) return false;
      if (timeRange !== "all") {
        const created = new Date(r.created_at).getTime();
        if (!created || now - created > qMs[timeRange]) return false;
      }
      if (q) {
        const hay = `${r.ipo_symbol} ${r.prediction_type} ${r.prediction_id}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [reflections, search, symbolFilter, timeRange]);

  const totalPredictions = filtered.length;
  const verified = filtered.filter((r) => r.accuracy > 0.5).length;
  const avgAccuracy =
    filtered.length > 0
      ? Math.round(
          (filtered.reduce((s, r) => s + r.accuracy, 0) / filtered.length) * 100
        )
      : 0;
  const totalLessons = filtered.reduce(
    (s, r) => s + r.lessons_extracted.length + r.missing_factors.length,
    0
  );

  const accuracyByType = Object.entries(
    filtered.reduce((acc: Record<string, number[]>, r) => {
      (acc[r.prediction_type] = acc[r.prediction_type] || []).push(r.accuracy);
      return acc;
    }, {})
  ).map(([type, accs]) => ({
    type,
    avg: Math.round((accs.reduce((a, b) => a + b, 0) / accs.length) * 100),
    count: accs.length,
  }));

  const bins = ["0-30%", "30-50%", "50-70%", "70-90%", "90-100%"].map(
    (range) => {
      const [lo, hi] = range.replace("%", "").split("-").map(Number);
      const items = filtered.filter((r) => {
        const pct = r.accuracy * 100;
        return pct >= lo && pct < hi;
      });
      const avg =
        items.length > 0
          ? Math.round(
              (items.reduce((s, r) => s + r.accuracy * 100, 0) / items.length)
            )
          : 0;
      return { range, conf: avg, acc: avg, count: items.length };
    }
  );

  const uniqueSymbols = [...new Set(reflections.map((r) => r.ipo_symbol))];

  const runCycle = async () => {
    setCycleRunning(true);
    try {
      await analysisService.runReflection({ min_delay_days: 30, batch_size: 50 });
      const fresh = await memoryService.getReflections({ limit: 100 });
      setReflections(fresh);
    } catch (err) {
      console.error("Reflection cycle failed:", err);
    } finally {
      setCycleRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Reflection Engine</h1>
            <p className="text-muted-foreground">
              Analyze prediction accuracy and extract lessons for continuous
              improvement
            </p>
          </div>
          <Button variant="outline" onClick={runCycle} disabled={cycleRunning}>
            <Zap className={`h-4 w-4 mr-2 ${cycleRunning ? "animate-pulse" : ""}`} />
            {cycleRunning ? "Running cycle..." : "Run Reflection Cycle"}
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Predictions</CardTitle>
              <Target className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalPredictions}</div>
              <p className="text-xs text-muted-foreground">All time</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Verified</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-500">{verified}</div>
              <p className="text-xs text-muted-foreground">
                {totalPredictions > 0
                  ? Math.round((verified / totalPredictions) * 100)
                  : 0}
                % verified
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Accuracy</CardTitle>
              <TrendingUp className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{avgAccuracy}%</div>
              <p className="text-xs text-muted-foreground">Across all predictions</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Lessons Extracted</CardTitle>
              <Brain className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalLessons}</div>
              <p className="text-xs text-muted-foreground">From verified outcomes</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle>Prediction Accuracy by Type</CardTitle>
              <Select value={timeRange} onValueChange={(v) => setTimeRange(v as TimeRange)}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="All Time" />
                </SelectTrigger>
                <SelectContent>
                  {(Object.keys(TIME_LABELS) as TimeRange[]).map((k) => (
                    <SelectItem key={k} value={k}>
                      {TIME_LABELS[k]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {accuracyByType.length === 0 && (
                  <p className="text-sm text-muted-foreground py-4">
                    No reflection data yet. Run a reflection cycle after
                    outcomes are verified.
                  </p>
                )}
                {accuracyByType.map((item, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-48 text-sm text-muted-foreground">{item.type}</div>
                      <div className="w-32 bg-muted rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all"
                          style={{ width: `${item.avg}%` }}
                        />
                      </div>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                      <span className="font-medium">{item.avg}%</span>
                      <span className="text-muted-foreground">({item.count})</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle>Calibration Curve</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {bins.map((item, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center gap-3 w-1/2">
                      <span className="w-24 text-sm text-muted-foreground">{item.range}</span>
                      <div className="flex-1 bg-muted rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all"
                          style={{ width: `${item.conf}%` }}
                        />
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-sm w-1/2 text-right">
                      <span className="text-muted-foreground">Conf: {item.conf}%</span>
                      <span className="font-medium">Acc: {item.acc}%</span>
                      <span className="text-muted-foreground">({item.count})</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle>Reflection Records</CardTitle>
            <div className="flex gap-2">
              <Input
                placeholder="Search reflections..."
                className="w-64"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <Select value={symbolFilter} onValueChange={setSymbolFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="All Symbols" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Symbols</SelectItem>
                  {uniqueSymbols.map((s) => (
                    <SelectItem key={s} value={s}>{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Predicted</TableHead>
                  <TableHead>Actual</TableHead>
                  <TableHead>Accuracy</TableHead>
                  <TableHead>Mistakes</TableHead>
                  <TableHead>Lessons</TableHead>
                  <TableHead>Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading && (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center text-muted-foreground py-8">
                      <Loader2 className="h-4 w-4 inline mr-2 animate-spin" />
                      Loading reflections...
                    </TableCell>
                  </TableRow>
                )}
                {!loading && filtered.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center text-muted-foreground py-8">
                      No reflection records yet. Predictions are evaluated after
                      listings mature.
                    </TableCell>
                  </TableRow>
                )}
                {filtered.map((ref, index) => (
                  <TableRow key={ref.prediction_id || index}>
                    <TableCell className="font-mono text-sm">{ref.prediction_id}</TableCell>
                    <TableCell><Badge variant="default">{ref.ipo_symbol}</Badge></TableCell>
                    <TableCell className="text-sm">{ref.prediction_type}</TableCell>
                    <TableCell className="font-mono">{Math.round(ref.predicted_value * 100)}%</TableCell>
                    <TableCell className="font-mono">{Math.round(ref.actual_value * 100)}%</TableCell>
                    <TableCell>
                      <Badge variant={ref.accuracy > 0.7 ? "success" : ref.accuracy > 0.5 ? "default" : "destructive"}>
                        {Math.round(ref.accuracy * 100)}%
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate">
                      {ref.mistakes_identified.join(", ") || "-"}
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate">
                      {ref.lessons_extracted.join(", ") || "-"}
                    </TableCell>
                    <TableCell>{new Date(ref.created_at).toLocaleDateString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </Card>
      </div>
    </div>
  );
}