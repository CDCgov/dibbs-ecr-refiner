import { Container, Content } from './Layout';
import InformationSvg from '../../assets/information.svg';
import { Button } from '../../components/Button';
import { Label, Select } from '@trussworks/react-uswds';

interface ReportableConditionsProps {
  conditionNames: string[];
  onClick: () => void;
}
export function ReportableConditions({
  conditionNames,
  onClick,
}: ReportableConditionsProps) {
  return (
    <Container color="blue">
      <Content className="flex flex-col items-center">
        <img className="p-3" src={InformationSvg} alt="Information icon" />
        <div className="flex flex-col items-center gap-10">
          <div className="flex flex-col items-center gap-6">
            <div className="flex flex-col items-center gap-3">
              <p className="text-center text-xl font-bold text-black">
                We found these reportable conditions:
              </p>
              {conditionNames.length > 0 ? (
                <ul className="list-disc text-xl font-bold text-black">
                  {conditionNames.map((name) => (
                    <li key={name}>{name}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          </div>
          <div className="flex w-full flex-col items-center">
            <Label htmlFor="filter-select">Select filter to test</Label>
            <Select id="filter-select" name="filter-select" className="w-full">
              <option>Sample filter</option>
            </Select>
          </div>

          <div>
            <Button onClick={onClick}>Refine eCR</Button>
          </div>
        </div>
      </Content>
    </Container>
  );
}
