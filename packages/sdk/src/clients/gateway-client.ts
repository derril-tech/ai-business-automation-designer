import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  Workflow, 
  WorkflowRun, 
  Connection, 
  ApiResponse, 
  PaginatedResponse 
} from '../types';

export class GatewayClient {
  private client: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:3001', token?: string) {
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
        console.error('Gateway API Error:', error.response?.data || error.message);
        throw error;
      }
    );
  }

  // Workflow methods
  async getWorkflows(page: number = 1, limit: number = 10): Promise<PaginatedResponse<Workflow>> {
    const response: AxiosResponse<PaginatedResponse<Workflow>> = await this.client.get('/workflows', {
      params: { page, limit },
    });
    return response.data;
  }

  async getWorkflow(id: string): Promise<Workflow> {
    const response: AxiosResponse<ApiResponse<Workflow>> = await this.client.get(`/workflows/${id}`);
    return response.data.data;
  }

  async createWorkflow(workflow: Partial<Workflow>): Promise<Workflow> {
    const response: AxiosResponse<ApiResponse<Workflow>> = await this.client.post('/workflows', workflow);
    return response.data.data;
  }

  async updateWorkflow(id: string, workflow: Partial<Workflow>): Promise<Workflow> {
    const response: AxiosResponse<ApiResponse<Workflow>> = await this.client.put(`/workflows/${id}`, workflow);
    return response.data.data;
  }

  async deleteWorkflow(id: string): Promise<void> {
    await this.client.delete(`/workflows/${id}`);
  }

  // Workflow runs methods
  async getWorkflowRuns(workflowId: string, page: number = 1, limit: number = 10): Promise<PaginatedResponse<WorkflowRun>> {
    const response: AxiosResponse<PaginatedResponse<WorkflowRun>> = await this.client.get(`/workflows/${workflowId}/runs`, {
      params: { page, limit },
    });
    return response.data;
  }

  async getWorkflowRun(id: string): Promise<WorkflowRun> {
    const response: AxiosResponse<ApiResponse<WorkflowRun>> = await this.client.get(`/runs/${id}`);
    return response.data.data;
  }

  async triggerWorkflow(workflowId: string, inputData: Record<string, any>): Promise<WorkflowRun> {
    const response: AxiosResponse<ApiResponse<WorkflowRun>> = await this.client.post(`/workflows/${workflowId}/trigger`, {
      input_data: inputData,
    });
    return response.data.data;
  }

  // Connection methods
  async getConnections(): Promise<Connection[]> {
    const response: AxiosResponse<ApiResponse<Connection[]>> = await this.client.get('/connections');
    return response.data.data;
  }

  async getConnection(id: string): Promise<Connection> {
    const response: AxiosResponse<ApiResponse<Connection>> = await this.client.get(`/connections/${id}`);
    return response.data.data;
  }

  async createConnection(connection: Partial<Connection>): Promise<Connection> {
    const response: AxiosResponse<ApiResponse<Connection>> = await this.client.post('/connections', connection);
    return response.data.data;
  }

  async updateConnection(id: string, connection: Partial<Connection>): Promise<Connection> {
    const response: AxiosResponse<ApiResponse<Connection>> = await this.client.put(`/connections/${id}`, connection);
    return response.data.data;
  }

  async deleteConnection(id: string): Promise<void> {
    await this.client.delete(`/connections/${id}`);
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response: AxiosResponse<{ status: string }> = await this.client.get('/health');
    return response.data;
  }
}
