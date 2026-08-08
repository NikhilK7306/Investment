"use client";

import IPOListScreen from "@/components/ipo-list-screen";

export default function IndianIPOsPage() {
  return (
    <IPOListScreen
      region="india"
      regionLabel="Indian"
      description="Discover and analyze upcoming Indian IPOs (NSE/BSE)"
      discoverSources={["investorgain"]}
    />
  );
}