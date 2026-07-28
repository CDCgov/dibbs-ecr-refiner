import { useParams } from 'react-router';
import { useGetConfiguration } from '../../../api/configurations/configurations';
import { useConfigLockRelease } from '../../../hooks/useConfigLockRelease';
import { Spinner } from '@components/Spinner';
import { Sections } from '../ManageCodes/Sections';
import { Header, SectionContainer } from '../layout';

export function CustomizeSections() {
  const { id } = useParams<{ id: string }>();

  // release lock on beforeunload
  useConfigLockRelease(id);

  const {
    data: configuration,
    isPending,
    isError,
  } = useGetConfiguration(id ?? '');

  if (isPending) return <Spinner variant="centered" />;
  if (!id || isError) return 'Error!';

  return (
    <>
      <Header configuration={configuration.data} />
      <SectionContainer>
        <Sections
          configurationId={configuration.data.id}
          disabled={false}
          sections={configuration.data.section_processing}
        />
      </SectionContainer>
    </>
  );
}
