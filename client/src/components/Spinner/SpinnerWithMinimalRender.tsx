import { useEffect, useRef, useState } from 'react';
import { sleep } from '../../utils';

type SpinnerWithMinimalRenderProps = {
  isLoading: boolean;
  renderWhenDone: React.ReactNode;
  loadingMessage?: string;
  minimalRenderDuration?: number;
};

const TWO_SECONDS_IN_MILLISECONDS = 2000;

export function SpinnerWithMinimalRender({
  isLoading,
  renderWhenDone,
  loadingMessage = 'Saving',
  minimalRenderDuration = TWO_SECONDS_IN_MILLISECONDS,
}: SpinnerWithMinimalRenderProps) {
  const shouldShowSpinner = useDisplaySpinnerWithMinimalRender(
    isLoading,
    minimalRenderDuration
  );

  return shouldShowSpinner ? (
    <SpinnerWithMessage loadingMessage={loadingMessage} />
  ) : (
    renderWhenDone
  );
}

type SpinnerWithMessageProps = {
  loadingMessage: string;
};
function SpinnerWithMessage({ loadingMessage }: SpinnerWithMessageProps) {
  return (
    <div className="flex items-center">
      <AnimatedSpinnerIcon />
      <div>{loadingMessage}</div>
    </div>
  );
}

function useDisplaySpinnerWithMinimalRender(
  isLoading: boolean,
  minimalRenderDuration: number
) {
  const [shouldShowSpinner, setShouldShowSpinner] = useState(false);
  const spinnerStart = useRef<number>(0);

  useEffect(() => {
    async function showSpinnerWithMinimalRenderDuration() {
      if (isLoading) {
        spinnerStart.current = performance.now();
        setShouldShowSpinner(true);
      }
      if (!isLoading && spinnerStart.current) {
        const spinnerEnd = performance.now();
        const spinnerDuration = spinnerEnd - spinnerStart.current;

        if (spinnerDuration < minimalRenderDuration) {
          // show the saving confirmation for at least desired duration so the
          // UI change registers to the user
          await sleep(minimalRenderDuration - spinnerDuration);
        }
        setShouldShowSpinner(false);
        spinnerStart.current = 0;
      }
    }

    void showSpinnerWithMinimalRenderDuration();
  }, [minimalRenderDuration, isLoading]);

  return shouldShowSpinner;
}

function AnimatedSpinnerIcon() {
  return (
    <svg
      aria-hidden
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      className="fill-blue-cool-50 animate-spin"
    >
      <path d="M12 6v3l4-4-4-4v3c-4.42 0-8 3.58-8 8 0 1.57.46 3.03 1.24 4.26L6.7 14.8A5.87 5.87 0 0 1 6 12c0-3.31 2.69-6 6-6zm6.76 1.74L17.3 9.2c.44.84.7 1.79.7 2.8 0 3.31-2.69 6-6 6v-3l-4 4 4 4v-3c4.42 0 8-3.58 8-8 0-1.57-.46-3.03-1.24-4.26z" />
    </svg>
  );
}
