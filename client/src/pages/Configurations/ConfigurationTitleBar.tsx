import { SpinnerWithMinimalRender } from '@components/Spinner/TimedSpinner';
import { useIsMutating } from '@tanstack/react-query';
import { Icon } from '@trussworks/react-uswds';

type ConfigurationSteps = 'build' | 'test' | 'activate';

type ConfigurationTitleBarProps = {
  step: ConfigurationSteps;
  condition: string;
};

type ConfigurationTitleContent = {
  title: string;
  subtitle: React.ReactNode;
};

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
                  stopShowingSpinnerConditional={numSavingActions > 0}
                  renderWhenDone={() => (
                    <div className="flex items-center">
                      <Icon.Check
                        role="presentation"
                        className="text-state-success h-6! w-6!"
                      />
                      Saved
                    </div>
                  )}
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
