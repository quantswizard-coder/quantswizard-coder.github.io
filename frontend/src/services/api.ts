import { 
  ApiResponse, 
  StrategyOption, 
  SimulationConfig, 
  SimulationState, 
  MarketData,
  StrategyParams 
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class ApiService {
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  // Strategy management
  async getAvailableStrategies(): Promise<ApiResponse<StrategyOption[]>> {
    return this.request<StrategyOption[]>('/strategies');
  }

  async getStrategyDefaults(strategyId: string): Promise<ApiResponse<StrategyParams>> {
    return this.request<StrategyParams>(`/strategies/${strategyId}/defaults`);
  }

  // Market data
  async getMarketData(
    symbol: string = 'BTC-USD', 
    days: number = 180
  ): Promise<ApiResponse<MarketData>> {
    return this.request<MarketData>(`/market-data/${symbol}?days=${days}`);
  }

  // Simulation management
  async createSimulation(
    strategyId: string,
    strategyParams: StrategyParams,
    config: SimulationConfig
  ): Promise<ApiResponse<{ simulation_id: string }>> {
    return this.request<{ simulation_id: string }>('/simulations', {
      method: 'POST',
      body: JSON.stringify({
        strategy_id: strategyId,
        strategy_params: strategyParams,
        config
      })
    });
  }

  async startSimulation(simulationId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/simulations/${simulationId}/start`, {
      method: 'POST'
    });
  }

  async pauseSimulation(simulationId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/simulations/${simulationId}/pause`, {
      method: 'POST'
    });
  }

  async stopSimulation(simulationId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/simulations/${simulationId}/stop`, {
      method: 'POST'
    });
  }

  async getSimulationState(simulationId: string): Promise<ApiResponse<SimulationState>> {
    return this.request<SimulationState>(`/simulations/${simulationId}/state`);
  }

  async deleteSimulation(simulationId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/simulations/${simulationId}`, {
      method: 'DELETE'
    });
  }

  // Real-time updates via Server-Sent Events
  createEventSource(simulationId: string): EventSource {
    return new EventSource(`${API_BASE_URL}/simulations/${simulationId}/stream`);
  }

  // Export functionality
  async exportResults(
    simulationId: string,
    format: 'csv' | 'pdf',
    options: any = {}
  ): Promise<Blob> {
    const response = await fetch(
      `${API_BASE_URL}/simulations/${simulationId}/export?format=${format}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(options)
      }
    );

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return response.blob();
  }

  // Validation
  async validateStrategyParams(
    strategyId: string,
    params: StrategyParams
  ): Promise<ApiResponse<{ valid: boolean; errors?: string[] }>> {
    return this.request<{ valid: boolean; errors?: string[] }>(
      `/strategies/${strategyId}/validate`,
      {
        method: 'POST',
        body: JSON.stringify(params)
      }
    );
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string; version: string }>> {
    return this.request<{ status: string; version: string }>('/health');
  }
}

export const apiService = new ApiService();

// React Query keys
export const queryKeys = {
  strategies: ['strategies'] as const,
  strategyDefaults: (id: string) => ['strategies', id, 'defaults'] as const,
  marketData: (symbol: string, days: number) => ['market-data', symbol, days] as const,
  simulationState: (id: string) => ['simulations', id, 'state'] as const,
  health: ['health'] as const,
} as const;
