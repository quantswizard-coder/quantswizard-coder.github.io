# 🏗️ Architecture Overview

## System Architecture

The Interactive Trading Simulator follows a modern full-stack architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │ Trading Engine  │
│                 │    │                 │    │                 │
│ • TypeScript    │◄──►│ • REST API      │◄──►│ • Strategies    │
│ • Tailwind CSS │    │ • Data Validation│    │ • Simulation    │
│ • React Query   │    │ • CORS Support  │    │ • Portfolio     │
│ • Recharts      │    │ • WebSocket     │    │ • Risk Mgmt     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Component Structure

### Frontend (`frontend/`)
- **Components**: Reusable UI components with TypeScript
- **Pages**: Main application views (Dashboard, Strategy, Simulation)
- **Hooks**: Custom React hooks for state management
- **Services**: API integration and data fetching
- **Types**: TypeScript type definitions

### Backend (`backend/`)
- **API Server**: FastAPI application with REST endpoints
- **Data Models**: Pydantic models for validation
- **CORS**: Cross-origin resource sharing configuration

### Core System (`src/`)
- **Strategies**: Trading strategy implementations
- **Simulation**: Portfolio tracking and simulation engine
- **Data**: Market data providers and processing
- **Backtesting**: Performance analysis and metrics
- **Utils**: Shared utilities and helpers

## Data Flow

1. **Market Data**: Yahoo Finance → Data Providers → Simulation Engine
2. **Strategy Signals**: Market Data → Strategies → Trading Decisions
3. **Portfolio Updates**: Trading Decisions → Portfolio Tracker → Performance Metrics
4. **Frontend Updates**: Backend API → React Query → UI Components

## Key Design Principles

- **Modularity**: Each component has a single responsibility
- **Type Safety**: TypeScript throughout frontend, Python typing in backend
- **Separation of Concerns**: Clear boundaries between layers
- **Extensibility**: Easy to add new strategies and features
- **Performance**: Efficient data processing and caching
