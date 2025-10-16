import classNames from 'classnames';
import { Button } from '../../components/Button';
import { WarningIcon } from '../../components/WarningIcon';

interface ReportableConditionsResultsProps {
  matchedConditions: string[];
  unmatchedConditions: string[];
  startOver: () => void;
  goToSuccessScreen: () => void;
}

export function ReportableConditionsResults({
  matchedConditions,
  unmatchedConditions,
  startOver,
  goToSuccessScreen,
}: ReportableConditionsResultsProps) {
  const hasFoundConditions = matchedConditions.length > 0;
  const hasMissingConditions = unmatchedConditions.length > 0;

  // TODO: This is placeholder design and copy.
  // No conditions to display.
  // This is when a valid eICR/RR zip is uploaded but doesn't contain the uploader's jurisdiction ID for any reportable conditions.
  if (!hasFoundConditions && !hasMissingConditions) {
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
  if (hasFoundConditions) {
    return (
      <Container className="lg:w-4/7">
        <ConditionsContainer>
          <FoundConditions foundConditions={matchedConditions} />
          {hasMissingConditions ? (
            <>
              <hr className="border-gray-cool-20" />
              <MissingConditions missingConditions={unmatchedConditions} />
            </>
          ) : null}
        </ConditionsContainer>
        <div className="flex flex-col gap-4 md:w-full">
          <p>Would you like to refine the eCR?</p>
          <p>
            Taking this action will split the original eICR, producing one
            refined eICR for each reportable condition and retaining content
            relevant only to that condition as defined in its configuration.
          </p>
        </div>
        <div className="flex flex-col gap-4 sm:flex-row sm:gap-0">
          <Button onClick={goToSuccessScreen}>Refine eCR</Button>
          <Button variant="secondary" onClick={startOver}>
            Start over
          </Button>
        </div>
      </Container>
    );
  }

  // Display only missing conditions
  return (
    <Container className="max-w-[47rem]">
      <ConditionsContainer>
        <MissingConditions missingConditions={unmatchedConditions} />
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
    <div className="!border-blue-cool-20 flex flex-col gap-5 rounded-lg border border-dashed bg-white px-6 py-8">
      {children}
    </div>
  );
}

interface FoundConditionsProps {
  foundConditions: string[];
}

function FoundConditions({ foundConditions }: FoundConditionsProps) {
  return (
    <div className="flex flex-col gap-4">
      <p className="font-bold">
        We found the following reportable condition(s) in the RR:
      </p>
      <ul className="ml-2 list-inside list-disc">
        {foundConditions.map((foundCondition) => (
          <li key={foundCondition}>{foundCondition}</li>
        ))}
      </ul>
    </div>
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
