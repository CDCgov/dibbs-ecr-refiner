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
          <p className="flex max-w-[500px] flex-col gap-4 text-center font-normal text-black">
            For this demo, we've provided a synthetic eICR/RR pair to test the
            Refiner that contains two reportable conditions.
            <span>
              The "Run test" button below will upload the test files to the
              Refiner.
            </span>
          </p>
          <Button onClick={onClick}>Run test</Button>
          <a
            className="justify-start font-bold text-blue-300 hover:underline"
            href="/api/v1/demo/download"
            download
          >
            Download test file
          </a>
        </div>
      </Content>
    </Container>
  );
}
