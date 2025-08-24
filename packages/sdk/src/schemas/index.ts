import { z } from 'zod';

// Workflow schemas
export const WorkflowSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().optional(),
  version: z.string(),
  status: z.enum(['draft', 'active', 'archived', 'error']),
  created_at: z.string(),
  updated_at: z.string(),
});

export const CreateWorkflowSchema = z.object({
  name: z.string().min(1),
  description: z.string().optional(),
});

export const UpdateWorkflowSchema = z.object({
  name: z.string().min(1).optional(),
  description: z.string().optional(),
  status: z.enum(['draft', 'active', 'archived', 'error']).optional(),
});

// Workflow run schemas
export const WorkflowRunSchema = z.object({
  id: z.string(),
  workflow_id: z.string(),
  version: z.string(),
  status: z.enum(['pending', 'running', 'completed', 'failed', 'cancelled']),
  input_data: z.record(z.any()),
  output_data: z.record(z.any()).optional(),
  started_at: z.string(),
  completed_at: z.string().optional(),
  error_message: z.string().optional(),
});

export const TriggerWorkflowSchema = z.object({
  input_data: z.record(z.any()),
});

// Connection schemas
export const ConnectionSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.enum(['http', 'slack', 'salesforce', 'hubspot', 'calendly', 'custom']),
  config: z.record(z.any()),
  status: z.enum(['active', 'inactive', 'error']),
  created_at: z.string(),
  updated_at: z.string(),
});

export const CreateConnectionSchema = z.object({
  name: z.string().min(1),
  type: z.enum(['http', 'slack', 'salesforce', 'hubspot', 'calendly', 'custom']),
  config: z.record(z.any()),
});

export const UpdateConnectionSchema = z.object({
  name: z.string().min(1).optional(),
  config: z.record(z.any()).optional(),
  status: z.enum(['active', 'inactive', 'error']).optional(),
});

// Design schemas
export const DraftFlowRequestSchema = z.object({
  goal: z.string().min(1),
  context: z.record(z.any()).optional(),
  constraints: z.array(z.string()).optional(),
});

export const DraftFlowResponseSchema = z.object({
  workflow_id: z.string(),
  version: z.string(),
  bpmn_data: z.record(z.any()),
  mappings: z.array(z.record(z.any())),
  estimated_cost: z.number(),
  estimated_latency: z.number(),
  confidence_score: z.number(),
});

// API response schemas
export const ApiResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    data: dataSchema,
    message: z.string().optional(),
    errors: z.array(z.string()).optional(),
  });

export const PaginatedResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    data: z.array(dataSchema),
    pagination: z.object({
      page: z.number(),
      limit: z.number(),
      total: z.number(),
      total_pages: z.number(),
    }),
  });

// Health check schemas
export const HealthResponseSchema = z.object({
  status: z.string(),
  message: z.string(),
  version: z.string(),
  timestamp: z.string(),
});
