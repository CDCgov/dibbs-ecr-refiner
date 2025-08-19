import React, { useEffect, useState } from 'react';
import FocusTrap from 'focus-trap-react';
import { Icon } from '@trussworks/react-uswds';
import classNames from 'classnames';
import { Search } from '../Search';

type DrawerProps = {
  title: string | React.ReactNode;
  subtitle?: string;
  placeHolder: string;
  toRender: React.ReactNode;
  isOpen: boolean;
  onSave: () => void;
  onClose: () => void;
  onSearch?: (filter: string) => void;
  drawerWidth?: '35%' | '60%';
};

const ConditionItem = () => {
  return (
    <div className="">
      <span>Condition code set</span>
      <span>State</span>
    </div>
  );
};

const Drawer = ({
  title,
  subtitle,
  placeHolder,
  toRender,
  isOpen,
  onSave,
  onClose,
  onSearch,
  drawerWidth,
}: DrawerProps) => {
  const [searchFilter, setSearchFilter] = useState('');

  useEffect(() => {
    if (onSearch) {
      onSearch(searchFilter);
    }
  }, [searchFilter]);

  /**
   * @description Closes the drawer
   */
  function handleClose() {
    setSearchFilter('');
    onClose();
  }

  useEffect(() => {
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
  }, []);

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
            'bg-gray-3 fixed top-0 z-[1050] flex h-full shrink-0 flex-col items-start gap-6 border-l border-solid border-gray-400 p-0 transition duration-300 ease-in-out',
            isOpen ? 'right-0 flex' : 'right-[-60%]',
            drawerWidth === '60%' ? 'w-[60%]' : 'w-[35%]'
          )}
          role="dialog"
          id="drawer-container"
          aria-label="drawer-container"
        >
          {isOpen ? (
            <div className="w-full p-8">
              <div className="max-w-[95%]">
                <button
                  className="absolute top-6 right-4 flex shrink-0 cursor-pointer items-center justify-center border-none bg-none p-0"
                  onClick={handleClose}
                  aria-label="Close drawer"
                  data-testid={'close-drawer'}
                >
                  <Icon.Close size={3} aria-label="X icon indicating closure" />
                </button>
                <h2
                  id="drawer-title"
                  data-testid={`drawer-title`}
                  className={classNames('m-0', subtitle ? 'pb-0' : 'pb-2')}
                >
                  {title}
                </h2>
                {subtitle ? (
                  <h3 className="m-0 flex py-4 text-gray-600">{subtitle}</h3>
                ) : (
                  <></>
                )}

                {onSearch && (
                  <div>
                    <Search
                      onChange={(e) => {
                        e.preventDefault();
                        setSearchFilter(e.target.value);
                      }}
                      id="code-search"
                      name="code-search"
                      type="search"
                      value={searchFilter}
                      placeholder={placeHolder}
                    />
                  </div>
                )}
              </div>

              <div className="">{toRender}</div>
            </div>
          ) : (
            <div className="hidden"></div>
          )}
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
