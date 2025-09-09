import { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router';
import DibbsLogo from '../../assets/dibbs-logo.svg';
import CdcLogo from '../../assets/cdc-logo.svg';

import NavigationBar from '../NavigationBar';
import { getUser } from '../../api/user/user.ts';
import type { GetUser200 } from '../../api/schemas';
import { Icon } from '@trussworks/react-uswds';

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
  const [currentUser, setCurrentUser] = useState<GetUser200>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    getUser()
      .then((response) => {
        setCurrentUser(response.data);
      })
      .catch((err) => {
        console.error('Failed to load user', err);
      });
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

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

        {/* User dropdown */}
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setMenuOpen((prev) => !prev)}
            className="font-public-sans hover:bg-blue-cool-70 flex items-center gap-2 rounded px-3 py-2 text-white focus:outline-none"
          >
            <Icon.Person size={3} aria-hidden />
            {currentUser ? currentUser.username : 'Loading...'}
          </button>

          {menuOpen && (
            <div className="ring-opacity-5 absolute right-0 mt-2 w-40 overflow-hidden rounded-md bg-white shadow-lg ring-1 ring-black">
              <a
                href="/api/logout"
                className="font-public-sans block w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              >
                Logout
              </a>
            </div>
          )}
        </div>
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
