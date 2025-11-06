import { useIsMutating } from '@tanstack/react-query';
import { Icon } from '@trussworks/react-uswds';

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

export function ConfigurationTitleBar({ step }: ConfigurationTitleBarProps) {
  const numSavingActions = useIsMutating();

  return (
    <div className="mt-8 mb-6 flex justify-start">
      <div className="flex flex-col">
        <div className="mb-2 flex items-center">
          <h2 className="text-gray-cool-90 mr-4 text-[1.75rem] font-bold">
            {CONFIGURATION_TITLE_CONTENTS[step].title}
          </h2>
          <div className="text-gray-cool-60 h-4 items-center italic">
            <div className="flex items-center">
              {numSavingActions > 0 ? (
                <>
                  <Icon.Autorenew className="text-blue-cool-50 rotate-circle h-6! w-6!"></Icon.Autorenew>
                  Saving
                </>
              ) : (
                <>
                  <Icon.Check className="text-state-success h-6! w-6!"></Icon.Check>{' '}
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
