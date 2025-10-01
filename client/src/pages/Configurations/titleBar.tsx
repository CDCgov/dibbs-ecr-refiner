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
  return (
    <div className="mt-8 mb-6 flex justify-start">
      <div className="flex flex-col">
        <h2 className="text-gray-cool-90 pb-2 text-[1.75rem] font-bold">
          {CONFIGURATION_TITLE_CONTENTS[step].title}
        </h2>
        <p> {CONFIGURATION_TITLE_CONTENTS[step].subtitle}</p>
      </div>
    </div>
  );
}
