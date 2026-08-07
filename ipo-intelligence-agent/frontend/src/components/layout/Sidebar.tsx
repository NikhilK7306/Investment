"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Calendar,
  FileText,
  BarChart2,
  Brain,
  AlertTriangle,
  CheckCircle,
  BookOpen,
  Settings,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
  Sun,
  Moon,
  Search,
  Bell,
  User,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "next-themes";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Upcoming IPOs", href: "/ipos", icon: Calendar },
  { name: "Analysis", href: "/analysis", icon: BarChart2 },
  { name: "Reports", href: "/reports", icon: FileText },
  { name: "Memory", href: "/memory", icon: Brain },
  { name: "Reflection", href: "/reflection", icon: AlertTriangle },
  { name: "Failures", href: "/failures", icon: AlertTriangle },
  { name: "Successes", href: "/successes", icon: CheckCircle },
  { name: "Knowledge", href: "/knowledge", icon: BookOpen },
  { name: "Chat", href: "/chat", icon: MessageSquare },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 h-screen bg-card border-r border-border transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div
          className={cn(
            "flex h-16 items-center justify-between px-4 border-b border-border",
            collapsed && "justify-center"
          )}
        >
          {!collapsed && (
            <Link href="/dashboard" className="flex items-center gap-2 font-bold text-lg">
              <BarChart2 className="h-6 w-6 text-primary" />
              <span>IPO Intelligence</span>
            </Link>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-2 rounded-md hover:bg-accent transition-colors"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                  collapsed && "justify-center"
                )}
                title={collapsed ? item.name : undefined}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" />
                {!collapsed && <span>{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Theme Toggle & User */}
        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="p-2 rounded-md hover:bg-accent transition-colors"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>
            {!collapsed && (
              <div className="flex-1">
                <div className="flex items-center gap-2 px-2 py-1">
                  <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
                    <User className="h-4 w-4 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">Analyst</p>
                    <p className="text-xs text-muted-foreground truncate">analyst@ipo.ai</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}

export function Header() {
  const { theme, setTheme } = useTheme();
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <header className="sticky top-0 z-30 h-16 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
      <div className="flex h-full items-center justify-between px-4">
        <div className="flex-1 max-w-md">
          <input
            type="search"
            placeholder="Search IPOs, companies, reports..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-9 px-3 rounded-md bg-accent border-0 placeholder:text-muted-foreground focus:ring-2 focus:ring-ring transition-colors"
          />
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="p-2 rounded-md hover:bg-accent transition-colors"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>
          <button className="relative p-2 rounded-md hover:bg-accent transition-colors">
            <Bell className="h-5 w-5" />
            <span className="absolute top-1 right-1 h-4 w-4 rounded-full bg-red-500 text-xs text-white flex items-center justify-center">
              3
            </span>
          </button>
          <div className="h-8 w-px bg-border mx-2" />
          <button className="p-2 rounded-md hover:bg-accent transition-colors">
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  );
}