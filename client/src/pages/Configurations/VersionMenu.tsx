import { MenuButton, MenuItems, MenuItem, Menu } from '@headlessui/react';
import { Icon } from '@trussworks/react-uswds';
import { Link } from 'react-router';
import {
  GetConfigurationsResponseStatus,
  GetConfigurationResponseVersion,
} from '../../api/schemas';

interface VersionMenuProps {
  id: string;
  currentVersion: number;
  status: GetConfigurationsResponseStatus;
  versions: GetConfigurationResponseVersion[];
  step: 'build' | 'test' | 'activate';
}

export function VersionMenu({
  currentVersion,
  status,
  versions,
  step,
}: VersionMenuProps) {
  return (
    <Menu as="div" className="z-10">
      <MenuButton>
        <div className="cursor-pointer">
          {status === 'draft' ? 'Editing' : 'Viewing'}: Version {currentVersion}
          <Icon.ArrowDropDown aria-hidden />
        </div>
      </MenuButton>
      <MenuItems className="absolute flex flex-col rounded-lg">
        {versions.map((v) => (
          <MenuItem key={v.id}>
            <Link
              className="hover:bg-gray-10 cursor-pointer bg-white p-4 font-bold"
              to={`/configurations/${v.id}/${step}`}
            >
              Version {v.version}
            </Link>
          </MenuItem>
        ))}
      </MenuItems>
    </Menu>
  );
}
