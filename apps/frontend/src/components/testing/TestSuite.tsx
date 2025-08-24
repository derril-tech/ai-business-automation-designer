"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Plus, Play, Save, Trash2, CheckCircle, XCircle, Clock, AlertTriangle } from "lucide-react"
import { useFlowStore } from "@/stores/flowStore"

interface TestCase {
  id: string
  name: string
  description: string
  initial_variables: Record<string, any>
  expected_outputs: Record<string, any>
  expected_status: "completed" | "failed"
  timeout_seconds: number
  enabled: boolean
}

interface TestResult {
  test_id: string
  test_name: string
  status: "passed" | "failed" | "running" | "pending"
  duration_ms?: number
  error?: string
  actual_outputs?: Record<string, any>
  actual_status?: string
}

interface TestSuite {
  id: string
  name: string
  description: string
  workflow_id: string
  test_cases: TestCase[]
  created_at: string
  updated_at: string
}

export function TestSuite() {
  const { currentWorkflow } = useFlowStore()
  const [testSuites, setTestSuites] = useState<TestSuite[]>([])
  const [selectedSuite, setSelectedSuite] = useState<TestSuite | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [testResults, setTestResults] = useState<TestResult[]>([])
  const [newTestCase, setNewTestCase] = useState<Partial<TestCase>>({
    name: "",
    description: "",
    initial_variables: {},
    expected_outputs: {},
    expected_status: "completed",
    timeout_seconds: 30,
    enabled: true
  })

  const createTestSuite = () => {
    if (!currentWorkflow) return

    const suite: TestSuite = {
      id: `suite_${Date.now()}`,
      name: `Test Suite for ${currentWorkflow.name}`,
      description: "Automated test suite for workflow validation",
      workflow_id: currentWorkflow.id,
      test_cases: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }

    setTestSuites([...testSuites, suite])
    setSelectedSuite(suite)
  }

  const addTestCase = () => {
    if (!selectedSuite || !newTestCase.name) return

    const testCase: TestCase = {
      id: `test_${Date.now()}`,
      name: newTestCase.name,
      description: newTestCase.description || "",
      initial_variables: newTestCase.initial_variables || {},
      expected_outputs: newTestCase.expected_outputs || {},
      expected_status: newTestCase.expected_status || "completed",
      timeout_seconds: newTestCase.timeout_seconds || 30,
      enabled: newTestCase.enabled !== false
    }

    const updatedSuite = {
      ...selectedSuite,
      test_cases: [...selectedSuite.test_cases, testCase],
      updated_at: new Date().toISOString()
    }

    setTestSuites(testSuites.map(s => s.id === selectedSuite.id ? updatedSuite : s))
    setSelectedSuite(updatedSuite)
    setNewTestCase({
      name: "",
      description: "",
      initial_variables: {},
      expected_outputs: {},
      expected_status: "completed",
      timeout_seconds: 30,
      enabled: true
    })
  }

  const removeTestCase = (testId: string) => {
    if (!selectedSuite) return

    const updatedSuite = {
      ...selectedSuite,
      test_cases: selectedSuite.test_cases.filter(t => t.id !== testId),
      updated_at: new Date().toISOString()
    }

    setTestSuites(testSuites.map(s => s.id === selectedSuite.id ? updatedSuite : s))
    setSelectedSuite(updatedSuite)
  }

  const runTestSuite = async () => {
    if (!selectedSuite) return

    setIsRunning(true)
    const results: TestResult[] = []

    for (const testCase of selectedSuite.test_cases) {
      if (!testCase.enabled) {
        results.push({
          test_id: testCase.id,
          test_name: testCase.name,
          status: "pending"
        })
        continue
      }

      // Mark as running
      results.push({
        test_id: testCase.id,
        test_name: testCase.name,
        status: "running"
      })
      setTestResults([...results])

      try {
        // In a real implementation, this would call the simulation API
        const response = await fetch("/api/simulation/simulate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            workflow_id: selectedSuite.workflow_id,
            config: {
              use_mock_data: true,
              enable_validation: true,
              stop_on_error: true,
              dry_run: false,
              step_timeout_seconds: testCase.timeout_seconds,
              max_steps: 100
            },
            initial_variables: testCase.initial_variables
          })
        })

        if (response.ok) {
          const simulationResult = await response.json()
          
          // Validate results
          const passed = validateTestResult(testCase, simulationResult)
          
          const result: TestResult = {
            test_id: testCase.id,
            test_name: testCase.name,
            status: passed ? "passed" : "failed",
            duration_ms: simulationResult.duration_ms,
            actual_outputs: simulationResult.variables,
            actual_status: simulationResult.status,
            error: passed ? undefined : "Test expectations not met"
          }
          
          results[results.length - 1] = result
        } else {
          results[results.length - 1] = {
            test_id: testCase.id,
            test_name: testCase.name,
            status: "failed",
            error: "Simulation failed"
          }
        }
      } catch (error) {
        results[results.length - 1] = {
          test_id: testCase.id,
          test_name: testCase.name,
          status: "failed",
          error: error instanceof Error ? error.message : "Unknown error"
        }
      }

      setTestResults([...results])
    }

    setIsRunning(false)
  }

  const validateTestResult = (testCase: TestCase, simulationResult: any): boolean => {
    // Check status
    if (testCase.expected_status !== simulationResult.status) {
      return false
    }

    // Check expected outputs
    for (const [key, expectedValue] of Object.entries(testCase.expected_outputs)) {
      const actualValue = simulationResult.variables[key]
      if (actualValue !== expectedValue) {
        return false
      }
    }

    return true
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "passed":
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
      case "passed":
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
        <h2 className="text-lg font-semibold">Test Suite</h2>
        <div className="flex space-x-2">
          <Button
            size="sm"
            onClick={createTestSuite}
            disabled={!currentWorkflow}
            className="flex items-center space-x-1"
          >
            <Plus className="w-4 h-4" />
            <span>New Suite</span>
          </Button>
          {selectedSuite && (
            <Button
              size="sm"
              onClick={runTestSuite}
              disabled={isRunning || selectedSuite.test_cases.length === 0}
              className="flex items-center space-x-1"
            >
              <Play className="w-4 h-4" />
              <span>Run Tests</span>
            </Button>
          )}
        </div>
      </div>

      <Separator />

      {/* Test Suite Selection */}
      {testSuites.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Test Suites</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {testSuites.map((suite) => (
                <div
                  key={suite.id}
                  className={`p-3 border rounded-md cursor-pointer transition-colors ${
                    selectedSuite?.id === suite.id ? "bg-blue-50 border-blue-200" : "hover:bg-gray-50"
                  }`}
                  onClick={() => setSelectedSuite(suite)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">{suite.name}</h3>
                      <p className="text-sm text-gray-600">{suite.description}</p>
                      <p className="text-xs text-gray-500">
                        {suite.test_cases.length} test cases
                      </p>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {suite.test_cases.filter(t => t.enabled).length} enabled
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Selected Test Suite */}
      {selectedSuite && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">{selectedSuite.name}</CardTitle>
            <CardDescription>{selectedSuite.description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Add New Test Case */}
            <div className="space-y-4 p-4 border rounded-md">
              <h4 className="font-medium">Add Test Case</h4>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="testName">Name</Label>
                  <Input
                    id="testName"
                    value={newTestCase.name}
                    onChange={(e) => setNewTestCase({ ...newTestCase, name: e.target.value })}
                    placeholder="Test case name"
                  />
                </div>
                <div>
                  <Label htmlFor="testTimeout">Timeout (s)</Label>
                  <Input
                    id="testTimeout"
                    type="number"
                    value={newTestCase.timeout_seconds}
                    onChange={(e) => setNewTestCase({ ...newTestCase, timeout_seconds: parseInt(e.target.value) })}
                    min={1}
                    max={300}
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="testDescription">Description</Label>
                <Textarea
                  id="testDescription"
                  value={newTestCase.description}
                  onChange={(e) => setNewTestCase({ ...newTestCase, description: e.target.value })}
                  placeholder="Test case description"
                  rows={2}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="initialVariables">Initial Variables (JSON)</Label>
                  <Textarea
                    id="initialVariables"
                    value={JSON.stringify(newTestCase.initial_variables, null, 2)}
                    onChange={(e) => {
                      try {
                        const parsed = JSON.parse(e.target.value)
                        setNewTestCase({ ...newTestCase, initial_variables: parsed })
                      } catch {
                        // Invalid JSON, ignore
                      }
                    }}
                    placeholder='{"user_id": "123"}'
                    rows={3}
                  />
                </div>
                <div>
                  <Label htmlFor="expectedOutputs">Expected Outputs (JSON)</Label>
                  <Textarea
                    id="expectedOutputs"
                    value={JSON.stringify(newTestCase.expected_outputs, null, 2)}
                    onChange={(e) => {
                      try {
                        const parsed = JSON.parse(e.target.value)
                        setNewTestCase({ ...newTestCase, expected_outputs: parsed })
                      } catch {
                        // Invalid JSON, ignore
                      }
                    }}
                    placeholder='{"result": "success"}'
                    rows={3}
                  />
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Switch
                    id="testEnabled"
                    checked={newTestCase.enabled}
                    onCheckedChange={(checked) => setNewTestCase({ ...newTestCase, enabled: checked })}
                  />
                  <Label htmlFor="testEnabled">Enabled</Label>
                </div>
                <Button size="sm" onClick={addTestCase} disabled={!newTestCase.name}>
                  <Plus className="w-4 h-4 mr-1" />
                  Add Test Case
                </Button>
              </div>
            </div>

            {/* Test Cases */}
            <div className="space-y-2">
              <h4 className="font-medium">Test Cases</h4>
              {selectedSuite.test_cases.map((testCase) => (
                <div
                  key={testCase.id}
                  className="p-3 border rounded-md hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Switch
                        checked={testCase.enabled}
                        onCheckedChange={(checked) => {
                          const updatedSuite = {
                            ...selectedSuite,
                            test_cases: selectedSuite.test_cases.map(t =>
                              t.id === testCase.id ? { ...t, enabled: checked } : t
                            )
                          }
                          setSelectedSuite(updatedSuite)
                          setTestSuites(testSuites.map(s => s.id === selectedSuite.id ? updatedSuite : s))
                        }}
                      />
                      <div>
                        <h5 className="font-medium">{testCase.name}</h5>
                        <p className="text-sm text-gray-600">{testCase.description}</p>
                        <div className="flex items-center space-x-2 mt-1">
                          <Badge variant="outline" className="text-xs">
                            {testCase.expected_status}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {testCase.timeout_seconds}s
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => removeTestCase(testCase.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Test Results */}
      {testResults.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Test Results</CardTitle>
            <CardDescription>
              {testResults.filter(r => r.status === "passed").length} passed,{" "}
              {testResults.filter(r => r.status === "failed").length} failed
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {testResults.map((result) => (
                <div
                  key={result.test_id}
                  className="p-3 border rounded-md hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(result.status)}
                      <div>
                        <h5 className="font-medium">{result.test_name}</h5>
                        {result.error && (
                          <p className="text-sm text-red-600">{result.error}</p>
                        )}
                        {result.duration_ms && (
                          <p className="text-xs text-gray-500">
                            Duration: {result.duration_ms}ms
                          </p>
                        )}
                      </div>
                    </div>
                    <Badge className={getStatusColor(result.status)}>
                      {result.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
