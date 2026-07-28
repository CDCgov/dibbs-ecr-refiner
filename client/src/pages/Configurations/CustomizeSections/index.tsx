import { useParams } from 'react-router';
import { useGetConfiguration } from '../../../api/configurations/configurations';
import { useConfigLockRelease } from '../../../hooks/useConfigLockRelease';
import { Spinner } from '@components/Spinner';
import { Sections } from './Sections';
import { Header, SectionContainer } from '../layout';
import { ConfigurationTitleBar } from '../ConfigurationTitleBar';
import { Button } from '@components/Button';
import { useState } from 'react';
import { DbConfigurationSectionProcessing } from '../../../api/schemas/dbConfigurationSectionProcessing';

export function CustomizeSections() {
  const { id } = useParams<{ id: string }>();

  // release lock on beforeunload
  useConfigLockRelease(id);

  const {
    data: configuration,
    isPending,
    isError,
  } = useGetConfiguration(id ?? '');
  const [selectedSection, setSelectedSection] =
    useState<DbConfigurationSectionProcessing | null>(null);
  const [isCustomSectionModalOpen, setIsCustomSectionModalOpen] =
    useState(false);

  if (isPending) return <Spinner variant="centered" />;
  if (!id || isError) return 'Error!';

  const isDisabled =
    configuration.data.is_locked || !configuration.data.is_draft;

  return (
    <div>
      <Header configuration={configuration.data} />
      <SectionContainer>
        <div className="flex items-start justify-between">
          <ConfigurationTitleBar
            title="Customize eICR Sections"
            subtitle="Choose which sections of your eICR to include, as well as whether to refine or retain each section."
          />
          {isDisabled ? null : (
            <Button
              variant="tertiary"
              onClick={() => {
                setSelectedSection(null);
                setIsCustomSectionModalOpen(true);
              }}
            >
              Add custom section <span aria-hidden>+</span>
            </Button>
          )}
        </div>
        <Sections
          configurationId={configuration.data.id}
          disabled={isDisabled}
          sections={configuration.data.section_processing}
          setSelectedSection={setSelectedSection}
          selectedSection={selectedSection}
          setIsCustomSectionModalOpen={setIsCustomSectionModalOpen}
          isCustomSectionModalOpen={isCustomSectionModalOpen}
        />
      </SectionContainer>
    </div>
  );
}
