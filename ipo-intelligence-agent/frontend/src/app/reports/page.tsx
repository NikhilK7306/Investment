"use client";

import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { TrendingUp, TrendingDown, Minus, CheckCircle, AlertTriangle, Target, Shield, Brain, FileText, Sparkles, AlertCircle, ExternalLink } from "lucide-react";
import Link from "next/link";

const mockReports = [
  { symbol: "TECH", name: "TechCorp Inc", date: "2024-01-15", score: 85, recommendation: "BUY", status: "COMPLETED" },
  { symbol: "BIOX", name: "BioTech Solutions", date: "2024-01-14", score: 72, recommendation: "ACCUMULATE", status: "COMPLETED" },
  { symbol: "FINV", name: "FinVest Holdings", date: "2024-01-13", score: 68, recommendation: "WATCH", status: "COMPLETED" },
  { symbol: "GREN", name: "GreenEnergy Corp", date: "2024-01-12", score: 79, recommendation: "BUY", status: "COMPLETED" },
  { symbol: "AILA", name: "AI Labs America", date: "2024-01-11", score: 88, recommendation: "AGGRESSIVE_BUY", status: "COMPLETED" },
];

export default function ReportsPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Investment Reports</h1>
            <p className="text-muted-foreground">View and manage generated investment research reports</p>
          </div>
          <Button>
            <Brain className="h-4 w-4 mr-2" />
            Generate New Report
          </Button>
        </div>

        <Tabs defaultValue="reports" className="space-y-4">
          <TabsList>
            <TabsTrigger value="reports">All Reports ({mockReports.length})</TabsTrigger>
            <TabsTrigger value="templates">Templates</TabsTrigger>
          </TabsList>

          <TabsContent value="reports" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle>Completed Reports</CardTitle>
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
                        <TableHead>Status</TableHead>
                        <TableHead className="w-48">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {mockReports.map((report, index) => (
                        <TableRow key={index} className="hover:bg-accent/50 cursor-pointer">
                          <TableCell>
                            <Link href={`/reports/${report.symbol}`}>
                              <div>
                                <p className="font-medium">{report.symbol}</p>
                                <p className="text-sm text-muted-foreground">{report.name}</p>
                              </div>
                            </Link>
                          </TableCell>
                          <TableCell>{report.date}</TableCell>
                          <TableCell>
                            <span className={cn(
                              "font-bold px-2 py-1 rounded text-sm",
                              report.score >= 80 ? "bg-green-100 text-green-700" :
                              report.score >= 70 ? "bg-blue-100 text-blue-700" :
                              report.score >= 60 ? "bg-yellow-100 text-yellow-700" :
                              "bg-red-100 text-red-700"
                            )}>
                              {report.score}
                            </span>
                          </TableCell>
                          <TableCell>
                            <Badge variant={report.recommendation === "BUY" || report.recommendation === "AGGRESSIVE_BUY" ? "success" :
                              report.recommendation === "ACCUMULATE" ? "default" :
                              report.recommendation === "WATCH" ? "secondary" : "outline"}>
                              {report.recommendation}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant="success">{report.status}</Badge>
                          </TableCell>
                          <TableCell>
                            <Link href={`/reports/${report.symbol}`}>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <ExternalLink className="h-4 w-4" />
                              </Button>
                            </Link>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="templates" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[
                { name: "Standard IPO Report", sections: 12, description: "Full analysis report with all sections" },
                { name: "Executive Summary", sections: 3, description: "Condensed report for quick review" },
                { name: "Risk Focus", sections: 5, description: "Detailed risk assessment report" },
                { name: "Valuation Deep Dive", sections: 6, description: "Comprehensive valuation analysis" },
              ].map((template, i) => (
                <Card key={i} className="hover:border-primary/50 transition-colors">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5 text-blue-500" />
                      {template.name}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="text-sm text-muted-foreground">{template.description}</p>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>{template.sections} sections</span>
                    </div>
                    <Button className="w-full">Use Template</Button>
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