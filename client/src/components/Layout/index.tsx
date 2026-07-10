import { Link } from 'react-router';
import DibbsLogo from '../../assets/dibbs-logo.svg';
import CdcLogo from '../../assets/cdc-logo.svg';
import { NavigationBar } from '../NavigationBar';
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
          <PersonIcon />
          {displayName}
        </MenuButton>
        <MenuItems
          anchor="bottom"
          className="ring-opacity-5 absolute right-0 mt-0.5 flex w-40 origin-top-right flex-col gap-2 rounded-md bg-white shadow-lg focus-within:outline-none!"
        >
          <MenuItem>
            <Link
              className="hover:bg-gray-cool-1 data-focus:outline-blue-40v block p-3 hover:outline-none! data-focus:rounded-md data-focus:outline-4 data-focus:-outline-offset-4"
              to="/app-updates"
            >
              App updates
            </Link>
          </MenuItem>
          <MenuItem>
            <Link
              className="hover:bg-gray-cool-1 data-focus:outline-blue-40v block p-3 hover:outline-none! data-focus:rounded-md data-focus:outline-4 data-focus:-outline-offset-4"
              to="/tes-updates"
            >
              TES updates
            </Link>
          </MenuItem>
          <MenuItem>
            <a
              className="hover:bg-gray-cool-1 data-focus:outline-blue-40v block p-3 hover:outline-none! data-focus:rounded-md data-focus:outline-4 data-focus:-outline-offset-4"
              href="/api/logout"
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
            To report issues, request support, or submit feedback or questions,
            please reach out via the{' '}
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

function PersonIcon() {
  return (
    <svg
      aria-hidden
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="currentColor"
    >
      <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
    </svg>
  );
}
