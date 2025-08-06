import { Link } from 'react-router';
import DibbsLogo from '../../assets/dibbs-logo.svg';
import CdcLogo from '../../assets/cdc-logo.svg';

import NavigationBar from '../NavigationBar';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <a className="usa-skipnav" href="#main-content">
        Skip to main content
      </a>
      <Header />
      <main
        id="main-content"
        className="bg-primary-container flex grow flex-col"
      >
        {children}
      </main>
      <Footer />
    </div>
  );
}

export function Header() {
  return (
    <header>
      <div className="bg-blue-cool-80 flex flex-col items-start justify-between gap-4 px-2 py-4 sm:flex-row sm:items-center xl:px-20">
        <Link to="/">
          <h1 className="flex items-center gap-3">
            <img src={DibbsLogo} alt="DIBBs" />
            <span className="font-merriweather text-2xl text-white">
              eCR Refiner
            </span>
          </h1>
        </Link>

        <NavigationBar />
        <a
          className="text-white hover:cursor-pointer hover:underline"
          href="/api/logout"
        >
          Logout
        </a>
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
            className="inline-block"
          >
            <img src={CdcLogo} alt="" />
            <span className="sr-only">
              CDC - U.S. Centers for Disease Control and Prevention
            </span>
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
