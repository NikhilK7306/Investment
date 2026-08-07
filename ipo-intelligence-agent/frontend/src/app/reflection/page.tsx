"use client";

import { useState, useEffect } from "react";
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
import { Brain, TrendingUp, CheckCircle, Target, Zap } from "lucide-react";
import { memoryService } from "@/services/memoryService";
import type { ReflectionItem } from "@/types/memory";

export default function ReflectionPage() {
  const [reflections, setReflections] = useState<ReflectionItem[]>([]);

  useEffect(() => {
    memoryService.getReflections({ processed: true, limit: 50 }).then(setReflections);
  }, []);

  const totalPredictions = reflections.length;
  const verified = reflections.filter((r) => r.accuracy > 0.5).length;
  const avgAccuracy =
    reflections.length > 0
      ? Math.round(
          (reflections.reduce((s, r) => s + r.accuracy, 0) / reflections.length) *
            100
        )
      : 0;
  const totalLessons = reflections.reduce(
    (s, r) => s + r.lessons_extracted.length,
    0
  );

  const accuracyByType = Object.entries(
    reflections.reduce((acc: Record<string, number[]>, r) => {
      (acc[r.prediction_type] = acc[r.prediction_type] || []).push(r.accuracy);
      return acc;
    }, {})
  ).map(([type, accs]) => ({
    type,
    avg: Math.round(
      (accs.reduce((a, b) => a + b, 0) / accs.length) * 100
    ),
    count: accs.length,
  }));

  const bins = ["0-30%", "30-50%", "50-70%", "70-90%", "90-100%"].map(
    (range) => {
      const [lo, hi] = range.replace("%", "").split("-").map(Number);
      const items = reflections.filter((r) => {
        const pct = r.accuracy * 100;
        return pct >= lo && pct < hi;
      });
      const avg =
        items.length > 0
          ? Math.round(
              items.reduce((s, r) => s + r.accuracy * 100, 0) / items.length
            )
          : 0;
      return { range, conf: avg, acc: avg, count: items.length };
    }
  );

  const uniqueSymbols = [...new Set(reflections.map((r) => r.ipo_symbol))];

  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Reflection Engine</h1>
            <p className="text-muted-foreground">Analyze prediction accuracy and extract lessons for continuous improvement</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => memoryService.getUnprocessedReflections()}><Zap className="h-4 w-4 mr-2" />Run Reflection Cycle</Button>
            <Button><Brain className="h-4 w-4 mr-2" />Extract Lessons</Button>
          </div>
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
              <p className="text-xs text-muted-foreground">{totalPredictions > 0 ? Math.round(verified / totalPredictions * 100) : 0}% verified</p>
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
              <p className="text-xs text-muted-foreground">This month</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle>Prediction Accuracy by Type</CardTitle>
              <div className="flex gap-2">
                <Select defaultValue="all">
                  <SelectTrigger className="w-[150px]">
                    <SelectValue placeholder="All Time" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Time</SelectItem>
                    <SelectItem value="30d">Last 30 Days</SelectItem>
                    <SelectItem value="90d">Last 90 Days</SelectItem>
                    <SelectItem value="1y">Last Year</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
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
              <Input placeholder="Search reflections..." className="w-64" />
              <Select defaultValue="all">
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
                {reflections.map((ref, index) => (
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
                    <TableCell className="max-w-[200px] truncate">{ref.mistakes_identified.join(", ")}</TableCell>
                    <TableCell className="max-w-[200px] truncate">{ref.missing_factors.join(", ")}</TableCell>
                    <TableCell>{ref.created_at}</TableCell>
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
