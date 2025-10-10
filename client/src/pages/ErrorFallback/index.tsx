import { AxiosError } from 'axios';
import SessionRedirect from '../SessionRedirect';

interface ErrorFallbackProps {
  error: AxiosError<unknown, unknown> | null;
}

export default function ErrorFallback({ error }: ErrorFallbackProps) {
  if (error?.status === 401) {
    // we're within the React Route with a pre-rendered header / footer already,
    // so no need to display an extra header / footer
    return <SessionRedirect displayHeaderAndFooter={false} />;
  }

  return `Error!`;
}
