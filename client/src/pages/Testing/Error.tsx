import ErrorSvg from '../../assets/red-x.svg';
import { Button } from '../../components/Button';

import { Container, Content } from './Layout';

interface ErrorProps {
  message: string | null;
  onClick: () => void;
}

export function Error({ message, onClick }: ErrorProps) {
  return (
    <Container color="red">
      <Content className="items-center gap-10">
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
              Please double check the format and size. It must be less than 10MB
              in size.
            </p>
            {message ? <p>Error: {message}</p> : null}
          </div>
        </div>
        <Button onClick={onClick}>Try again</Button>
      </Content>
    </Container>
  );
}
