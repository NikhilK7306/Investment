"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Brain, Search, Filter, Calendar, Building2, TrendingUp, ArrowUp, ArrowDown, Minus, Plus, FileText, BarChart2, ExternalLink } from "lucide-react";
import Link from "next/link";
import { ipoService } from "@/services/ipoService";
import type { IPOResponse } from "@/types/ipo";

const statusColors: Record<string, string> = {
  ANNOUNCED: "outline",
  FILED: "default",
  PRICED: "success",
  LISTED: "success",
  WITHDRAWN: "destructive",
  POSTPONED: "secondary",
};

export default function IPOsPage() {
  const router = useRouter();
  const [ipos, setIpos] = useState<IPOResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState("date");

  const fetchIPOs = async () => {
    setLoading(true);
    try {
      const data = await ipoService.listUpcoming({ limit: 100 });
      setIpos(data);
    } catch (err) {
      console.error("Failed to fetch IPOs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIPOs();
  }, []);

  const filtered = useMemo(() => {
    let result = [...ipos];

    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (ipo) =>
          ipo.symbol.toLowerCase().includes(q) ||
          ipo.company_name.toLowerCase().includes(q)
      );
    }

    if (statusFilter !== "all") {
      result = result.filter((ipo) => ipo.status === statusFilter);
    }

    result.sort((a, b) => {
      switch (sortBy) {
        case "date":
          return (a.expected_date || "").localeCompare(b.expected_date || "");
        case "name":
          return a.company_name.localeCompare(b.company_name);
        default:
          return 0;
      }
    });

    return result;
  }, [ipos, search, statusFilter, sortBy]);

  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Upcoming IPOs</h1>
            <p className="text-muted-foreground">Discover and analyze upcoming initial public offerings</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={fetchIPOs} disabled={loading}>
              <Calendar className="h-4 w-4 mr-2" />
              {loading ? "Loading..." : "Refresh"}
            </Button>
            <Button variant="outline" size="sm" onClick={() => router.push("/ipos")}>
              <Building2 className="h-4 w-4 mr-2" />
              All Exchanges
            </Button>
            <Button size="sm" onClick={() => router.push("/ipos")}>
              <Plus className="h-4 w-4 mr-2" />
              Add IPO
            </Button>
          </div>
        </div>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-lg">IPO Pipeline ({filtered.length} companies)</CardTitle>
            <div className="flex gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search IPOs..."
                  className="pl-10 w-64"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="ANNOUNCED">Announced</SelectItem>
                  <SelectItem value="FILED">Filed</SelectItem>
                  <SelectItem value="PRICED">Priced</SelectItem>
                  <SelectItem value="LISTED">Listed</SelectItem>
                </SelectContent>
              </Select>
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="date">Expected Date</SelectItem>
                  <SelectItem value="name">Company Name</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">Score</TableHead>
                    <TableHead>Company</TableHead>
                    <TableHead>Exchange</TableHead>
                    <TableHead>Sector</TableHead>
                    <TableHead>Expected Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Price Range</TableHead>
                    <TableHead className="w-32">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading && (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center text-muted-foreground py-8">
                        Loading IPOs...
                      </TableCell>
                    </TableRow>
                  )}
                  {!loading && filtered.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center text-muted-foreground py-8">
                        No IPOs found.
                      </TableCell>
                    </TableRow>
                  )}
                  {filtered.map((ipo) => (
                    <TableRow key={ipo.symbol} className="hover:bg-accent/50 cursor-pointer">
                      <TableCell>
                        <div className="flex items-center justify-center">
                          <Link href={`/ipos/${ipo.symbol}`}>
                            <span className={cn(
                              "font-bold px-2 py-1 rounded text-sm",
                              "bg-green-100 text-green-700",
                            )}>
                              --
                            </span>
                          </Link>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Link href={`/ipos/${ipo.symbol}`} className="hover:underline">
                          <div>
                            <p className="font-medium">{ipo.symbol}</p>
                            <p className="text-sm text-muted-foreground">{ipo.company_name}</p>
                          </div>
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs">{ipo.exchange}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="text-xs">{ipo.sector}</Badge>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm">
                          {ipo.expected_date ? new Date(ipo.expected_date).toLocaleDateString() : "TBD"}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge variant={(statusColors[ipo.status] || "default") as "default" | "outline" | "success" | "destructive" | "secondary"}>
                          {ipo.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm font-medium">
                          {ipo.price_range
                            ? `$${ipo.price_range.low}-${ipo.price_range.high}`
                            : "N/A"}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Link href={`/ipos/${ipo.symbol}`}>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <ExternalLink className="h-4 w-4" />
                            </Button>
                          </Link>
                          <Link href={`/analysis?symbol=${ipo.symbol}`}>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <BarChart2 className="h-4 w-4" />
                            </Button>
                          </Link>
                          <Link href={`/reports/${ipo.symbol}`}>
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
      </div>
    </div>
  );
}
