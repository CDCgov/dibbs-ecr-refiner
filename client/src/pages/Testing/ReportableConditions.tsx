import { Container, Content } from './Layout';
import { Button } from '../../components/Button';
import { Title } from './Title';

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
      <Title>Test filter</Title>
      <Container color="blue">
        <Content className="flex flex-col">
          <div className="flex flex-col gap-10">
            <div className="flex flex-col gap-6">
              <div className="flex flex-col gap-3">
                <p className="text-xl font-bold text-black">
                  We found the following reportable condition(s) in the RR:
                </p>
                {conditionNames.length > 0 ? (
                  <ul className="list-none text-xl font-bold text-black">
                    {conditionNames.map((name) => (
                      <li
                        className="relative pl-4 before:absolute before:left-0 before:text-2xl before:text-black before:content-['•']"
                        key={name}
                      >
                        {name}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
              <div className="flex max-w-[800px] flex-col gap-4">
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
