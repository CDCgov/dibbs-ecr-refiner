import ErrorSvg from '../../assets/red-x.svg';
import { Button } from '../../components/Button';

import { Container, Content } from './Layout';

interface ErrorProps {
  onClick: () => void;
}

export function Error({ onClick }: ErrorProps) {
  return (
    <Container color="red">
      <Content className="gap-10">
        <div className="flex flex-col items-center">
          <img
            className="p-8"
            src={ErrorSvg}
            alt="Red X indicating an error occured during upload."
          />
          <div className="flex flex-col items-center gap-6">
            <p className="text-xl font-bold text-black">
              The file could not be read.
            </p>
            <p className="leading-snug">
              Please double check the format and size. It must be less than 1GB.
            </p>
          </div>
        </div>
        <Button onClick={onClick}>Try again</Button>
      </Content>
    </Container>
  );
}
