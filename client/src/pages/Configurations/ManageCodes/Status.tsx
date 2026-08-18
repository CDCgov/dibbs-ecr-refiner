import { StatusIndicator } from '../../../components/StatusIndicator';

interface StatusProps {
  version: number | null;
}

export function Status({ version }: StatusProps) {
  return (
    <p className="font-bold">
      <StatusIndicator isActive={!!version} />
    </p>
  );
}
