import classNames from 'classnames';
import { Button } from '../../components/Button';
import { Icon } from '@trussworks/react-uswds';

// PLACEHOLDER - this will come from the API
interface Conditions {
  found: { display_name: string }[];
  missing: { display_name: string }[];
}

interface ReportableConditionsResultsProps {
  conditions: Conditions;
  startOver: () => void;
  goToSuccessScreen: () => void;
}

export function ReportableConditionsResults({
  conditions,
  startOver,
  goToSuccessScreen,
}: ReportableConditionsResultsProps) {
  const hasFoundConditions = conditions.found.length > 0;
  // const hasFoundConditions = false;
  // PLACEHOLDER - remove this

  const hasMissingConditions = conditions.missing.length > 0;

  if (hasFoundConditions) {
    return (
      <Container className="lg:w-4/7">
        <ConditionsContainer>
          <FoundConditions foundConditions={conditions.found} />
          {hasMissingConditions ? (
            <>
              <hr className="border-gray-cool-20" />
              <MissingConditions missingConditions={conditions.missing} />
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

  return (
    <Container className="max-w-[47rem]">
      <ConditionsContainer>
        <MissingConditions missingConditions={conditions.missing} />
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
  foundConditions: { display_name: string }[];
}

function FoundConditions({ foundConditions }: FoundConditionsProps) {
  return (
    <div className="flex flex-col gap-4">
      <p className="font-bold">
        We found the following reportable condition(s) in the RR:
      </p>
      <ul className="ml-2 list-inside list-disc">
        {foundConditions.map((foundCondition) => (
          <li key={foundCondition.display_name}>
            {foundCondition.display_name}
          </li>
        ))}
      </ul>
    </div>
  );
}

interface MissingConditionsProps {
  missingConditions: { display_name: string }[];
}

function MissingConditions({ missingConditions }: MissingConditionsProps) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-4">
        <Icon.Warning
          className="[&_path]:fill-state-error shrink-0"
          aria-label="Warning"
          size={3}
        />
        <p className="text-state-error-dark">
          The following detected conditions have not been configured and will
          not produce a refined eICR in the output
        </p>
      </div>
      <ul className="ml-2 list-inside list-disc">
        {missingConditions.map((missingCondition) => (
          <li key={missingCondition.display_name}>
            {missingCondition.display_name}
          </li>
        ))}
      </ul>
    </div>
  );
}
