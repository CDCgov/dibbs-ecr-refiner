import { Container, Content } from './Layout';
import InformationSvg from '../../assets/information.svg';
import { Button } from '../../components/Button';

interface ReportableConditionsProps {
  conditions: string[];
  onClick: () => void;
}
export function ReportableConditions({
  conditions,
  onClick,
}: ReportableConditionsProps) {
  return (
    <Container color="blue">
      <Content className="flex flex-col">
        <img className="p-3" src={InformationSvg} alt="Information icon" />
        <div className="flex flex-col items-center gap-10">
          <div className="flex flex-col gap-6">
            <div className="flex flex-col items-center gap-3">
              <p className="text-center text-xl font-bold text-black">
                We found the following reportable condition(s):
              </p>
              {conditions.length > 0 ? (
                <ul className="list-disc text-xl font-bold text-black">
                  {conditions.map((condition) => (
                    <li key={condition}>{condition}</li>
                  ))}
                </ul>
              ) : null}
            </div>
            <div className="flex flex-col items-center gap-2">
              <p>Would you like to refine the eCR?</p>
              <p>
                Taking this action will retain information relevant only to the
                conditions listed.
              </p>
            </div>
          </div>
          <div>
            <Button onClick={onClick}>Refine eCR</Button>
          </div>
        </div>
      </Content>
    </Container>
  );
}
