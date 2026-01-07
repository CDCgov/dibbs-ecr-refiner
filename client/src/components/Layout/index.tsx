import { Link } from 'react-router';
import DibbsLogo from '../../assets/dibbs-logo.svg';
import CdcLogo from '../../assets/cdc-logo.svg';
import { ProvideFeedbackButton } from '../ProvideFeedbackButton';
import { NavigationBar } from '../NavigationBar';
import { Icon } from '@trussworks/react-uswds';
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react';
import { ExternalLink } from '../ExternalLink';

interface LayoutProps {
  children: React.ReactNode;
  displayName: string;
}

export function Layout({ displayName, children }: LayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <a className="usa-skipnav" href="#main-content">
        Skip to main content
      </a>
      <Header displayName={displayName} />
      <main
        id="main-content"
        className="bg-primary-container flex grow flex-col"
      >
        {children}
      </main>
      <ProvideFeedbackButton />
      <Footer />
    </div>
  );
}

interface HeaderProps {
  displayName?: string;
}

export function Header({ displayName }: HeaderProps) {
  const loggedInHeaderContent = (
    <>
      <NavigationBar />
      <Menu>
        <MenuButton
          aria-label="Open settings menu"
          className="font-public-sans hover:bg-blue-cool-70 flex cursor-pointer items-center gap-2 rounded px-3 py-2 text-white focus:outline-none"
        >
          <Icon.Person size={3} aria-hidden />
          {displayName}
        </MenuButton>
        <MenuItems
          anchor="bottom"
          className="ring-opacity-5 absolute right-0 mt-2 w-40 origin-top-right rounded-md bg-white shadow-lg focus:outline-none"
        >
          <MenuItem>
            <a
              href="/api/logout"
              className="!border-gray-cool-40 block w-full rounded-md border px-4 py-2 text-sm text-gray-700 data-[focus]:bg-gray-100 data-[focus]:text-gray-900"
            >
              Log out
            </a>
          </MenuItem>
        </MenuItems>
      </Menu>
    </>
  );

  return (
    <header>
      <div className="bg-blue-cool-80 flex flex-col items-start justify-between gap-4 px-2 sm:flex-row sm:items-center xl:px-20">
        <Link to="/" aria-label="Link back to the home configurations page">
          <div className="my-4 flex items-center gap-3">
            <img src={DibbsLogo} alt="DIBBs" role="presentation" />
            <span className="font-merriweather text-2xl text-white">
              eCR Refiner
            </span>
          </div>
        </Link>

        {displayName && loggedInHeaderContent}
      </div>
    </header>
  );
}

export function Footer() {
  return (
    <footer>
      <div className="bg-blue-cool-80 flex flex-col items-center justify-between gap-5 px-5 py-5 md:flex-row md:px-20">
        <div>
          <ExternalLink
            href="https://www.cdc.gov"
            className="inline-block"
            includeIcon={false}
          >
            <img src={CdcLogo} alt="" />
            <span className="sr-only">
              CDC - U.S. Centers for Disease Control and Prevention
            </span>
          </ExternalLink>
        </div>
        <div className="flex flex-col gap-2 lg:items-end lg:gap-1">
          <p className="text-white">
            For more information about this solution, send us an email at{' '}
            <a
              className="font-bold hover:underline"
              href="mailto:dibbs@cdc.gov"
              aria-label="Email us at dibbs@cdc.gov (will open your email client)"
            >
              dibbs@cdc.gov
            </a>
          </p>
          <p className="text-gray-cool-20 text-xs">
            Version code: {import.meta.env.VITE_GIT_HASH ?? 'local'}
          </p>
        </div>
      </div>
    </footer>
  );
}
