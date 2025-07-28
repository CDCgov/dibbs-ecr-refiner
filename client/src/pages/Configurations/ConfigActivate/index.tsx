import { useParams } from 'react-router';
import { Title } from '../../../components/Title';
import NotFound from '../../NotFound';
import { NavigationContainer, SectionContainer } from '../layout';
import { StepsContainer, Steps } from '../Steps';

export default function ConfigActivate() {
  const { id } = useParams<{ id: string }>();

  if (!id) return <NotFound />;

  return (
    <div>
      <NavigationContainer>
        <Title>Name</Title>
        <StepsContainer>
          <Steps configurationId={id} />
        </StepsContainer>
      </NavigationContainer>
      <SectionContainer>
        <div>Configuration activation</div>
      </SectionContainer>
    </div>
  );
}
