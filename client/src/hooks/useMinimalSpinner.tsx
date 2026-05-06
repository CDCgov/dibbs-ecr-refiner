import { useEffect, useRef, useState } from 'react';
import { sleep } from '../utils';
import { Icon } from '@trussworks/react-uswds';

const TWO_SECONDS_IN_MILLISECONDS = 2000;

// Spinner that renders for at least the value of minimalRenderDuration
// to make sure the UI doesn't blink to the user
export function useSpinnerWithMinimalRenderDuration(
  stopShowingSpinnerConditional: boolean,
  loadingMessage = 'Loading...',
  minimalRenderDuration = TWO_SECONDS_IN_MILLISECONDS
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

  return {
    shouldShowSpinner: shouldShowSpinner,
    minimalRenderSpinner: (
      <div className="flex items-center">
        <Icon.Autorenew
          role="presentation"
          className="text-blue-cool-50 h-6! w-6! animate-spin"
          aria-hidden
        />
        <div>{loadingMessage}</div>
      </div>
    ),
  };
}
