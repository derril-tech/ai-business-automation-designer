"use client"

import { useState, useCallback } from "react"
import { ReactFlow, Node, Edge, addEdge, Connection, useNodesState, useEdgesState } from "reactflow"
import "reactflow/dist/style.css"

import { Toolbar } from "./Toolbar"
import { Sidebar } from "./Sidebar"
import { NodePanel } from "./NodePanel"
import { SimulationPanel } from "../simulation/SimulationPanel"
import { TestSuite } from "../testing/TestSuite"
import { useFlowStore } from "@/stores/flowStore"
import { CustomNode } from "./nodes/CustomNode"
import { nodeTypes } from "./nodes/nodeTypes"

export function FlowBuilder() {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const { selectedNode, setSelectedNode, rightPanel } = useFlowStore()

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node)
  }, [])

  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
  }, [])

  return (
    <div className="flex h-full w-full">
      {/* Left Sidebar - Node Palette */}
      <Sidebar />
      
      {/* Main Flow Area */}
      <div className="flex flex-1 flex-col">
        {/* Toolbar */}
        <Toolbar />
        
        {/* Flow Canvas */}
        <div className="flex flex-1">
          <div className="flex-1">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              onPaneClick={onPaneClick}
              nodeTypes={nodeTypes}
              fitView
              className="bg-muted/20"
            />
          </div>
          
          {/* Right Sidebar - Dynamic Content */}
          {rightPanel === "node" && selectedNode && (
            <NodePanel 
              node={selectedNode} 
              onClose={() => setSelectedNode(null)}
            />
          )}
          {rightPanel === "simulation" && (
            <SimulationPanel />
          )}
          {rightPanel === "testing" && (
            <TestSuite />
          )}
        </div>
      </div>
    </div>
  )
}
