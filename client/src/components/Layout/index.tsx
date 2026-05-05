import { Link } from 'react-router';
import DibbsLogo from '../../assets/dibbs-logo.svg';
import CdcLogo from '../../assets/cdc-logo.svg';
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
          className="ring-opacity-5 absolute right-0 mt-0.5 w-40 origin-top-right rounded-md bg-white shadow-lg"
        >
          <MenuItem>
            <Link
              to="/app-updates"
              className="border-gray-cool-40! block w-full rounded-md border px-4 py-2 text-sm text-gray-700 data-focus:bg-gray-300 data-focus:text-gray-900"
            >
              App updates
            </Link>
          </MenuItem>
          <MenuItem>
            <a
              href="/api/logout"
              className="border-gray-cool-40! block w-full rounded-md border px-4 py-2 text-sm text-gray-700 data-focus:bg-gray-300 data-focus:text-gray-900"
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

function generateVersionInformation() {
  const commitHash = import.meta.env.VITE_GIT_HASH?.slice(0, 7);
  const versionTag = import.meta.env.VITE_APP_VERSION;

  const versionInformation = [];

  if (versionTag !== 'main' && versionTag) {
    versionInformation.push(versionTag);
  }
  if (commitHash) {
    versionInformation.push(commitHash);
  }
  // fall back to local if both aren't available
  if (versionInformation.length === 0) {
    versionInformation.push('local');
  }

  return versionInformation.join(' | ');
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
        <div className="flex max-w-3/5 flex-col gap-2 lg:items-end">
          <p className="text-white">
            For feedback, recommendations, or questions, please reach out to the{' '}
            <ExternalLink
              className="link-dark-bg font-bold hover:underline"
              href="https://aphlinformatics.atlassian.net/servicedesk/customer/portal/23/group/75&sa=D&source=docs&ust=1774202313083225&usg=AOvVaw2YRGisxYOIbeiR156Pek2p"
            >
              APHL Service Desk{' '}
            </ExternalLink>{' '}
            using the “eCR Functionality / Enhancements" category
          </p>
          <p className="text-gray-cool-20 text-xs">
            Version code: {generateVersionInformation()}
          </p>
        </div>
      </div>
    </footer>
  );
}
