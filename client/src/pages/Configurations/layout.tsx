import { Modal, ModalBody, ModalHeader, ModalTitle } from '@components/Modal';
import { Title } from '@components/Title';
import { QuestionIcon } from '@components/Tooltip/QuestionIcon';
import { Button } from '@components/Button';
import { useState } from 'react';
import { GetConfigurationResponse, DbCode } from '../../api/schemas';
import { DraftBanner } from './ManageCodes/DraftBanner';
import { ConfigLockBanner } from './ManageCodes/Lock/ConfigLockBanner';
import { Status } from './ManageCodes/Status';
import { VersionMenu } from './ManageCodes/VersionMenu';
import { SerializedContentButton } from './SerializedContentButton';
import { StepsContainer, Steps } from './Steps';
import { ActivationButtons } from './ActivationButtons';

export function NavigationContainer({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="bg-blue-cool-5 drop-shadow-nav flex flex-col items-start gap-4 px-8 py-2 md:flex-row md:items-center md:py-2 lg:px-20">
      {children}
    </div>
  );
}

export function SectionContainer({ children }: { children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-8 px-8 py-9 lg:px-20">
      {children}
    </section>
  );
}

export function TitleContainer({ children }: { children: React.ReactNode }) {
  return <div className="px-8 py-6 shadow-lg lg:px-20">{children}</div>;
}

interface HeaderProps {
  configuration: GetConfigurationResponse;
}

export function Header({ configuration }: HeaderProps) {
  const [isRsgDetailsModalOpen, setIsRsgDetailsModalOpen] = useState(false);
  return (
    <div>
      <TitleContainer>
        <div className="flex flex-col items-start gap-2 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-col">
            <div className="flex flex-row items-center gap-2">
              <Title>{configuration.display_name}</Title>
              <Button
                variant="tertiary"
                onClick={() => setIsRsgDetailsModalOpen(true)}
                className="p-0!"
                aria-label="Open reporting specification details modal"
              >
                <QuestionIcon />
              </Button>
              <RsgDetailsModal
                open={isRsgDetailsModalOpen}
                onClose={() => setIsRsgDetailsModalOpen(false)}
                primaryConditionDisplayName={configuration.display_name}
                rsgCodes={configuration.rsg_codes}
              />
            </div>
            <Status version={configuration.active_version} />
          </div>
          <div className="flex flex-col gap-2 md:items-end">
            <ActivationButtons configurationData={configuration} />
            {configuration.active_version === configuration.version && (
              <SerializedContentButton configurationId={configuration.id} />
            )}
          </div>
        </div>
      </TitleContainer>
      <NavigationContainer>
        <VersionMenu
          id={configuration.id}
          currentVersion={configuration.version}
          status={configuration.status}
          versions={configuration.all_versions}
        />
        <StepsContainer>
          <Steps configurationId={configuration.id} />
        </StepsContainer>
      </NavigationContainer>
      {configuration.status !== 'draft' ? (
        <DraftBanner
          draftId={configuration.draft_id}
          conditionId={configuration.condition_id}
          latestVersion={configuration.latest_version}
        />
      ) : null}
      {configuration.is_locked ? (
        <ConfigLockBanner
          lockedByName={configuration.locked_by?.name}
          lockedByEmail={configuration.locked_by?.email}
        />
      ) : null}
    </div>
  );
}

interface RsgDetailsModal {
  open: boolean;
  onClose: () => void;
  rsgCodes: DbCode[];
  primaryConditionDisplayName: string;
}

function RsgDetailsModal({
  open,
  onClose,
  rsgCodes,
  primaryConditionDisplayName,
}: RsgDetailsModal) {
  return (
    <Modal
      className="max-w-160!"
      open={open}
      onClose={onClose}
      position="center"
    >
      <ModalHeader>
        <ModalTitle>{primaryConditionDisplayName}</ModalTitle>
        <p>
          Applies to eCR documents reportable for the conditions below. Only one
          output will be produced per condition group.
        </p>
      </ModalHeader>
      <ModalBody>
        <table>
          <thead className="border-b-gray-cool-20 border-b">
            <tr>
              <th scope="col" className="w-[40%] px-2 py-3 font-bold">
                SNOMED code
              </th>
              <th className="w-[60%] px-2 py-3 font-bold">Display name</th>
            </tr>
          </thead>
          <tbody className="divide-gray-cool-20 divide-y">
            {rsgCodes.map((c) => {
              return (
                <tr key={c.code}>
                  <td className="py-3 pl-2">{c.code}</td>
                  <td className="py-3 pl-2">{c.display}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </ModalBody>
    </Modal>
  );
}
