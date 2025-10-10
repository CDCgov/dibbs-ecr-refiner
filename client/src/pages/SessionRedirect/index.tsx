import { Icon } from '@trussworks/react-uswds';
import classNames from 'classnames';
import { Link } from 'react-router';
import { PRIMARY_BUTTON_STYLES } from '../../components/Button';
import { Footer, Header } from '../../components/Layout';

export default function SessionRedirect() {
  return (
    <div>
      <Header />

      <main>
        <div className="flex h-screen items-center justify-center bg-gray-200">
          <div className="mx-auto flex max-w-[40rem] flex-col items-center">
            <Icon.Home className="text-gray-cool-50 !h-[120px] !w-[120px]"></Icon.Home>
            <h1 className="text-center">
              Your session has ended. <br />
              Please log back in to access the app.
            </h1>
            <Link
              to="/"
              className={classNames(
                PRIMARY_BUTTON_STYLES,
                'usa-button !w-[12.5rem]'
              )}
            >
              Return to home page
            </Link>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
