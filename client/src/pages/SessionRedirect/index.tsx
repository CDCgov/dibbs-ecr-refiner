import { Footer, Header } from '@components/Layout';
import { Button } from '@components/Button';

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
            <HomeIcon />
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

function HomeIcon() {
  return (
    <svg
      aria-hidden
      xmlns="http://www.w3.org/2000/svg"
      width="120"
      height="120"
      viewBox="0 0 24 24"
      className="fill-gray-cool-50"
    >
      <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z" />
    </svg>
  );
}
