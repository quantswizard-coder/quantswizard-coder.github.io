import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService, queryKeys } from '../services/api';
import { SimulationState, StrategyParams, SimulationConfig } from '../types';
import toast from 'react-hot-toast';

export const useSimulation = () => {
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const queryClient = useQueryClient();

  // Get simulation state
  const {
    data: simulationStateResponse,
    isLoading: isLoadingState,
    error: stateError
  } = useQuery({
    queryKey: queryKeys.simulationState(simulationId || ''),
    queryFn: async () => {
      const response = await apiService.getSimulationState(simulationId!);
      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to get simulation state');
      }
      return response.data;
    },
    enabled: !!simulationId,
    refetchInterval: simulationId && !isConnected ? 2000 : false, // Fallback polling
  });

  const simulationState = simulationStateResponse;

  // Create simulation mutation
  const createSimulationMutation = useMutation({
    mutationFn: async ({
      strategyId,
      strategyParams,
      config
    }: {
      strategyId: string;
      strategyParams: StrategyParams;
      config: SimulationConfig;
    }) => {
      const response = await apiService.createSimulation(strategyId, strategyParams, config);
      if (!response.success || !response.data) {
        throw new Error(response.error || 'Failed to create simulation');
      }
      return response.data.simulation_id;
    },
    onSuccess: (newSimulationId) => {
      setSimulationId(newSimulationId);
      toast.success('Simulation created successfully');
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error(`Failed to create simulation: ${message}`);
    },
  });

  // Start simulation mutation
  const startSimulationMutation = useMutation({
    mutationFn: async () => {
      const response = await apiService.startSimulation(simulationId!);
      if (!response.success) {
        throw new Error(response.error || 'Failed to start simulation');
      }
      return response;
    },
    onSuccess: () => {
      toast.success('Simulation started');
      queryClient.invalidateQueries({ queryKey: queryKeys.simulationState(simulationId!) });
    },
    onError: (error: any) => {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error(`Failed to start simulation: ${message}`);
    },
  });

  // Pause simulation mutation
  const pauseSimulationMutation = useMutation({
    mutationFn: async () => {
      const response = await apiService.pauseSimulation(simulationId!);
      if (!response.success) {
        throw new Error(response.error || 'Failed to pause simulation');
      }
      return response;
    },
    onSuccess: () => {
      toast.success('Simulation paused');
      queryClient.invalidateQueries({ queryKey: queryKeys.simulationState(simulationId!) });
    },
    onError: (error: any) => {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error(`Failed to pause simulation: ${message}`);
    },
  });

  // Stop simulation mutation
  const stopSimulationMutation = useMutation({
    mutationFn: async () => {
      const response = await apiService.stopSimulation(simulationId!);
      if (!response.success) {
        throw new Error(response.error || 'Failed to stop simulation');
      }
      return response;
    },
    onSuccess: () => {
      toast.success('Simulation stopped');
      queryClient.invalidateQueries({ queryKey: queryKeys.simulationState(simulationId!) });
    },
    onError: (error: any) => {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error(`Failed to stop simulation: ${message}`);
    },
  });

  // Setup real-time connection
  const connectToSimulation = useCallback(() => {
    if (!simulationId || eventSourceRef.current) return;

    try {
      const eventSource = apiService.createEventSource(simulationId);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setIsConnected(true);
        console.log('Connected to simulation stream');
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Update the query cache with real-time data
          queryClient.setQueryData(
            queryKeys.simulationState(simulationId),
            { success: true, data }
          );
        } catch (error) {
          console.error('Failed to parse simulation update:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        setIsConnected(false);
        eventSource.close();
        eventSourceRef.current = null;
        
        // Retry connection after 5 seconds
        setTimeout(() => {
          if (simulationId) {
            connectToSimulation();
          }
        }, 5000);
      };
    } catch (error) {
      console.error('Failed to create EventSource:', error);
      setIsConnected(false);
    }
  }, [simulationId, queryClient]);

  // Disconnect from simulation
  const disconnectFromSimulation = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
  }, []);

  // Connect when simulation ID changes
  useEffect(() => {
    if (simulationId) {
      connectToSimulation();
    } else {
      disconnectFromSimulation();
    }

    return () => {
      disconnectFromSimulation();
    };
  }, [simulationId, connectToSimulation, disconnectFromSimulation]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectFromSimulation();
    };
  }, [disconnectFromSimulation]);

  return {
    // State
    simulationId,
    simulationState,
    isConnected,
    isLoadingState,
    stateError,

    // Actions
    createSimulation: createSimulationMutation.mutate,
    startSimulation: startSimulationMutation.mutate,
    pauseSimulation: pauseSimulationMutation.mutate,
    stopSimulation: stopSimulationMutation.mutate,
    
    // Loading states
    isCreating: createSimulationMutation.isPending,
    isStarting: startSimulationMutation.isPending,
    isPausing: pauseSimulationMutation.isPending,
    isStopping: stopSimulationMutation.isPending,

    // Utilities
    resetSimulation: () => {
      disconnectFromSimulation();
      setSimulationId(null);
    },
  };
};
