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
                  className="data-focus:bg-gray-10 block p-2"
                  to={`/configurations/${v.id}/${step}`}
                >
                  <div className="flex flex-col">
                    <span className="font-bold">Version {v.version}</span>
                    <MenuItemDetail
                      className="text-gray-50"
                      created_at={v.created_at}
                      last_activated_at={v.last_activated_at}
                      created_by={v.created_by}
                    />
                  </div>
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

type MenuItemDetailProps = Pick<
  GetConfigurationResponseVersion,
  'created_at' | 'last_activated_at' | 'created_by'
> & {
  className?: string;
};
function MenuItemDetail({
  created_at,
  last_activated_at,
  created_by,
  className,
}: MenuItemDetailProps) {
  if (last_activated_at) {
    return (
      <span className={className}>
        Last activated {new Date(last_activated_at).toLocaleString()} by{' '}
        {created_by}
      </span>
    );
  }

  return (
    <span className={className}>
      Draft created {new Date(created_at).toLocaleString()} by {created_by}
    </span>
  );
}
