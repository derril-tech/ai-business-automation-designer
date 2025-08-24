"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { 
  Save, 
  Play, 
  Square, 
  Download, 
  Upload, 
  Settings, 
  Eye,
  EyeOff,
  Sparkles,
  History,
  TestTube,
  Zap
} from "lucide-react"
import { useFlowStore } from "@/stores/flowStore"

export function Toolbar() {
  const { 
    isDesignMode, 
    toggleDesignMode, 
    isExecuting, 
    executionId,
    currentWorkflow,
    rightPanel,
    setRightPanel
  } = useFlowStore()

  const handleSave = () => {
    // TODO: Save workflow
    console.log("Saving workflow...")
  }

  const handleExecute = () => {
    // TODO: Execute workflow
    console.log("Executing workflow...")
  }

  const handleStop = () => {
    // TODO: Stop execution
    console.log("Stopping execution...")
  }

  const handleExport = () => {
    // TODO: Export workflow
    console.log("Exporting workflow...")
  }

  const handleImport = () => {
    // TODO: Import workflow
    console.log("Importing workflow...")
  }

  return (
    <div className="border-b bg-background px-4 py-2">
      <div className="flex items-center justify-between">
        {/* Left side - Workflow info */}
        <div className="flex items-center gap-4">
          <div>
            <h1 className="text-lg font-semibold">
              {currentWorkflow?.name || "Untitled Workflow"}
            </h1>
            {currentWorkflow?.description && (
              <p className="text-sm text-muted-foreground">
                {currentWorkflow.description}
              </p>
            )}
          </div>
          
          {executionId && (
            <Badge variant="secondary">
              Execution: {executionId.slice(0, 8)}...
            </Badge>
          )}
        </div>

        {/* Center - Mode toggle */}
        <div className="flex items-center gap-2">
          <Button
            variant={isDesignMode ? "default" : "outline"}
            size="sm"
            onClick={toggleDesignMode}
          >
            <Eye className="w-4 h-4 mr-2" />
            Design Mode
          </Button>
          <Button
            variant={!isDesignMode ? "default" : "outline"}
            size="sm"
            onClick={toggleDesignMode}
          >
            <EyeOff className="w-4 h-4 mr-2" />
            Execution Mode
          </Button>
        </div>

        {/* Right side - Actions */}
        <div className="flex items-center gap-2">
          {/* Panel Toggles */}
          <Button
            variant={rightPanel === "node" ? "default" : "outline"}
            size="sm"
            onClick={() => setRightPanel("node")}
          >
            <Settings className="w-4 h-4 mr-2" />
            Properties
          </Button>
          <Button
            variant={rightPanel === "simulation" ? "default" : "outline"}
            size="sm"
            onClick={() => setRightPanel("simulation")}
          >
            <Zap className="w-4 h-4 mr-2" />
            Simulation
          </Button>
          <Button
            variant={rightPanel === "testing" ? "default" : "outline"}
            size="sm"
            onClick={() => setRightPanel("testing")}
          >
            <TestTube className="w-4 h-4 mr-2" />
            Testing
          </Button>

          {/* AI Design */}
          <Button variant="outline" size="sm">
            <Sparkles className="w-4 h-4 mr-2" />
            AI Design
          </Button>

          {/* History */}
          <Button variant="outline" size="sm">
            <History className="w-4 h-4 mr-2" />
            History
          </Button>

          {/* Import/Export */}
          <Button variant="outline" size="sm" onClick={handleImport}>
            <Upload className="w-4 h-4 mr-2" />
            Import
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>

          {/* Settings */}
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4" />
          </Button>

          {/* Save */}
          <Button variant="outline" size="sm" onClick={handleSave}>
            <Save className="w-4 h-4 mr-2" />
            Save
          </Button>

          {/* Execute/Stop */}
          {isExecuting ? (
            <Button variant="destructive" size="sm" onClick={handleStop}>
              <Square className="w-4 h-4 mr-2" />
              Stop
            </Button>
          ) : (
            <Button variant="default" size="sm" onClick={handleExecute}>
              <Play className="w-4 h-4 mr-2" />
              Execute
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
