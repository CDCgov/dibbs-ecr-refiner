import { useEffect, useRef, useState } from 'react';
import { sleep } from '../../utils';
import { Icon } from '@trussworks/react-uswds';

type SpinnerWithMinimalRenderProps = {
  stopShowingSpinnerConditional: boolean;
  renderWhenDone: React.ReactNode;
  loadingMessage?: string;
  minimalRenderDuration?: number;
};

const TWO_SECONDS_IN_MILLISECONDS = 2000;

export function SpinnerWithMinimalRender({
  stopShowingSpinnerConditional,
  renderWhenDone,
  loadingMessage = 'Saving',
  minimalRenderDuration = TWO_SECONDS_IN_MILLISECONDS,
}: SpinnerWithMinimalRenderProps) {
  const shouldShowSpinner = useDisplaySpinnerWithMinimalRender(
    stopShowingSpinnerConditional,
    minimalRenderDuration
  );

  return shouldShowSpinner ? (
    <SpinnerWithMessage loadingMessage={loadingMessage}></SpinnerWithMessage>
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
      <Icon.Autorenew
        role="presentation"
        className="text-blue-cool-50 h-6! w-6! animate-spin"
        aria-hidden
      />
      <div>{loadingMessage}</div>
    </div>
  );
}

function useDisplaySpinnerWithMinimalRender(
  stopShowingSpinnerConditional: boolean,
  minimalRenderDuration: number
) {
  const [shouldShowSpinner, setShouldShowSpinner] = useState(false);
  const spinnerStart = useRef<number>(0);

  useEffect(() => {
    async function showSpinnerWithMinimalRenderDuration() {
      if (stopShowingSpinnerConditional) {
        spinnerStart.current = performance.now();
        setShouldShowSpinner(true);
      }
      if (!stopShowingSpinnerConditional && spinnerStart.current) {
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
  }, [minimalRenderDuration, stopShowingSpinnerConditional]);

  return shouldShowSpinner;
}
