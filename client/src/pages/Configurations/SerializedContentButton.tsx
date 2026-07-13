import { Button } from '@components/Button';
import { useGetEnv } from '../../hooks/useGetEnv';

interface SerializedContentButtonProps {
  configurationId: string;
}

export function SerializedContentButton({
  configurationId,
}: SerializedContentButtonProps) {
  const env = useGetEnv();
  if (env === 'live') return;

  return (
    <Button
      className="m-0! p-0!"
      to={`/configurations/${configurationId}/serialized`}
      variant="tertiary"
    >
      View serialized configuration (local only)
    </Button>
  );
}
