import React from 'react';
import { 
  ChartBarIcon,
  CogIcon,
  PlayIcon,
  DocumentChartBarIcon,
  BookmarkIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  className?: string;
}

const tabs = [
  {
    id: 'dashboard',
    name: 'Dashboard',
    icon: ChartBarIcon,
    description: 'View simulation results and performance metrics',
  },
  {
    id: 'strategy',
    name: 'Strategy',
    icon: CogIcon,
    description: 'Configure trading strategy parameters',
  },
  {
    id: 'simulation',
    name: 'Simulation',
    icon: PlayIcon,
    description: 'Run and control trading simulations',
  },
  {
    id: 'analysis',
    name: 'Analysis',
    icon: DocumentChartBarIcon,
    description: 'Detailed performance analysis and reports',
  },
  {
    id: 'saved',
    name: 'Saved Configs',
    icon: BookmarkIcon,
    description: 'Manage saved strategy configurations',
  },
];

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  className,
}) => {
  return (
    <aside className={clsx(
      'bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700',
      'transition-colors duration-200',
      className
    )}>
      <nav className="p-4 space-y-2">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={clsx(
                'w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left',
                'transition-all duration-200 group',
                isActive
                  ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
              )}
            >
              <Icon className={clsx(
                'w-5 h-5 flex-shrink-0',
                isActive
                  ? 'text-primary-600 dark:text-primary-400'
                  : 'text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-300'
              )} />
              <div className="flex-1 min-w-0">
                <p className={clsx(
                  'text-sm font-medium',
                  isActive
                    ? 'text-primary-700 dark:text-primary-300'
                    : 'text-gray-900 dark:text-white'
                )}>
                  {tab.name}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {tab.description}
                </p>
              </div>
            </button>
          );
        })}
      </nav>
    </aside>
  );
};
