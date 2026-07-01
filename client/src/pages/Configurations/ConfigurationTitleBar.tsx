import { SpinnerWithMinimalRender } from '@components/Spinner/SpinnerWithMinimalRender';
import { useIsMutating } from '@tanstack/react-query';

type ConfigurationSteps = 'build' | 'test' | 'activate';

interface ConfigurationTitleBarProps {
  step: ConfigurationSteps;
  condition: string;
}

interface ConfigurationTitleContent {
  title: string;
  subtitle: React.ReactNode;
}

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

  const numSavingActions = useIsMutating();

  return (
    <div className="mt-8 mb-6 flex justify-start">
      <div className="flex flex-col">
        <div className="mb-2 flex items-center">
          <h2 className="text-gray-cool-90 mr-4 text-[1.75rem] font-bold">
            {CONFIGURATION_TITLE_CONTENTS[step].title}
          </h2>
          {step === 'build' && (
            <div className="text-gray-cool-60 h-4 items-center italic">
              <div className="flex items-center">
                <SpinnerWithMinimalRender
                  isLoading={numSavingActions > 0}
                  renderWhenDone={
                    <div className="flex items-center">
                      <CheckIcon />
                      Saved
                    </div>
                  }
                />
              </div>
            </div>
          )}
        </div>
        {CONFIGURATION_TITLE_CONTENTS[step].subtitle}
      </div>
    </div>
  );
}

function CheckIcon() {
  return (
    <svg
      aria-hidden
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      className="fill-state-success"
    >
      <path d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
    </svg>
  );
}
