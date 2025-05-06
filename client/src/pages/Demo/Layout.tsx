import classNames from 'classnames';

interface ContainerProps {
  color: 'blue' | 'red' | 'green';
  children: React.ReactNode;
  className?: string;
}

export function Container({ color, children, className }: ContainerProps) {
  const defaultStyles =
    'items-center gap-6 rounded-lg border-1 border-dashed px-20 py-8';
  return (
    <div
      className={classNames(defaultStyles, className, {
        'border-blue-300 bg-blue-100': color === 'blue',
        'border-red-300 bg-rose-600/10': color === 'red',
        'border-green-500 bg-green-500/10': color === 'green',
      })}
    >
      {children}
    </div>
  );
}

interface ContentProps {
  children: React.ReactNode;
  className?: string;
}

export function Content({ children, className }: ContentProps) {
  return (
    <div className={classNames('flex flex-col items-center', className)}>
      {children}
    </div>
  );
}
