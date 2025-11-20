import { useParams } from 'react-router';
import { Title } from '../../../components/Title';
import { NotFound } from '../../NotFound';
import {
  NavigationContainer,
  SectionContainer,
  TitleContainer,
} from '../layout';
import { StepsContainer, Steps } from '../Steps';
import { ConfigurationTitleBar } from '../titleBar';

export function ConfigActivate() {
  const { id } = useParams<{ id: string }>();

  if (!id) return <NotFound />;

  return (
    <div>
      <TitleContainer>
        <Title>Condition name</Title>
      </TitleContainer>
      <NavigationContainer>
        <StepsContainer>
          <Steps configurationId={id} />
        </StepsContainer>
      </NavigationContainer>
      <SectionContainer>
        <ConfigurationTitleBar step="activate" />
        <div>Configuration activation</div>
      </SectionContainer>
    </div>
  );
}
