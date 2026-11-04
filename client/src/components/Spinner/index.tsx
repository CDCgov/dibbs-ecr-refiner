import { ClipLoader } from 'react-spinners';

type SpinnerProps = React.ComponentProps<typeof ClipLoader> & {
  variant?: 'centered';
};

export function Spinner({ variant, ...props }: SpinnerProps) {
  if (variant === 'centered') {
    return (
      <div
        data-testid={'spinner'}
        className="absolute inset-0 flex items-center justify-center"
      >
        <ClipLoader {...props} />
      </div>
    );
  }

  return <ClipLoader data-testid={'spinner'} {...props} />;
}
