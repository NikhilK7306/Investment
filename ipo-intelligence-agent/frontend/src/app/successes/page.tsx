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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { CheckCircle, Brain, Sparkles, TrendingUp, Star } from "lucide-react";
import { memoryService } from "@/services/memoryService";
import type { SuccessResponse } from "@/types/memory";

function getContextString(context: Record<string, unknown>): string {
  if (typeof context === "string") return context;
  if (context?.summary) return String(context.summary);
  if (context?.description) return String(context.description);
  if (context?.industry) return String(context.industry);
  if (context?.sector) return String(context.sector);
  return "";
}

export default function SuccessesPage() {
  const router = useRouter();
  const [successes, setSuccesses] = useState<SuccessResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    memoryService
      .getSuccesses({ limit: 50 })
      .then(setSuccesses)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const totalStrategies = successes.length;
  const avgSuccessRate =
    successes.length > 0
      ? Math.round(
          (successes.reduce((sum, s) => sum + s.success_rate, 0) / successes.length) * 100
        )
      : 0;
  const totalReuses = successes.reduce((sum, s) => sum + s.reuse_count, 0);
  const avgConfidence =
    successes.length > 0
      ? Math.round(
          (successes.reduce((sum, s) => sum + s.confidence, 0) / successes.length) * 100
        )
      : 0;

  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Success Memory</h1>
            <p className="text-muted-foreground">
              Reusable strategies and winning patterns from successful analyses
            </p>
          </div>
          <Button onClick={() => router.push("/successes/record")}>
            <Sparkles className="h-4 w-4 mr-2" />
            Record Success
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Strategies</CardTitle>
              <Star className="h-4 w-4 text-yellow-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalStrategies}</div>
              <p className="text-xs text-muted-foreground">+{totalStrategies} total recorded</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Success Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-500">{avgSuccessRate}%</div>
              <p className="text-xs text-muted-foreground">Average across strategies</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Reuses</CardTitle>
              <TrendingUp className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalReuses}</div>
              <p className="text-xs text-muted-foreground">Across all strategies</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
              <Brain className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{avgConfidence}%</div>
              <p className="text-xs text-muted-foreground">High confidence strategies</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle>Successful Strategies</CardTitle>
            <div className="flex gap-2">
              <Input placeholder="Search strategies..." className="w-64" />
              <Select defaultValue="all">
                <SelectTrigger className="w-[150px]">
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
            </div>
          </CardHeader>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[60px]">#</TableHead>
                  <TableHead>Strategy</TableHead>
                  <TableHead className="w-[100px]">Agent</TableHead>
                  <TableHead className="w-[100px]">Confidence</TableHead>
                  <TableHead className="w-[100px]">Success Rate</TableHead>
                  <TableHead className="w-[120px]">Context</TableHead>
                  <TableHead className="w-[80px]">Reuses</TableHead>
                  <TableHead className="w-[100px]">Last Used</TableHead>
                  <TableHead className="w-48">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center text-muted-foreground py-8">
                      Loading...
                    </TableCell>
                  </TableRow>
                ) : successes.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center text-muted-foreground py-8">
                      No successful strategies recorded yet
                    </TableCell>
                  </TableRow>
                ) : (
                  successes.map((success, index) => (
                    <TableRow key={success.success_id}>
                      <TableCell className="font-mono text-sm">{index + 1}</TableCell>
                      <TableCell className="max-w-[250px] truncate">
                        {success.strategy_description}
                      </TableCell>
                      <TableCell>
                        <Badge variant="default">{success.agent_name}</Badge>
                      </TableCell>
                      <TableCell className="font-mono">
                        {Math.round(success.confidence * 100)}%
                      </TableCell>
                      <TableCell className="font-mono text-green-600">
                        {Math.round(success.success_rate * 100)}%
                      </TableCell>
                      <TableCell className="max-w-[150px] truncate">
                        {getContextString(success.context)}
                      </TableCell>
                      <TableCell className="font-mono">{success.reuse_count}</TableCell>
                      <TableCell>{success.ipo_symbol ?? "-"}</TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => router.push(`/successes/${success.success_id}`)}
                        >
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </Card>
      </div>
    </div>
  );
}
