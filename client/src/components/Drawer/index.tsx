import React, { useEffect, useState } from 'react';
import FocusTrap from 'focus-trap-react';
import { Icon } from '@trussworks/react-uswds';

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
      <section>
        <button
          className=""
          onClick={handleClose}
          aria-label="Close drawer"
          data-testid={'close-drawer'}
        >
          <Icon.Close size={3} aria-label="X icon indicating closure" />
        </button>
      </section>
    </FocusTrap>
  );
};

export default Drawer;
