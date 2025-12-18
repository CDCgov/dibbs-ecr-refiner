import classNames from 'classnames';

interface TitleProps {
  children: React.ReactNode;
  className?: string;
}
export function Title({ children, className }: TitleProps) {
  return (
    <h1
      className={classNames(
        'font-merriweather !m-0 text-3xl font-bold text-black',
        className
      )}
    >
      {children}
    </h1>
  );
}
