import { Header, SectionContainer } from '../layout';
import { useParams } from 'react-router';
import { useGetConfiguration } from '../../../api/configurations/configurations';
import { ConfigurationTitleBar } from '../ConfigurationTitleBar';
import { Button } from '@components/Button';
import { Spinner } from '@components/Spinner';
import { useConfigLock } from '../../../hooks/useConfigLock';

export function Overrides() {
  const { id } = useParams<{ id: string }>();

  // lock on mount, schedule release on unmount
  useConfigLock(id);

  const {
    data: configuration,
    isPending,
    isError,
  } = useGetConfiguration(id ?? '');

  if (isPending) return <Spinner variant="centered" />;
  if (!id || isError) return 'Error!';

  const isDisabled =
    configuration.data.is_locked || !configuration.data.is_draft;

  return (
    <div>
      <Header configuration={configuration.data} />
      <SectionContainer>
        <div className="mb-4 flex items-center justify-between">
          <ConfigurationTitleBar
            title="Apply overrides"
            subtitle="Choose which code groups to omit from the refined output.
            Selections here take priority over previous configuration choices —
            any group omitted here is removed regardless of your Customize eICR
            sections and Manage codes selections."
          />
          {!isDisabled && (
            <Button
              variant="secondary"
              className="m-0! p-2! px-4! text-sm! whitespace-nowrap"
              onClick={() => {}}
            >
              Add code group <span aria-hidden>+</span>
            </Button>
          )}
        </div>

        <div className="bg-gray-cool-5 rounded-lg border border-gray-200 p-8 text-center">
          <h2 className="mb-4 text-2xl font-semibold text-gray-700">
            Coming Soon
          </h2>
          <p className="text-gray-700">
            The Overrides functionality is currently under development and will
            be available in a future release.
          </p>
        </div>
      </SectionContainer>
    </div>
  );
}
