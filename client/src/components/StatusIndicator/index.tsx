import classNames from 'classnames';

interface StatusIndicatorProps {
  isActive: boolean;
  className?: string;
}

/**
 * StatusIndicator renders a circular icon and a text label indicating
 * whether a configuration or item is enabled or disabled.
 */
export function StatusIndicator({ isActive, className }: StatusIndicatorProps) {
  const statusClasses = classNames(
    'flex items-center',
    isActive ? 'text-success-dark' : 'text-gray-cool-60',
    className
  );

  const dotClasses = classNames(
    'mr-1 inline-block h-3 w-3 rounded-full',
    isActive ? 'bg-state-success-dark' : 'bg-gray-cool-60'
  );

  return (
    <span className={statusClasses}>
      <span className={dotClasses} aria-hidden />
      {isActive ? 'enabled' : 'disabled'}
    </span>
  );
}
