import classNames from 'classnames';
import { Button } from '@components/Button';
import { WarningIcon } from '@components/WarningIcon';
import { DiscoveredConfigurationGroup } from '../../api/schemas';
import { Field } from '@components/Field';
import { Label } from '@components/Label';
import { Select, SelectContainer } from '@components/Select';
import { Checkbox } from '@components/Checkbox';
import { useState } from 'react';

interface ReportableConditionsResultsProps {
  configurationGroups: DiscoveredConfigurationGroup[];
  inactiveConditions: string[];
  unmatchedConditions: string[];
  startOver: () => void;
  goToSuccessScreen: () => void;
}

export function ReportableConditionsResults({
  configurationGroups,
  unmatchedConditions,
  startOver,
  goToSuccessScreen,
}: ReportableConditionsResultsProps) {
  const matchedGroupsWithConfig = configurationGroups.filter(
    (cg) => cg.versions.length > 0
  );
  const matchedGroupsWithoutConfig = configurationGroups.filter(
    (cg) => cg.versions.length === 0
  );

  const [groupSelections, setGroupSelections] = useState<
    Map<string, { checked: boolean; selectedId: string }>
  >(
    () =>
      new Map(
        matchedGroupsWithConfig.map((cg) => [
          cg.name,
          {
            checked: true,
            // try to set "active" as the default, otherwise fall back to whatever is first
            selectedId:
              cg.versions.find((v) => v.status === 'active')?.id ??
              cg.versions[0]?.id,
          },
        ])
      )
  );

  const checkedSelections = [...groupSelections.values()].filter(
    (s) => s.checked
  );

  function toggleGroup(name: string) {
    setGroupSelections((prev) => {
      const next = new Map(prev);
      const current = next.get(name)!;
      next.set(name, { ...current, checked: !current.checked });
      return next;
    });
  }

  function setSelectedId(name: string, id: string) {
    setGroupSelections((prev) => {
      const next = new Map(prev);
      const current = next.get(name)!;
      next.set(name, { ...current, selectedId: id });
      return next;
    });
  }

  // TODO: This is placeholder design and copy.
  // No conditions to display.
  // This is when a valid eICR/RR zip is uploaded but doesn't contain the uploader's jurisdiction ID for any reportable conditions.
  if (configurationGroups.length === 0) {
    return (
      <Container>
        <ConditionsContainer>
          <div className="flex items-center gap-4">
            <WarningIcon aria-label="Warning" size={3} />
            <p className="text-state-error-dark">
              No conditions reportable to your jurisdiction were found in the
              RR.
            </p>
          </div>
        </ConditionsContainer>
        <div>
          <Button variant="primary" onClick={startOver}>
            Start over
          </Button>
        </div>
      </Container>
    );
  }

  // Display matched conditions and potentially also missing conditions
  if (matchedGroupsWithConfig.length > 0) {
    return (
      <Container className="lg:w-4/7">
        <ConditionsContainer>
          <p className="font-bold">
            We found the following reportable condition(s) in the RR:
          </p>
          {matchedGroupsWithConfig.map((cg) => {
            const selection = groupSelections.get(cg.name)!;
            return (
              <div key={cg.name} className="flex gap-2">
                <Checkbox
                  checked={selection.checked}
                  onChange={() => toggleGroup(cg.name)}
                />
                <SelectContainer>
                  <Field>
                    <Label>{cg.name}</Label>
                    <Select
                      value={selection.selectedId}
                      onChange={(e) => setSelectedId(cg.name, e.target.value)}
                    >
                      {cg.versions.map((v) => (
                        <option key={v.id} value={v.id}>
                          Version {v.version} ({v.status})
                        </option>
                      ))}
                    </Select>
                  </Field>
                </SelectContainer>
              </div>
            );
          })}

          {matchedGroupsWithoutConfig.length > 0 && (
            <>
              <hr className="border-gray-cool-20" />

              <ConditionWarnings
                missingConditions={matchedGroupsWithoutConfig.map(
                  (wc) => wc.name
                )}
              />
            </>
          )}
        </ConditionsContainer>
        <div className="flex flex-col gap-4 md:w-full">
          <p>Would you like to refine the eCR?</p>
          <p>
            Taking this action will split the original eICR, producing one
            refined eICR for each reportable condition and retaining content
            relevant only to that condition as defined in its configuration.
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:gap-4">
          <Button
            disabled={checkedSelections.length === 0}
            onClick={goToSuccessScreen}
          >
            Refine eCR
          </Button>
          <Button variant="secondary" onClick={startOver}>
            Start over
          </Button>
        </div>
      </Container>
    );
  }

  // Display only condition warnings
  return (
    <Container className="max-w-188">
      <ConditionsContainer>
        <ConditionWarnings missingConditions={unmatchedConditions} />
      </ConditionsContainer>
      <div className="flex flex-col gap-4 md:w-lg">
        <p>
          Please either create configurations for these conditions or upload a
          file that includes conditions that have been configured.
        </p>
        <div>
          <Button onClick={startOver}>Start over</Button>
        </div>
      </div>
    </Container>
  );
}

interface ContainerProps {
  children: React.ReactNode;
  className?: string;
}

function Container({ children, className }: ContainerProps) {
  return (
    <div className={classNames('flex flex-col gap-8', className)}>
      {children}
    </div>
  );
}

function ConditionsContainer({ children }: { children: React.ReactNode }) {
  return (
    <div className="border-blue-cool-20! flex flex-col gap-5 rounded-lg border border-dashed bg-white px-6 py-8">
      {children}
    </div>
  );
}

interface ConditionWarningsProps {
  missingConditions: string[];
}
function ConditionWarnings({ missingConditions }: ConditionWarningsProps) {
  const hasMissingConditions = missingConditions.length > 0;
  return (
    <>
      {hasMissingConditions ? (
        <MissingConditions missingConditions={missingConditions} />
      ) : null}
    </>
  );
}
interface MissingConditionsProps {
  missingConditions: string[];
}
function MissingConditions({ missingConditions }: MissingConditionsProps) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-4">
        <WarningIcon aria-label="Warning" size={3} />
        <p className="text-state-error-dark">
          The following detected conditions have not been configured and will
          not produce a refined eICR in the output.
        </p>
      </div>
      <ul className="ml-2 list-inside list-disc">
        {missingConditions.map((missingCondition) => (
          <li key={missingCondition}>{missingCondition}</li>
        ))}
      </ul>
    </div>
  );
}
