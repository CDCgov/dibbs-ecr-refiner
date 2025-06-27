import { Link } from 'react-router';
import DibbsLogo from '../../assets/dibbs-logo.svg';
import CdcLogo from '../../assets/cdc-logo.svg';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="bg-primary-container flex grow flex-col">
        {children}
      </main>
      <Footer />
    </div>
  );
}

export function Header() {
  return (
    <header>
      <div className="bg-blue-cool-80 flex items-center justify-between px-2 py-4 xl:px-20">
        <Link to="/">
          <h1 className="flex items-center gap-3">
            <img src={DibbsLogo} alt="DIBBs" />
            <span className="font-merriweather text-2xl text-white">
              eCR Refiner
            </span>
          </h1>
        </Link>
        <nav className='flex flex-row min-w-[632px] place-content-end font-public-sans text-lg text-white text-center'>
          <span className='inline-block border-b-3 mx-6 py-1'>
            <Link to="/filter-library">
              Filter library
            </Link>
          </span>
          <span className='inline-block mx-6 py-1'>
            <Link to="/filter-testing">
              Filters testing
            </Link>
          </span>
          <span className='inline-block mx-6 py-1'>
            <Link to="/conditions">
              Conditions
            </Link>
          </span>
        </nav>
      </div>
    </header>
  );
}

export function Footer() {
  return (
    <footer>
      <div className="bg-blue-cool-80 flex flex-col items-center justify-between gap-5 px-20 py-5 md:flex-row">
        <div>
          <a
            href="https://www.cdc.gov"
            target="_blank"
            rel="noreferrer noopener"
          >
            <img src={CdcLogo} alt="" />
          </a>
        </div>
        <div>
          <p className="text-white">
            For more information about this solution, send us an email at{' '}
            <a
              className="font-bold hover:underline"
              href="mailto:dibbs@cdc.gov"
            >
              dibbs@cdc.gov
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
}
