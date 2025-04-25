import classNames from 'classnames';
import { Link } from 'react-router';

interface ButtonProps {
  children: React.ReactNode;
  color?: 'blue' | 'black';
  inverted?: boolean;
  to?: string;
  onClick?: () => void;
}

export function Button({
  children,
  color = 'blue',
  inverted = false,
  to,
  onClick,
}: ButtonProps) {
  const defaultStyles =
    'inline-flex cursor-pointer items-center justify-center gap-2.5 overflow-hidden rounded px-5 py-3 font-bold';

  const btnClass = classNames(
    {
      'bg-blue-300': color === 'blue' && !inverted,
      'bg-black': color === 'black' && !inverted,
      'hover:text-slate-200':
        (color === 'blue' || color === 'black') && !inverted,
      'text-white': !inverted,
      'hover:bg-slate-200 bg-white text-blue-300 border-blue-300': inverted,
    },
    defaultStyles
  );

  if (to) {
    return (
      <Link onClick={onClick} to={to} className={btnClass}>
        {children}
      </Link>
    );
  }

  return (
    <button onClick={onClick} className={btnClass}>
      {children}
    </button>
  );
}
