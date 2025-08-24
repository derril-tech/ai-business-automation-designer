"use client"

import { useState } from "react"
import { Node } from "reactflow"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { X, Settings, Code, Database, Globe } from "lucide-react"
import { cn } from "@/lib/utils"

interface NodePanelProps {
  node: Node
  onClose: () => void
}

export function NodePanel({ node, onClose }: NodePanelProps) {
  const [activeTab, setActiveTab] = useState<"general" | "config" | "inputs" | "outputs">("general")

  const tabs = [
    { id: "general", label: "General", icon: Settings },
    { id: "config", label: "Config", icon: Code },
    { id: "inputs", label: "Inputs", icon: Database },
    { id: "outputs", label: "Outputs", icon: Globe },
  ]

  const getNodeTypeColor = (type: string) => {
    const colorMap: Record<string, string> = {
      start: "bg-green-500",
      webhook: "bg-blue-500",
      connector: "bg-purple-500",
      transform: "bg-orange-500",
      condition: "bg-yellow-500",
      delay: "bg-gray-500",
      end: "bg-red-500",
    }
    return colorMap[type] || "bg-gray-500"
  }

  return (
    <div className="w-80 border-l bg-background flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-2">
          <div className={cn("w-3 h-3 rounded-full", getNodeTypeColor(node.data.type))} />
          <h2 className="text-lg font-semibold">Node Properties</h2>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex border-b">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={cn(
                "flex-1 px-3 py-2 text-xs font-medium transition-colors flex items-center justify-center gap-1",
                activeTab === tab.id 
                  ? "border-b-2 border-primary text-primary" 
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Icon className="w-3 h-3" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === "general" && (
          <div className="space-y-4">
            <div>
              <Label htmlFor="node-name">Name</Label>
              <Input
                id="node-name"
                value={node.data.label || ""}
                onChange={(e) => {
                  // TODO: Update node label
                  console.log("Update node label:", e.target.value)
                }}
                placeholder="Enter node name"
              />
            </div>

            <div>
              <Label htmlFor="node-description">Description</Label>
              <Textarea
                id="node-description"
                value={node.data.description || ""}
                onChange={(e) => {
                  // TODO: Update node description
                  console.log("Update node description:", e.target.value)
                }}
                placeholder="Enter node description"
                rows={3}
              />
            </div>

            <div>
              <Label>Type</Label>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="outline">{node.data.type}</Badge>
              </div>
            </div>

            <div>
              <Label>Status</Label>
              <div className="flex items-center gap-2 mt-1">
                <Badge 
                  variant={
                    node.data.status === "completed" ? "default" :
                    node.data.status === "running" ? "secondary" :
                    node.data.status === "failed" ? "destructive" :
                    "outline"
                  }
                >
                  {node.data.status || "pending"}
                </Badge>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="node-enabled">Enabled</Label>
              <Switch
                id="node-enabled"
                checked={node.data.enabled !== false}
                onCheckedChange={(checked) => {
                  // TODO: Update node enabled state
                  console.log("Update node enabled:", checked)
                }}
              />
            </div>
          </div>
        )}

        {activeTab === "config" && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Configuration</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="text-xs bg-muted p-2 rounded overflow-auto">
                  {JSON.stringify(node.data.config || {}, null, 2)}
                </pre>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "inputs" && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Input Variables</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="text-xs bg-muted p-2 rounded overflow-auto">
                  {JSON.stringify(node.data.inputs || {}, null, 2)}
                </pre>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "outputs" && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Output Variables</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="text-xs bg-muted p-2 rounded overflow-auto">
                  {JSON.stringify(node.data.outputs || {}, null, 2)}
                </pre>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
