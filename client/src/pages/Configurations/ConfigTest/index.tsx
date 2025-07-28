import { NavigationContainer, SectionContainer } from '../layout';
import { StepsContainer, Steps } from '../Steps';
import { useParams } from 'react-router';
import NotFound from '../../NotFound';
import { Button } from '../../../components/Button';
import { Title } from '../../../components/Title';

export default function ConfigTest() {
  const { id } = useParams<{ id: string }>();

  if (!id) return <NotFound />;

  return (
    <div>
      <NavigationContainer>
        <Title>Condition name</Title>
        <StepsContainer>
          <Steps configurationId={id} />
          <Button to={`/configurations/${id}/activate`}>
            Next: Turn on configuration
          </Button>
        </StepsContainer>
      </NavigationContainer>
      <SectionContainer>
        <div>Configuration testing</div>
      </SectionContainer>
    </div>
  );
}
