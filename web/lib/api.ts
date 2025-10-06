// API configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export interface CompanyInfo {
  ticker: string;
  name: string;
  sector: string;
  industry: string;
}

export interface EarningsMetadata {
  date: string;
  eps_actual: number | null;
  eps_estimate: number | null;
  revenue: string | number;
  guidance: string;
}

export interface PricePerformance {
  since_earnings: string;
  vs_sp500: string;
  vs_sector: string;
  sector_etf: string;
  max_drawdown: string;
  current_price: string;
  volatility: string;
  volatility_pct: string;
}

export interface Event {
  date: string;
  description: string;
  source: string;
}

export interface InsightReport {
  headline: string;
  story: string;
  retail_perspective: string;
  the_gap: string;
  whats_next: string;
  key_dates: Event[];
  sources: string[];
}

export interface AnalysisStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: string;
  message?: string;
  updated_at?: string;
}

export interface AnalysisResult {
  job_id: string;
  status: string;
  ticker: string;
  company_info?: CompanyInfo;
  earnings_metadata?: EarningsMetadata;
  price_performance?: PricePerformance;
  reddit_analysis?: any;
  insight_report?: InsightReport;
  error?: string;
}

export interface InProgressJob {
  job_id: string;
  ticker: string;
  started_at: string;
}

// LocalStorage helpers
export const storage = {
  /**
   * Save an in-progress job
   */
  saveInProgressJob(job: InProgressJob) {
    if (typeof window === 'undefined') return;
    const jobs = this.getInProgressJobs();
    jobs.push(job);
    localStorage.setItem('inProgressJobs', JSON.stringify(jobs));
  },

  /**
   * Get all in-progress jobs
   */
  getInProgressJobs(): InProgressJob[] {
    if (typeof window === 'undefined') return [];
    const data = localStorage.getItem('inProgressJobs');
    return data ? JSON.parse(data) : [];
  },

  /**
   * Remove a job from in-progress list
   */
  removeInProgressJob(job_id: string) {
    if (typeof window === 'undefined') return;
    const jobs = this.getInProgressJobs().filter(j => j.job_id !== job_id);
    localStorage.setItem('inProgressJobs', JSON.stringify(jobs));
  },

  /**
   * Clean up old in-progress jobs (older than 24 hours)
   */
  cleanupOldJobs() {
    if (typeof window === 'undefined') return;
    const jobs = this.getInProgressJobs();
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
    const validJobs = jobs.filter(j => new Date(j.started_at) > oneDayAgo);
    localStorage.setItem('inProgressJobs', JSON.stringify(validJobs));
  }
};

class APIError extends Error {
  constructor(public statusCode: number, message: string) {
    super(message);
    this.name = 'APIError';
  }
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new APIError(response.status, error.detail || 'Request failed');
    }

    return response.json();
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(0, `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

export const api = {
  /**
   * Health check
   */
  async healthCheck() {
    return fetchAPI<{ service: string; status: string; version: string }>('/');
  },

  /**
   * Validate a ticker symbol
   */
  async validateTicker(ticker: string) {
    return fetchAPI<{ valid: boolean; ticker: string; company_info: CompanyInfo }>(
      `/api/validate/${ticker.toUpperCase()}`
    );
  },

  /**
   * Start a new analysis job
   */
  async startAnalysis(ticker: string) {
    return fetchAPI<AnalysisStatus>('/api/analyze', {
      method: 'POST',
      body: JSON.stringify({ ticker: ticker.toUpperCase() }),
    });
  },

  /**
   * Get the status of an analysis job
   */
  async getStatus(jobId: string) {
    return fetchAPI<AnalysisStatus>(`/api/status/${jobId}`);
  },

  /**
   * Get the results of a completed analysis
   */
  async getResult(jobId: string) {
    return fetchAPI<AnalysisResult>(`/api/result/${jobId}`);
  },

  /**
   * Poll for analysis completion
   * Returns a promise that resolves when analysis is complete
   */
  async pollForCompletion(
    jobId: string,
    onProgress?: (status: AnalysisStatus) => void,
    intervalMs: number = 2000
  ): Promise<AnalysisResult> {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const status = await this.getStatus(jobId);
          
          if (onProgress) {
            onProgress(status);
          }

          if (status.status === 'completed') {
            const result = await this.getResult(jobId);
            resolve(result);
            return;
          }

          if (status.status === 'failed') {
            reject(new Error(status.message || 'Analysis failed'));
            return;
          }

          // Continue polling
          setTimeout(poll, intervalMs);
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  },

  /**
   * Analyze a stock using WebSocket for real-time updates
   */
  async analyzeStockWithWebSocket(
    ticker: string,
    onStatus?: (status: AnalysisStatus) => void,
    onComplete?: (result: AnalysisResult) => void,
    onError?: (error: string) => void
  ): Promise<() => void> {
    // Start the analysis job and get the job_id
    const analysisPromise = this.startAnalysis(ticker);
    
    // Wait for job_id
    const { job_id } = await analysisPromise;
    
    // Save to localStorage immediately so we can resume if page closes
    storage.saveInProgressJob({
      job_id,
      ticker: ticker.toUpperCase(),
      started_at: new Date().toISOString()
    });
    
    // Immediately connect to WebSocket (before the job makes much progress)
    const ws = new WebSocket(`${WS_BASE_URL}/ws/${job_id}`);
    
    ws.onopen = () => {
      console.log('WebSocket connected for job:', job_id);
    };
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        switch (message.type) {
          case 'status':
            if (onStatus) {
              onStatus(message.data);
            }
            break;
            
          case 'result':
            // Remove from in-progress list when completed
            storage.removeInProgressJob(job_id);
            if (onComplete) {
              onComplete(message.data);
            }
            ws.close();
            break;
            
          case 'error':
            // Remove from in-progress list on error
            storage.removeInProgressJob(job_id);
            if (onError) {
              onError(message.data.error || 'Analysis failed');
            }
            ws.close();
            break;
            
          case 'pong':
            // Keep-alive response
            break;
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError) {
        onError('Connection error');
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket closed for job:', job_id);
    };
    
    // Send periodic pings to keep connection alive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
      } else {
        clearInterval(pingInterval);
      }
    }, 30000); // Every 30 seconds
    
    // Return cleanup function
    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  },

  /**
   * Resume an in-progress job by reconnecting to its WebSocket
   */
  async resumeJob(
    job_id: string,
    onStatus?: (status: AnalysisStatus) => void,
    onComplete?: (result: AnalysisResult) => void,
    onError?: (error: string) => void
  ): Promise<() => void> {
    // First check if job is already complete
    try {
      const result = await this.getResult(job_id);
      if (onComplete) {
        onComplete(result);
      }
      storage.removeInProgressJob(job_id);
      return () => {}; // No-op cleanup
    } catch (error) {
      // Job not complete yet, continue to WebSocket connection
    }
    
    // Connect to WebSocket for live updates
    const ws = new WebSocket(`${WS_BASE_URL}/ws/${job_id}`);
    
    ws.onopen = () => {
      console.log('WebSocket reconnected for job:', job_id);
    };
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        switch (message.type) {
          case 'status':
            if (onStatus) {
              onStatus(message.data);
            }
            break;
            
          case 'result':
            storage.removeInProgressJob(job_id);
            if (onComplete) {
              onComplete(message.data);
            }
            ws.close();
            break;
            
          case 'error':
            storage.removeInProgressJob(job_id);
            if (onError) {
              onError(message.data.error || 'Analysis failed');
            }
            ws.close();
            break;
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError) {
        onError('Connection error');
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket closed for job:', job_id);
    };
    
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
      } else {
        clearInterval(pingInterval);
      }
    }, 30000);
    
    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  },

  /**
   * Analyze a stock (start analysis and wait for completion)
   * This is a convenience method that combines startAnalysis and pollForCompletion
   * DEPRECATED: Use analyzeStockWithWebSocket instead
   */
  async analyzeStock(
    ticker: string,
    onProgress?: (status: AnalysisStatus) => void
  ): Promise<AnalysisResult> {
    const { job_id } = await this.startAnalysis(ticker);
    return this.pollForCompletion(job_id, onProgress);
  },
};

export default api;
