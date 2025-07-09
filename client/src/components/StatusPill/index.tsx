interface StatusPillProps {
  status: string;
}

export function StatusPill({ status }: StatusPillProps) {
  return (
    <span
      data-configuration-status={status}
      data-testid='status-pill'
      className="rounded-full px-2 py-1 text-white font-bold"
    >
      Refiner {status}
    </span>
  );
}
