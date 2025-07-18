import classNames from 'classnames';

interface StatusPillProps {
  status: 'on' | 'off';
}

export function StatusPill({ status }: StatusPillProps) {
  const styles = classNames(
    'rounded-full px-2 py-1 font-bold text-white text-nowrap',
    {
      'bg-state-success-dark': status === 'on',
      'bg-state-error-dark': status === 'off',
    }
  );

  return <span className={styles}>Refiner {status}</span>;
}
