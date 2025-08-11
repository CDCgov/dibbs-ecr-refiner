import { useState } from 'react';
import { Condition } from '../../services/demo';
import { Label, Select } from '@trussworks/react-uswds';
import { Title } from '../../components/Title';
import { Diff } from '../../components/Diff';

interface SuccessProps {
  conditions: Condition[];
  unrefinedEicr: string;
  presignedDownloadUrl: string;
}

export function Success({
  conditions,
  presignedDownloadUrl,
  unrefinedEicr,
}: SuccessProps) {
  // defaults to first condition found
  const [selectedCondition, setSelectedCondition] = useState<Condition>(
    conditions[0]
  );

  function onChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const value = e.currentTarget.value;
    const newSelectedCondition = conditions.find((c) => c.code === value);

    if (!newSelectedCondition) return selectedCondition;

    setSelectedCondition(newSelectedCondition);
  }

  return (
    <div>
      <div className="flex items-center gap-4">
        <Title>eCR refinement results</Title>
          <Label htmlFor="condition-select" className="text-bold">
            CONDITION:
          </Label>
          <Select
            id="condition-select"
            name="condition-select"
            defaultValue={selectedCondition.code}
            onChange={onChange}
          >
            {conditions.map((c) => (
              <option key={c.code} value={c.code}>
                {c.display_name}
              </option>
            ))}
          </Select>
        </div>
        <Diff
          condition={selectedCondition}
          unrefinedEicr={unrefinedEicr}
          presignedDownloadUrl={presignedDownloadUrl}
        />
    </div>
  );
}
