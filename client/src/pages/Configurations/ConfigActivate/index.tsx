import { useParams } from 'react-router';
import { Title } from '../../../components/Title';
import { NotFound } from '../../NotFound';
import {
  NavigationContainer,
  SectionContainer,
  TitleContainer,
} from '../layout';
import { StepsContainer, Steps } from '../Steps';
import { ConfigurationTitleBar } from '../ConfigurationTitleBar';
// import { useGetConfiguration } from '../../../api/configurations/configurations';
// import { Spinner } from '../../../components/Spinner';

export function ConfigActivate() {
  const { id } = useParams<{ id: string }>();

  // const {
  //   data: response,
  //   isPending,
  //   isError
  // } = useGetConfiguration(id ?? '');

  // if (isPending) return <Spinner variant="centered" />;
  // if (!id || isError) return 'Error!';

  /**
   * Delete this and uncomment everything else.
   */
  if (!id) return <NotFound />;

  return (
    <div>
      <TitleContainer>
        <Title>Condition name</Title>
        {/* <Status version={response.data.active_version} /> */}
      </TitleContainer>
      <NavigationContainer>
        {/* <VersionMenu
          id={response.data.id}
          currentVersion={response.data.version}
          status={response.data.status}
          versions={response.data.all_versions}
          step="activate"
        /> */}
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
