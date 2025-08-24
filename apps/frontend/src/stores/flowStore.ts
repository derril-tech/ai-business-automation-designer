import { create } from "zustand"
import { Node, Edge } from "reactflow"

export interface WorkflowData {
  id: string
  name: string
  description: string
  nodes: Node[]
  edges: Edge[]
  variables: Record<string, any>
  metadata: Record<string, any>
}

interface FlowStore {
  // Design mode state
  isDesignMode: boolean
  toggleDesignMode: () => void
  
  // Current workflow
  currentWorkflow: WorkflowData | null
  setCurrentWorkflow: (workflow: WorkflowData | null) => void
  
  // Selected elements
  selectedNode: Node | null
  setSelectedNode: (node: Node | null) => void
  
  // AI Design state
  isDesigning: boolean
  designGoal: string
  setDesignGoal: (goal: string) => void
  startAIDesign: () => void
  stopAIDesign: () => void
  
  // Execution state
  isExecuting: boolean
  executionId: string | null
  startExecution: (executionId: string) => void
  stopExecution: () => void
  
  // UI state
  sidebarOpen: boolean
  toggleSidebar: () => void
  nodePanelOpen: boolean
  toggleNodePanel: () => void
  rightPanel: "node" | "simulation" | "testing"
  setRightPanel: (panel: "node" | "simulation" | "testing") => void
}

export const useFlowStore = create<FlowStore>((set, get) => ({
  // Design mode state
  isDesignMode: true,
  toggleDesignMode: () => set((state) => ({ isDesignMode: !state.isDesignMode })),
  
  // Current workflow
  currentWorkflow: null,
  setCurrentWorkflow: (workflow) => set({ currentWorkflow: workflow }),
  
  // Selected elements
  selectedNode: null,
  setSelectedNode: (node) => set({ selectedNode: node }),
  
  // AI Design state
  isDesigning: false,
  designGoal: "",
  setDesignGoal: (goal) => set({ designGoal: goal }),
  startAIDesign: () => set({ isDesigning: true }),
  stopAIDesign: () => set({ isDesigning: false }),
  
  // Execution state
  isExecuting: false,
  executionId: null,
  startExecution: (executionId) => set({ isExecuting: true, executionId }),
  stopExecution: () => set({ isExecuting: false, executionId: null }),
  
  // UI state
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  nodePanelOpen: false,
  toggleNodePanel: () => set((state) => ({ nodePanelOpen: !state.nodePanelOpen })),
  rightPanel: "node" as const,
  setRightPanel: (panel) => set({ rightPanel: panel }),
}))
