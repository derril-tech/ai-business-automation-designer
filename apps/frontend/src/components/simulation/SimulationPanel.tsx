"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Play, Square, RotateCcw, Eye, AlertTriangle, CheckCircle, Clock, XCircle } from "lucide-react"
import { useFlowStore } from "@/stores/flowStore"

interface SimulationStep {
  step_id: string
  step_type: string
  name: string
  status: string
  start_time?: string
  end_time?: string
  duration_ms?: number
  inputs: Record<string, any>
  outputs: Record<string, any>
  error?: string
  mock_data_used: Record<string, any>
}

interface SimulationResult {
  simulation_id: string
  workflow_id: string
  workflow_name: string
  status: string
  start_time: string
  end_time?: string
  duration_ms?: number
  steps: SimulationStep[]
  variables: Record<string, any>
  mock_data_config: Record<string, any>
  validation_errors: string[]
  execution_path: string[]
  performance_metrics: Record<string, any>
}

export function SimulationPanel() {
  const { currentWorkflow } = useFlowStore()
  const [isSimulating, setIsSimulating] = useState(false)
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null)
  const [config, setConfig] = useState({
    useMockData: true,
    enableValidation: true,
    stopOnError: true,
    dryRun: false,
    stepTimeout: 30,
    maxSteps: 100
  })
  const [initialVariables, setInitialVariables] = useState("")
  const [mockDataConfig, setMockDataConfig] = useState("")

  const startSimulation = async () => {
    if (!currentWorkflow) return

    setIsSimulating(true)
    try {
      // In a real implementation, this would call the simulation API
      const response = await fetch("/api/simulation/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workflow_id: currentWorkflow.id,
          config: {
            use_mock_data: config.useMockData,
            enable_validation: config.enableValidation,
            stop_on_error: config.stopOnError,
            dry_run: config.dryRun,
            step_timeout_seconds: config.stepTimeout,
            max_steps: config.maxSteps
          },
          initial_variables: initialVariables ? JSON.parse(initialVariables) : undefined,
          mock_data_config: mockDataConfig ? JSON.parse(mockDataConfig) : undefined
        })
      })

      if (response.ok) {
        const result = await response.json()
        setSimulationResult(result)
      } else {
        console.error("Simulation failed:", await response.text())
      }
    } catch (error) {
      console.error("Simulation error:", error)
    } finally {
      setIsSimulating(false)
    }
  }

  const cancelSimulation = async () => {
    if (!simulationResult) return

    try {
      await fetch(`/api/simulation/simulate/${simulationResult.simulation_id}/cancel`, {
        method: "POST"
      })
      // Refresh simulation status
    } catch (error) {
      console.error("Cancel error:", error)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "failed":
        return <XCircle className="w-4 h-4 text-red-500" />
      case "running":
        return <Clock className="w-4 h-4 text-blue-500" />
      case "pending":
        return <Clock className="w-4 h-4 text-gray-400" />
      default:
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800"
      case "failed":
        return "bg-red-100 text-red-800"
      case "running":
        return "bg-blue-100 text-blue-800"
      case "pending":
        return "bg-gray-100 text-gray-800"
      default:
        return "bg-yellow-100 text-yellow-800"
    }
  }

  return (
    <div className="h-full flex flex-col space-y-4 p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Simulation</h2>
        <div className="flex space-x-2">
          <Button
            size="sm"
            onClick={startSimulation}
            disabled={isSimulating || !currentWorkflow}
            className="flex items-center space-x-1"
          >
            <Play className="w-4 h-4" />
            <span>Start</span>
          </Button>
          {isSimulating && (
            <Button
              size="sm"
              variant="outline"
              onClick={cancelSimulation}
              className="flex items-center space-x-1"
            >
              <Square className="w-4 h-4" />
              <span>Cancel</span>
            </Button>
          )}
        </div>
      </div>

      <Separator />

      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-2">
            <Switch
              id="useMockData"
              checked={config.useMockData}
              onCheckedChange={(checked) => setConfig({ ...config, useMockData: checked })}
            />
            <Label htmlFor="useMockData">Use Mock Data</Label>
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="enableValidation"
              checked={config.enableValidation}
              onCheckedChange={(checked) => setConfig({ ...config, enableValidation: checked })}
            />
            <Label htmlFor="enableValidation">Enable Validation</Label>
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="stopOnError"
              checked={config.stopOnError}
              onCheckedChange={(checked) => setConfig({ ...config, stopOnError: checked })}
            />
            <Label htmlFor="stopOnError">Stop on Error</Label>
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="dryRun"
              checked={config.dryRun}
              onCheckedChange={(checked) => setConfig({ ...config, dryRun: checked })}
            />
            <Label htmlFor="dryRun">Dry Run</Label>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="stepTimeout">Step Timeout (s)</Label>
              <Input
                id="stepTimeout"
                type="number"
                value={config.stepTimeout}
                onChange={(e) => setConfig({ ...config, stepTimeout: parseInt(e.target.value) })}
                min={1}
                max={300}
              />
            </div>
            <div>
              <Label htmlFor="maxSteps">Max Steps</Label>
              <Input
                id="maxSteps"
                type="number"
                value={config.maxSteps}
                onChange={(e) => setConfig({ ...config, maxSteps: parseInt(e.target.value) })}
                min={1}
                max={1000}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Initial Variables */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Initial Variables (JSON)</CardTitle>
          <CardDescription>Variables to initialize the simulation with</CardDescription>
        </CardHeader>
        <CardContent>
          <Textarea
            placeholder='{"user_id": "123", "email": "test@example.com"}'
            value={initialVariables}
            onChange={(e) => setInitialVariables(e.target.value)}
            rows={3}
          />
        </CardContent>
      </Card>

      {/* Mock Data Config */}
      {config.useMockData && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Mock Data Configuration (JSON)</CardTitle>
            <CardDescription>Customize mock data generation</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              placeholder='{"http": {"status_code": 200}, "email": {"to": ["test@example.com"]}}'
              value={mockDataConfig}
              onChange={(e) => setMockDataConfig(e.target.value)}
              rows={3}
            />
          </CardContent>
        </Card>
      )}

      {/* Simulation Results */}
      {simulationResult && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Results</CardTitle>
            <CardDescription>
              Simulation completed in {simulationResult.duration_ms}ms
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-2">
              <Badge className={getStatusColor(simulationResult.status)}>
                {simulationResult.status}
              </Badge>
              <span className="text-sm text-gray-600">
                {simulationResult.steps.length} steps
              </span>
            </div>

            {simulationResult.validation_errors.length > 0 && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                <h4 className="text-sm font-medium text-red-800 mb-2">Validation Errors</h4>
                <ul className="text-sm text-red-700 space-y-1">
                  {simulationResult.validation_errors.map((error, index) => (
                    <li key={index}>• {error}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="space-y-2">
              <h4 className="text-sm font-medium">Execution Path</h4>
              <div className="flex flex-wrap gap-1">
                {simulationResult.execution_path.map((stepId, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {stepId}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="text-sm font-medium">Steps</h4>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {simulationResult.steps.map((step) => (
                  <div
                    key={step.step_id}
                    className="p-3 border rounded-md hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(step.status)}
                        <span className="text-sm font-medium">{step.name}</span>
                        <Badge variant="outline" className="text-xs">
                          {step.step_type}
                        </Badge>
                      </div>
                      {step.duration_ms && (
                        <span className="text-xs text-gray-500">
                          {step.duration_ms}ms
                        </span>
                      )}
                    </div>

                    {step.error && (
                      <div className="text-sm text-red-600 mb-2">
                        Error: {step.error}
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div>
                        <span className="font-medium text-gray-600">Inputs:</span>
                        <pre className="mt-1 text-gray-800 bg-gray-100 p-2 rounded overflow-x-auto">
                          {JSON.stringify(step.inputs, null, 2)}
                        </pre>
                      </div>
                      <div>
                        <span className="font-medium text-gray-600">Outputs:</span>
                        <pre className="mt-1 text-gray-800 bg-gray-100 p-2 rounded overflow-x-auto">
                          {JSON.stringify(step.outputs, null, 2)}
                        </pre>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
