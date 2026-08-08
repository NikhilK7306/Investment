"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Search, Calendar, RefreshCw, ExternalLink, BarChart2, FileText, Rocket } from "lucide-react";
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

type Phase = "upcoming" | "current" | "listed";

const PHASE_LABELS: Record<Phase, string> = {
  upcoming: "Upcoming",
  current: "Current",
  listed: "Listed",
};

export default function IPOListScreen({
  region,
  regionLabel,
  description,
  discoverSources,
}: {
  region: "india" | "foreign";
  regionLabel: string;
  description: string;
  discoverSources: string[];
}) {
  const router = useRouter();
  const [byPhase, setByPhase] = useState<Record<Phase, IPOResponse[]>>({
    upcoming: [],
    current: [],
    listed: [],
  });
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [phase, setPhase] = useState<Phase>("upcoming");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("date");

  const dedupe = (items: IPOResponse[]): IPOResponse[] => {
    const seen = new Set<string>();
    const out: IPOResponse[] = [];
    for (const item of items) {
      if (!seen.has(item.symbol)) {
        seen.add(item.symbol);
        out.push(item);
      }
    }
    return out;
  };

  const fetchPhase = useCallback(
    async (p: Phase): Promise<IPOResponse[]> => {
      const data = await ipoService.listUpcoming({ limit: 200, region, phase: p });
      return dedupe(data);
    },
    [region]
  );

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [upcoming, current, listed] = await Promise.all([
        fetchPhase("upcoming"),
        fetchPhase("current"),
        fetchPhase("listed"),
      ]);
      setByPhase({ upcoming, current, listed });
    } catch (err) {
      console.error("Failed to fetch IPOs:", err);
    } finally {
      setLoading(false);
    }
  }, [fetchPhase]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const discover = async () => {
    setDiscovering(true);
    try {
      await ipoService.discover({ lookahead_days: 120, sources: discoverSources });
      await fetchAll();
    } catch (err) {
      console.error("Discovery failed:", err);
    } finally {
      setDiscovering(false);
    }
  };

  const filtered = useMemo(() => {
    let result = [...byPhase[phase]];
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (ipo) =>
          ipo.symbol.toLowerCase().includes(q) ||
          ipo.company_name.toLowerCase().includes(q)
      );
    }
    result.sort((a, b) => {
      if (sortBy === "name") return a.company_name.localeCompare(b.company_name);
      return (a.expected_date || "9999").localeCompare(b.expected_date || "9999");
    });
    return result;
  }, [byPhase, phase, search, sortBy]);

  const totals = useMemo(
    () => ({
      upcoming: byPhase.upcoming.length,
      current: byPhase.current.length,
      listed: byPhase.listed.length,
    }),
    [byPhase]
  );

  const currencySymbol = (exchange: string) =>
    exchange === "NSE" || exchange === "BSE" ? "₹" : "$";

  const formatPrice = (ipo: IPOResponse): string => {
    if (!ipo.price_range || ipo.price_range.low === undefined) return "N/A";
    const sym = currencySymbol(ipo.exchange);
    const { low, high } = ipo.price_range;
    if (low === high) return `${sym}${low}`;
    return `${sym}${low} - ${sym}${high}`;
  };

  const isIndia = region === "india";
  const accent = isIndia
    ? "from-orange-500/20 via-amber-500/10 to-transparent"
    : "from-sky-500/20 via-indigo-500/10 to-transparent";
  const accentText = isIndia ? "text-orange-600" : "text-indigo-600";
  const regionTag = isIndia ? "NSE · BSE" : "NASDAQ · NYSE · US";
  const tagStyles = isIndia
    ? "border-orange-500/40 bg-orange-500/10 text-orange-600"
    : "border-sky-500/40 bg-sky-500/10 text-sky-600";

  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6">
        <div className={`rounded-xl bg-gradient-to-r ${accent} border p-6`}>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold tracking-tight">{regionLabel} IPOs</h1>
                <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${tagStyles}`}>
                  {regionTag}
                </span>
              </div>
              <p className={accentText}>{description}</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={discover} disabled={discovering}>
                <Rocket className={`h-4 w-4 mr-2 ${discovering ? "animate-pulse" : ""}`} />
                {discovering ? "Discovering..." : "Discover"}
              </Button>
              <Button variant="outline" size="sm" onClick={fetchAll} disabled={loading}>
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
                {loading ? "Loading..." : "Refresh"}
              </Button>
            </div>
          </div>
        </div>

        <Tabs value={phase} onValueChange={(v) => setPhase(v as Phase)}>
          <TabsList className="grid w-full max-w-md grid-cols-3">
            <TabsTrigger value="upcoming">
              <Calendar className="h-4 w-4 mr-2" />
              Upcoming ({totals.upcoming})
            </TabsTrigger>
            <TabsTrigger value="current">
              <span className="inline-flex h-2 w-2 rounded-full bg-green-500 mr-2 animate-pulse" />
              Current ({totals.current})
            </TabsTrigger>
            <TabsTrigger value="listed">
              <BarChart2 className="h-4 w-4 mr-2" />
              Listed ({totals.listed})
            </TabsTrigger>
          </TabsList>

          {(["upcoming", "current", "listed"] as Phase[]).map((p) => (
            <TabsContent key={p} value={p} className="space-y-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-lg">
                    {PHASE_LABELS[p]} {regionLabel} IPOs ({filtered.length} listed)
                  </CardTitle>
                  <div className="flex gap-2">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Search IPOs..."
                        className="pl-10 w-56"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                      />
                    </div>
                    <Select value={sortBy} onValueChange={setSortBy}>
                      <SelectTrigger className="w-[160px]">
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
                          <TableHead>Company</TableHead>
                          <TableHead>Exchange</TableHead>
                          <TableHead>Sector</TableHead>
                          <TableHead>Expected Date</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Price</TableHead>
                          <TableHead className="w-32">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {loading && (
                          <TableRow>
                            <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                              Loading IPOs...
                            </TableCell>
                          </TableRow>
                        )}
                        {!loading && filtered.length === 0 && (
                          <TableRow>
                            <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                              No {PHASE_LABELS[p].toLowerCase()} IPOs found.
                              {region === "foreign" && p === "upcoming" && " Run Discover to fetch the latest offerings."}
                            </TableCell>
                          </TableRow>
                        )}
                        {filtered.map((ipo) => (
                          <TableRow key={ipo.symbol} className="hover:bg-accent/50 cursor-pointer">
                            <TableCell onClick={() => router.push(`/ipos/${ipo.symbol}`)}>
                              <div>
                                <p className="font-medium">{ipo.symbol}</p>
                                <p className="text-sm text-muted-foreground">{ipo.company_name}</p>
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className="text-xs">{ipo.exchange}</Badge>
                            </TableCell>
                            <TableCell>
                              <Badge variant="secondary" className="text-xs">{ipo.sector || "N/A"}</Badge>
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
                              <span className="text-sm font-medium">{formatPrice(ipo)}</span>
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
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </div>
  );
}