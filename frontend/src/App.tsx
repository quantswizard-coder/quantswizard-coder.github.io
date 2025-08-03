import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { ThemeProvider } from './contexts/ThemeContext';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Strategy } from './pages/Strategy';
import { Simulation } from './pages/Simulation';
import './index.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'strategy':
        return <Strategy />;
      case 'simulation':
        return <Simulation />;
      case 'analysis':
        return (
          <div className="text-center py-12">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Analysis Coming Soon
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Advanced performance analysis and reporting features will be available here.
            </p>
          </div>
        );
      case 'saved':
        return (
          <div className="text-center py-12">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Saved Configurations
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Manage your saved strategy configurations from the Strategy tab.
            </p>
          </div>
        );
      default:
        return <Dashboard />;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
          {/* Header */}
          <Header />
          
          {/* Main Layout */}
          <div className="flex h-[calc(100vh-73px)]">
            {/* Sidebar */}
            <Sidebar
              activeTab={activeTab}
              onTabChange={setActiveTab}
              className="w-64 flex-shrink-0"
            />
            
            {/* Main Content */}
            <main className="flex-1 overflow-auto">
              <div className="max-w-7xl mx-auto p-6">
                {renderContent()}
              </div>
            </main>
          </div>
          
          {/* Toast Notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              className: 'dark:bg-gray-800 dark:text-white',
            }}
          />
        </div>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
