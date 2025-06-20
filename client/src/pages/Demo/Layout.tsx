import classNames from 'classnames';

interface ContainerProps {
  color: 'blue' | 'red' | 'green' | 'white';
  children: React.ReactNode;
  className?: string;
}

export function Container({ color, children, className }: ContainerProps) {
  const defaultStyles =
    'items-center gap-6 rounded-lg border-thin border-dashed px-10 py-4 md:px-20 md:py-8';
  return (
    <div
      className={classNames(defaultStyles, className, {
        'border-blue-cool-20 bg-blue-cool-5': color === 'blue',
        'border-red-300 bg-rose-600/10': color === 'red',
        'border-green-500 bg-green-500/10': color === 'green',
        'border-blue-cool-20 bg-white': color === 'white',
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
    <div className={classNames('flex flex-col', className)}>{children}</div>
  );
}
