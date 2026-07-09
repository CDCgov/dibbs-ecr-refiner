import { Button } from '@components/Button';

interface SerializedContentButtonProps {
  configurationId: string;
}

export function SerializedContentButton({
  configurationId,
}: SerializedContentButtonProps) {
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
