import { Button } from '../../components/Button';
import { Container, Content } from './Layout';
import UploadSvg from '../../assets/upload.svg';

interface RunTestProps {
  onClick: () => void;
}
export function RunTest({ onClick }: RunTestProps) {
  return (
    <Container color="blue">
      <Content className="flex gap-3">
        <img src={UploadSvg} alt="" className="p-3" />
        <div className="flex flex-col items-center gap-6">
          <p className="text-base font-normal text-black">
            We will upload a test file for you to view the refinement results
          </p>
          <Button onClick={onClick}>Run test</Button>
          <a
            className="justify-start text-base font-bold text-blue-300 hover:underline"
            href="/api/demo/download"
            download
          >
            Download test file
          </a>
        </div>
      </Content>
    </Container>
  );
}
