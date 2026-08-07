"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Shield, User, Bell, Palette, Database, Key, Zap, ShieldAlert, Globe, Cpu, HardDrive, Save, Loader2, Plus, AlertTriangle, AlertCircle } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="space-y-6 max-w-4xl">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">Manage your account and application preferences</p>
        </div>

        <Tabs defaultValue="profile" className="space-y-4">
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="profile">Profile</TabsTrigger>
            <TabsTrigger value="account">Account</TabsTrigger>
            <TabsTrigger value="appearance">Appearance</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="api">API Keys</TabsTrigger>
            <TabsTrigger value="advanced">Advanced</TabsTrigger>
          </TabsList>

          <TabsContent value="profile" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4">
                  <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
                    <span className="text-2xl font-bold text-primary">AI</span>
                  </div>
                  <div>
                    <Button variant="outline" size="sm">Change Avatar</Button>
                    <p className="text-sm text-muted-foreground mt-1">JPG, PNG or GIF. Max 2MB.</p>
                  </div>
                </div>
                <Separator />
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="fullName">Full Name</Label>
                    <Input id="fullName" defaultValue="Alex Johnson" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" type="email" defaultValue="alex.johnson@company.com" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="role">Role</Label>
                    <Select defaultValue="analyst">
                      <SelectTrigger>
                        <SelectValue placeholder="Select role" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="analyst">Analyst</SelectItem>
                        <SelectItem value="senior_analyst">Senior Analyst</SelectItem>
                        <SelectItem value="portfolio_manager">Portfolio Manager</SelectItem>
                        <SelectItem value="admin">Administrator</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="department">Department</Label>
                    <Input id="department" defaultValue="Equity Research" />
                  </div>
                </div>
                <Separator />
                <div className="space-y-2">
                  <Label htmlFor="bio">Bio</Label>
                  <Input id="bio" defaultValue="Senior equity analyst specializing in tech IPOs and growth investing." />
                </div>
                <Button onClick={() => alert("Profile saved!")}>Save Changes</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Preferences</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Default Analysis Depth</p>
                    <p className="text-sm text-muted-foreground">Default depth for new analyses</p>
                  </div>
                  <Select defaultValue="standard">
                    <SelectTrigger className="w-[200px]">
                      <SelectValue placeholder="Select depth" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="standard">Standard</SelectItem>
                      <SelectItem value="deep">Deep</SelectItem>
                      <SelectItem value="comprehensive">Comprehensive</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Default Report Format</p>
                    <p className="text-sm text-muted-foreground">Format for generated reports</p>
                  </div>
                  <Select defaultValue="markdown">
                    <SelectTrigger className="w-[200px]">
                      <SelectValue placeholder="Select format" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="markdown">Markdown</SelectItem>
                      <SelectItem value="html">HTML</SelectItem>
                      <SelectItem value="pdf">PDF</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Auto-save analyses</p>
                    <p className="text-sm text-muted-foreground">Automatically save analysis progress</p>
                  </div>
                  <Switch defaultChecked />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="account" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Account Security</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <h4 className="font-medium">Change Password</h4>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="currentPassword">Current Password</Label>
                      <Input id="currentPassword" type="password" placeholder="Enter current password" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="newPassword">New Password</Label>
                      <Input id="newPassword" type="password" placeholder="Enter new password" />
                    </div>
                    <div className="space-y-2 md:col-span-2">
                      <Label htmlFor="confirmPassword">Confirm New Password</Label>
                      <Input id="confirmPassword" type="password" placeholder="Confirm new password" />
                    </div>
                  </div>
                  <Button onClick={() => alert("Password updated!")}>Update Password</Button>
                </div>

                <Separator />

                <div className="space-y-4">
                  <h4 className="font-medium">Two-Factor Authentication</h4>
                  <p className="text-sm text-muted-foreground">Add an extra layer of security to your account.</p>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Authenticator App</p>
                      <p className="text-sm text-muted-foreground">Use Google Authenticator, Authy, or similar</p>
                    </div>
                    <Button onClick={() => alert("2FA setup initiated")}>Enable 2FA</Button>
                  </div>
                </div>

                <Separator />

                <div className="space-y-4">
                  <h4 className="font-medium">Active Sessions</h4>
                  <p className="text-sm text-muted-foreground">Manage your active login sessions.</p>
                  <div className="space-y-3">
                    {[
                      { device: "Chrome on macOS", location: "San Francisco, CA", current: true, lastActive: "Now" },
                      { device: "Safari on iPhone", location: "San Francisco, CA", current: false, lastActive: "2 hours ago" },
                      { device: "Chrome on Windows", location: "New York, NY", current: false, lastActive: "1 day ago" },
                    ].map((session, i) => (
                      <div key={i} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                            <Cpu className="h-5 w-5 text-primary" />
                          </div>
                          <div>
                            <p className="font-medium">{session.device}</p>
                            <p className="text-sm text-muted-foreground">{session.location} · {session.lastActive}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {session.current && <Badge variant="success">Current</Badge>}
                          <Button variant="ghost" size="sm" onClick={() => alert("Session revoked")}>Revoke</Button>
                        </div>
                      </div>
                    ))}
                  </div>
                  <Button variant="outline" onClick={() => alert("All other sessions revoked")}>
                    Revoke All Other Sessions
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="appearance" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Theme</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  {[
                    { value: "light", label: "Light", icon: <span className="text-2xl">☀️</span> },
                    { value: "dark", label: "Dark", icon: <span className="text-2xl">🌙</span> },
                    { value: "system", label: "System", icon: <span className="text-2xl">💻</span> },
                  ].map((theme) => (
                    <button
                      key={theme.value}
                      className="relative aspect-square border-2 rounded-lg p-4 flex flex-col items-center justify-center gap-2 transition-all hover:border-primary/50"
                    >
                      {theme.icon}
                      <span className="font-medium">{theme.label}</span>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Language & Region</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="language">Language</Label>
                    <Select defaultValue="en">
                      <SelectTrigger>
                        <SelectValue placeholder="Select language" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="en">English</SelectItem>
                        <SelectItem value="es">Spanish</SelectItem>
                        <SelectItem value="fr">French</SelectItem>
                        <SelectItem value="de">German</SelectItem>
                        <SelectItem value="zh">Chinese</SelectItem>
                        <SelectItem value="ja">Japanese</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="timezone">Timezone</Label>
                    <Select defaultValue="America/Los_Angeles">
                      <SelectTrigger>
                        <SelectValue placeholder="Select timezone" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="America/Los_Angeles">Pacific Time (UTC-8)</SelectItem>
                        <SelectItem value="America/Denver">Mountain Time (UTC-7)</SelectItem>
                        <SelectItem value="America/Chicago">Central Time (UTC-6)</SelectItem>
                        <SelectItem value="America/New_York">Eastern Time (UTC-5)</SelectItem>
                        <SelectItem value="Europe/London">London (UTC+0)</SelectItem>
                        <SelectItem value="Europe/Paris">Paris (UTC+1)</SelectItem>
                        <SelectItem value="Asia/Tokyo">Tokyo (UTC+9)</SelectItem>
                        <SelectItem value="Asia/Shanghai">Shanghai (UTC+8)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="notifications" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Email Notifications</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {[
                  { label: "Analysis Complete", description: "When an analysis finishes", enabled: true },
                  { label: "New IPO Discovered", description: "New IPO matching your criteria", enabled: true },
                  { label: "Report Generated", description: "When a report is ready", enabled: true },
                  { label: "Risk Alert", description: "High-risk flag detected", enabled: true },
                  { label: "Weekly Digest", description: "Weekly summary of IPO activity", enabled: false },
                  { label: "System Updates", description: "Platform updates and maintenance", enabled: false },
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{item.label}</p>
                      <p className="text-sm text-muted-foreground">{item.description}</p>
                    </div>
                    <Switch defaultChecked={item.enabled} />
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>In-App Notifications</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {[
                  { label: "Analysis Complete", description: "Show toast when analysis completes", enabled: true },
                  { label: "Job Status Changes", description: "Background job status updates", enabled: true },
                  { label: "System Alerts", description: "Critical system notifications", enabled: true },
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{item.label}</p>
                      <p className="text-sm text-muted-foreground">{item.description}</p>
                    </div>
                    <Switch defaultChecked={item.enabled} />
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="api" className="space-y-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>API Keys</CardTitle>
                <Button><Plus className="h-4 w-4 mr-2" />Create New Key</Button>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">Manage your API keys for programmatic access to the IPO Intelligence API.</p>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Key Preview</TableHead>
                        <TableHead>Scopes</TableHead>
                        <TableHead>Last Used</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="w-24">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {[
                        { name: "Production API", key: "ipo_sk_live_...", scopes: "read:ipos,read:analyses,write:analyses", lastUsed: "2 hours ago", active: true },
                        { name: "Development", key: "ipo_sk_test_...", scopes: "read:ipos,read:analyses", lastUsed: "3 days ago", active: true },
                        { name: "Read-only Access", key: "ipo_sk_read_...", scopes: "read:ipos", lastUsed: "1 week ago", active: false },
                      ].map((key, i) => (
                        <TableRow key={i}>
                          <TableCell className="font-medium">{key.name}</TableCell>
                          <TableCell className="font-mono text-sm">{key.key}</TableCell>
                          <TableCell className="text-sm text-muted-foreground">{key.scopes}</TableCell>
                          <TableCell>{key.lastUsed}</TableCell>
                          <TableCell>
                            <Badge variant={key.active ? "success" : "secondary"}>{key.active ? "Active" : "Revoked"}</Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              <Button variant="ghost" size="icon" className="h-8 w-8"><AlertTriangle className="h-4 w-4" /></Button>
                              <Button variant="ghost" size="icon" className="h-8 w-8"><AlertCircle className="h-4 w-4" /></Button>
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

          <TabsContent value="advanced" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Data Management</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Data Retention</p>
                    <p className="text-sm text-muted-foreground">How long to keep analysis data</p>
                  </div>
                  <Select defaultValue="365">
                    <SelectTrigger className="w-[200px]">
                      <SelectValue placeholder="Select period" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="90">90 Days</SelectItem>
                      <SelectItem value="180">180 Days</SelectItem>
                      <SelectItem value="365">365 Days</SelectItem>
                      <SelectItem value="730">2 Years</SelectItem>
                      <SelectItem value="1825">5 Years</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Auto-cleanup Expired Data</p>
                    <p className="text-sm text-muted-foreground">Automatically remove expired short-term memory</p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Anonymize Old Data</p>
                    <p className="text-sm text-muted-foreground">Replace PII in data older than retention period</p>
                  </div>
                  <Switch />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Parallel Analysis Limit</p>
                    <p className="text-sm text-muted-foreground">Max concurrent analyses</p>
                  </div>
                  <Select defaultValue="4">
                    <SelectTrigger className="w-[100px]">
                      <SelectValue placeholder="Select limit" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1</SelectItem>
                      <SelectItem value="2">2</SelectItem>
                      <SelectItem value="4">4</SelectItem>
                      <SelectItem value="8">8</SelectItem>
                      <SelectItem value="16">16</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Cache TTL</p>
                    <p className="text-sm text-muted-foreground">Time-to-live for cached results</p>
                  </div>
                  <Select defaultValue="3600">
                    <SelectTrigger className="w-[150px]">
                      <SelectValue placeholder="Select TTL" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="300">5 Minutes</SelectItem>
                      <SelectItem value="900">15 Minutes</SelectItem>
                      <SelectItem value="1800">30 Minutes</SelectItem>
                      <SelectItem value="3600">1 Hour</SelectItem>
                      <SelectItem value="7200">2 Hours</SelectItem>
                      <SelectItem value="86400">24 Hours</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Enable Query Caching</p>
                    <p className="text-sm text-muted-foreground">Cache database query results</p>
                  </div>
                  <Switch defaultChecked />
                </div>
              </CardContent>
            </Card>

            <Card className="border-red-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-red-500" />Danger Zone</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 border border-red-200 rounded-lg bg-red-50">
                  <p className="font-medium text-red-700">These actions are irreversible. Proceed with caution.</p>
                </div>
                <div className="grid gap-4 md:grid-cols-3">
                  <Card className="border-red-200">
                    <CardHeader>
                      <CardTitle className="text-red-600">Delete All Data</CardTitle>
                      <CardDescription>Permanently delete all your analyses, reports, and settings</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button variant="destructive" className="w-full">Delete All Data</Button>
                    </CardContent>
                  </Card>
                  <Card className="border-red-200">
                    <CardHeader>
                      <CardTitle className="text-red-600">Reset Account</CardTitle>
                      <CardDescription>Reset to default settings, keep data</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button variant="destructive" className="w-full">Reset Account</Button>
                    </CardContent>
                  </Card>
                  <Card className="border-red-200">
                    <CardHeader>
                      <CardTitle className="text-red-600">Delete Account</CardTitle>
                      <CardDescription>Permanently delete your account and all data</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button variant="destructive" className="w-full">Delete Account</Button>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}