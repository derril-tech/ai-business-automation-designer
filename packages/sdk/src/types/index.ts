// Workflow types
export interface Workflow {
  id: string;
  name: string;
  description?: string;
  version: string;
  status: WorkflowStatus;
  created_at: string;
  updated_at: string;
}

export type WorkflowStatus = 'draft' | 'active' | 'archived' | 'error';

// Workflow execution types
export interface WorkflowRun {
  id: string;
  workflow_id: string;
  version: string;
  status: RunStatus;
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  started_at: string;
  completed_at?: string;
  error_message?: string;
}

export type RunStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

// Step types
export interface WorkflowStep {
  id: string;
  workflow_id: string;
  name: string;
  type: StepType;
  config: Record<string, any>;
  position: {
    x: number;
    y: number;
  };
}

export type StepType = 'trigger' | 'action' | 'branch' | 'loop' | 'parallel' | 'approval' | 'delay' | 'http' | 'datamap';

// Connection types
export interface Connection {
  id: string;
  name: string;
  type: ConnectionType;
  config: Record<string, any>;
  status: ConnectionStatus;
  created_at: string;
  updated_at: string;
}

export type ConnectionType = 'http' | 'slack' | 'salesforce' | 'hubspot' | 'calendly' | 'custom';
export type ConnectionStatus = 'active' | 'inactive' | 'error';

// Design types
export interface DraftFlowRequest {
  goal: string;
  context?: Record<string, any>;
  constraints?: string[];
}

export interface DraftFlowResponse {
  workflow_id: string;
  version: string;
  bpmn_data: Record<string, any>;
  mappings: Record<string, any>[];
  estimated_cost: number;
  estimated_latency: number;
  confidence_score: number;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  errors?: string[];
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}
