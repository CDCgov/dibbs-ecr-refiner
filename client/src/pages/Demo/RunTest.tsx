import { Button } from '../../components/Button';
import { Container, Content } from './Layout';
import UploadSvg from '../../assets/upload.svg';
import ForwardSvg from '../../assets/forward.svg';
import { Title } from './Title';

interface RunTestProps {
  onClick: () => void;
}
export function RunTest({ onClick }: RunTestProps) {
  return (
    <div className="flex flex-col gap-12">
      <Title>
        Test filter
      </Title>
      <div className="flex flex-col gap-6 xl:flex-row">
        <Container color="white">
          <Content className="flex items-start gap-6">
            <img className="px-3 py-1" src={UploadSvg} alt="" />
            <div className="flex flex-col gap-10">
              <p className="flex flex-col gap-2 text-black">
                <span className="font-bold">
                  Want to refine your own eCR file?
                </span>
                <span>Please upload a single eICR/RR pair as a .zip file.</span>
              </p>
              <div>
                <Button onClick={() => null}>Upload .zip file</Button>
              </div>
            </div>
          </Content>
        </Container>
        <Container color="blue">
          <Content className="flex items-start gap-6">
            <img className="px-3 py-5" src={ForwardSvg} alt="" />
            <div className="flex flex-col gap-10">
              <p className="flex flex-col gap-2 text-black">
                <span className="font-bold">Don't have a file ready?</span>
                <span>You can try out eCR Refiner with our test file.</span>
              </p>
              <div className="flex flex-col items-center gap-4 md:flex-row">
                <Button variant="secondary" onClick={onClick}>
                  Use test file
                </Button>
                <a
                  className="text-violet-warm-60 hover:text-violet-warm-70 justify-start font-bold hover:underline"
                  href="/api/v1/demo/download"
                  download
                >
                  Download test file
                </a>
              </div>
            </div>
          </Content>
        </Container>
      </div>
    </div>
  );
}
