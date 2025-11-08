import { GetConfigurationsResponse } from '../../api/schemas';

interface StatusPillProps {
  status: GetConfigurationsResponse['status'];
}

export function StatusPill({ status }: StatusPillProps) {
  if (status === 'active') {
    return (
      <span className="text-success-dark">
        <span className="text-color-success pr-1">⏺︎</span>Active
      </span>
    );
  }

  return <span>Inactive</span>;
}
