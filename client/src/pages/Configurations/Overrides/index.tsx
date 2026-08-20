import { Header, SectionContainer } from '../layout';
import { useParams } from 'react-router';
import { useGetConfiguration } from '../../../api/configurations/configurations';
import { ConfigurationTitleBar } from '../ConfigurationTitleBar';
import { Spinner } from '@components/Spinner';

export function Overrides() {
  const { id } = useParams<{ id: string }>();
  const {
    data: configuration,
    isPending,
    isError,
  } = useGetConfiguration(id ?? '');

  if (isPending) return <Spinner variant="centered" />;
  if (!id || isError) return 'Error!';

  return (
    <div>
      <Header configuration={configuration.data} />
      <SectionContainer>
        <div className="flex flex-wrap justify-between">
          <ConfigurationTitleBar
            title="Overrides"
            subtitle="Configure custom overrides for reportable conditions processing."
          />
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
