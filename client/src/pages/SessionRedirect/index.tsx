import { Icon } from '@trussworks/react-uswds';
import { Footer, Header } from '../../components/Layout';
import { Button } from '../../components/Button';

interface SessionRedirectProps {
  displayHeaderAndFooter?: boolean;
}
export function SessionRedirect({
  displayHeaderAndFooter = false,
}: SessionRedirectProps) {
  return (
    <div>
      {displayHeaderAndFooter && <Header />}

      <main>
        <div className="flex h-screen items-center justify-center bg-gray-200">
          <div className="mx-auto flex max-w-160 flex-col items-center">
            <Icon.Home
              aria-label="Home icon indicating a need to return to homepage to login again"
              className="text-gray-cool-50 h-30! w-30!"
            ></Icon.Home>
            <h1 className="text-center">
              Your session has ended. <br />
              Please log back in to access the app.
            </h1>
            <Button to="/" className="w-50!">
              Return to home page
            </Button>
          </div>
        </div>
      </main>
      {displayHeaderAndFooter && <Footer />}
    </div>
  );
}
