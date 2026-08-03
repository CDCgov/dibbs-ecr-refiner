import { Button, ButtonProps } from '@components/Button';

type ActivateButtonProps = Pick<ButtonProps, 'onClick' | 'disabled'>;

/**
 * This is a thin wrapper around a button to use for both "activating"
 * and "switching".
 */
export function ActivateButton({ onClick, disabled }: ActivateButtonProps) {
  return (
    <Button onClick={onClick} variant="primary" disabled={disabled}>
      Activate this version
    </Button>
  );
}
