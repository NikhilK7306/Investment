"use client";

import IPOListScreen from "@/components/ipo-list-screen";

export default function ForeignIPOsPage() {
  return (
    <IPOListScreen
      region="foreign"
      regionLabel="Foreign"
      description="Discover and analyze international IPOs (NASDAQ, NYSE, LSE, and more)"
      discoverSources={["nasdaq", "nyse", "sec", "renaissance"]}
    />
  );
}