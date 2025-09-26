import { Link } from 'react-router';
import DibbsLogo from '../../assets/dibbs-logo.svg';
import CdcLogo from '../../assets/cdc-logo.svg';

import NavigationBar from '../NavigationBar';
import { Icon } from '@trussworks/react-uswds';
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react';

interface LayoutProps {
  children: React.ReactNode;
  username: string;
}

export function Layout({ username, children }: LayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <a className="usa-skipnav" href="#main-content">
        Skip to main content
      </a>
      <Header username={username} />
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
  username?: string;
}

export function Header({ username }: HeaderProps) {
  const loggedInHeaderContent = (
    <>
      <NavigationBar />
      <Menu>
        <MenuButton className="font-public-sans hover:bg-blue-cool-70 flex cursor-pointer items-center gap-2 rounded px-3 py-2 text-white focus:outline-none">
          <Icon.Person size={3} aria-hidden />
          {username}
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
      <div className="bg-blue-cool-80 flex flex-col items-start justify-between gap-4 px-2 py-4 sm:flex-row sm:items-center xl:px-20">
        <Link to="/">
          <h1 className="flex items-center gap-3">
            <img src={DibbsLogo} alt="DIBBs" />
            <span className="font-merriweather text-2xl text-white">
              eCR Refiner
            </span>
          </h1>
        </Link>

        {username ? loggedInHeaderContent : <></>}
      </div>
    </header>
  );
}

export function Footer() {
  return (
    <footer>
      <div className="bg-blue-cool-80 flex flex-col items-center justify-between gap-5 px-5 py-5 md:flex-row md:px-20">
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
        <div className="flex flex-col gap-2 lg:items-end lg:gap-1">
          <p className="text-white">
            For more information about this solution, send us an email at{' '}
            <a
              className="font-bold hover:underline"
              href="mailto:dibbs@cdc.gov"
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
