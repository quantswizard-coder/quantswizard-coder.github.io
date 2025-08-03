import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  animate?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  animate = true,
  className,
  disabled,
  ...props
}) => {
  const baseClasses = [
    'inline-flex items-center justify-center font-medium rounded-lg',
    'transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    fullWidth && 'w-full',
  ];

  const variantClasses = {
    primary: [
      'bg-primary-600 hover:bg-primary-700 text-white',
      'focus:ring-primary-500 dark:focus:ring-primary-400',
      'shadow-sm hover:shadow-md',
    ],
    secondary: [
      'bg-gray-100 hover:bg-gray-200 text-gray-900',
      'dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-white',
      'focus:ring-gray-500 dark:focus:ring-gray-400',
    ],
    success: [
      'bg-success-600 hover:bg-success-700 text-white',
      'focus:ring-success-500 dark:focus:ring-success-400',
      'shadow-sm hover:shadow-md',
    ],
    danger: [
      'bg-danger-600 hover:bg-danger-700 text-white',
      'focus:ring-danger-500 dark:focus:ring-danger-400',
      'shadow-sm hover:shadow-md',
    ],
    warning: [
      'bg-warning-600 hover:bg-warning-700 text-white',
      'focus:ring-warning-500 dark:focus:ring-warning-400',
      'shadow-sm hover:shadow-md',
    ],
    ghost: [
      'bg-transparent hover:bg-gray-100 text-gray-700',
      'dark:hover:bg-gray-800 dark:text-gray-300',
      'focus:ring-gray-500 dark:focus:ring-gray-400',
    ],
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  const iconSizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  const buttonContent = (
    <button
      className={clsx(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <>
          <div className={clsx('animate-spin rounded-full border-2 border-current border-t-transparent', iconSizeClasses[size])} />
          {children && <span className="ml-2">{children}</span>}
        </>
      ) : (
        <>
          {icon && iconPosition === 'left' && (
            <span className={clsx(iconSizeClasses[size], children ? 'mr-2' : '')}>
              {icon}
            </span>
          )}
          {children}
          {icon && iconPosition === 'right' && (
            <span className={clsx(iconSizeClasses[size], children ? 'ml-2' : '')}>
              {icon}
            </span>
          )}
        </>
      )}
    </button>
  );

  if (animate && !disabled && !loading) {
    return (
      <motion.div
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        transition={{ duration: 0.1 }}
      >
        {buttonContent}
      </motion.div>
    );
  }

  return buttonContent;
};

interface IconButtonProps extends Omit<ButtonProps, 'children'> {
  icon: React.ReactNode;
  'aria-label': string;
}

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  size = 'md',
  variant = 'ghost',
  className,
  ...props
}) => {
  const sizeClasses = {
    sm: 'p-1.5',
    md: 'p-2',
    lg: 'p-3',
  };

  return (
    <Button
      variant={variant}
      className={clsx('rounded-full', sizeClasses[size], className)}
      {...props}
    >
      {icon}
    </Button>
  );
};
