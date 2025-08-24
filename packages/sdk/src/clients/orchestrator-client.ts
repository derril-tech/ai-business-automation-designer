import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  DraftFlowRequest, 
  DraftFlowResponse, 
  ApiResponse 
} from '../types';

export class OrchestratorClient {
  private client: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:8000', token?: string) {
    this.client = axios.create({
      baseURL: `${baseURL}/v1`,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('Orchestrator API Error:', error.response?.data || error.message);
        throw error;
      }
    );
  }

  // Design methods
  async draftFlow(request: DraftFlowRequest): Promise<DraftFlowResponse> {
    const response: AxiosResponse<DraftFlowResponse> = await this.client.post('/design/draft', request);
    return response.data;
  }

  async suggestMapping(sourceSchema: Record<string, any>, targetSchema: Record<string, any>): Promise<Record<string, any>[]> {
    const response: AxiosResponse<ApiResponse<Record<string, any>[]>> = await this.client.post('/design/mapping', {
      source_schema: sourceSchema,
      target_schema: targetSchema,
    });
    return response.data.data;
  }

  async generateTestPlan(workflowId: string, version: string): Promise<Record<string, any>> {
    const response: AxiosResponse<ApiResponse<Record<string, any>>> = await this.client.post('/design/testplan', {
      workflow_id: workflowId,
      version: version,
    });
    return response.data.data;
  }

  async complianceScan(workflowId: string, version: string): Promise<Record<string, any>> {
    const response: AxiosResponse<ApiResponse<Record<string, any>>> = await this.client.post('/design/scan', {
      workflow_id: workflowId,
      version: version,
    });
    return response.data.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; message: string; version: string; timestamp: string }> {
    const response: AxiosResponse<{ status: string; message: string; version: string; timestamp: string }> = await this.client.get('/health');
    return response.data;
  }

  async readinessCheck(): Promise<{ status: string }> {
    const response: AxiosResponse<{ status: string }> = await this.client.get('/health/ready');
    return response.data;
  }

  async livenessCheck(): Promise<{ status: string }> {
    const response: AxiosResponse<{ status: string }> = await this.client.get('/health/live');
    return response.data;
  }
}
