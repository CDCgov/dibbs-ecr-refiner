import { useParams } from 'react-router';
import NotFound from '../../NotFound';
import { Title } from '../../../components/Title';
import { Button } from '../../../components/Button';
import { Steps, StepsContainer } from '../Steps';
import { NavigationContainer, SectionContainer } from '../layout';

export default function ConfigBuild() {
  // Fetch config by ID on page load for each of these steps
  // build -> test -> activate
  const { id } = useParams<{ id: string }>();

  if (!id) return <NotFound />;

  return (
    <div>
      <NavigationContainer>
        <Title>Name</Title>
        <StepsContainer>
          <Steps configurationId={id} />
          <Button to={`/configurations/${id}/test`}>
            Next: Test Configuration
          </Button>
        </StepsContainer>
      </NavigationContainer>
      <SectionContainer>
        <div>Configuration building</div>
      </SectionContainer>
    </div>
  );
}
