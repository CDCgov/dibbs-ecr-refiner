import { useIsMutating } from '@tanstack/react-query';
import { Icon } from '@trussworks/react-uswds';
import { useEffect, useRef, useState } from 'react';
import { sleep } from '../../utils';

type ConfigurationSteps = 'build' | 'test' | 'activate';

type ConfigurationTitleBarProps = {
  step: ConfigurationSteps;
  condition: string;
};

type ConfigurationTitleContent = {
  title: string;
  subtitle: React.ReactNode;
};

const TWO_SECONDS_IN_MILLISECONDS = 2000;

export function ConfigurationTitleBar({
  step,
  condition,
}: ConfigurationTitleBarProps) {
  const CONFIGURATION_TITLE_CONTENTS: {
    [step: string]: ConfigurationTitleContent;
  } = {
    build: {
      title: 'Build configuration',
      subtitle: (
        <p>Review and select the data to retain in the eCRs you receive.</p>
      ),
    },
    test: {
      title: 'Test configuration',
      subtitle: (
        <p>Check the results of your configuration before turning it on.</p>
      ),
    },
    activate: {
      title: 'Turn on configuration',
      subtitle: (
        <span>
          Refiner will <span className="font-bold">immediately</span> start to
          refine eCRs with {condition} as a reportable condition, in accordance
          with this configuration.
        </span>
      ),
    },
  };
  const [shouldShowSpinner, setShouldShowSpinner] = useState(false);
  const spinnerStart = useRef<number>(0);
  const numSavingActions = useIsMutating();

  useEffect(() => {
    async function resolveSpinnerDisplay() {
      if (numSavingActions > 0) {
        spinnerStart.current = performance.now();
        setShouldShowSpinner(true);
      }
      if (numSavingActions === 0 && spinnerStart.current) {
        const spinnerEnd = performance.now();
        const spinnerDuration = spinnerEnd - spinnerStart.current;

        if (spinnerDuration < TWO_SECONDS_IN_MILLISECONDS) {
          // show the saving confirmation for at least two seconds so the
          // UI change registers to the user
          await sleep(TWO_SECONDS_IN_MILLISECONDS - spinnerDuration);
        }
        setShouldShowSpinner(false);
        spinnerStart.current = 0;
      }
    }

    void resolveSpinnerDisplay();
  }, [numSavingActions]);

  return (
    <div className="mt-8 mb-6 flex justify-start">
      <div className="flex flex-col">
        <div className="mb-2 flex items-center">
          <h2 className="text-gray-cool-90 mr-4 text-[1.75rem] font-bold">
            {CONFIGURATION_TITLE_CONTENTS[step].title}
          </h2>
          <div className="text-gray-cool-60 h-4 items-center italic">
            <div className="flex items-center">
              {shouldShowSpinner ? (
                <>
                  <Icon.Autorenew
                    role="presentation"
                    className="text-blue-cool-50 h-6! w-6! animate-spin"
                  ></Icon.Autorenew>
                  Saving
                </>
              ) : (
                <>
                  <Icon.Check
                    role="presentation"
                    className="text-state-success h-6! w-6!"
                  ></Icon.Check>{' '}
                  Saved
                </>
              )}
            </div>
          </div>
        </div>
        {CONFIGURATION_TITLE_CONTENTS[step].subtitle}
      </div>
    </div>
  );
}
