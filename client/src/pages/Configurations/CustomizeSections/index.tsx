import { useParams } from 'react-router';
import { useGetConfiguration } from '../../../api/configurations/configurations';
import { Spinner } from '@components/Spinner';
import { Button } from '@components/Button';
import { SectionModalState, Sections } from './Sections';
import { Header, SectionContainer } from '../layout';
import { ConfigurationTitleBar } from '../ConfigurationTitleBar';
import { useState } from 'react';
import { useConfigLock } from '../../../hooks/useConfigLock';

export function CustomizeSections() {
  const { id } = useParams<{ id: string }>();

  // acquire lock on mount, schedule release on unmount
  useConfigLock(id);

  const {
    data: configuration,
    isPending,
    isError,
  } = useGetConfiguration(id ?? '');

  const [modalState, setModalState] = useState<SectionModalState>({
    isOpen: false,
    selectedSection: null,
  });

  if (isPending) return <Spinner variant="centered" />;
  if (!id || isError) return 'Error!';

  const isDisabled =
    configuration.data.is_locked || !configuration.data.is_draft;

  return (
    <div className="flex flex-1 flex-col">
      <Header configuration={configuration.data} />
      <SectionContainer>
        <div className="mb-4 flex items-center justify-between">
          <ConfigurationTitleBar
            title="Customize eICR sections"
            subtitle="Choose which sections of your eICR to include, as well as whether to refine or retain each section."
          />
          {!isDisabled && (
            <Button
              variant="secondary"
              className="m-0! p-2! px-4! text-sm! whitespace-nowrap"
              onClick={() =>
                setModalState({ isOpen: true, selectedSection: null })
              }
            >
              Add custom section <span aria-hidden>+</span>
            </Button>
          )}
        </div>
        <Sections
          configuration={configuration.data}
          disabled={isDisabled}
          modalState={modalState}
          setModalState={setModalState}
        />
      </SectionContainer>
    </div>
  );
}
