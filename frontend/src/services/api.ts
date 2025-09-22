import axios, { AxiosResponse } from 'axios'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for repository analysis
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request/Response Types
export interface AnalyzeRepositoryRequest {
  repo_url: string
  branch?: string
}

export interface AnalyzeRepositoryResponse {
  success: boolean
  job_id?: string
  message?: string
  error?: string
}

export interface ChatbotQueryRequest {
  question: string
  top_k?: number
}

export interface CodeSnippet {
  node_id: string
  file_path: string
  function_name: string
  code: string
  doc?: string
  score?: number
}

export interface PathNode {
  id: string
  label?: string
  name?: string  // Backend might send 'name' instead of 'label'
  type?: string
  file_path?: string
  file?: string  // Backend might send 'file' instead of 'file_path'
}

export interface PathEdge {
  source: string
  target: string
  type: string
}

export interface ChatbotQueryResponse {
  success: boolean
  query: string
  answer_path: PathNode[]
  path_edges: PathEdge[]
  snippets: CodeSnippet[]
  worker_summary?: any
  summary?: string
  processing_time: number
  error?: string
}

export interface GraphData {
  nodes: PathNode[]
  edges: PathEdge[]
}

export interface JobStatus {
  job_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress?: number
  message?: string
  result?: any
  error?: string
}

// API Service Class
class ApiService {
  /**
   * Analyze a repository - parse and index it for search
   */
  async analyzeRepository(request: AnalyzeRepositoryRequest): Promise<AnalyzeRepositoryResponse> {
    try {
      const response: AxiosResponse<AnalyzeRepositoryResponse> = await apiClient.post('/parse-and-index', {
        repo_url: request.repo_url,
        branch: request.branch || 'main',
        recreate_collection: true
      })
      return response.data
    } catch (error: any) {
      console.error('Failed to analyze repository:', error)
      throw new Error(error.response?.data?.detail || 'Failed to analyze repository')
    }
  }

  /**
   * Get job status for long-running operations
   */
  async getJobStatus(jobId: string): Promise<JobStatus> {
    try {
      const response: AxiosResponse<JobStatus> = await apiClient.get(`/status/${jobId}`)
      return response.data
    } catch (error: any) {
      console.error('Failed to get job status:', error)
      throw new Error(error.response?.data?.detail || 'Failed to get job status')
    }
  }

  /**
   * Query the chatbot with semantic search and graph analysis
   */
  async queryChatbot(request: ChatbotQueryRequest): Promise<ChatbotQueryResponse> {
    try {
      const response: AxiosResponse<ChatbotQueryResponse> = await apiClient.post('/ask', {
        question: request.question,
        top_k: request.top_k || 10
      })
      return response.data
    } catch (error: any) {
      console.error('Failed to query chatbot:', error)
      throw new Error(error.response?.data?.detail || 'Failed to process your query')
    }
  }

  /**
   * Get current graph data
   */
  async getGraphData(): Promise<GraphData> {
    try {
      const response: AxiosResponse<GraphData> = await apiClient.get('/graph')
      return response.data
    } catch (error: any) {
      console.error('Failed to get graph data:', error)
      throw new Error(error.response?.data?.detail || 'Failed to get graph data')
    }
  }

  /**
   * Perform semantic search
   */
  async searchRepository(query: string, topK: number = 10): Promise<{
    results: CodeSnippet[]
    processing_time: number
  }> {
    try {
      const response = await apiClient.post('/search', {
        query,
        top_k: topK
      })
      return response.data
    } catch (error: any) {
      console.error('Failed to search repository:', error)
      throw new Error(error.response?.data?.detail || 'Failed to search repository')
    }
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string }> {
    try {
      const response = await apiClient.get('/health')
      return response.data
    } catch (error: any) {
      console.error('Health check failed:', error)
      throw new Error('Backend service is not available')
    }
  }
}

// Export singleton instance
export const apiService = new ApiService()