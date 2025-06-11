import { Container, Content } from './Layout';
import InformationSvg from '../../assets/information.svg';
import { Button } from '../../components/Button';

interface ReportableConditionsProps {
  conditionNames: string[];
  onClick: () => void;
}
export function ReportableConditions({
  conditionNames,
  onClick,
}: ReportableConditionsProps) {
  return (
    <div className="flex flex-col gap-12">
      <h2 className="font-merriweather text-3xl font-bold text-black">
        Test filter
      </h2>
      <Container color="blue">
        <Content className="flex flex-col items-center">
          <img className="p-3" src={InformationSvg} alt="Information icon" />
          <div className="flex flex-col items-center gap-10">
            <div className="flex flex-col items-center gap-6">
              <div className="flex flex-col items-center gap-3">
                <p className="text-center text-xl font-bold text-black">
                  We found the following reportable condition(s) in the RR:
                </p>
                {conditionNames.length > 0 ? (
                  <ul className="list-disc text-xl font-bold text-black">
                    {conditionNames.map((name) => (
                      <li key={name}>{name}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
              <div className="flex max-w-[800px] flex-col items-center gap-4 text-center">
                <p>Would you like to refine the eCR?</p>
                <p>
                  Taking this action will split the original eICR into two
                  eICRs, one for each reportable condition, and retain content
                  relevant only to that condition as defined in the TES (see
                  landing page for more details).
                </p>
              </div>
            </div>
            <div>
              <Button onClick={onClick}>Refine eCR</Button>
            </div>
          </div>
        </Content>
      </Container>
    </div>
  );
}
