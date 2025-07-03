import classNames from 'classnames';

interface TitleProps {
  children: React.ReactNode;
  className?: string;
}
export function Title({ children, className }: TitleProps) {
  return (
    <h2
      className={classNames(
        'font-merriweather text-3xl font-bold text-black',
        className
      )}
    >
      {children}
    </h2>
  );
}
