"use client"

import { useState } from "react"
import { useReactFlow } from "reactflow"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { 
  PanelLeft, 
  Sparkles, 
  Play, 
  Webhook, 
  Link, 
  Settings, 
  GitBranch, 
  Clock, 
  Square,
  LucideIcon 
} from "lucide-react"
import { useFlowStore } from "@/stores/flowStore"
import { nodeCategories } from "./nodes/nodeTypes"
import { cn } from "@/lib/utils"

const iconMap: Record<string, LucideIcon> = {
  start: Play,
  webhook: Webhook,
  connector: Link,
  transform: Settings,
  condition: GitBranch,
  delay: Clock,
  end: Square,
}

export function Sidebar() {
  const { addNodes } = useReactFlow()
  const { sidebarOpen, toggleSidebar, isDesignMode, designGoal, setDesignGoal, startAIDesign, isDesigning } = useFlowStore()
  const [activeTab, setActiveTab] = useState<"nodes" | "ai">("nodes")

  const onDragStart = (event: React.DragEvent, nodeType: string, label: string) => {
    event.dataTransfer.setData("application/reactflow", JSON.stringify({
      type: nodeType,
      label,
      data: { type: nodeType, label }
    }))
    event.dataTransfer.effectAllowed = "move"
  }

  const handleAIDesign = async () => {
    if (!designGoal.trim()) return
    
    startAIDesign()
    // TODO: Call AI design API
    console.log("Starting AI design with goal:", designGoal)
  }

  if (!sidebarOpen) {
    return (
      <div className="border-r bg-background">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="h-12 w-12"
        >
          <PanelLeft className="h-4 w-4" />
        </Button>
      </div>
    )
  }

  return (
    <div className="w-80 border-r bg-background flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="text-lg font-semibold">Flow Builder</h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
        >
          <PanelLeft className="h-4 w-4" />
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex border-b">
        <button
          onClick={() => setActiveTab("nodes")}
          className={cn(
            "flex-1 px-4 py-2 text-sm font-medium transition-colors",
            activeTab === "nodes" 
              ? "border-b-2 border-primary text-primary" 
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          Nodes
        </button>
        <button
          onClick={() => setActiveTab("ai")}
          className={cn(
            "flex-1 px-4 py-2 text-sm font-medium transition-colors",
            activeTab === "ai" 
              ? "border-b-2 border-primary text-primary" 
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <Sparkles className="w-4 h-4 inline mr-1" />
          AI Design
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === "nodes" ? (
          <div className="space-y-4">
            {Object.entries(nodeCategories).map(([category, nodes]) => (
              <div key={category}>
                <h3 className="text-sm font-medium text-muted-foreground mb-2 capitalize">
                  {category}
                </h3>
                <div className="space-y-2">
                  {nodes.map((node) => {
                    const Icon = iconMap[node.type]
                    return (
                      <div
                        key={node.type}
                        draggable
                        onDragStart={(e) => onDragStart(e, node.type, node.label)}
                        className="flex items-center gap-2 p-2 rounded border bg-card hover:bg-accent cursor-grab active:cursor-grabbing transition-colors"
                      >
                        <div className={cn("p-1 rounded", `bg-${node.color}-500`)}>
                          <Icon className="w-4 h-4 text-white" />
                        </div>
                        <span className="text-sm">{node.label}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">AI-Powered Design</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Describe your workflow goal
                  </label>
                  <textarea
                    value={designGoal}
                    onChange={(e) => setDesignGoal(e.target.value)}
                    placeholder="e.g., Create a workflow that fetches weather data and sends notifications when it rains"
                    className="w-full p-2 border rounded-md text-sm resize-none"
                    rows={4}
                  />
                </div>
                <Button
                  onClick={handleAIDesign}
                  disabled={!designGoal.trim() || isDesigning}
                  className="w-full"
                >
                  {isDesigning ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                      Designing...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Design Workflow
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Recent Designs</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground">
                  No recent designs yet
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
