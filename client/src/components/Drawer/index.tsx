/**
 * Drawer: Sidebar overlay component used to display grouped content in a modal-like drawer with search and close functionality.
 * Designed for accessibility, keyboard navigation, and seamless integration with dialog workflows.
 * Handles focus trapping and supports variable width, subtitle, and search filtering for child content.
 */
import React, { useCallback, useEffect, useState } from 'react';
import FocusTrap from 'focus-trap-react';
import { Icon } from '@trussworks/react-uswds';
import classNames from 'classnames';
import { Search } from '../Search';
import { Title } from '../Title';

type DrawerProps = {
  title: string | React.ReactNode;
  subtitle?: string | React.ReactNode;
  searchPlaceholder: string;
  children: React.ReactNode;
  isOpen: boolean;
  // onSave: () => void;
  onClose: () => void;
  onSearch?: (filter: string) => void;
  drawerWidth?: '35%' | '60%';
};

/**
 * Drawer component used as a sidebar overlay for displaying grouped content.
 * Supports a title, subtitle, search filter, and custom children.
 *
 * @param {string | React.ReactNode} title - The drawer's title.
 * @param {string | React.ReactNode} subtitle - Optional drawer subtitle.
 * @param {string} placeHolder - The placeholder for the search field.
 * @param {React.ReactNode} children - Contents of the drawer.
 * @param {boolean} isOpen - If true, drawer is visible.
 * @param {() => void} onClose - Callback to close the drawer.
 * @param {(filter: string) => void} [onSearch] - Optional callback for search events.
 * @param {'35%' | '60%'} [drawerWidth] - Drawer width.
 */
const Drawer = ({
  title,
  subtitle,
  searchPlaceholder,
  children,
  isOpen,
  // onSave,
  onClose,
  onSearch,
  drawerWidth,
}: DrawerProps): React.ReactElement<DrawerProps> => {
  const [searchFilter, setSearchFilter] = useState('');

  useEffect(() => {
    if (onSearch) {
      onSearch(searchFilter);
    }
  }, [onSearch, searchFilter]);

  /**
   * @description Closes the drawer
   */
  const handleClose = useCallback(() => {
    setSearchFilter('');
    onClose();
  }, [onClose]);

  useEffect(() => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const handleEscape = (e: KeyboardEvent) => {
      e = e || window.event;
      if (isOpen && (e.key === 'Escape' || e.key === 'Esc')) {
        handleClose();
      }
      window.addEventListener('keyup', handleEscape);
      return () => {
        window.removeEventListener('keyup', handleEscape);
      };
    };
  }, [handleClose, isOpen]);

  return (
    <FocusTrap
      active={isOpen}
      focusTrapOptions={{
        onDeactivate: handleClose,
        escapeDeactivates: true,
      }}
    >
      <div>
        <div
          className={classNames(
            'bg-gray-3 fixed top-0 z-[1050] flex h-full shrink-0 flex-col items-start gap-6 border-l border-solid border-gray-400 p-0 shadow-2xl transition-all duration-300 ease-linear',
            isOpen ? 'right-0 opacity-100' : 'right-[-60%] opacity-0',
            drawerWidth === '60%' ? 'w-[60%]' : 'w-[35%]'
          )}
          role="dialog"
          id="drawer-container"
          aria-label="drawer-container"
        >
          <div className="w-full overflow-y-scroll p-8">
            <div className="max-w-[95%]">
              <button
                className="absolute top-6 right-4 flex shrink-0 cursor-pointer items-center justify-center border-none bg-none p-0"
                onClick={handleClose}
                aria-label="Close drawer"
                data-testid={'close-drawer'}
              >
                <Icon.Close size={3} aria-label="X icon indicating closure" />
              </button>
              <section className="p-4">
                <Title>{title}</Title>
                {subtitle ? (
                  <div className="m-0 !py-4 text-gray-600">{subtitle}</div>
                ) : (
                  <></>
                )}
                {onSearch && (
                  <>
                    <Search
                      onChange={(e) => {
                        e.preventDefault();
                        setSearchFilter(e.target.value);
                      }}
                      id="code-set-search"
                      name="code-set-search"
                      type="search"
                      value={searchFilter}
                      placeholder={searchPlaceholder}
                    />
                  </>
                )}
              </section>
            </div>

            <div className="flex flex-col pt-4">{children}</div>
          </div>
        </div>

        {isOpen && (
          <div
            className="fixed top-0 left-0 z-[1040] h-full w-full"
            onClick={handleClose}
          ></div>
        )}
      </div>
    </FocusTrap>
  );
};

export default Drawer;
