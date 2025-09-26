interface StatusPillProps {
  status: 'on' | 'off';
}

export function StatusPill({ status }: StatusPillProps) {
  const statusDisplay =
    status === 'on' ? (
      <span className="text-success-dark">
        <span className="text-color-success pr-1">⏺︎</span>Active
      </span>
    ) : (
      <span>Refiner off</span>
    );

  return statusDisplay;
}
