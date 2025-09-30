interface StatusPillProps {
  status: 'on' | 'off';
}

export function StatusPill({ status }: StatusPillProps) {
  if (status === 'on') {
    return (
      <span className="text-success-dark">
        <span className="text-color-success pr-1">⏺︎</span>Active
      </span>
    );
  }

  return <span>Refiner off</span>;
}
