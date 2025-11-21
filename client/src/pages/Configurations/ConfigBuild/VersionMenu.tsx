import { MenuButton, MenuItems, MenuItem, Menu } from '@headlessui/react';
import { Icon } from '@trussworks/react-uswds';
import { Link } from 'react-router';
import {
  GetConfigurationsResponseStatus,
  GetConfigurationResponseVersion,
} from '../../../api/schemas';
import { Fragment } from 'react';

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
    <>
      <Menu as="div" className="z-10">
        <MenuButton>
          <div className="cursor-pointer">
            <span className="font-bold">
              {status === 'draft' ? 'Editing' : 'Viewing'}: Version{' '}
              {currentVersion}
            </span>
            <Icon.ArrowDropDown aria-hidden />
          </div>
        </MenuButton>
        <MenuItems className="absolute mt-1 ml-4 flex flex-col rounded-lg bg-white px-4 py-2 shadow-lg">
          {versions.map((v, i) => (
            <Fragment key={v.id}>
              <MenuItem>
                <Link
                  className="data-focus:bg-gray-10 block p-4 font-bold"
                  to={`/configurations/${v.id}/${step}`}
                >
                  Version {v.version}
                </Link>
              </MenuItem>
              {versions.length - 1 !== i && (
                <div
                  aria-hidden
                  key={`${v.id}-divider`}
                  className="bg-gray-cool-10 my-1 h-px"
                ></div>
              )}
            </Fragment>
          ))}
        </MenuItems>
      </Menu>
      <div
        aria-hidden
        className="border-gray-cool-20 mx-1 hidden h-10 border-l md:block"
      ></div>
    </>
  );
}
