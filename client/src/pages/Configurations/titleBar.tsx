import { useIsMutating } from '@tanstack/react-query';
import { Icon } from '@trussworks/react-uswds';
import { useEffect, useState } from 'react';

type ConfigurationSteps = 'build' | 'test' | 'activate';

type ConfigurationTitleBarProps = {
  step: ConfigurationSteps;
};

const CONFIGURATION_TITLE_CONTENTS = {
  build: {
    title: 'Build configuration',
    subtitle: 'Review and select the data to retain in the eCRs you receive.',
  },
  test: {
    title: 'Test configuration',
    subtitle: 'Check the results of your configuration before turning it on.',
  },
  activate: {
    title: 'Turn on configuration',
    subtitle:
      'Refiner will immediately start to refine eCRs with gonorrhea as a reportable condition, in accordance with this configuration.',
  },
};

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

const TWO_SECONDS_IN_MILLISECONDS = 2000;

export function ConfigurationTitleBar({ step }: ConfigurationTitleBarProps) {
  const [shouldShowIsSpinning, setShouldShowIsSpinning] = useState(false);
  const numSavingActions = useIsMutating();

  useEffect(() => {
    async function showSavingStateWithDelay() {
      const start = performance.now();
      setShouldShowIsSpinning(true);
      const end = performance.now();
      const duration = start - end;
      if (duration < TWO_SECONDS_IN_MILLISECONDS) {
        await sleep(TWO_SECONDS_IN_MILLISECONDS - duration);
      }
      setShouldShowIsSpinning(false);
    }
    if (numSavingActions > 0) {
      void showSavingStateWithDelay();
    }
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
              {shouldShowIsSpinning ? (
                <>
                  <Icon.Autorenew
                    aria-label="icon indicating saving in progress"
                    className="text-blue-cool-50 h-6! w-6! animate-spin"
                  ></Icon.Autorenew>
                  Saving
                </>
              ) : (
                <>
                  <Icon.Check
                    aria-label="icon indicating saving completed"
                    className="text-state-success h-6! w-6!"
                  ></Icon.Check>{' '}
                  Saved
                </>
              )}
            </div>
          </div>
        </div>
        <p> {CONFIGURATION_TITLE_CONTENTS[step].subtitle}</p>
      </div>
    </div>
  );
}
